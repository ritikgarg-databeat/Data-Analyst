from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import AdminUser, CurrentUserId
from app.dependencies.services import get_case_service
from app.models.enums import CaseCategory
from app.schemas.case import (
    CaseAdminListItemSchema,
    CaseAttemptSchema,
    CaseListItemSchema,
    CaseSchema,
    RecordStageTimeRequest,
    RevealCaseSolutionResponse,
    RevealHintResponse,
    SaveClarificationRequest,
    SaveDatasetSelectionRequest,
    SaveExecutiveSummaryRequest,
    SaveFramingRequest,
    SaveRecommendationRequest,
    SaveReflectionRequest,
    SubmitCaseAttemptRequest,
    UpdateCaseAdminRequest,
    UpdateStageRequest,
)
from app.services.case_service import CaseService, to_case_schema

router = APIRouter(prefix="/cases", tags=["cases"])


# Registered before GET /{slug} so "admin" isn't swallowed by the slug route.
@router.get("/admin", response_model=list[CaseAdminListItemSchema])
def list_cases_admin(
    admin: AdminUser,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> list[CaseAdminListItemSchema]:
    return [CaseAdminListItemSchema.model_validate(c) for c in service.list_cases_admin()]


@router.patch("/admin/{case_id}", response_model=CaseAdminListItemSchema)
def update_case_admin(
    case_id: str,
    payload: UpdateCaseAdminRequest,
    admin: AdminUser,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAdminListItemSchema:
    return CaseAdminListItemSchema.model_validate(service.update_case_admin(case_id, payload.is_active))


def _to_attempt_schema(service: CaseService, attempt) -> CaseAttemptSchema:  # noqa: ANN001
    schema = CaseAttemptSchema.model_validate(attempt)
    schema.submission_readiness = service.submission_readiness(attempt)
    return schema


@router.get("", response_model=list[CaseListItemSchema])
def list_cases(
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
    category: CaseCategory | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[CaseListItemSchema]:
    results = service.list_cases(user_id, category=category, difficulty=difficulty, search=search)
    return [
        CaseListItemSchema(
            case=to_case_schema(case),
            attempt_id=attempt.id if attempt else None,
            attempt_status=attempt.status if attempt else None,
            attempt_score=(attempt.score or {}).get("overall") if attempt and attempt.score else None,
        )
        for case, attempt in results
    ]


@router.get("/attempts", response_model=list[CaseAttemptSchema])
def list_my_attempts(
    user_id: CurrentUserId, service: Annotated[CaseService, Depends(get_case_service)]
) -> list[CaseAttemptSchema]:
    return [_to_attempt_schema(service, a) for a in service.list_attempts(user_id)]


@router.get("/attempts/{attempt_id}", response_model=CaseAttemptSchema)
def get_attempt(
    attempt_id: str, user_id: CurrentUserId, service: Annotated[CaseService, Depends(get_case_service)]
) -> CaseAttemptSchema:
    return _to_attempt_schema(service, service.get_attempt(user_id, attempt_id))


@router.get("/{slug}", response_model=CaseSchema)
def get_case(slug: str, service: Annotated[CaseService, Depends(get_case_service)]) -> CaseSchema:
    return to_case_schema(service.get_case_by_slug(slug))


@router.post("/{slug}/start", response_model=CaseAttemptSchema, status_code=201)
def start_attempt(
    slug: str, user_id: CurrentUserId, service: Annotated[CaseService, Depends(get_case_service)]
) -> CaseAttemptSchema:
    return _to_attempt_schema(service, service.start_attempt(user_id, slug))


@router.patch("/attempts/{attempt_id}/stage", response_model=CaseAttemptSchema)
def update_stage(
    attempt_id: str,
    payload: UpdateStageRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(service, service.update_stage(user_id, attempt_id, payload.stage))


@router.patch("/attempts/{attempt_id}/clarification", response_model=CaseAttemptSchema)
def save_clarification(
    attempt_id: str,
    payload: SaveClarificationRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(service, service.save_clarification(user_id, attempt_id, payload.questions))


@router.patch("/attempts/{attempt_id}/framing", response_model=CaseAttemptSchema)
def save_framing(
    attempt_id: str,
    payload: SaveFramingRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service, service.save_framing(user_id, attempt_id, payload.framing.model_dump())
    )


@router.patch("/attempts/{attempt_id}/datasets", response_model=CaseAttemptSchema)
def save_dataset_selection(
    attempt_id: str,
    payload: SaveDatasetSelectionRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service, service.save_dataset_selection(user_id, attempt_id, payload.dataset_slugs)
    )


@router.patch("/attempts/{attempt_id}/recommendation", response_model=CaseAttemptSchema)
def save_recommendation(
    attempt_id: str,
    payload: SaveRecommendationRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service, service.save_recommendation(user_id, attempt_id, payload.recommendation.model_dump())
    )


@router.patch("/attempts/{attempt_id}/executive-summary", response_model=CaseAttemptSchema)
def save_executive_summary(
    attempt_id: str,
    payload: SaveExecutiveSummaryRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service,
        service.save_executive_summary(user_id, attempt_id, payload.executive_summary.model_dump()),
    )


@router.post("/attempts/{attempt_id}/stage-time", response_model=CaseAttemptSchema)
def record_stage_time(
    attempt_id: str,
    payload: RecordStageTimeRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service, service.record_stage_time(user_id, attempt_id, payload.stage, payload.seconds)
    )


@router.post("/attempts/{attempt_id}/hint", response_model=RevealHintResponse)
def reveal_hint(
    attempt_id: str, user_id: CurrentUserId, service: Annotated[CaseService, Depends(get_case_service)]
) -> RevealHintResponse:
    attempt, hint = service.reveal_hint(user_id, attempt_id)
    return RevealHintResponse(hint=hint, hints_used=attempt.hints_used)


@router.post("/attempts/{attempt_id}/submit", response_model=CaseAttemptSchema)
def submit_attempt(
    attempt_id: str,
    payload: SubmitCaseAttemptRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(service, service.submit_attempt(user_id, attempt_id, payload.rubric_selections))


@router.post("/attempts/{attempt_id}/reveal-solution", response_model=RevealCaseSolutionResponse)
def reveal_solution(
    attempt_id: str, user_id: CurrentUserId, service: Annotated[CaseService, Depends(get_case_service)]
) -> RevealCaseSolutionResponse:
    attempt = service.reveal_solution(user_id, attempt_id)
    return RevealCaseSolutionResponse(**attempt.case.reference_solution)


@router.patch("/attempts/{attempt_id}/reflection", response_model=CaseAttemptSchema)
def save_reflection(
    attempt_id: str,
    payload: SaveReflectionRequest,
    user_id: CurrentUserId,
    service: Annotated[CaseService, Depends(get_case_service)],
) -> CaseAttemptSchema:
    return _to_attempt_schema(
        service, service.save_reflection(user_id, attempt_id, payload.reflection.model_dump())
    )
