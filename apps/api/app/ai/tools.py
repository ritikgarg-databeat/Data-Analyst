"""Data-aware AI tool interfaces (spec section 18) — scoped, read-only,
resource-limited, auditable wrappers around EXISTING services. Nothing here
queries a database directly; every method delegates to a real,
already-tested service (`DatasetAnalysisService`, `SqlExecutionService`,
`SkillService`, `CaseService`) so a tool call can never do anything that
service doesn't already allow.

Why there is no live tool-calling loop: OpenAI's and Anthropic's
function-calling wire formats differ enough that a provider-agnostic
implementation would roughly double this phase's surface area for a benefit
(the model choosing which tool to call mid-conversation, instead of the
service pre-fetching the right one) that doesn't change what the learner
sees for any capability this phase implements — every feature's context need
is already knowable from which endpoint was called — so every current
feature's service builds its context payload directly rather than routing
through this toolbox. `AIToolbox` (and `AIService.build_toolbox`, which
constructs one) exist as the scoped, read-only, auditable interface a real
tool-calling loop would use if one is added later; every call would be
recorded in `self.calls` so it could be audited the same way a Gateway call
is (spec section 53) — but as of this phase, nothing in the codebase
actually constructs or calls one during a real request."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.errors import AppError

# spec section 54's permission table, enforced by construction (not just
# documented): AIToolbox has no write_* method, `execute_readonly_sql` only
# ever reaches `SqlExecutionService.execute`, whose engines enforce a
# statement-level denylist (app/sql/safety.py) before anything touches a
# database — there is no path from this class to a mutating statement.
TOOL_PERMISSIONS: dict[str, str] = {
    "get_dataset_schema": "dataset:metadata (read-only)",
    "preview_table": "sql:read-only (row-capped sample)",
    "get_column_profile": "dataset:metadata (read-only)",
    "execute_readonly_sql": "sql:read-only (denylist-enforced, row/time capped)",
    "get_user_skill_profile": "skills:read-only",
    "get_case_context": "case:public-fields-only",
    "get_metric_definition": "metrics:read-only",
}


@dataclass(frozen=True)
class ToolCallRecord:
    tool: str
    scope: str
    args_summary: str


class AIToolbox:
    """Constructed per-request with the services it may call through to.
    There is deliberately no `write_*` method on this class."""

    def __init__(
        self,
        *,
        user_id: str,
        dataset_analysis_service: Any,
        sql_execution_service: Any,
        skill_service: Any,
        case_service: Any,
        metrics_service: Any | None = None,
    ) -> None:
        self._user_id = user_id
        self._datasets = dataset_analysis_service
        self._sql = sql_execution_service
        self._skills = skill_service
        self._cases = case_service
        self._metrics = metrics_service
        self.calls: list[ToolCallRecord] = []

    def _record(self, tool: str, args_summary: str) -> None:
        self.calls.append(
            ToolCallRecord(tool=tool, scope=TOOL_PERMISSIONS[tool], args_summary=args_summary[:150])
        )

    def get_dataset_schema(self, dataset_id_or_slug: str, table_name: str | None = None) -> Any:
        self._record("get_dataset_schema", dataset_id_or_slug)
        schema = self._datasets.get_schema(dataset_id_or_slug, table_name)
        if schema:
            return schema
        return self._datasets.get_raw_schema(dataset_id_or_slug, table_name)

    def preview_table(self, database: str, table: str, *, engine: str = "duckdb") -> Any:
        self._record("preview_table", f"{engine}/{database}/{table}")
        return self._sql.preview_table(engine, database, table)

    def get_column_profile(self, dataset_id_or_slug: str, table_name: str, column_name: str) -> Any:
        self._record("get_column_profile", f"{dataset_id_or_slug}.{table_name}.{column_name}")
        profile = self._datasets.get_profile(dataset_id_or_slug)
        for table in profile.tables:
            if table.table_name != table_name:
                continue
            for column in table.columns:
                if column.column_name == column_name:
                    return column
        raise AppError(f"No profile found for column '{column_name}' on table '{table_name}'.")

    def execute_readonly_sql(self, engine: str, database: str, query: str) -> Any:
        self._record("execute_readonly_sql", query)
        return self._sql.execute(
            user_id=self._user_id, engine_name=engine, database_name=database, query=query
        )

    def get_user_skill_profile(self) -> Any:
        self._record("get_user_skill_profile", self._user_id)
        return self._skills.list_user_skills(self._user_id)

    def get_case_context(self, case_slug: str) -> Any:
        self._record("get_case_context", case_slug)
        return self._cases.get_case_by_slug(case_slug)

    def get_metric_definition(self, metric_slug: str) -> Any:
        if self._metrics is None:
            raise AppError("Metric definitions are not available in this context.")
        self._record("get_metric_definition", metric_slug)
        return self._metrics.get(metric_slug)
