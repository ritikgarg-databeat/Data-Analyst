from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DbtCommand, DbtRunStatus
from app.schemas.common import ORMSchema


class RunDbtCommandRequest(BaseModel):
    command: DbtCommand
    selector: str | None = None


class DbtRunSchema(ORMSchema):
    id: str
    command: DbtCommand
    selector: str | None
    status: DbtRunStatus
    summary: dict
    log: str | None
    started_at: datetime
    finished_at: datetime | None


class ProjectTreeItemSchema(BaseModel):
    category: str
    name: str
    relative_path: str


class LineageNodeSchema(BaseModel):
    unique_id: str
    name: str
    resource_type: str
    layer: str | None
    materialized: str | None
    description: str
    depends_on: list[str]


class LineageEdgeSchema(BaseModel):
    from_unique_id: str
    to_unique_id: str


class LineageGraphSchema(BaseModel):
    nodes: list[LineageNodeSchema]
    edges: list[LineageEdgeSchema]
    generated_at: str | None


class ColumnDocSchema(BaseModel):
    name: str
    data_type: str | None
    description: str


class NodeDocSchema(BaseModel):
    unique_id: str
    name: str
    resource_type: str
    description: str
    materialized: str | None
    schema_name: str | None
    columns: list[ColumnDocSchema]
    test_unique_ids: list[str]


class TestResultSchema(BaseModel):
    unique_id: str
    name: str
    status: str
    failures: int | None
    message: str | None
    execution_time: float | None


class DbtExerciseContent(BaseModel):
    business_context: str | None
    dbt_model_name: str
    starter_sql: str | None
    hint_count: int


class SubmitDbtExerciseRequest(BaseModel):
    submitted_sql: str


class DbtExerciseTestOutcome(BaseModel):
    name: str
    passed: bool
    message: str | None = None


class SubmitDbtExerciseResponse(BaseModel):
    attempt_id: str
    status: str
    score: float
    passed: bool
    model_built: bool
    test_outcomes: list[DbtExerciseTestOutcome]
    log: str | None
    explanation: str | None
