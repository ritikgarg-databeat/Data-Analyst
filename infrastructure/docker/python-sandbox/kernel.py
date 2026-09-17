"""The actual code-execution engine for the Python Lab sandbox.

Deliberately self-contained: stdlib + the pinned data-science stack only, no
dependency on the rest of the FastAPI app (apps/api never imports this
module directly — only `server.py`, running *inside* the sandbox container,
does). Kept import-free of `app.*` so this file can be copied into the
sandbox Docker image on its own and, for testing, imported directly by
apps/api/tests/test_python_kernel.py against a real pandas/numpy/etc
(installed there via the `sandbox` extra) without needing Docker at all.

`PythonKernel` holds one persistent namespace (`self.globals`) across many
`execute()` calls — that's what gives "cells" their notebook-like behavior
(a variable assigned in one call is visible in the next). A fresh
`PythonKernel()` (or `.restart()`) is a full reset.

This module has NO knowledge of the outer isolation boundary (the container,
its resource limits, its network policy) — that's `server.py` and the
Docker container config's job. This module's own job is purely: run code,
capture what a notebook cell would show, and never let a single execution
corrupt state so badly the kernel can't keep going.
"""

from __future__ import annotations

import ast
import base64
import contextlib
import io
import math
import signal
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

MAX_OUTPUT_CHARS = 20_000
# Matches the SQL Lab's row_limit=1000 convention (see app/core/config.py
# Settings.sql_lab_row_limit) — used both for the interactive DataFrame
# viewer (paginated client-side over these rows, like the SQL results grid)
# and, since it's the same execute() path, as the effective ceiling on how
# many rows exercise-grading comparisons can see. Not unbounded: a 1000-row
# cap is a deliberate, already-precedented tradeoff in this codebase.
MAX_DATAFRAME_PREVIEW_ROWS = 1000
MAX_REPR_CHARS = 2_000
DEFAULT_TIMEOUT_SECONDS = 10.0

_RESERVED_GLOBAL_NAMES = {"__name__", "__builtins__", "__doc__", "__package__", "__loader__", "__spec__"}


@dataclass
class KernelError:
    error_type: str
    message: str
    line: int | None
    traceback_text: str
    hint: str | None = None


@dataclass
class ChartOutput:
    kind: str  # "matplotlib" | "plotly"
    format: str  # "png_base64" | "plotly_json"
    data: str
    title: str | None = None


@dataclass
class DataFrameSummary:
    row_count: int
    column_count: int
    columns: list[dict[str, Any]]  # [{name, dtype, null_count, unique_count}]
    preview_rows: list[list[Any]]
    preview_row_count: int
    truncated: bool
    memory_usage_bytes: int | None = None


@dataclass
class VariableSummary:
    name: str
    type_name: str
    preview: str
    dataframe: DataFrameSummary | None = None
    shape: list[int] | None = None
    # The actual JSON-safe value, populated only for plain scalars/lists/dicts
    # (int/float/str/bool/None and JSON-safe containers of those) — this is
    # what exercise grading compares with numeric tolerance; `preview` above
    # is a human-readable repr for display only and is never compared.
    value: Any | None = None


@dataclass
class ExecutionResult:
    status: str  # "success" | "error"
    stdout: str
    stdout_truncated: bool
    display_value: VariableSummary | None  # the auto-displayed trailing expression, if any
    variables: list[VariableSummary]  # every top-level variable currently in scope (post-execution)
    charts: list[ChartOutput]
    error: KernelError | None
    execution_time_ms: int


class KernelTimeoutError(Exception):
    pass


