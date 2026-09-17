from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_portfolio_service
from app.schemas.ai import AIStructuredResponse
from app.schemas.portfolio import (
    CreatePortfolioItemRequest,
    PortfolioGapSuggestionSchema,
    PortfolioQualityScoreResponse,
    PortfolioSchema,
    UpdatePortfolioItemRequest,
    UpdatePortfolioRequest,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PortfolioServiceDep = Annotated[PortfolioService, Depends(get_portfolio_service)]


@router.get("", response_model=PortfolioSchema)
def get_portfolio(user_id: CurrentUserId, service: PortfolioServiceDep) -> PortfolioSchema:
    return service.get_portfolio(user_id)


@router.patch("", response_model=PortfolioSchema)
def update_portfolio(
    payload: UpdatePortfolioRequest, user_id: CurrentUserId, service: PortfolioServiceDep
) -> PortfolioSchema:
    return service.update_portfolio(user_id, payload)


@router.post("/items", response_model=PortfolioSchema, status_code=201)
def add_item(
    payload: CreatePortfolioItemRequest, user_id: CurrentUserId, service: PortfolioServiceDep
) -> PortfolioSchema:
    return service.add_item(user_id, payload)


@router.patch("/items/{item_id}", response_model=PortfolioSchema)
def update_item(
    item_id: str, payload: UpdatePortfolioItemRequest, user_id: CurrentUserId, service: PortfolioServiceDep
) -> PortfolioSchema:
    return service.update_item(user_id, item_id, payload)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str, user_id: CurrentUserId, service: PortfolioServiceDep) -> None:
    service.delete_item(user_id, item_id)


@router.get("/quality-score", response_model=PortfolioQualityScoreResponse)
def get_quality_score(user_id: CurrentUserId, service: PortfolioServiceDep) -> PortfolioQualityScoreResponse:
    return service.quality_score(user_id)


@router.post("/review", response_model=AIStructuredResponse)
def review_portfolio(user_id: CurrentUserId, service: PortfolioServiceDep) -> AIStructuredResponse:
    return service.ai_review(user_id)


@router.get("/gaps", response_model=list[PortfolioGapSuggestionSchema])
def detect_gaps(
    user_id: CurrentUserId, service: PortfolioServiceDep, target_role_id: str | None = None
) -> list[PortfolioGapSuggestionSchema]:
    return service.detect_gaps(user_id, target_role_id)
