"""Next Best Action engine (Phase 12) — a thin, read-only composition layer
over five ALREADY-EXISTING, independently-scored recommendation systems
(lesson recommendations, interview weakness detection, JD skill gaps,
portfolio gap detection, career goals). It never recomputes or duplicates
any of their scoring logic — it only picks the single highest-signal item
from each domain that has one, and returns a small, capped list so the
dashboard never overwhelms the learner with every possible thing to do.

A Phase 12 audit of the whole platform found five separate, siloed
"what should I do next" systems with no unifying layer between them — this
service is that layer, added on top, never a replacement for any of them."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.models.enums import CareerGoalStatus, JDRequirementPriority
from app.services.career_goal_service import CareerGoalService
from app.services.career_profile_service import CareerProfileService
from app.services.interview_readiness_service import InterviewReadinessService
from app.services.jd_service import JDService
from app.services.portfolio_service import PortfolioService
from app.services.recommendations import RecommendationService

ActionSource = Literal["lesson", "interview", "job_description", "portfolio", "goal"]


@dataclass
class NextBestActionItem:
    title: str
    why: str
    source: ActionSource
    url_path: str


def _humanize_skill(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


class NextBestActionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _interview_action(self, user_id: str) -> NextBestActionItem | None:
        weaknesses = InterviewReadinessService(self.db).get_weaknesses(user_id)
        if not weaknesses:
            return None
        top = max(weaknesses, key=lambda w: w.occurrences)
        return NextBestActionItem(
            title=f"Practice {top.interview_type} — {top.gap_type.replace('_', ' ').title()}",
            why=(
                f"{top.occurrences} recent occurrence(s), average score {top.average_score}. {top.detail}"
            ),
            source="interview",
            url_path="/interview",
        )

    def _job_description_action(self, user_id: str) -> NextBestActionItem | None:
        jd_service = JDService(self.db)
        jds = jd_service.list_job_descriptions(user_id)  # ordered by created_at desc
        if not jds:
            return None
        active_jd = jds[0]
        gap_table = jd_service.compute_skill_gaps(user_id, active_jd.id)
        must_have_gaps = [
            g for g in gap_table.gaps if g.gap_size > 0 and g.priority == JDRequirementPriority.MUST_HAVE
        ]
        if not must_have_gaps:
            return None
        top_gap = max(must_have_gaps, key=lambda g: g.gap_size)
        return NextBestActionItem(
            title=f"Close skill gap: {_humanize_skill(top_gap.skill_slug)}",
            why=(
                f"A must-have requirement for '{active_jd.title}'"
                f"{f' at {active_jd.company}' if active_jd.company else ''} — current mastery "
                f"{top_gap.current_mastery_score}."
            ),
            source="job_description",
            url_path=f"/career/job-descriptions/{active_jd.id}",
        )

    def _lesson_action(self, user_id: str) -> NextBestActionItem | None:
        recs = RecommendationService(self.db).get_next(user_id, limit=5)
        if not recs:
            return None
        pick = next(
            (r for r in recs if r.reason in ("weak_skill", "incomplete_prerequisite")), recs[0]
        )
        lesson = pick.lesson
        return NextBestActionItem(
            title=f"Complete: {lesson.title}",
            why=pick.explanation,
            source="lesson",
            url_path=f"/learn/{lesson.module.domain.slug}/{lesson.module.slug}/{lesson.slug}",
        )

    def _portfolio_action(self, user_id: str) -> NextBestActionItem | None:
        profile = CareerProfileService(self.db).get_or_create_profile(user_id)
        if not profile.primary_target_role_id:
            return None
        gaps = PortfolioService(self.db).detect_gaps(user_id, profile.primary_target_role_id)
        if not gaps:
            return None
        top_gap = gaps[0]
        return NextBestActionItem(
            title=f"Build portfolio evidence: {_humanize_skill(top_gap.skill_slug)}",
            why="Your primary target role expects this skill, but no portfolio item demonstrates it yet.",
            source="portfolio",
            url_path="/career/portfolio",
        )

    def _goal_action(self, user_id: str) -> NextBestActionItem | None:
        all_goals = CareerGoalService(self.db).list_goals(user_id)
        goals = [g for g in all_goals if g.status == CareerGoalStatus.ACTIVE]
        if not goals:
            return None
        today = datetime.now(UTC).date()
        overdue = [g for g in goals if g.target_date and g.target_date < today]
        pick = overdue[0] if overdue else goals[0]
        return NextBestActionItem(
            title=f"Goal check-in: {pick.title}",
            why=(
                "This goal's target date has passed — update its progress or adjust the date."
                if pick in overdue
                else "An active goal you set — keep the momentum going."
            ),
            source="goal",
            url_path="/career",
        )

    def get_actions(self, user_id: str, limit: int = 3) -> list[NextBestActionItem]:
        candidates = [
            action
            for action in (
                self._interview_action(user_id),
                self._job_description_action(user_id),
                self._lesson_action(user_id),
                self._portfolio_action(user_id),
                self._goal_action(user_id),
            )
            if action is not None
        ]
        return candidates[:limit]
