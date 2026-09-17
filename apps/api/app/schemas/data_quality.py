from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DataQualityRuleType, DataQualityStatus
from app.schemas.common import ORMSchema


class CreateDataQualityRuleRequest(BaseModel):
    dataset_id: str
    table_name: str
    column_name: str | None = None
    rule_type: DataQualityRuleType
    config: dict = {}
    name: str | None = None


class DataQualityRuleSchema(ORMSchema):
    id: str
    dataset_id: str
    table_name: str
    column_name: str | None
    rule_type: DataQualityRuleType
    config: dict
    name: str | None
    created_at: datetime


class DataQualityRunSchema(ORMSchema):
    id: str
    rule_id: str
    status: DataQualityStatus
    expected_value: str | None
    actual_value: str | None
    details: dict
    executed_at: datetime
