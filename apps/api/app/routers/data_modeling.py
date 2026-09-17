"""One router backs the Data Modeler, the Architecture Diagram Builder, and
the Pipeline Playground's saved graphs — they differ only in which
`model_kind` they pass (DIMENSIONAL / ARCHITECTURE / PIPELINE); see
DataModel's docstring for why this is one shared graph schema rather than
three near-duplicate ones."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.data_modeling.service import DataModelService
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_data_model_service
from app.models.enums import DataModelKind
from app.schemas.data_model import (
    CreateDataModelRequest,
    DataModelSchema,
    DataModelSummarySchema,
    SaveDataModelGraphRequest,
    UpdateDataModelRequest,
    ValidationFindingSchema,
    ValidationResultSchema,
)

router = APIRouter(prefix="/modeling", tags=["modeling"])


@router.get("/models", response_model=list[DataModelSummarySchema])
def list_models(
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
    model_kind: DataModelKind | None = Query(default=None),
) -> list[DataModelSummarySchema]:
    return [DataModelSummarySchema.model_validate(m) for m in service.list_models(user_id, model_kind)]


@router.post("/models", response_model=DataModelSchema, status_code=201)
def create_model(
    payload: CreateDataModelRequest,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> DataModelSchema:
    model = service.create_model(
        user_id, name=payload.name, description=payload.description, model_kind=payload.model_kind
    )
    return DataModelSchema.model_validate(model)


@router.get("/models/{model_id}", response_model=DataModelSchema)
def get_model(
    model_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> DataModelSchema:
    return DataModelSchema.model_validate(service.get_model(user_id, model_id))


@router.patch("/models/{model_id}", response_model=DataModelSchema)
def update_model(
    model_id: str,
    payload: UpdateDataModelRequest,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> DataModelSchema:
    model = service.update_model(user_id, model_id, name=payload.name, description=payload.description)
    return DataModelSchema.model_validate(model)


@router.delete("/models/{model_id}", status_code=204)
def delete_model(
    model_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> None:
    service.delete_model(user_id, model_id)


@router.put("/models/{model_id}/graph", response_model=DataModelSchema)
def save_graph(
    model_id: str,
    payload: SaveDataModelGraphRequest,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> DataModelSchema:
    model = service.replace_graph(
        user_id,
        model_id,
        tables=[t.model_dump() for t in payload.tables],
        relationships=[r.model_dump() for r in payload.relationships],
    )
    return DataModelSchema.model_validate(model)


@router.post("/models/{model_id}/validate", response_model=ValidationResultSchema)
def validate_model(
    model_id: str,
    user_id: CurrentUserId,
    service: Annotated[DataModelService, Depends(get_data_model_service)],
) -> ValidationResultSchema:
    findings = service.validate_model(user_id, model_id)
    schemas = [ValidationFindingSchema(**vars(f)) for f in findings]
    return ValidationResultSchema(
        findings=schemas,
        error_count=sum(1 for f in schemas if f.severity == "error"),
        warning_count=sum(1 for f in schemas if f.severity == "warning"),
    )
