from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DataModelKind, DataModelRelationshipType, DataModelTableType
from app.schemas.common import ORMSchema


class DataModelColumnSchema(BaseModel):
    name: str
    data_type: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: str | None = None
    references_column: str | None = None


class CreateDataModelRequest(BaseModel):
    name: str
    description: str | None = None
    model_kind: DataModelKind


class UpdateDataModelRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class DataModelTableSchema(ORMSchema):
    id: str
    name: str
    table_type: DataModelTableType
    grain: str | None
    notes: str | None
    columns: list[dict]
    position_x: float
    position_y: float


class DataModelRelationshipSchema(ORMSchema):
    id: str
    from_table_id: str
    to_table_id: str
    from_column: str | None
    to_column: str | None
    relationship_type: DataModelRelationshipType
    label: str | None


class DataModelSchema(ORMSchema):
    id: str
    name: str
    description: str | None
    model_kind: DataModelKind
    created_at: datetime
    updated_at: datetime
    tables: list[DataModelTableSchema] = []
    # The ORM attribute is `relationships_` (trailing underscore avoids
    # shadowing SQLAlchemy's own `relationship()` import) — not something the
    # API contract should expose, so it's aliased back to a clean name here.
    relationships: list[DataModelRelationshipSchema] = Field(default=[], validation_alias="relationships_")


class DataModelSummarySchema(ORMSchema):
    id: str
    name: str
    description: str | None
    model_kind: DataModelKind
    created_at: datetime
    updated_at: datetime


class SaveTableInput(BaseModel):
    key: str
    name: str
    table_type: DataModelTableType = DataModelTableType.OTHER
    grain: str | None = None
    notes: str | None = None
    columns: list[DataModelColumnSchema] = []
    position_x: float = 0.0
    position_y: float = 0.0


class SaveRelationshipInput(BaseModel):
    from_key: str
    to_key: str
    from_column: str | None = None
    to_column: str | None = None
    relationship_type: DataModelRelationshipType = DataModelRelationshipType.ONE_TO_MANY
    label: str | None = None


class SaveDataModelGraphRequest(BaseModel):
    tables: list[SaveTableInput]
    relationships: list[SaveRelationshipInput] = []


class ValidationFindingSchema(BaseModel):
    severity: str
    code: str
    message: str
    table_id: str | None = None
    table_name: str | None = None


class ValidationResultSchema(BaseModel):
    findings: list[ValidationFindingSchema]
    error_count: int
    warning_count: int
