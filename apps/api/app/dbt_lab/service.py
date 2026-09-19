"""DB-aware orchestration layer between the dbt Lab router and the real
`dbt` CLI — mirrors app/sql/service.py's shape: one service class routers
depend on via DI, the actual execution/parsing isolated behind it, each real
invocation logged to history (DbtRun)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError, NotFoundError
from app.dbt_lab import artifacts
from app.dbt_lab.paths import DBT_PROJECT_DIR, resolve_target_dir
from app.dbt_lab.runner import DbtCliResult, DbtRunnerError, run_dbt
from app.models.dbt import DbtRun
from app.models.enums import DbtCommand, DbtRunStatus

_COMMAND_ARGS: dict[DbtCommand, list[str]] = {
    DbtCommand.RUN: ["run"],
    DbtCommand.TEST: ["test"],
    DbtCommand.BUILD: ["build"],
    DbtCommand.COMPILE: ["compile"],
    DbtCommand.DOCS_GENERATE: ["docs", "generate"],
}

# `docs generate` doesn't take a --select the same way the others do, so a
# selector is silently ignored for it rather than passed through.
_SELECTABLE_COMMANDS = {DbtCommand.RUN, DbtCommand.TEST, DbtCommand.BUILD, DbtCommand.COMPILE}
_USER_LOCKS: dict[str, Lock] = {}

_PROJECT_TREE_DIRS: list[tuple[str, str]] = [
    ("staging", "models/staging"),
    ("intermediate", "models/intermediate"),
    ("marts", "models/marts"),
    ("seeds", "seeds"),
    ("snapshots", "snapshots"),
    ("macros", "macros"),
    ("tests", "tests"),
    ("analyses", "analyses"),
]


@dataclass
class ProjectTreeItem:
    category: str
    name: str
    relative_path: str


class DbtLabService:
    def __init__(self, db: Session, settings: Settings | None = None, user_id: str | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.user_id = user_id
        self.target_dir = resolve_target_dir(user_id)

    # --- Execution -----------------------------------------------------

    def execute(self, *, user_id: str, command: DbtCommand, selector: str | None = None) -> DbtRun:
        """Runs a real `dbt <command>` subprocess and persists the outcome.
        Never raises for a dbt-side failure (failed tests, a broken model) —
        that comes back as a FAILED DbtRun, same as a normal API response.
        Only a genuinely broken invocation (dbt missing, timeout) is ERROR."""
        args = list(_COMMAND_ARGS[command])
        if selector and command in _SELECTABLE_COMMANDS:
            args += ["--select", selector]

        started_at = datetime.now(UTC)
        try:
            lock = _USER_LOCKS.setdefault(user_id, Lock())
            with lock:
                result = run_dbt(args, settings=self.settings, user_id=user_id)
        except DbtRunnerError as exc:
            return self._save_run(
                user_id=user_id,
                command=command,
                selector=selector,
                status=DbtRunStatus.ERROR,
                summary={"error": str(exc)},
                log=str(exc),
                started_at=started_at,
            )

        return self._save_run(
            user_id=user_id,
            command=command,
            selector=selector,
            status=DbtRunStatus.SUCCESS if result.success else DbtRunStatus.FAILED,
            summary=self._summarize(result, user_id),
            log=(result.stdout + ("\n" + result.stderr if result.stderr else "")).strip(),
            started_at=started_at,
        )

    def _save_run(
        self,
        *,
        user_id: str,
        command: DbtCommand,
        selector: str | None,
        status: DbtRunStatus,
        summary: dict,
        log: str,
        started_at: datetime,
    ) -> DbtRun:
        run = DbtRun(
            user_id=user_id,
            command=command,
            selector=selector,
            status=status,
            summary=summary,
            log=log,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _summarize(self, result: DbtCliResult, user_id: str) -> dict:
        summary: dict = {
            "returncode": result.returncode,
            "duration_seconds": round(result.duration_seconds, 3),
        }
        run_results = artifacts.get_run_results(resolve_target_dir(user_id))
        if run_results is not None:
            counts: dict[str, int] = {}
            for r in run_results.get("results", []):
                status = r.get("status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            summary["result_counts"] = counts
            summary["node_count"] = len(run_results.get("results", []))
        return summary

    # --- Run history -----------------------------------------------------

    def get_run(self, user_id: str, run_id: str) -> DbtRun:
        run = self.db.get(DbtRun, run_id)
        if run is None or run.user_id != user_id:
            raise NotFoundError(f"dbt run '{run_id}' not found.")
        return run

    def list_runs(self, user_id: str, limit: int = 20) -> list[DbtRun]:
        stmt = select(DbtRun).where(DbtRun.user_id == user_id).order_by(DbtRun.started_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    # --- Project introspection (dbt's own artifacts, not app state) ------

    def get_lineage(self, user_id: str | None = None) -> artifacts.LineageGraph:
        graph = artifacts.build_lineage_graph(resolve_target_dir(user_id or self.user_id))
        if graph is None:
            raise AppError(
                "No dbt lineage available yet — run the dbt Lab (Run/Build/Docs) at least once first."
            )
        return graph

    def get_docs(self, user_id: str | None = None) -> list[artifacts.NodeDoc]:
        docs = artifacts.build_docs(resolve_target_dir(user_id or self.user_id))
        if docs is None:
            raise AppError("No dbt docs available yet — run the dbt Lab at least once first.")
        return docs

    def get_test_results(self, user_id: str | None = None) -> list[artifacts.TestResult]:
        results = artifacts.build_test_results(resolve_target_dir(user_id or self.user_id))
        if results is None:
            raise AppError("No dbt test results available yet — run `dbt test` or `dbt build` first.")
        return results

    def get_project_tree(self) -> list[ProjectTreeItem]:
        items: list[ProjectTreeItem] = []
        for category, subdir in _PROJECT_TREE_DIRS:
            directory = DBT_PROJECT_DIR / subdir
            if not directory.exists():
                continue
            for sql_file in sorted(directory.glob("*.sql")):
                items.append(
                    ProjectTreeItem(
                        category=category,
                        name=sql_file.stem,
                        relative_path=str(sql_file.relative_to(DBT_PROJECT_DIR)).replace("\\", "/"),
                    )
                )
            for csv_file in sorted(directory.glob("*.csv")):
                items.append(
                    ProjectTreeItem(
                        category=category,
                        name=csv_file.stem,
                        relative_path=str(csv_file.relative_to(DBT_PROJECT_DIR)).replace("\\", "/"),
                    )
                )
        return items
