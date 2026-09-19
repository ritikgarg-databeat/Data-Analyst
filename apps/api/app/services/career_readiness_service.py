"""Career Readiness Rubric (Phase 11, spec sections 23-24) — reads the
existing deterministic engines (MasteryService via UserSkill, the Case/
Project/Interview engines, InterviewReadinessService) as INPUT SIGNALS and
computes its own 8-dimension rubric + gated Final Readiness Level on top.
Never a second, competing mastery/interview score — see
app/models/enums.py's Phase 11 section header.

`overall_readiness_level` and `gating_passed` explicitly never imply a
correspondence to an actual hiring decision (spec section 24) — this is the
platform's own estimate of preparation, always paired with `explanation`
answering "why" per dimension (spec section 35)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.career import CareerAssessment, Portfolio, PortfolioItem, TargetRole
from app.models.enums import CareerReadinessLevel, CareerRubricDimension, PrivacyLevel, SkillCategory
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.schemas.career import CareerAssessmentSchema
from app.services.interview_readiness_service import InterviewReadinessService

DEFAULT_RUBRIC_WEIGHTS: dict[str, float] = {
    CareerRubricDimension.TECHNICAL: 20.0,
    CareerRubricDimension.ANALYTICAL: 15.0,
    CareerRubricDimension.BUSINESS: 12.5,
    CareerRubricDimension.PRODUCT: 10.0,
    CareerRubricDimension.DATA_ENGINEERING_AWARENESS: 10.0,
    CareerRubricDimension.COMMUNICATION: 12.5,
    CareerRubricDimension.INTERVIEW: 12.5,
    CareerRubricDimension.PORTFOLIO: 7.0,
}

TECHNICAL_CATEGORIES = [
    SkillCategory.SQL,
    SkillCategory.PYTHON,
    SkillCategory.EXCEL,
    SkillCategory.DATA_VISUALIZATION,
]
ANALYTICAL_CATEGORIES = [SkillCategory.STATISTICS, SkillCategory.MACHINE_LEARNING]
DATA_ENGINEERING_CATEGORIES = [
    SkillCategory.DATA_ENGINEERING,
    SkillCategory.DATA_WAREHOUSING,
    SkillCategory.DATA_MODELING,
]
COMMUNICATION_SKILL_SLUG = "communication"

# Level thresholds on the 0-100 weighted overall score.
LEVEL_THRESHOLDS: list[tuple[float, CareerReadinessLevel]] = [
    (90, CareerReadinessLevel.EXCEPTIONAL),
    (75, CareerReadinessLevel.STRONG_CANDIDATE),
    (60, CareerReadinessLevel.INTERVIEW_READY),
    (40, CareerReadinessLevel.INTERMEDIATE),
    (20, CareerReadinessLevel.DEVELOPING),
    (0, CareerReadinessLevel.FOUNDATION),
]
# A single strong dimension must never hide major weaknesses elsewhere (spec
# section 25's gating requirement) — every dimension must clear this floor
# before INTERVIEW_READY or above is reachable, regardless of overall score.
GATING_MINIMUM_PER_DIMENSION = 40.0
GATED_LEVELS = {
    CareerReadinessLevel.INTERVIEW_READY,
    CareerReadinessLevel.STRONG_CANDIDATE,
    CareerReadinessLevel.EXCEPTIONAL,
}


class CareerReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Per-dimension scoring -------------------------------------------------

    def _category_average(self, user_id: str, categories: list[SkillCategory]) -> tuple[float, int]:
        skills = self.db.execute(select(Skill).where(Skill.category.in_(categories))).scalars().all()
        if not skills:
            return 0.0, 0
        user_skills = {
            us.skill_id: us
            for us in self.db.execute(select(UserSkill).where(UserSkill.user_id == user_id)).scalars().all()
        }
        scores = [user_skills[s.id].mastery_score for s in skills if s.id in user_skills]
        return (round(sum(scores) / len(skills), 1), len(skills))

    def _communication_score(self, user_id: str) -> float:
        skill = self.db.execute(
            select(Skill).where(Skill.slug == COMMUNICATION_SKILL_SLUG)
        ).scalar_one_or_none()
        if skill is None:
            return 0.0
        row = self.db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
        ).scalar_one_or_none()
        return row.mastery_score if row else 0.0

    def _interview_score(self, user_id: str) -> float:
        # Blends the real interview-engine readiness score (mock/timed
        # interview performance) with the INTERVIEW_READINESS-category
        # skills (interview-sql, analytics-case-studies, product-cases,
        # behavioral-interviewing) — found by a Phase 12 audit to be the
        # only SkillCategory never feeding any of the 8 rubric dimensions.
        engine_score = InterviewReadinessService(self.db).get_readiness(user_id).overall_score
        category_score, category_count = self._category_average(user_id, [SkillCategory.INTERVIEW_READINESS])
        if category_count == 0:
            return engine_score
        return round(0.7 * engine_score + 0.3 * category_score, 1)

    def _portfolio_score(self, user_id: str) -> float:
        portfolio = self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        ).scalar_one_or_none()
        if portfolio is None:
            return 0.0
        items = (
            self.db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
            .scalars()
            .all()
        )
        if not items:
            return 0.0
        described = sum(1 for i in items if i.description and i.description.strip())
        visible = sum(1 for i in items if i.privacy != PrivacyLevel.PRIVATE)
        # Completeness (up to 6 items counted), description quality, and
        # actually being visible beyond PRIVATE all matter — a portfolio full
        # of undescribed PRIVATE items scores near zero on purpose.
        completeness = min(len(items), 6) / 6 * 40
        description_quality = (described / len(items)) * 30
        visibility = (visible / len(items)) * 30
        return round(completeness + description_quality + visibility, 1)

    def compute_rubric_scores(self, user_id: str) -> dict[str, float]:
        technical, _ = self._category_average(user_id, TECHNICAL_CATEGORIES)
        analytical, _ = self._category_average(user_id, ANALYTICAL_CATEGORIES)
        business, _ = self._category_average(user_id, [SkillCategory.BUSINESS_ANALYTICS])
        product, _ = self._category_average(user_id, [SkillCategory.PRODUCT_ANALYTICS])
        data_eng, _ = self._category_average(user_id, DATA_ENGINEERING_CATEGORIES)
        return {
            CareerRubricDimension.TECHNICAL: technical,
            CareerRubricDimension.ANALYTICAL: analytical,
            CareerRubricDimension.BUSINESS: business,
            CareerRubricDimension.PRODUCT: product,
            CareerRubricDimension.DATA_ENGINEERING_AWARENESS: data_eng,
            CareerRubricDimension.COMMUNICATION: self._communication_score(user_id),
            CareerRubricDimension.INTERVIEW: self._interview_score(user_id),
            CareerRubricDimension.PORTFOLIO: self._portfolio_score(user_id),
        }

    # --- Level + gating ---------------------------------------------------------

    def _level_for_score(self, score: float) -> CareerReadinessLevel:
        for threshold, level in LEVEL_THRESHOLDS:
            if score >= threshold:
                return level
        return CareerReadinessLevel.FOUNDATION

    def _explanation(self, scores: dict[str, float], weights: dict[str, float]) -> dict[str, list[str]]:
        explanation: dict[str, list[str]] = {}
        for dimension, score in scores.items():
            weight = weights.get(dimension, 0.0)
            reasons = [f"Scored {score} (weight {weight}% of overall)."]
            if score < GATING_MINIMUM_PER_DIMENSION:
                reasons.append(
                    f"Below the {GATING_MINIMUM_PER_DIMENSION}-point minimum required across every "
                    "dimension to reach Interview-Ready or above."
                )
            explanation[dimension] = reasons
        return explanation

    def compute(self, user_id: str, target_role_id: str | None = None) -> CareerAssessmentSchema:
        if target_role_id is not None:
            target_role = self.db.get(TargetRole, target_role_id)
            if target_role is None or target_role.user_id != user_id:
                raise NotFoundError("Target role was not found.")

        weights = DEFAULT_RUBRIC_WEIGHTS
        scores = self.compute_rubric_scores(user_id)
        total_weight = sum(weights.values())
        overall_score = round(sum(scores[dim] * weight for dim, weight in weights.items()) / total_weight, 1)

        raw_level = self._level_for_score(overall_score)
        gating_passed = all(score >= GATING_MINIMUM_PER_DIMENSION for score in scores.values())
        if raw_level in GATED_LEVELS and not gating_passed:
            # Cap at the tier just below the gated tiers rather than silently
            # inflating a level a real weakness would undermine.
            level = CareerReadinessLevel.INTERMEDIATE
        else:
            level = raw_level

        explanation = self._explanation(scores, weights)
        explanation.setdefault("overall", []).append(
            f"Overall score {overall_score} maps to raw level {raw_level.value}"
            + ("" if level == raw_level else f", capped to {level.value} because gating did not pass")
            + ". This is the platform's own estimate of preparation, not a guarantee of any real "
            "employer's hiring decision."
        )

        assessment = CareerAssessment(
            user_id=user_id,
            target_role_id=target_role_id,
            rubric_scores=scores,
            overall_score=overall_score,
            overall_readiness_level=level,
            gating_passed=gating_passed,
            explanation=explanation,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return CareerAssessmentSchema.model_validate(assessment)

    def get_latest(self, user_id: str) -> CareerAssessmentSchema | None:
        row = (
            self.db.execute(
                select(CareerAssessment)
                .where(CareerAssessment.user_id == user_id)
                .order_by(CareerAssessment.computed_at.desc())
            )
            .scalars()
            .first()
        )
        return CareerAssessmentSchema.model_validate(row) if row else None

    def get_history(self, user_id: str) -> list[CareerAssessmentSchema]:
        rows = (
            self.db.execute(
                select(CareerAssessment)
                .where(CareerAssessment.user_id == user_id)
                .order_by(CareerAssessment.computed_at.asc())
            )
            .scalars()
            .all()
        )
        return [CareerAssessmentSchema.model_validate(r) for r in rows]
