from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.content.loader import load_exercise_file
from app.core.errors import AppError
from app.dbt_lab.service import DbtLabService
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_dbt_exercise_service, get_dbt_lab_service, get_exercise_service
from app.schemas.dbt import (
    ColumnDocSchema,
    DbtExerciseContent,
    DbtRunSchema,
    LineageEdgeSchema,
    LineageGraphSchema,
    LineageNodeSchema,
    NodeDocSchema,
    ProjectTreeItemSchema,
    RunDbtCommandRequest,
    SubmitDbtExerciseRequest,
    SubmitDbtExerciseResponse,
    TestResultSchema,
)
from app.services.dbt_exercise_service import DbtExerciseService
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/dbt", tags=["dbt"])


@router.get("/project-tree", response_model=list[ProjectTreeItemSchema])
def get_project_tree(
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> list[ProjectTreeItemSchema]:
    return [ProjectTreeItemSchema(**vars(item)) for item in service.get_project_tree()]


@router.post("/run", response_model=DbtRunSchema, status_code=201)
def run_dbt_command(
    payload: RunDbtCommandRequest,
    user_id: CurrentUserId,
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> DbtRunSchema:
    run = service.execute(user_id=user_id, command=payload.command, selector=payload.selector)
    return DbtRunSchema.model_validate(run)


@router.get("/runs", response_model=list[DbtRunSchema])
def list_dbt_runs(
    user_id: CurrentUserId,
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DbtRunSchema]:
    return [DbtRunSchema.model_validate(run) for run in service.list_runs(user_id, limit=limit)]


@router.get("/runs/{run_id}", response_model=DbtRunSchema)
def get_dbt_run(
    run_id: str,
    user_id: CurrentUserId,
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> DbtRunSchema:
    return DbtRunSchema.model_validate(service.get_run(user_id, run_id))


@router.get("/lineage", response_model=LineageGraphSchema)
def get_lineage(
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> LineageGraphSchema:
    graph = service.get_lineage()
    return LineageGraphSchema(
        nodes=[LineageNodeSchema(**vars(n)) for n in graph.nodes],
        edges=[LineageEdgeSchema(from_unique_id=f, to_unique_id=t) for f, t in graph.edges],
        generated_at=graph.generated_at,
    )


@router.get("/docs", response_model=list[NodeDocSchema])
def get_docs(
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> list[NodeDocSchema]:
    docs = service.get_docs()
    return [
        NodeDocSchema(
            unique_id=d.unique_id,
            name=d.name,
            resource_type=d.resource_type,
            description=d.description,
            materialized=d.materialized,
            schema_name=d.schema_name,
            columns=[ColumnDocSchema(**vars(c)) for c in d.columns],
            test_unique_ids=d.test_unique_ids,
        )
        for d in docs
    ]


@router.get("/test-results", response_model=list[TestResultSchema])
def get_test_results(
    service: Annotated[DbtLabService, Depends(get_dbt_lab_service)],
) -> list[TestResultSchema]:
    return [TestResultSchema(**vars(r)) for r in service.get_test_results()]


@router.get("/exercises/{slug}", response_model=DbtExerciseContent)
def get_dbt_exercise_content(
    slug: str,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    dbt_exercise_service: Annotated[DbtExerciseService, Depends(get_dbt_exercise_service)],
) -> DbtExerciseContent:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "DBT":
        raise AppError(f"'{slug}' is not a dbt exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return dbt_exercise_service.get_exercise_content(content)


@router.post("/exercises/{slug}/submit", response_model=SubmitDbtExerciseResponse)
def submit_dbt_exercise(
    slug: str,
    payload: SubmitDbtExerciseRequest,
    user_id: CurrentUserId,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    dbt_exercise_service: Annotated[DbtExerciseService, Depends(get_dbt_exercise_service)],
) -> SubmitDbtExerciseResponse:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "DBT":
        raise AppError(f"'{slug}' is not a dbt exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return dbt_exercise_service.submit(user_id, exercise, content, payload.submitted_sql)
