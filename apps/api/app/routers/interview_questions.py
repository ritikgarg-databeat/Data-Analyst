from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_interview_question_service
from app.schemas.interview import (
    CreateBookmarkRequest,
    CreateNoteRequest,
    DueReviewSchema,
    InterviewBookmarkSchema,
    InterviewNoteSchema,
    InterviewQuestionAdminListItemSchema,
    InterviewQuestionDetail,
    InterviewQuestionListItem,
    UpdateInterviewQuestionAdminRequest,
    UpdateNoteRequest,
)
from app.services.interview_question_service import InterviewQuestionService

router = APIRouter(prefix="/interview/questions", tags=["interview-questions"])


# Registered before GET /{slug} so "admin" isn't swallowed by the slug route.
@router.get("/admin", response_model=list[InterviewQuestionAdminListItemSchema])
def list_questions_admin(
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> list[InterviewQuestionAdminListItemSchema]:
    return service.list_questions_admin()


@router.patch("/admin/{question_id}", response_model=InterviewQuestionAdminListItemSchema)
def update_question_admin(
    question_id: str,
    payload: UpdateInterviewQuestionAdminRequest,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> InterviewQuestionAdminListItemSchema:
    return service.update_question_admin(question_id, payload.is_active)


@router.get("", response_model=list[InterviewQuestionListItem])
def list_questions(
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
    interview_type: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    company_archetype: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    search: str | None = Query(default=None),
    bookmarked_only: bool = Query(default=False),
) -> list[InterviewQuestionListItem]:
    return service.list_questions(
        user_id,
        interview_type=interview_type,
        difficulty=difficulty,
        company_archetype=company_archetype,
        tag=tag,
        search=search,
        bookmarked_only=bookmarked_only,
    )


# Registered before GET /{slug} so "review-queue" isn't swallowed by the slug route.
@router.get("/review-queue", response_model=list[DueReviewSchema])
def get_review_queue(
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[DueReviewSchema]:
    return service.get_review_queue(user_id, limit=limit)


@router.get("/{slug}", response_model=InterviewQuestionDetail)
def get_question(
    slug: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> InterviewQuestionDetail:
    return service.get_question(slug, user_id)


bookmarks_router = APIRouter(prefix="/interview/bookmarks", tags=["interview-bookmarks"])


@bookmarks_router.get("", response_model=list[InterviewBookmarkSchema])
def list_bookmarks(
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> list[InterviewBookmarkSchema]:
    return service.list_bookmarks(user_id)


@bookmarks_router.post("", response_model=InterviewBookmarkSchema, status_code=201)
def create_bookmark(
    payload: CreateBookmarkRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> InterviewBookmarkSchema:
    return service.create_bookmark(user_id, payload)


@bookmarks_router.delete("/{bookmark_id}", status_code=204)
def delete_bookmark(
    bookmark_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> None:
    service.delete_bookmark(user_id, bookmark_id)


notes_router = APIRouter(prefix="/interview/notes", tags=["interview-notes"])


@notes_router.get("", response_model=list[InterviewNoteSchema])
def list_notes(
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
) -> list[InterviewNoteSchema]:
    return service.list_notes(user_id, target_type=target_type, target_id=target_id)


@notes_router.post("", response_model=InterviewNoteSchema, status_code=201)
def create_note(
    payload: CreateNoteRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> InterviewNoteSchema:
    return service.create_note(user_id, payload)


@notes_router.patch("/{note_id}", response_model=InterviewNoteSchema)
def update_note(
    note_id: str,
    payload: UpdateNoteRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> InterviewNoteSchema:
    return service.update_note(user_id, note_id, payload)


@notes_router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewQuestionService, Depends(get_interview_question_service)],
) -> None:
    service.delete_note(user_id, note_id)
