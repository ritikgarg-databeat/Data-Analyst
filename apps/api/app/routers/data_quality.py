from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.data_quality.service import DataQualityService
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_data_quality_service
from app.schemas.data_quality import (
    CreateDataQualityRuleRequest,
    DataQualityRuleSchema,
    DataQualityRunSchema,
)

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.get("/rules", response_model=list[DataQualityRuleSchema])
def list_rules(
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
    dataset_id: str | None = Query(default=None),
) -> list[DataQualityRuleSchema]:
    return [DataQualityRuleSchema.model_validate(r) for r in service.list_rules(user_id, dataset_id)]


@router.post("/rules", response_model=DataQualityRuleSchema, status_code=201)
def create_rule(
    payload: CreateDataQualityRuleRequest,
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
) -> DataQualityRuleSchema:
    rule = service.create_rule(
        user_id,
        dataset_id=payload.dataset_id,
        table_name=payload.table_name,
        column_name=payload.column_name,
        rule_type=payload.rule_type,
        config=payload.config,
        name=payload.name,
    )
    return DataQualityRuleSchema.model_validate(rule)


@router.get("/rules/{rule_id}", response_model=DataQualityRuleSchema)
def get_rule(
    rule_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
) -> DataQualityRuleSchema:
    return DataQualityRuleSchema.model_validate(service.get_rule(user_id, rule_id))


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(
    rule_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
) -> None:
    service.delete_rule(user_id, rule_id)


@router.post("/rules/{rule_id}/run", response_model=DataQualityRunSchema, status_code=201)
def run_rule(
    rule_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
) -> DataQualityRunSchema:
    return DataQualityRunSchema.model_validate(service.run_rule(user_id, rule_id))


@router.get("/rules/{rule_id}/runs", response_model=list[DataQualityRunSchema])
def list_runs(
    rule_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataQualityService, Depends(get_data_quality_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DataQualityRunSchema]:
    return [DataQualityRunSchema.model_validate(r) for r in service.list_runs(user_id, rule_id, limit=limit)]