@contextlib.contextmanager
def _time_limit(seconds: float):
    """POSIX-only wall-clock interrupt (SIGALRM) — the sandbox container
    always runs Linux regardless of host OS, so this is safe to rely on
    there. Callers that need a cross-platform fallback (e.g. this file's own
    unit tests running directly on Windows) should catch the AttributeError
    from `signal.SIGALRM` not existing and fall back to a plain call with no
    interior interrupt (the outer test/orchestration layer's own timeout
    still applies)."""

    def _handler(signum: int, frame: Any) -> None:
        raise KernelTimeoutError(f"Execution exceeded the {seconds:.0f}s time limit and was interrupted.")

    has_alarm = hasattr(signal, "SIGALRM")
    if has_alarm:
        previous = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        if has_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def _safe_repr(value: Any, limit: int = MAX_REPR_CHARS) -> str:
    try:
        text = repr(value)
    except Exception as exc:  # a broken __repr__ shouldn't crash the kernel
        return f"<repr() failed: {exc}>"
    truncated, was_truncated = _truncate(text, limit)
    return truncated + ("…" if was_truncated else "")


class PythonKernel:
    def __init__(self, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds
        self.globals: dict[str, Any] = {}
        self._matplotlib_ready = False
        self._plotly_ready = False
        self._captured_charts: list[ChartOutput] = []
        self.restart()

    def restart(self) -> None:
        self.globals = {"__name__": "__main__", "__builtins__": __builtins__}
        self._matplotlib_ready = False
        self._plotly_ready = False

    def _ensure_matplotlib_agg(self) -> None:
        if self._matplotlib_ready:
            return
        try:
            import matplotlib

            matplotlib.use("Agg", force=True)
        except ImportError:
            pass
        self._matplotlib_ready = True

    def _patch_plotly_show(self) -> None:
        if self._plotly_ready:
            return
        try:
            import plotly.basedatatypes

            kernel = self

            def _captured_show(fig_self: Any, *args: Any, **kwargs: Any) -> None:
                kernel._captured_charts.append(
                    ChartOutput(
                        kind="plotly",
                        format="plotly_json",
                        data=fig_self.to_json(),
                        title=(fig_self.layout.title.text if fig_self.layout.title else None),
                    )
                )

            plotly.basedatatypes.BaseFigure.show = _captured_show
        except ImportError:
            pass
        self._plotly_ready = True

    def _capture_matplotlib_figures(self) -> list[ChartOutput]:
        charts: list[ChartOutput] = []
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return charts
        for num in plt.get_fignums():
            fig = plt.figure(num)
            buf = io.BytesIO()
            try:
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
                encoded = base64.b64encode(buf.getvalue()).decode("ascii")
                title = self._matplotlib_figure_title(fig)
                charts.append(ChartOutput(kind="matplotlib", format="png_base64", data=encoded, title=title))
            except Exception:  # noqa: S110 — a figure that fails to render just isn't captured
                pass
        plt.close("all")
        return charts

    @staticmethod
    def _matplotlib_figure_title(fig: Any) -> str | None:
        if fig._suptitle:
            return fig._suptitle.get_text()
        for ax in fig.axes:
            text = ax.get_title()
            if text:
                return text
        return None

    def _summarize_dataframe(self, df: Any) -> DataFrameSummary | None:
        try:
            import pandas as pd
        except ImportError:
            pd = None  # type: ignore[assignment]
        try:
            import polars as pl
        except ImportError:
            pl = None  # type: ignore[assignment]

        is_pandas = pd is not None and isinstance(df, pd.DataFrame)
        is_polars = pl is not None and isinstance(df, pl.DataFrame)
        if not is_pandas and not is_polars:
            return None

        if is_pandas:
            row_count, column_count = df.shape
            preview_df = df.head(MAX_DATAFRAME_PREVIEW_ROWS)
            columns = []
            for col in df.columns:
                series = df[col]
                columns.append(
                    {
                        "name": str(col),
                        "dtype": str(series.dtype),
                        "null_count": int(series.isna().sum()),
                        "unique_count": int(series.nunique(dropna=True)),
                    }
                )
            preview_rows = [
                [_json_safe(v) for v in row] for row in preview_df.itertuples(index=False, name=None)
            ]
            try:
                memory_usage = int(df.memory_usage(deep=True).sum())
            except Exception:  # noqa: S110
                memory_usage = None
            return DataFrameSummary(
                row_count=row_count,
                column_count=column_count,
                columns=columns,
                preview_rows=preview_rows,
                preview_row_count=len(preview_rows),
                truncated=row_count > MAX_DATAFRAME_PREVIEW_ROWS,
                memory_usage_bytes=memory_usage,
            )

        # Polars
        row_count, column_count = df.shape
        preview_df = df.head(MAX_DATAFRAME_PREVIEW_ROWS)
        columns = []
        for name, dtype in zip(df.columns, df.dtypes, strict=True):
            col = df[name]
            columns.append(
                {
                    "name": str(name),
                    "dtype": str(dtype),
                    "null_count": int(col.null_count()),
                    "unique_count": int(col.n_unique()),
                }
            )
        preview_rows = [[_json_safe(v) for v in row] for row in preview_df.iter_rows()]
        return DataFrameSummary(
            row_count=row_count,
            column_count=column_count,
            columns=columns,
            preview_rows=preview_rows,
            preview_row_count=len(preview_rows),
            truncated=row_count > MAX_DATAFRAME_PREVIEW_ROWS,
            memory_usage_bytes=df.estimated_size() if hasattr(df, "estimated_size") else None,
        )

    def _summarize_variable(self, name: str, value: Any) -> VariableSummary:
        dataframe = self._summarize_dataframe(value)
        type_name = type(value).__name__
        shape = None
        json_value = _plain_json_value(value)
        if dataframe is not None:
            shape = [dataframe.row_count, dataframe.column_count]
            preview = f"{dataframe.row_count:,} rows × {dataframe.column_count} columns"
        else:
            shape_attr = getattr(value, "shape", None)
            if isinstance(shape_attr, tuple):
                shape = list(shape_attr)
            preview = _safe_repr(value)
        return VariableSummary(
            name=name, type_name=type_name, preview=preview, dataframe=dataframe, shape=shape, value=json_value
        )

    def _visible_variables(self) -> dict[str, Any]:
        return {
            name: value
            for name, value in self.globals.items()
            if name not in _RESERVED_GLOBAL_NAMES
            and not name.startswith("_")
            and not isinstance(value, type(sys))  # exclude imported modules
        }

    def _format_error(self, exc: BaseException, source: str) -> KernelError:
        tb_list = traceback.extract_tb(exc.__traceback__)
        # Drop frames belonging to this kernel's own exec()/eval() call machinery —
        # only frames whose filename is our synthetic "<cell>" belong to the student.
        user_frames = [f for f in tb_list if f.filename == "<cell>"]
        line = user_frames[-1].lineno if user_frames else None
        traceback_text = "".join(traceback.format_list(user_frames)) + f"{type(exc).__name__}: {exc}"

        hint = None
        if isinstance(exc, KeyError) and len(exc.args) == 1:
            missing_key = exc.args[0]
            df_columns = self._nearest_dataframe_columns(missing_key)
            if df_columns is not None:
                hint = f"'{missing_key}' is not a column in that DataFrame. Available columns: {', '.join(df_columns)}"
        elif isinstance(exc, NameError):
            hint = "Check for a typo, or a variable defined in a cell that hasn't been run yet."
        elif isinstance(exc, ZeroDivisionError):
            hint = "Check whether a denominator can legitimately be zero (e.g. after a filter removes all rows)."

        return KernelError(
            error_type=type(exc).__name__,
            message=str(exc),
            line=line,
            traceback_text=traceback_text,
            hint=hint,
        )

    def _nearest_dataframe_columns(self, missing_key: Any) -> list[str] | None:
        """Best-effort, never fabricated: only returns real column names from a
        real DataFrame currently in scope whose columns do NOT include the
        missing key — used solely to make a KeyError's hint concrete."""
        for value in self._visible_variables().values():
            columns = getattr(value, "columns", None)
            if columns is None:
                continue
            try:
                names = [str(c) for c in columns]
            except Exception:  # noqa: S110
                continue
            if str(missing_key) not in names:
                return names
        return None

    def execute(self, code: str) -> ExecutionResult:
        self._ensure_matplotlib_agg()
        self._patch_plotly_show()
        self._captured_charts = []

        start = time.monotonic()
        stdout_buffer = io.StringIO()
        display_value: VariableSummary | None = None
        error: KernelError | None = None

        try:
            tree = ast.parse(code, filename="<cell>", mode="exec")
        except SyntaxError as exc:
            error = KernelError(
                error_type="SyntaxError",
                message=str(exc.msg),
                line=exc.lineno,
                traceback_text=f"SyntaxError: {exc.msg} (line {exc.lineno})",
                hint="Check for a missing colon, unmatched parenthesis/quote, or bad indentation.",
            )
            return ExecutionResult(
                status="error",
                stdout="",
                stdout_truncated=False,
                display_value=None,
                variables=self._current_variable_summaries(),
                charts=[],
                error=error,
                execution_time_ms=int((time.monotonic() - start) * 1000),
            )

        trailing_expr: ast.Expression | None = None
        body = tree.body
        if body and isinstance(body[-1], ast.Expr):
            trailing_expr = ast.Expression(body[-1].value)
            body = body[:-1]

        try:
            with _time_limit(self.timeout_seconds), contextlib.redirect_stdout(stdout_buffer):
                if body:
                    exec_code = compile(ast.Module(body=body, type_ignores=[]), "<cell>", "exec")
                    exec(exec_code, self.globals)  # noqa: S102 — this IS the sandboxed executor
                if trailing_expr is not None:
                    eval_code = compile(trailing_expr, "<cell>", "eval")
                    result = eval(eval_code, self.globals)  # noqa: S307
                    if result is not None:
                        display_value = self._summarize_variable("_", result)
                        self.globals["_"] = result
        except KernelTimeoutError as exc:
            error = KernelError(
                error_type="TimeoutError", message=str(exc), line=None, traceback_text=str(exc), hint=None
            )
        except BaseException as exc:  # noqa: BLE001 — student code can raise literally anything
            error = self._format_error(exc, code)

        charts = self._capture_matplotlib_figures() + self._captured_charts
        stdout_text, stdout_truncated = _truncate(stdout_buffer.getvalue(), MAX_OUTPUT_CHARS)

        return ExecutionResult(
            status="error" if error else "success",
            stdout=stdout_text,
            stdout_truncated=stdout_truncated,
            display_value=display_value,
            variables=self._current_variable_summaries(),
            charts=charts,
            error=error,
            execution_time_ms=int((time.monotonic() - start) * 1000),
        )

    def _current_variable_summaries(self) -> list[VariableSummary]:
        return [self._summarize_variable(name, value) for name, value in self._visible_variables().items()]

    def get_variable(self, name: str) -> Any:
        """Direct namespace access for exercise grading — never exposed over
        the wire to a client, only used server-side by the evaluator."""
        return self.globals.get(name)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        # A +inf/-inf cell (e.g. a division by zero in a DataFrame column —
        # ordinary, non-raising pandas behavior) must be stripped the same
        # way NaN already is: Python's json module (and this project's
        # installed Starlette/FastAPI JSONResponse, which renders with
        # allow_nan=False) rejects a raw inf value outright, crashing
        # response serialization for an otherwise successfully executed
        # cell or exercise submission — see _plain_json_value below, which
        # already handled this correctly.
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    try:
        import pandas as pd

        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if value is pd.NaT:
            return None
    except ImportError:
        pass
    from datetime import date, datetime, time as _time

    if isinstance(value, (datetime, date, _time)):
        return value.isoformat()
    return _safe_repr(value, limit=500)


def _plain_json_value(value: Any, *, _depth: int = 0) -> Any:
    """Unlike `_json_safe` (used for DataFrame cells, always returns
    *something* displayable), this returns None for anything that isn't
    genuinely a plain JSON scalar/list/dict — used to populate
    `VariableSummary.value`, which exercise grading treats as "the real
    value" and must never receive a repr string standing in for a value that
    couldn't actually be represented."""
    if _depth > 5:
        return None
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return _plain_json_value(value.item(), _depth=_depth + 1)
    except ImportError:
        pass
    if isinstance(value, (list, tuple)):
        return [_plain_json_value(v, _depth=_depth + 1) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain_json_value(v, _depth=_depth + 1) for k, v in value.items()}
    return None
