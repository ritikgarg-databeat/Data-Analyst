from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.dependencies.services import get_kaggle_service
from app.schemas.dataset import Dataset
from app.schemas.kaggle import (
    KaggleFilesResponse,
    KaggleImportRequest,
    KaggleSearchResponse,
    KaggleStatusResponse,
)
from app.services.kaggle_service import KaggleService

router = APIRouter(prefix="/kaggle", tags=["kaggle"])


@router.get("/status", response_model=KaggleStatusResponse)
def get_status(service: Annotated[KaggleService, Depends(get_kaggle_service)]) -> KaggleStatusResponse:
    return service.status()


@router.get("/search", response_model=KaggleSearchResponse)
def search(
    service: Annotated[KaggleService, Depends(get_kaggle_service)],
    q: Annotated[str, Query(min_length=1)],
    page: int = Query(default=1, ge=1),
) -> KaggleSearchResponse:
    return service.search(q, page=page)


@router.get("/datasets/{owner}/{name}/files", response_model=KaggleFilesResponse)
def list_files(
    owner: str, name: str, service: Annotated[KaggleService, Depends(get_kaggle_service)]
) -> KaggleFilesResponse:
    return service.list_files(f"{owner}/{name}")


@router.post("/datasets/{owner}/{name}/import", response_model=Dataset, status_code=201)
def import_dataset(
    owner: str,
    name: str,
    payload: KaggleImportRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[KaggleService, Depends(get_kaggle_service)],
) -> Dataset:
    return service.start_import(f"{owner}/{name}", payload, background_tasks)
