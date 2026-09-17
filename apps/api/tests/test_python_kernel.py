"""White-box tests of the actual sandbox execution engine
(infrastructure/docker/python-sandbox/kernel.py) — run directly, in-process,
against a real pandas/numpy/matplotlib/plotly (installed via this project's
`sandbox` extra: `uv sync --project apps/api --extra dev --extra sandbox`).

This deliberately does NOT go through Docker — it's a unit test of the
reusable execution/output-capture logic that the sandbox container's
server.py wraps, not a test of the container boundary itself (see
test_python_lab_security.py for what IS and isn't verified about that
boundary in this environment). Importing kernel.py this way is safe for
tests (trusted, developer-written code) even though production code
(app/python_lab/*) never imports it — only a running sandbox container's
own server.py does that, from a copy of this exact file baked into the
image (see infrastructure/docker/python-sandbox/Dockerfile)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

KERNEL_PATH = (
    Path(__file__).resolve().parents[3] / "infrastructure" / "docker" / "python-sandbox" / "kernel.py"
)
spec = importlib.util.spec_from_file_location("sandbox_kernel", KERNEL_PATH)
kernel_module = importlib.util.module_from_spec(spec)
sys.modules["sandbox_kernel"] = kernel_module
spec.loader.exec_module(kernel_module)

PythonKernel = kernel_module.PythonKernel


@pytest.fixture
def kernel():
    return PythonKernel(timeout_seconds=5.0)


def _var(result, name):
    return next((v for v in result.variables if v.name == name), None)


class TestBasicExecution:
    def test_simple_assignment_succeeds(self, kernel):
        result = kernel.execute("x = 1 + 2")
        assert result.status == "success"
        assert _var(result, "x").value == 3

    def test_variables_persist_across_calls(self, kernel):
        kernel.execute("x = 10")
        result = kernel.execute("y = x * 2")
        assert _var(result, "y").value == 20

    def test_trailing_bare_expression_auto_displays(self, kernel):
        kernel.execute("x = 5")
        result = kernel.execute("x + 1")
        assert result.display_value is not None
        assert result.display_value.value == 6

    def test_assignment_as_last_line_does_not_auto_display(self, kernel):
        result = kernel.execute("z = 99")
        assert result.display_value is None

    def test_print_is_captured_as_stdout(self, kernel):
        result = kernel.execute("print('hello', 42)")
        assert result.stdout == "hello 42\n"

    def test_restart_clears_all_state(self, kernel):
        kernel.execute("x = 1")
        kernel.restart()
        result = kernel.execute("x")
        assert result.status == "error"
        assert result.error.error_type == "NameError"


class TestErrorHandling:
    def test_name_error_is_reported_with_line_and_hint(self, kernel):
        result = kernel.execute("undefined_variable")
        assert result.status == "error"
        assert result.error.error_type == "NameError"
        assert result.error.line == 1
        assert result.error.hint

    def test_key_error_on_dataframe_reports_real_columns_never_fabricated(self, kernel):
        kernel.execute("import pandas as pd\ndf = pd.DataFrame({'a': [1], 'b': [2]})")
        result = kernel.execute("df['nope']")
        assert result.status == "error"
        assert result.error.error_type == "KeyError"
        assert "a" in result.error.hint
        assert "b" in result.error.hint
        assert "nope" not in result.error.hint.split("Available columns:")[1]

    def test_zero_division_error_has_a_hint(self, kernel):
        result = kernel.execute("1 / 0")
        assert result.status == "error"
        assert result.error.error_type == "ZeroDivisionError"
        assert result.error.hint

    def test_syntax_error_is_reported_without_crashing_the_kernel(self, kernel):
        result = kernel.execute("def broken(:")
        assert result.status == "error"
        assert result.error.error_type == "SyntaxError"
        # the kernel must still be usable after a syntax error
        followup = kernel.execute("x = 1")
        assert followup.status == "success"

    def test_a_runtime_error_does_not_lose_previously_defined_variables(self, kernel):
        kernel.execute("x = 42")
        kernel.execute("1 / 0")
        result = kernel.execute("x")
        assert result.display_value.value == 42

    def test_error_traceback_only_contains_user_code_frames(self, kernel):
        result = kernel.execute("raise ValueError('boom')")
        assert "kernel.py" not in result.error.traceback_text
        assert "boom" in result.error.traceback_text


class TestDataFrames:
    def test_pandas_dataframe_is_summarized_correctly(self, kernel):
        result = kernel.execute(
            "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})"
        )
        df_var = _var(result, "df")
        assert df_var.dataframe.row_count == 3
        assert df_var.dataframe.column_count == 2
        assert {c["name"] if isinstance(c, dict) else c.name for c in df_var.dataframe.columns} == {"a", "b"}
        assert df_var.dataframe.preview_rows == [[1, "x"], [2, "y"], [3, "z"]]

    def test_dataframe_null_counts_are_accurate(self, kernel):
        result = kernel.execute("import pandas as pd\ndf = pd.DataFrame({'a': [1, None, 3]})")
        df_var = _var(result, "df")
        col = df_var.dataframe.columns[0]
        null_count = col["null_count"] if isinstance(col, dict) else col.null_count
        assert null_count == 1

    def test_large_dataframe_preview_is_truncated_not_the_full_data(self, kernel):
        result = kernel.execute("import pandas as pd\ndf = pd.DataFrame({'a': range(5000)})")
        df_var = _var(result, "df")
        assert df_var.dataframe.row_count == 5000
        assert df_var.dataframe.truncated is True
        assert len(df_var.dataframe.preview_rows) <= 1000

    def test_polars_dataframe_is_also_summarized(self, kernel):
        result = kernel.execute("import polars as pl\ndf = pl.DataFrame({'a': [1, 2], 'b': [3, 4]})")
        df_var = _var(result, "df")
        assert df_var.dataframe is not None
        assert df_var.dataframe.row_count == 2
        assert df_var.dataframe.column_count == 2

    def test_dataframe_head_as_trailing_expression_auto_displays_as_a_dataframe(self, kernel):
        kernel.execute("import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})")
        result = kernel.execute("df.head()")
        assert result.display_value.dataframe is not None
        assert result.display_value.dataframe.row_count == 3

    def test_a_division_by_zero_infinity_cell_is_json_safe_not_a_raw_float(self, kernel):
        """Regression test: `_json_safe` stripped NaN but not Infinity, so a
        real (non-raising) pandas division-by-zero column produced a raw
        Python `inf` in `preview_rows` — later crashing FastAPI/Starlette's
        JSONResponse serialization (`allow_nan=False` in this project),
        turning a fully correct, successfully executed cell into a generic
        500 instead of showing its real output."""
        result = kernel.execute(
            "import pandas as pd\n"
            "df = pd.DataFrame({'a': [10.0, 5.0], 'b': [1.0, 0.0]})\n"
            "df['ratio'] = df['a'] / df['b']"
        )
        df_var = _var(result, "df")
        ratio_values = [row[-1] for row in df_var.dataframe.preview_rows]
        assert ratio_values == [10.0, None]  # inf -> None, never a raw float('inf')

        import json

        json.dumps(df_var.dataframe.preview_rows, allow_nan=False)  # must not raise


class TestCharts:
    def test_matplotlib_figure_is_captured_as_base64_png(self, kernel):
        result = kernel.execute(
            "import matplotlib.pyplot as plt\nplt.plot([1, 2, 3], [4, 5, 6])\nplt.title('trend')"
        )
        assert result.status == "success"
        assert len(result.charts) == 1
        assert result.charts[0].kind == "matplotlib"
        assert result.charts[0].format == "png_base64"
        assert result.charts[0].title == "trend"
        assert len(result.charts[0].data) > 100  # a real image, not an empty stub

    def test_matplotlib_figures_are_closed_after_capture_not_leaked_across_cells(self, kernel):
        kernel.execute("import matplotlib.pyplot as plt\nplt.plot([1, 2])")
        result = kernel.execute("x = 1")  # a cell with no new figure
        assert result.charts == []

    def test_plotly_figure_show_is_captured_not_attempted_to_render(self, kernel):
        result = kernel.execute(
            "import plotly.express as px\nfig = px.scatter(x=[1, 2], y=[3, 4])\nfig.show()"
        )
        assert result.status == "success"
        assert len(result.charts) == 1
        assert result.charts[0].kind == "plotly"
        assert result.charts[0].format == "plotly_json"
        assert "scatter" in result.charts[0].data


class TestOutputLimits:
    def test_very_long_stdout_is_truncated(self, kernel):
        result = kernel.execute("print('x' * 50000)")
        assert result.stdout_truncated is True
        assert len(result.stdout) <= kernel_module.MAX_OUTPUT_CHARS

    def test_a_broken_repr_does_not_crash_variable_summarization(self, kernel):
        result = kernel.execute(
            "class Bad:\n    def __repr__(self):\n        raise RuntimeError('nope')\nb = Bad()"
        )
        assert result.status == "success"
        b_var = _var(result, "b")
        assert b_var is not None
        assert "repr" in b_var.preview.lower() or "failed" in b_var.preview.lower()


class TestScientificStack:
    def test_numpy_arrays_work(self, kernel):
        result = kernel.execute("import numpy as np\narr = np.array([1, 2, 3])\ntotal = int(arr.sum())")
        assert result.status == "success"
        assert _var(result, "total").value == 6

    def test_scipy_stats_works(self, kernel):
        result = kernel.execute("from scipy import stats\nr = stats.norm.cdf(0.0)")
        assert result.status == "success"
        assert _var(result, "r").value == pytest.approx(0.5, abs=1e-6)

    def test_statsmodels_ols_works(self, kernel):
        result = kernel.execute(
            "import statsmodels.api as sm\nimport numpy as np\n"
            "x = sm.add_constant(np.arange(10))\ny = np.arange(10) * 2.0\n"
            "model = sm.OLS(y, x).fit()\nslope = float(model.params[1])"
        )
        assert result.status == "success"
        assert _var(result, "slope").value == pytest.approx(2.0, abs=1e-6)

    def test_sklearn_train_test_split_and_linear_regression_work(self, kernel):
        result = kernel.execute(
            "from sklearn.linear_model import LinearRegression\nimport numpy as np\n"
            "X = np.arange(20).reshape(-1, 1)\ny = (np.arange(20) * 3 + 1).astype(float)\n"
            "model = LinearRegression().fit(X, y)\ncoef = float(model.coef_[0])"
        )
        assert result.status == "success"
        assert _var(result, "coef").value == pytest.approx(3.0, abs=1e-6)

    def test_pyarrow_is_importable_and_interops_with_pandas(self, kernel):
        result = kernel.execute(
            "import pyarrow as pa\nimport pandas as pd\n"
            "table = pa.table({'a': [1, 2, 3]})\ndf = table.to_pandas()\nn = len(df)"
        )
        assert result.status == "success"
        assert _var(result, "n").value == 3
