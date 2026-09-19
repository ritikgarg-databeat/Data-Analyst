from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.content.loader import load_exercise_file
from app.core.errors import AppError
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import (
    get_exercise_service,
    get_python_execution_service,
    get_python_exercise_service,
    get_python_workspace_service,
)
from app.python_lab.converters import to_execution_result_schema
from app.python_lab.service import PythonExecutionService
from app.schemas.python_lab import (
    CreatePythonCellRequest,
    CreatePythonWorkspaceRequest,
    ExecutePythonRequest,
    PythonAvailabilitySchema,
    PythonCellSchema,
    PythonDatasetFileSchema,
    PythonExecutionResultSchema,
    PythonExerciseContent,
    PythonHistoryItemSchema,
    PythonRuntimeSchema,
    PythonWorkspaceSchema,
    RecordCellResultRequest,
    SubmitPythonExerciseRequest,
    SubmitPythonExerciseResponse,
    UpdatePythonCellRequest,
    UpdatePythonWorkspaceRequest,
)
from app.services.exercise_service import ExerciseService
from app.services.python_exercise_service import PythonExerciseService
from app.services.python_workspace_service import PythonWorkspaceService

router = APIRouter(prefix="/python", tags=["python"])


@router.get("/availability", response_model=PythonAvailabilitySchema)
def get_availability(
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> PythonAvailabilitySchema:
    available, reason = service.is_available()
    return PythonAvailabilitySchema(available=available, reason=reason)


@router.get("/datasets", response_model=list[PythonDatasetFileSchema])
def list_datasets(
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> list[PythonDatasetFileSchema]:
    return [PythonDatasetFileSchema(**vars(f)) for f in service.list_datasets(user_id)]


# --- Runtimes --------------------------------------------------------------


@router.get("/runtimes", response_model=list[PythonRuntimeSchema])
def list_runtimes(
    user_id: CurrentUserId, service: Annotated[PythonExecutionService, Depends(get_python_execution_service)]
) -> list[PythonRuntimeSchema]:
    service.reap_idle_runtimes()
    return list(service.list_runtimes(user_id))


@router.post("/runtimes", response_model=PythonRuntimeSchema, status_code=201)
def create_runtime(
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
    workspace_id: str | None = Query(default=None),
) -> PythonRuntimeSchema:
    service.reap_idle_runtimes()
    return service.create_runtime(user_id, workspace_id=workspace_id)


@router.get("/runtimes/{runtime_id}", response_model=PythonRuntimeSchema)
def get_runtime(
    runtime_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> PythonRuntimeSchema:
    return service.get_runtime(runtime_id, user_id)


@router.post("/runtimes/{runtime_id}/execute", response_model=PythonExecutionResultSchema)
def execute_code(
    runtime_id: str,
    payload: ExecutePythonRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> PythonExecutionResultSchema:
    result = service.execute(runtime_id, user_id, payload.code, workspace_id=payload.workspace_id)
    return to_execution_result_schema(result)


@router.post("/runtimes/{runtime_id}/restart", response_model=PythonRuntimeSchema)
def restart_runtime(
    runtime_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> PythonRuntimeSchema:
    return service.restart_runtime(runtime_id, user_id)


@router.delete("/runtimes/{runtime_id}", status_code=204)
def destroy_runtime(
    runtime_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> None:
    service.destroy_runtime(runtime_id, user_id)


# --- History -----------------------------------------------------------


@router.get("/history", response_model=list[PythonHistoryItemSchema])
def list_history(
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[PythonHistoryItemSchema]:
    return list(service.list_history(user_id, workspace_id=workspace_id, limit=limit))


@router.delete("/history/{history_id}", status_code=204)
def delete_history_entry(
    history_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonExecutionService, Depends(get_python_execution_service)],
) -> None:
    service.delete_history_entry(user_id, history_id)


# --- Workspaces & cells ------------------------------------------------


@router.get("/workspaces", response_model=list[PythonWorkspaceSchema])
def list_workspaces(
    user_id: CurrentUserId, service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)]
) -> list[PythonWorkspaceSchema]:
    return list(service.list_workspaces(user_id))


@router.post("/workspaces", response_model=PythonWorkspaceSchema, status_code=201)
def create_workspace(
    payload: CreatePythonWorkspaceRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonWorkspaceSchema:
    return service.create_workspace(user_id, payload)


@router.get("/workspaces/{workspace_id}", response_model=PythonWorkspaceSchema)
def get_workspace(
    workspace_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonWorkspaceSchema:
    return service.get_workspace(user_id, workspace_id)


@router.patch("/workspaces/{workspace_id}", response_model=PythonWorkspaceSchema)
def update_workspace(
    workspace_id: str,
    payload: UpdatePythonWorkspaceRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonWorkspaceSchema:
    return service.update_workspace(user_id, workspace_id, payload)


@router.delete("/workspaces/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> None:
    service.delete_workspace(user_id, workspace_id)


@router.get("/workspaces/{workspace_id}/cells", response_model=list[PythonCellSchema])
def list_cells(
    workspace_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> list[PythonCellSchema]:
    return list(service.list_cells(user_id, workspace_id))


@router.post("/workspaces/{workspace_id}/cells", response_model=PythonCellSchema, status_code=201)
def add_cell(
    workspace_id: str,
    payload: CreatePythonCellRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonCellSchema:
    return service.add_cell(user_id, workspace_id, code=payload.code)


@router.patch("/workspaces/{workspace_id}/cells/{cell_id}", response_model=PythonCellSchema)
def update_cell(
    workspace_id: str,
    cell_id: str,
    payload: UpdatePythonCellRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonCellSchema:
    return service.update_cell(user_id, workspace_id, cell_id, payload)


@router.post("/workspaces/{workspace_id}/cells/{cell_id}/result", response_model=PythonCellSchema)
def record_cell_result(
    workspace_id: str,
    cell_id: str,
    payload: RecordCellResultRequest,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> PythonCellSchema:
    return service.record_cell_result(user_id, workspace_id, cell_id, payload.result.model_dump())


@router.delete("/workspaces/{workspace_id}/cells/{cell_id}", status_code=204)
def delete_cell(
    workspace_id: str,
    cell_id: str,
    user_id: CurrentUserId,
    service: Annotated[PythonWorkspaceService, Depends(get_python_workspace_service)],
) -> None:
    service.delete_cell(user_id, workspace_id, cell_id)


# --- Python exercises ----------------------------------------------------


@router.get("/exercises/{slug}", response_model=PythonExerciseContent)
def get_python_exercise_content(
    slug: str,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    python_exercise_service: Annotated[PythonExerciseService, Depends(get_python_exercise_service)],
) -> PythonExerciseContent:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "PYTHON":
        raise AppError(f"'{slug}' is not a Python exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return python_exercise_service.get_exercise_content(exercise, content)


@router.post("/exercises/{slug}/submit", response_model=SubmitPythonExerciseResponse)
def submit_python_exercise(
    slug: str,
    payload: SubmitPythonExerciseRequest,
    user_id: CurrentUserId,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    python_exercise_service: Annotated[PythonExerciseService, Depends(get_python_exercise_service)],
) -> SubmitPythonExerciseResponse:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "PYTHON":
        raise AppError(f"'{slug}' is not a Python exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return python_exercise_service.submit(user_id, exercise, content, payload.submitted_code)
