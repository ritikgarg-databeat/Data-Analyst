"""Career Knowledge Base (Phase 11, spec section 39) — a small, feature-
scoped note model (see CareerNote's docstring for why this doesn't reuse
InterviewNote's target_type/target_id shape)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import CareerNote
from app.schemas.career import CareerNoteSchema, CreateCareerNoteRequest, UpdateCareerNoteRequest


class CareerNoteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_notes(self, user_id: str, query: str | None = None) -> list[CareerNoteSchema]:
        stmt = select(CareerNote).where(CareerNote.user_id == user_id)
        rows = self.db.execute(stmt.order_by(CareerNote.updated_at.desc())).scalars().all()
        if query:
            needle = query.lower()
            rows = [
                r for r in rows
                if needle in r.body.lower() or (r.topic and needle in r.topic.lower())
            ]
        return [CareerNoteSchema.model_validate(r) for r in rows]

    def create_note(self, user_id: str, payload: CreateCareerNoteRequest) -> CareerNoteSchema:
        note = CareerNote(user_id=user_id, topic=payload.topic, body=payload.body)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return CareerNoteSchema.model_validate(note)

    def _get_owned(self, user_id: str, note_id: str) -> CareerNote:
        note = self.db.get(CareerNote, note_id)
        if note is None or note.user_id != user_id:
            raise NotFoundError("Career note was not found.")
        return note

    def update_note(self, user_id: str, note_id: str, payload: UpdateCareerNoteRequest) -> CareerNoteSchema:
        note = self._get_owned(user_id, note_id)
        if payload.topic is not None:
            note.topic = payload.topic
        if payload.body is not None:
            note.body = payload.body
        self.db.commit()
        self.db.refresh(note)
        return CareerNoteSchema.model_validate(note)

    def delete_note(self, user_id: str, note_id: str) -> None:
        note = self._get_owned(user_id, note_id)
        self.db.delete(note)
        self.db.commit()
