"""Interview question catalog — search/filter/bookmarks/notes (spec sections
50-55). Question *content* (prompt/rubric/hints/solution) is always reached
through `InterviewService._question_detail`, composed here rather than
duplicated, since that method already assembles an `InterviewQuestionDetail`
from the wrapped `Exercise`'s real content file.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.interview_engine.spaced_review import ReviewItem, due_reviews
from app.models.enums import ExerciseAttemptStatus, InterviewTargetType
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview, InterviewBookmark, InterviewNote, InterviewQuestion
from app.models.tag import ExerciseTag, Tag
from app.schemas.interview import (
    CreateBookmarkRequest,
    CreateNoteRequest,
    DueReviewSchema,
    InterviewBookmarkSchema,
    InterviewNoteSchema,
    InterviewQuestionAdminListItemSchema,
    InterviewQuestionDetail,
    InterviewQuestionListItem,
    UpdateNoteRequest,
)
from app.services.interview_service import InterviewService


class InterviewQuestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.interview_service = InterviewService(db)

    # --- Catalog ---------------------------------------------------------------

    def _exercise_tags(self, exercise_id: str) -> list[str]:
        stmt = (
            select(Tag.slug)
            .join(ExerciseTag, ExerciseTag.tag_id == Tag.id)
            .where(ExerciseTag.exercise_id == exercise_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def _bookmarked_ids(self, user_id: str) -> set[str]:
        stmt = select(InterviewBookmark.target_id).where(
            InterviewBookmark.user_id == user_id, InterviewBookmark.target_type == "QUESTION"
        )
        return set(self.db.execute(stmt).scalars().all())

    def list_questions(
        self,
        user_id: str,
        *,
        interview_type: str | None = None,
        difficulty: str | None = None,
        company_archetype: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        bookmarked_only: bool = False,
    ) -> list[InterviewQuestionListItem]:
        stmt = (
            select(InterviewQuestion, Exercise)
            .join(Exercise, Exercise.id == InterviewQuestion.exercise_id)
            .where(InterviewQuestion.is_active.is_(True))
        )
        if interview_type:
            stmt = stmt.where(InterviewQuestion.interview_type == interview_type)
        if difficulty:
            stmt = stmt.where(Exercise.difficulty == difficulty)

        rows = self.db.execute(stmt.order_by(Exercise.title)).all()
        bookmarked_ids = self._bookmarked_ids(user_id)

        items: list[InterviewQuestionListItem] = []
        for question, exercise in rows:
            if company_archetype and company_archetype not in question.company_archetypes:
                continue
            tags = self._exercise_tags(exercise.id)
            if tag and tag not in tags:
                continue
            if search:
                needle = search.strip().lower()
                if (
                    needle not in exercise.title.lower()
                    and needle not in (exercise.description or "").lower()
                ):
                    continue
            if bookmarked_only and question.id not in bookmarked_ids:
                continue

            attempts = list(
                self.db.execute(
                    select(ExerciseAttempt).where(
                        ExerciseAttempt.user_id == user_id, ExerciseAttempt.exercise_id == exercise.id
                    )
                )
                .scalars()
                .all()
            )
            best_score = max((a.score for a in attempts if a.score is not None), default=None)

            items.append(
                InterviewQuestionListItem(
                    id=question.id,
                    slug=question.slug,
                    interview_type=question.interview_type,
                    difficulty=exercise.difficulty,
                    title=exercise.title,
                    points=exercise.points,
                    time_limit_seconds=question.time_limit_seconds,
                    company_archetypes=question.company_archetypes,
                    tags=tags,
                    is_bookmarked=question.id in bookmarked_ids,
                    best_score=best_score,
                    attempt_count=len(attempts),
                )
            )
        return items

    def get_question(self, slug: str, user_id: str) -> InterviewQuestionDetail:
        detail = self.interview_service.get_question_by_slug(slug, user_id)
        bookmarked_ids = self._bookmarked_ids(user_id)
        detail.is_bookmarked = detail.id in bookmarked_ids
        return detail

    # --- Content Admin (spec section 61) -------------------------------------------

    def list_questions_admin(self) -> list[InterviewQuestionAdminListItemSchema]:
        """All interview questions, active and inactive — for the Content
        Admin panel. Questions are content-authored, so admin only
        lists/activates/deactivates, mirroring CaseService.list_cases_admin."""
        rows = self.db.execute(
            select(InterviewQuestion, Exercise)
            .join(Exercise, Exercise.id == InterviewQuestion.exercise_id)
            .order_by(InterviewQuestion.interview_type, Exercise.title)
        ).all()
        return [
            InterviewQuestionAdminListItemSchema(
                id=question.id,
                slug=question.slug,
                interview_type=question.interview_type,
                exercise_slug=exercise.slug,
                time_limit_seconds=question.time_limit_seconds,
                is_active=question.is_active,
                version=question.version,
            )
            for question, exercise in rows
        ]

    def update_question_admin(
        self, question_id: str, is_active: bool
    ) -> InterviewQuestionAdminListItemSchema:
        question = self.db.get(InterviewQuestion, question_id)
        if question is None:
            raise NotFoundError(f"Interview question '{question_id}' not found.")
        question.is_active = is_active
        self.db.commit()
        self.db.refresh(question)
        exercise = self.db.get(Exercise, question.exercise_id)
        return InterviewQuestionAdminListItemSchema(
            id=question.id,
            slug=question.slug,
            interview_type=question.interview_type,
            exercise_slug=exercise.slug if exercise else "",
            time_limit_seconds=question.time_limit_seconds,
            is_active=question.is_active,
            version=question.version,
        )

    # --- Spaced review (spec section 53) -------------------------------------------

    def get_review_queue(self, user_id: str, limit: int = 20) -> list[DueReviewSchema]:
        """Which already-attempted interview questions are worth seeing again
        now. Built entirely from real `ExerciseAttempt` history — no separate
        scheduling table to drift out of sync with what actually happened."""
        rows = self.db.execute(
            select(InterviewQuestion, ExerciseAttempt)
            .join(ExerciseAttempt, ExerciseAttempt.exercise_id == InterviewQuestion.exercise_id)
            .where(
                InterviewQuestion.is_active.is_(True),
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.score.is_not(None),
                ExerciseAttempt.status != ExerciseAttemptStatus.PENDING,
            )
            .order_by(ExerciseAttempt.attempted_at)
        ).all()

        by_question: dict[str, list[ExerciseAttempt]] = {}
        question_by_id: dict[str, InterviewQuestion] = {}
        for question, attempt in rows:
            by_question.setdefault(question.id, []).append(attempt)
            question_by_id[question.id] = question

        items: list[ReviewItem] = []
        for question_id, attempts in by_question.items():
            question = question_by_id[question_id]
            latest = attempts[-1]
            consecutive_good = 0
            for attempt in reversed(attempts):
                if (attempt.score or 0) >= 85.0:
                    consecutive_good += 1
                else:
                    break
            items.append(
                ReviewItem(
                    question_id=question_id,
                    interview_type=question.interview_type,
                    last_score=latest.score or 0.0,
                    last_attempted_at=latest.attempted_at,
                    attempt_count=len(attempts),
                    consecutive_good=consecutive_good,
                )
            )

        due = due_reviews(items, limit=limit)
        return [
            DueReviewSchema(
                question_id=d.question_id,
                slug=question_by_id[d.question_id].slug,
                title=question_by_id[d.question_id].exercise.title,
                interview_type=d.interview_type,
                last_score=d.last_score,
                days_since_last_attempt=d.days_since_last_attempt,
                interval_days=d.interval_days,
                days_overdue=d.days_overdue,
                priority=d.priority,
                reason=d.reason,
            )
            for d in due
        ]

    # --- Bookmarks ---------------------------------------------------------------

    def list_bookmarks(self, user_id: str) -> list[InterviewBookmarkSchema]:
        stmt = (
            select(InterviewBookmark)
            .where(InterviewBookmark.user_id == user_id)
            .order_by(InterviewBookmark.created_at.desc())
        )
        return [InterviewBookmarkSchema.model_validate(b) for b in self.db.execute(stmt).scalars().all()]

    def create_bookmark(self, user_id: str, payload: CreateBookmarkRequest) -> InterviewBookmarkSchema:
        if payload.target_type == InterviewTargetType.INTERVIEW:
            interview = self.db.get(Interview, payload.target_id)
            if interview is None or interview.user_id != user_id:
                raise NotFoundError(f"Interview '{payload.target_id}' not found.")
        existing = self.db.execute(
            select(InterviewBookmark).where(
                InterviewBookmark.user_id == user_id,
                InterviewBookmark.target_type == payload.target_type,
                InterviewBookmark.target_id == payload.target_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return InterviewBookmarkSchema.model_validate(existing)

        bookmark = InterviewBookmark(
            user_id=user_id, target_type=payload.target_type, target_id=payload.target_id
        )
        self.db.add(bookmark)
        self.db.commit()
        self.db.refresh(bookmark)
        return InterviewBookmarkSchema.model_validate(bookmark)

    def delete_bookmark(self, user_id: str, bookmark_id: str) -> None:
        bookmark = self.db.get(InterviewBookmark, bookmark_id)
        if bookmark is None or bookmark.user_id != user_id:
            raise NotFoundError(f"Bookmark '{bookmark_id}' not found.")
        self.db.delete(bookmark)
        self.db.commit()

    # --- Notes -------------------------------------------------------------------

    def list_notes(
        self, user_id: str, target_type: str | None = None, target_id: str | None = None
    ) -> list[InterviewNoteSchema]:
        stmt = select(InterviewNote).where(InterviewNote.user_id == user_id)
        if target_type:
            stmt = stmt.where(InterviewNote.target_type == target_type)
        if target_id:
            stmt = stmt.where(InterviewNote.target_id == target_id)
        stmt = stmt.order_by(InterviewNote.updated_at.desc())
        return [InterviewNoteSchema.model_validate(n) for n in self.db.execute(stmt).scalars().all()]

    def create_note(self, user_id: str, payload: CreateNoteRequest) -> InterviewNoteSchema:
        if payload.target_type == InterviewTargetType.INTERVIEW:
            interview = self.db.get(Interview, payload.target_id)
            if interview is None or interview.user_id != user_id:
                raise NotFoundError(f"Interview '{payload.target_id}' not found.")
        note = InterviewNote(
            user_id=user_id, target_type=payload.target_type, target_id=payload.target_id, note=payload.note
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return InterviewNoteSchema.model_validate(note)

    def update_note(self, user_id: str, note_id: str, payload: UpdateNoteRequest) -> InterviewNoteSchema:
        note = self.db.get(InterviewNote, note_id)
        if note is None or note.user_id != user_id:
            raise NotFoundError(f"Note '{note_id}' not found.")
        note.note = payload.note
        self.db.commit()
        self.db.refresh(note)
        return InterviewNoteSchema.model_validate(note)

    def delete_note(self, user_id: str, note_id: str) -> None:
        note = self.db.get(InterviewNote, note_id)
        if note is None or note.user_id != user_id:
            raise NotFoundError(f"Note '{note_id}' not found.")
        self.db.delete(note)
        self.db.commit()
