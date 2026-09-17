"""Career Readiness gating, Achievement idempotency, Behavioral Story
coverage, and the required 12-step Career Readiness E2E flow (Phase 11
spec): create career profile -> set target role -> paste JD -> analyze JD
-> view skill gaps -> generate preparation plan -> review resume -> map
resume evidence -> select portfolio projects -> complete missing practice
-> run readiness assessment -> view readiness -> open career report."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career import Achievement, CareerAssessment, UserAchievement
from app.models.enums import CareerReadinessLevel, CaseAttemptStatus
from app.models.project import Project
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.services.career_profile_service import CareerProfileService
from app.services.career_readiness_service import GATED_LEVELS, CareerReadinessService


class TestInterviewDimensionBlendsCategorySkills:
    """Phase 12 audit finding: SkillCategory.INTERVIEW_READINESS (interview-
    sql, analytics-case-studies, product-cases, behavioral-interviewing) fed
    into none of the 8 rubric dimensions. Fixed by blending it into
    INTERVIEW alongside the real interview-engine readiness score."""

    def test_interview_readiness_category_mastery_raises_the_interview_dimension(
        self, client: TestClient, db_session: Session
    ) -> None:
        user_id = client.get("/api/v1/users/me").json()["id"]
        service = CareerReadinessService(db_session)
        before = service.compute_rubric_scores(user_id)["INTERVIEW"]

        for slug in ("interview-sql", "analytics-case-studies", "product-cases", "behavioral-interviewing"):
            skill = db_session.query(Skill).filter(Skill.slug == slug).one()
            user_skill = (
                db_session.query(UserSkill)
                .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
                .one_or_none()
            )
            if user_skill is None:
                user_skill = UserSkill(user_id=user_id, skill_id=skill.id)
                db_session.add(user_skill)
            user_skill.mastery_score = 100.0
            user_skill.questions_attempted = 5
        db_session.commit()

        after = service.compute_rubric_scores(user_id)["INTERVIEW"]
        assert after > before


class TestReadinessGating:
    def test_one_weak_dimension_caps_an_otherwise_high_level(
        self, client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_id = client.get("/api/v1/users/me").json()["id"]
        service = CareerReadinessService(db_session)

        strong_except_portfolio = {
            "TECHNICAL": 95.0, "ANALYTICAL": 95.0, "BUSINESS": 95.0, "PRODUCT": 95.0,
            "DATA_ENGINEERING_AWARENESS": 95.0, "COMMUNICATION": 95.0, "INTERVIEW": 95.0,
            "PORTFOLIO": 10.0,
        }
        monkeypatch.setattr(service, "compute_rubric_scores", lambda _user_id: strong_except_portfolio)

        result = service.compute(user_id)
        assert result.overall_score > 75  # would qualify for STRONG_CANDIDATE or higher on score alone
        assert result.gating_passed is False
        assert result.overall_readiness_level == CareerReadinessLevel.INTERMEDIATE
        assert result.overall_readiness_level not in GATED_LEVELS

    def test_all_dimensions_strong_reaches_the_gated_level(
        self, client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_id = client.get("/api/v1/users/me").json()["id"]
        service = CareerReadinessService(db_session)

        all_strong = {dim: 95.0 for dim in [
            "TECHNICAL", "ANALYTICAL", "BUSINESS", "PRODUCT", "DATA_ENGINEERING_AWARENESS",
            "COMMUNICATION", "INTERVIEW", "PORTFOLIO",
        ]}
        monkeypatch.setattr(service, "compute_rubric_scores", lambda _user_id: all_strong)

        result = service.compute(user_id)
        assert result.gating_passed is True
        assert result.overall_readiness_level == CareerReadinessLevel.EXCEPTIONAL

    def test_explanation_always_answers_why_per_dimension(
        self, client: TestClient, db_session: Session
    ) -> None:
        user_id = client.get("/api/v1/users/me").json()["id"]
        result = CareerReadinessService(db_session).compute(user_id)
        for dimension in [
            "TECHNICAL", "ANALYTICAL", "BUSINESS", "PRODUCT", "DATA_ENGINEERING_AWARENESS",
            "COMMUNICATION", "INTERVIEW", "PORTFOLIO",
        ]:
            assert dimension in result.explanation
            assert len(result.explanation[dimension]) >= 1
        assert "overall" in result.explanation


class TestAchievementIdempotency:
    def test_syncing_twice_never_duplicates_an_earned_achievement(self, client: TestClient) -> None:
        first = client.get("/api/v1/career/achievements/earned").json()
        second = client.get("/api/v1/career/achievements/earned").json()
        first_slugs = sorted(a["achievement"]["slug"] for a in first)
        second_slugs = sorted(a["achievement"]["slug"] for a in second)
        assert first_slugs == second_slugs
        assert len(first_slugs) == len(set(first_slugs))


class TestBehavioralStoryCoverage:
    def test_missing_categories_excludes_a_category_with_a_story(self, client: TestClient) -> None:
        client.post(
            "/api/v1/career/behavioral-stories",
            json={
                "category": "FAILURE", "title": "A failure story", "situation": "s", "task": "t",
                "action": "a", "result": "r",
            },
        )
        coverage = client.get("/api/v1/career/behavioral-stories/coverage").json()
        assert "FAILURE" not in coverage["missing_categories"]
        covered_entry = next(c for c in coverage["coverage"] if c["category"] == "FAILURE")
        assert covered_entry["has_coverage"] is True
        assert covered_entry["story_count"] >= 1


class TestCareerReadinessE2EFlow:
    def test_full_12_step_flow(self, client: TestClient, db_session: Session) -> None:
        # 1. Create career profile (implicit — GET creates it on first access).
        profile = client.get("/api/v1/career/profile").json()
        assert profile["id"]

        # 2. Set target role.
        target_role = client.post(
            "/api/v1/career/target-roles",
            json={"role_template_slug": "product-analyst", "is_primary": True},
        ).json()
        client.patch("/api/v1/career/profile", json={"primary_target_role_id": target_role["id"]})

        # 3. Paste JD.
        jd = client.post(
            "/api/v1/jobs/descriptions",
            json={
                "title": "Product Analyst",
                "company": "E2E Corp",
                "source": "PASTED",
                "raw_text": (
                    "Seeking a Product Analyst with Product Metrics and Experimentation experience. "
                    "SQL Fundamentals required. Statistics knowledge is a plus."
                ),
                "target_role_id": target_role["id"],
            },
        ).json()
        client.post(f"/api/v1/jobs/descriptions/{jd['id']}/extract")

        # 4. Analyze JD.
        analysis = client.post(f"/api/v1/jobs/descriptions/{jd['id']}/analyze", json={}).json()
        assert analysis["readiness_score"] is not None

        # 5. View skill gaps.
        gaps = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/skill-gaps").json()["gaps"]
        assert len(gaps) > 0

        # 6. Generate preparation plan.
        plan = client.get(f"/api/v1/jobs/descriptions/{jd['id']}/preparation-plan").json()
        assert "tasks" in plan

        # 7. Review resume.
        resume = client.post("/api/v1/resume", json={"title": "E2E Resume", "is_primary": True}).json()
        version = client.post(
            f"/api/v1/resume/{resume['id']}/versions",
            json={"source": "PASTED", "raw_text": "Analyzed Product Metrics using SQL Fundamentals daily."},
        ).json()
        review = client.post(f"/api/v1/resume/versions/{version['id']}/review").json()
        assert review["quality_score"] is not None

        # 8. Map resume evidence.
        evidence = client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence").json()
        assert any(e["skill_slug"] == "product-metrics" for e in evidence)

        # 9. Select portfolio projects.
        portfolio = client.post(
            "/api/v1/portfolio/items",
            json={
                "item_type": "SKILL_HIGHLIGHT", "title": "Product Metrics work",
                "description": "Analyzed funnels and retention.", "privacy": "PORTFOLIO",
            },
        ).json()
        assert any(i["title"] == "Product Metrics work" for i in portfolio["items"])

        # 10. Complete missing practice — close one real gap by recording real mastery.
        gapped_slug = next(g["skill_slug"] for g in gaps if g["gap_size"] > 0)
        skill = db_session.query(Skill).filter(Skill.slug == gapped_slug).one()
        user_id = client.get("/api/v1/users/me").json()["id"]
        user_skill = (
            db_session.query(UserSkill)
            .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill.id)
            .one_or_none()
        )
        if user_skill is None:
            user_skill = UserSkill(user_id=user_id, skill_id=skill.id)
            db_session.add(user_skill)
        user_skill.mastery_score = 90.0
        user_skill.questions_attempted = 3
        db_session.commit()

        # 11. Run readiness assessment.
        assessment = client.post(
            "/api/v1/career/readiness/compute", json={"target_role_id": target_role["id"]}
        ).json()
        assert assessment["overall_readiness_level"] in [level.value for level in CareerReadinessLevel]

        # 12. View readiness + open career report.
        latest = client.get("/api/v1/career/readiness/latest").json()
        assert latest["id"] == assessment["id"]

        report = client.get("/api/v1/career/report").json()
        assert report["latest_assessment"]["id"] == assessment["id"]
        assert any(r["id"] == target_role["id"] for r in report["target_roles"])


class TestDashboardAndReportSyncAchievementsBeforeCounting:
    """Regression tests — `get_dashboard`/`get_report` used to count
    UserAchievement rows without ever calling AchievementService.sync_for_user
    first, so a badge earned by a just-completed skill/case/project only
    showed up once the user separately opened the Career Analytics
    achievements panel (the one actual caller of sync_for_user). Uses a
    synthetic user_id (unenforced FK on SQLite, same convention as
    test_ai_lifecycle.py's TestConversationHistoryRedaction) so this is
    fully isolated from the shared dev user other tests in this session
    exercise."""

    def test_dashboard_reflects_a_freshly_earned_achievement_with_no_prior_sync_call(
        self, db_session: Session
    ) -> None:
        user_id = "dashboard-achievement-sync-test-user"
        skill = db_session.execute(select(Skill)).scalars().first()
        db_session.add(
            UserSkill(user_id=user_id, skill_id=skill.id, mastery_score=95.0, questions_attempted=5)
        )
        db_session.commit()

        # Ground truth: this freshly-created user has never been synced, so no
        # UserAchievement row exists yet even though they now qualify.
        assert db_session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars().all() == []

        dashboard = CareerProfileService(db_session).get_dashboard(user_id)

        earned = db_session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars().all()
        assert len(earned) >= 1
        assert dashboard.achievement_count == len(earned)

    def test_report_reflects_a_freshly_earned_achievement_with_no_prior_sync_call(
        self, db_session: Session
    ) -> None:
        user_id = "report-achievement-sync-test-user"
        skill = db_session.execute(select(Skill)).scalars().first()
        db_session.add(
            UserSkill(user_id=user_id, skill_id=skill.id, mastery_score=95.0, questions_attempted=5)
        )
        db_session.commit()

        assert db_session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars().all() == []

        report = CareerProfileService(db_session).get_report(user_id)

        earned = db_session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).scalars().all()
        assert len(earned) >= 1
        assert report.achievement_count == len(earned)


class TestMilestoneTimelineDedupesByTitleAndTimestamp:
    """Regression test — `_existing_titles` used to dedupe on title alone, so
    a second genuine completion of the SAME project/case/interview template
    (a fully supported retry — see ProjectService/CaseService/
    InterviewService) was silently dropped as if it were a duplicate sync of
    the first completion. Keying on (title, achieved_at) instead lets two
    real completions at different real timestamps both appear, while a true
    duplicate sync (re-running for an already-recorded event) still
    correctly no-ops."""

    def test_two_genuine_completions_of_the_same_project_both_appear_and_a_resync_does_not_duplicate_them(
        self, db_session: Session
    ) -> None:
        user_id = "milestone-retry-dedup-test-user"
        title = "Completed project: Retail Churn Analysis"
        first_completed_at = datetime(2026, 1, 1, 12, 0, 0)
        second_completed_at = datetime(2026, 2, 1, 12, 0, 0)
        db_session.add_all(
            [
                Project(
                    user_id=user_id, name="Retail Churn Analysis",
                    status=CaseAttemptStatus.COMPLETED, completed_at=first_completed_at,
                ),
                Project(
                    user_id=user_id, name="Retail Churn Analysis",
                    status=CaseAttemptStatus.COMPLETED, completed_at=second_completed_at,
                ),
            ]
        )
        db_session.commit()

        service = CareerProfileService(db_session)
        milestones = service.sync_milestones(user_id)
        matching = [m for m in milestones if m.title == title]
        assert len(matching) == 2

        # A resync (e.g. a second dashboard load) must not duplicate either
        # genuine completion — this is the real duplicate-sync case.
        resynced = service.sync_milestones(user_id)
        resynced_matching = [m for m in resynced if m.title == title]
        assert len(resynced_matching) == 2


class TestReadinessLevelUpMilestones:
    """Regression tests for CareerMilestoneType.READINESS_LEVEL_UP, one of
    three enum values (alongside ASSESSMENT_PASSED, ACHIEVEMENT_EARNED) that
    were defined but never synced into the Career Progress Timeline at all.
    A "level up" is recorded only the first time a NEW PEAK readiness level
    is reached — readiness fluctuates run to run, so every recomputation
    would otherwise spam a milestone even when the trend is flat or down."""

    def test_only_new_peak_levels_are_recorded_a_regression_in_between_is_skipped(
        self, db_session: Session
    ) -> None:
        user_id = "readiness-level-up-test-user"
        timestamps = [datetime(2026, 1, d, 12, 0, 0) for d in (1, 2, 3, 4)]
        levels = [
            CareerReadinessLevel.FOUNDATION,
            CareerReadinessLevel.INTERMEDIATE,
            CareerReadinessLevel.DEVELOPING,  # a regression relative to INTERMEDIATE — not a new peak
            CareerReadinessLevel.EXCEPTIONAL,
        ]
        for ts, level in zip(timestamps, levels, strict=True):
            db_session.add(
                CareerAssessment(
                    user_id=user_id,
                    rubric_scores={},
                    overall_score=50.0,
                    overall_readiness_level=level,
                    explanation={},
                    computed_at=ts,
                )
            )
        db_session.commit()

        service = CareerProfileService(db_session)
        milestones = service.sync_milestones(user_id)
        level_up_titles = sorted(
            m.title for m in milestones if m.milestone_type == "READINESS_LEVEL_UP"
        )
        assert level_up_titles == [
            "Reached EXCEPTIONAL readiness",
            "Reached FOUNDATION readiness",
            "Reached INTERMEDIATE readiness",
        ]

        # Resyncing must not duplicate any of the three real level-ups.
        resynced = service.sync_milestones(user_id)
        resynced_level_ups = [m for m in resynced if m.milestone_type == "READINESS_LEVEL_UP"]
        assert len(resynced_level_ups) == 3


class TestAchievementEarnedMilestones:
    """Regression test for CareerMilestoneType.ACHIEVEMENT_EARNED — also
    defined but never synced. sync_milestones() now syncs achievements
    FIRST, so a badge earned during this same call (e.g. from
    _sync_mastery_milestones' own mastery check) is reflected as a milestone
    in the same pass rather than needing a second call."""

    def test_a_freshly_earned_achievement_is_recorded_as_a_milestone_in_the_same_sync_call(
        self, db_session: Session
    ) -> None:
        user_id = "achievement-earned-milestone-test-user"
        skill = db_session.execute(select(Skill)).scalars().first()
        db_session.add(
            UserSkill(user_id=user_id, skill_id=skill.id, mastery_score=95.0, questions_attempted=5)
        )
        db_session.commit()

        service = CareerProfileService(db_session)
        milestones = service.sync_milestones(user_id)

        earned = db_session.execute(
            select(UserAchievement, Achievement)
            .join(Achievement, Achievement.id == UserAchievement.achievement_id)
            .where(UserAchievement.user_id == user_id)
        ).all()
        assert len(earned) >= 1
        expected_titles = {f"Earned achievement: {a.title}" for _, a in earned}
        actual_titles = {m.title for m in milestones if m.milestone_type == "ACHIEVEMENT_EARNED"}
        assert actual_titles == expected_titles

        # Resyncing must not duplicate the achievement milestone.
        resynced = service.sync_milestones(user_id)
        resynced_titles = {m.title for m in resynced if m.milestone_type == "ACHIEVEMENT_EARNED"}
        assert resynced_titles == expected_titles
