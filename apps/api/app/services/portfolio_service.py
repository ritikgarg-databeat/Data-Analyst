"""Portfolio Builder (Phase 11, spec sections 19-21, 36). Every artifact
defaults to PRIVATE (spec section 20) — nothing becomes visible without an
explicit privacy-level change by the user. Portfolio Quality Score is a
deterministic heuristic (never AI-generated); AI (PORTFOLIO_REVIEW) only
narrates around it. Portfolio Gap Detection compares real project/case
template skill lists against what's actually in the portfolio."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models.career import Portfolio, PortfolioItem, TargetRole
from app.models.case import CaseAttempt
from app.models.enums import PortfolioItemType, PrivacyLevel
from app.models.project import Project, ProjectTemplate
from app.schemas.ai import AIStructuredResponse
from app.schemas.portfolio import (
    CreatePortfolioItemRequest,
    PortfolioGapSuggestionSchema,
    PortfolioQualityScoreResponse,
    PortfolioSchema,
    UpdatePortfolioItemRequest,
    UpdatePortfolioRequest,
)
from app.services.ai_career_service import AICareerService

MAX_ITEMS_FOR_COMPLETENESS = 6


class PortfolioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, user_id: str) -> Portfolio:
        portfolio = self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        ).scalar_one_or_none()
        if portfolio is None:
            portfolio = Portfolio(user_id=user_id)
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
        return portfolio

    def get_portfolio(self, user_id: str) -> PortfolioSchema:
        return PortfolioSchema.model_validate(self.get_or_create(user_id))

    def update_portfolio(self, user_id: str, payload: UpdatePortfolioRequest) -> PortfolioSchema:
        portfolio = self.get_or_create(user_id)
        if payload.headline is not None:
            portfolio.headline = payload.headline
        if payload.about is not None:
            portfolio.about = payload.about
        if payload.is_public_ready is not None:
            portfolio.is_public_ready = payload.is_public_ready
        self.db.commit()
        self.db.refresh(portfolio)
        return PortfolioSchema.model_validate(portfolio)

    # --- Items ---------------------------------------------------------------------

    def add_item(self, user_id: str, payload: CreatePortfolioItemRequest) -> PortfolioSchema:
        portfolio = self.get_or_create(user_id)
        item = PortfolioItem(
            portfolio_id=portfolio.id,
            item_type=payload.item_type,
            ref_id=payload.ref_id,
            title=payload.title,
            description=payload.description,
            privacy=payload.privacy,
        )
        self.db.add(item)
        self.db.commit()
        return self.get_portfolio(user_id)

    def _get_owned_item(self, user_id: str, item_id: str) -> PortfolioItem:
        item = self.db.get(PortfolioItem, item_id)
        if item is None or item.portfolio.user_id != user_id:
            raise NotFoundError("Portfolio item was not found.")
        return item

    def update_item(self, user_id: str, item_id: str, payload: UpdatePortfolioItemRequest) -> PortfolioSchema:
        item = self._get_owned_item(user_id, item_id)
        for field in ("title", "description", "privacy", "display_order"):
            value = getattr(payload, field)
            if value is not None:
                setattr(item, field, value)
        self.db.commit()
        return self.get_portfolio(user_id)

    def delete_item(self, user_id: str, item_id: str) -> None:
        item = self._get_owned_item(user_id, item_id)
        self.db.delete(item)
        self.db.commit()

    # --- Quality score (deterministic) --------------------------------------------------

    def quality_score(self, user_id: str) -> PortfolioQualityScoreResponse:
        portfolio = self.get_or_create(user_id)
        items = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id)
        ).scalars().all()
        if not items:
            return PortfolioQualityScoreResponse(
                score=0.0, item_count=0, items_with_description=0, portfolio_ready_item_count=0,
                suggestions=["Add at least one project, case study, or skill highlight to your portfolio."],
            )

        described = sum(1 for i in items if i.description and i.description.strip())
        ready = sum(1 for i in items if i.privacy != PrivacyLevel.PRIVATE)
        completeness = min(len(items), MAX_ITEMS_FOR_COMPLETENESS) / MAX_ITEMS_FOR_COMPLETENESS * 40
        description_quality = (described / len(items)) * 30
        visibility = (ready / len(items)) * 30
        score = round(completeness + description_quality + visibility, 1)

        suggestions = []
        if len(items) < MAX_ITEMS_FOR_COMPLETENESS:
            suggestions.append(
                f"Add more items — a strong portfolio typically has {MAX_ITEMS_FOR_COMPLETENESS}+."
            )
        if described < len(items):
            suggestions.append(f"{len(items) - described} item(s) have no description yet.")
        if ready == 0:
            suggestions.append(
                "Every item is still PRIVATE — change privacy to PORTFOLIO or PUBLIC_READY when ready "
                "to show it."
            )
        if not any(i.item_type == PortfolioItemType.CASE_STUDY for i in items):
            suggestions.append("Consider adding a case study to show end-to-end business reasoning.")

        return PortfolioQualityScoreResponse(
            score=score, item_count=len(items), items_with_description=described,
            portfolio_ready_item_count=ready, suggestions=suggestions,
        )

    # --- AI review wrapper ---------------------------------------------------------------

    def ai_review(self, user_id: str) -> AIStructuredResponse:
        portfolio = self.get_or_create(user_id)
        items = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id)
        ).scalars().all()
        return AICareerService(self.db).review_portfolio(
            user_id,
            headline=portfolio.headline,
            items=[
                {
                    "title": i.title, "description": i.description,
                    "item_type": i.item_type.value, "privacy": i.privacy.value,
                }
                for i in items
            ],
        )

    # --- Gap detection -------------------------------------------------------------------

    def _covered_skill_slugs(self, user_id: str, portfolio_id: str) -> set[str]:
        items = self.db.execute(
            select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio_id)
        ).scalars().all()

        # Batch-fetch every referenced Project/CaseAttempt (with its
        # template/case eager-loaded) in one query per type, instead of a
        # db.get() plus a lazy-loaded relationship access per item.
        project_ref_ids = {i.ref_id for i in items if i.item_type == PortfolioItemType.PROJECT and i.ref_id}
        case_ref_ids = {i.ref_id for i in items if i.item_type == PortfolioItemType.CASE_STUDY and i.ref_id}
        projects_by_id = (
            {
                p.id: p
                for p in self.db.execute(
                    select(Project)
                    .options(selectinload(Project.template))
                    .where(Project.id.in_(project_ref_ids))
                ).scalars().all()
            }
            if project_ref_ids
            else {}
        )
        attempts_by_id = (
            {
                a.id: a
                for a in self.db.execute(
                    select(CaseAttempt)
                    .options(selectinload(CaseAttempt.case))
                    .where(CaseAttempt.id.in_(case_ref_ids))
                ).scalars().all()
            }
            if case_ref_ids
            else {}
        )

        covered: set[str] = set()
        for item in items:
            if not item.ref_id:
                continue
            if item.item_type == PortfolioItemType.PROJECT:
                project = projects_by_id.get(item.ref_id)
                if project and project.user_id == user_id and project.template is not None:
                    covered.update(project.template.required_skills or [])
            elif item.item_type == PortfolioItemType.CASE_STUDY:
                attempt = attempts_by_id.get(item.ref_id)
                if attempt and attempt.user_id == user_id:
                    covered.update(attempt.case.skills or [])
        return covered

    def detect_gaps(self, user_id: str, target_role_id: str | None) -> list[PortfolioGapSuggestionSchema]:
        portfolio = self.get_or_create(user_id)
        covered = self._covered_skill_slugs(user_id, portfolio.id)

        target_skills: set[str] = set()
        if target_role_id:
            target_role = self.db.get(TargetRole, target_role_id)
            if target_role and target_role.user_id == user_id and target_role.role_template is not None:
                target_skills = set(target_role.role_template.core_skills)

        templates = self.db.execute(
            select(ProjectTemplate).where(ProjectTemplate.is_active.is_(True))
        ).scalars().all()
        gaps = []
        for skill_slug in sorted(target_skills - covered):
            recommended = [t.slug for t in templates if skill_slug in (t.required_skills or [])][:3]
            gaps.append(
                PortfolioGapSuggestionSchema(
                    skill_slug=skill_slug, recommended_project_template_slugs=recommended
                )
            )
        return gaps
