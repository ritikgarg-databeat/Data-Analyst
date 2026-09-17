"""AI Layer (Phase 10 infrastructure) extension for the Career layer (Phase
11) — JD requirement extraction, resume review, career coaching, portfolio
review. Mirrors `app/services/ai_coach_service.py`'s composition pattern:
wraps `AIService`'s shared dispatch plumbing, takes already-fetched real
context from its callers (JDService/ResumeService/PortfolioService/routers)
rather than querying the DB itself, and never persists anything — callers
own persistence and own validating any AI-suggested skill slug against the
real taxonomy before storing it (see JD_EXTRACTION's prompt docstring)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import AIFeature
from app.schemas.ai import AIChatResponse, AIStructuredResponse
from app.services.ai_service import AIService


class AICareerService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.ai = AIService(db, settings)

    def extract_jd_requirements(
        self, user_id: str, *, raw_text: str, known_skill_slugs: list[str]
    ) -> AIStructuredResponse:
        context_payload = {"raw_text": raw_text, "known_skill_slugs": known_skill_slugs}
        return self.ai._structured_dispatch(  # noqa: SLF001 — intra-package reuse of shared dispatch plumbing
            user_id=user_id,
            feature=AIFeature.JD_EXTRACTION,
            context_payload=context_payload,
            user_message="Extract structured requirements from this job description.",
            context_type="job_description",
        )

    def review_resume(
        self, user_id: str, *, resume_text: str, target_role: str | None, evidence: list[dict]
    ) -> AIStructuredResponse:
        context_payload = {"resume_text": resume_text, "target_role": target_role, "evidence": evidence}
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.RESUME_REVIEW,
            context_payload=context_payload,
            user_message="Review this resume.",
            context_type="resume",
        )

    def review_portfolio(
        self, user_id: str, *, headline: str | None, items: list[dict]
    ) -> AIStructuredResponse:
        context_payload = {"headline": headline, "items": items}
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.PORTFOLIO_REVIEW,
            context_payload=context_payload,
            user_message="Review this portfolio.",
            context_type="portfolio",
        )

    def career_coach(
        self, user_id: str, *, message: str, topic: str, career_context: dict, conversation_id: str | None
    ) -> AIChatResponse:
        context_payload = {"topic": topic, "career_context": career_context}
        return self.ai._chat_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.CAREER_COACH,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="career",
            context_id=None,
            mode="COACH",
        )
