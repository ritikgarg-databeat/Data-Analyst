from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.services import get_experiment_service
from app.schemas.experiments import (
    AnalyzeABTestRequest,
    AnalyzeABTestResponse,
    PowerRequest,
    PowerResponse,
    SampleSizeRequest,
    SampleSizeResponse,
    SimulateABTestRequest,
    SimulateABTestResponse,
)
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/sample-size", response_model=SampleSizeResponse)
def sample_size(
    payload: SampleSizeRequest, service: Annotated[ExperimentService, Depends(get_experiment_service)]
) -> SampleSizeResponse:
    return service.sample_size(payload)


@router.post("/power", response_model=PowerResponse)
def power(
    payload: PowerRequest, service: Annotated[ExperimentService, Depends(get_experiment_service)]
) -> PowerResponse:
    return service.power(payload)


@router.post("/analyze", response_model=AnalyzeABTestResponse)
def analyze(
    payload: AnalyzeABTestRequest, service: Annotated[ExperimentService, Depends(get_experiment_service)]
) -> AnalyzeABTestResponse:
    return service.analyze(payload)


@router.post("/simulate", response_model=SimulateABTestResponse)
def simulate(
    payload: SimulateABTestRequest, service: Annotated[ExperimentService, Depends(get_experiment_service)]
) -> SimulateABTestResponse:
    return service.simulate(payload)
