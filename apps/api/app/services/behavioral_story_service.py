"""Behavioral Story Bank + Interview Story Coverage (Phase 11, spec section
38). `category` matches the real tag taxonomy already used by Phase 9's
behavioral exercises (content/exercises/behavioral/*.yaml) — coverage is
computed against that same fixed 12-category list."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import BehavioralStory
from app.models.enums import BehavioralStoryCategory
from app.schemas.career import (
    BehavioralStorySchema,
    CreateBehavioralStoryRequest,
    StoryCoverageEntrySchema,
    StoryCoverageResponse,
    UpdateBehavioralStoryRequest,
)


class BehavioralStoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_stories(self, user_id: str) -> list[BehavioralStorySchema]:
        rows = self.db.execute(
            select(BehavioralStory)
            .where(BehavioralStory.user_id == user_id)
            .order_by(BehavioralStory.created_at)
        ).scalars().all()
        return [BehavioralStorySchema.model_validate(s) for s in rows]

    def create_story(self, user_id: str, payload: CreateBehavioralStoryRequest) -> BehavioralStorySchema:
        story = BehavioralStory(
            user_id=user_id,
            category=payload.category,
            title=payload.title,
            situation=payload.situation,
            task=payload.task,
            action=payload.action,
            result=payload.result,
        )
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)
        return BehavioralStorySchema.model_validate(story)

    def _get_owned(self, user_id: str, story_id: str) -> BehavioralStory:
        story = self.db.get(BehavioralStory, story_id)
        if story is None or story.user_id != user_id:
            raise NotFoundError("Behavioral story was not found.")
        return story

    def update_story(
        self, user_id: str, story_id: str, payload: UpdateBehavioralStoryRequest
    ) -> BehavioralStorySchema:
        story = self._get_owned(user_id, story_id)
        for field in ("title", "situation", "task", "action", "result"):
            value = getattr(payload, field)
            if value is not None:
                setattr(story, field, value)
        self.db.commit()
        self.db.refresh(story)
        return BehavioralStorySchema.model_validate(story)

    def delete_story(self, user_id: str, story_id: str) -> None:
        story = self._get_owned(user_id, story_id)
        self.db.delete(story)
        self.db.commit()

    def mark_practiced(self, user_id: str, story_id: str) -> BehavioralStorySchema:
        story = self._get_owned(user_id, story_id)
        story.last_practiced_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(story)
        return BehavioralStorySchema.model_validate(story)

    def get_coverage(self, user_id: str) -> StoryCoverageResponse:
        rows = self.db.execute(
            select(BehavioralStory.category).where(BehavioralStory.user_id == user_id)
        ).scalars().all()
        counts: dict[BehavioralStoryCategory, int] = {c: 0 for c in BehavioralStoryCategory}
        for category in rows:
            counts[category] += 1

        coverage = [
            StoryCoverageEntrySchema(category=c, story_count=n, has_coverage=n > 0) for c, n in counts.items()
        ]
        missing = [c for c, n in counts.items() if n == 0]
        return StoryCoverageResponse(coverage=coverage, missing_categories=missing)
