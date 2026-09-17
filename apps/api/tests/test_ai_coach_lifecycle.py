"""Integration tests for the Phase 10 AI Layer's case/interview/project
coaching endpoints (app/services/ai_coach_service.py) — real Case/Interview/
Project content, `AI_PROVIDER=local` by default for structural checks, plus
one `monkeypatch`-installed fake provider (mirrors this suite's existing
mocking style — see test_python_lab_security.py's mock_docker_module) for
the one behavior that specifically needs realistic structured JSON back:
the Case Interviewer's revealed-topic tracking across turns."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import AIProviderResponse, AIProviderUsage
from app.models.ai import AISkillDiagnosis
from app.models.case import Case
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.project import ProjectTemplate

CORRECT_SQL = (
    "SELECT ROUND(SUM(quantity * unit_price * (1 - discount / 100.0)), 2) AS total_revenue FROM order_items;"
)


def _start_any_case_attempt(client: TestClient, db_session: Session) -> str:
    case = db_session.execute(select(Case).where(Case.is_active.is_(True))).scalars().first()
    assert case is not None, "expected at least one active seeded case"
    response = client.post(f"/api/v1/cases/{case.slug}/start")
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _complete_any_interview(client: TestClient, db_session: Session) -> str:
    from app.models.interview import InterviewQuestion

    question = (
        db_session.execute(
            select(InterviewQuestion).where(
                InterviewQuestion.interview_type == "SQL", InterviewQuestion.is_active.is_(True)
            )
        )
        .scalars()
        .first()
    )
    assert question is not None

    created = client.post("/api/v1/interviews", json={"mode": "PRACTICE", "question_id": question.id})
    assert created.status_code == 201, created.text
    interview_id = created.json()["id"]
    answered = client.post(f"/api/v1/interviews/{interview_id}/answer", json={"submitted_query": CORRECT_SQL})
    assert answered.status_code == 200, answered.text
    assert answered.json()["interview"]["status"] == "COMPLETED"
    return interview_id


class TestCaseCoach:
    def test_case_coach_replies_without_leaking_hidden_case_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        attempt_id = _start_any_case_attempt(client, db_session)
        response = client.post(
            f"/api/v1/ai/cases/{attempt_id}/coach",
            json={"message": "What should I clarify first?", "coaching_mode": "STANDARD"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["conversation_id"]
        assert body["reply"]

    def test_unknown_attempt_id_404s(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ai/cases/not-a-real-attempt-id/coach",
            json={"message": "hi", "coaching_mode": "STANDARD"},
        )
        assert response.status_code == 404


class TestCaseInterviewer:
    def test_a_turn_replies_and_persists_a_conversation(
        self, client: TestClient, db_session: Session
    ) -> None:
        attempt_id = _start_any_case_attempt(client, db_session)
        response = client.post(
            f"/api/v1/ai/cases/{attempt_id}/interviewer",
            json={"message": "Did this happen across all segments?"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["conversation_id"]

    def test_revealed_topics_accumulate_across_turns_with_a_realistic_provider(
        self, client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Uses a fake provider (matching this suite's existing style of
        mocking an entire external client — see test_python_lab_security.py)
        that actually returns realistic structured JSON, since the default
        LocalProvider can't produce valid structured output and would make
        this specific tracking behavior untestable."""

        class _FakeInterviewerProvider:
            name = "fake"
            calls = 0

            def generate(self, messages, *, max_tokens: int, temperature: float = 0.3):
                _FakeInterviewerProvider.calls += 1
                keys = ["0"] if _FakeInterviewerProvider.calls == 1 else ["1"]
                text = json.dumps(
                    {
                        "interviewer_message": "Good question.",
                        "revealed_info_keys": keys,
                        "follow_up_asked": True,
                    }
                )
                return AIProviderResponse(text=text, model="fake", usage=AIProviderUsage(10, 10))

        monkeypatch.setattr(
            "app.services.ai_service.build_provider",
            lambda settings, provider_override=None: _FakeInterviewerProvider(),
        )

        attempt_id = _start_any_case_attempt(client, db_session)
        first = client.post(
            f"/api/v1/ai/cases/{attempt_id}/interviewer",
            json={"message": "Did this happen across all segments?"},
        )
        assert first.status_code == 200, first.text
        conversation_id = first.json()["conversation_id"]
        assert first.json()["structured"]["revealed_info_keys"] == ["0"]

        second = client.post(
            f"/api/v1/ai/cases/{attempt_id}/interviewer",
            json={"message": "Did anything change recently?", "conversation_id": conversation_id},
        )
        assert second.status_code == 200, second.text
        assert second.json()["structured"]["revealed_info_keys"] == ["1"]

        detail = client.get(f"/api/v1/ai/conversations/{conversation_id}").json()
        assert len(detail["messages"]) == 4


class TestInterviewDebrief:
    def test_debrief_narrates_a_real_completed_interview(
        self, client: TestClient, db_session: Session
    ) -> None:
        interview_id = _complete_any_interview(client, db_session)
        response = client.post(f"/api/v1/ai/interviews/{interview_id}/debrief")
        assert response.status_code == 200, response.text
        assert response.json()["raw_text"]

    def test_debrief_of_an_incomplete_interview_fails_cleanly(
        self, client: TestClient, db_session: Session
    ) -> None:
        from app.models.interview import InterviewQuestion

        question = (
            db_session.execute(
                select(InterviewQuestion).where(
                    InterviewQuestion.interview_type == "SQL", InterviewQuestion.is_active.is_(True)
                )
            )
            .scalars()
            .first()
        )
        created = client.post("/api/v1/interviews", json={"mode": "PRACTICE", "question_id": question.id})
        interview_id = created.json()["id"]
        response = client.post(f"/api/v1/ai/interviews/{interview_id}/debrief")
        assert response.status_code == 400


class TestLearningPlanExplanation:
    def test_explains_every_real_day_even_without_a_configured_provider(self, client: TestClient) -> None:
        """AI_PROVIDER=local (this environment's default) never returns valid
        structured JSON, so this asserts the fallback populates a real
        explanation for every day of the real plan rather than an empty
        list — the bug this test guards against."""
        plan = client.post("/api/v1/interview/recommendations/plan")
        assert plan.status_code == 201, plan.text
        plan_id = plan.json()["id"]
        real_day_numbers = {d["day_number"] for d in plan.json()["days"]}

        response = client.post("/api/v1/ai/plan/explain", json={"plan_id": plan_id})
        assert response.status_code == 200, response.text
        explanations = response.json()["day_explanations"]
        assert {e["day_number"] for e in explanations} == real_day_numbers
        assert all(e["why"] for e in explanations)

    def test_unknown_plan_id_404s(self, client: TestClient) -> None:
        response = client.post("/api/v1/ai/plan/explain", json={"plan_id": "not-a-real-plan-id"})
        assert response.status_code == 404


class TestDomainCoach:
    def test_domain_coach_accepts_an_arbitrary_real_result_payload(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ai/coach/domain",
            json={
                "domain": "EXPERIMENTATION",
                "question": "Is this significant?",
                "result_ref": {
                    "p_value": 0.03,
                    "verdict": "Statistically significant but too small to matter",
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["raw_text"]


class TestSkillDiagnosis:
    def test_diagnose_skill_persists_a_diagnosis_row(self, client: TestClient, db_session: Session) -> None:
        exercise = db_session.execute(select(Exercise).where(Exercise.is_active.is_(True))).scalars().first()
        assert exercise is not None
        attempt = ExerciseAttempt(
            user_id=_seeded_user_id(db_session), exercise_id=exercise.id, score=80.0, submitted_answer="x"
        )
        db_session.add(attempt)
        db_session.commit()

        before = db_session.query(AISkillDiagnosis).count()
        response = client.post("/api/v1/ai/skill-diagnosis", json={"exercise_attempt_id": attempt.id})
        assert response.status_code == 200, response.text
        assert response.json()["diagnosis_summary"]
        assert db_session.query(AISkillDiagnosis).count() == before + 1


class TestProjectReview:
    def test_project_review_works_end_to_end(self, client: TestClient, db_session: Session) -> None:
        template = (
            db_session.execute(select(ProjectTemplate).where(ProjectTemplate.is_active.is_(True)))
            .scalars()
            .first()
        )
        assert template is not None, "expected at least one active seeded project template"
        created = client.post("/api/v1/projects/from-template", json={"template_slug": template.slug})
        assert created.status_code in (200, 201), created.text
        project_id = created.json()["id"]

        response = client.post(f"/api/v1/ai/projects/{project_id}/review")
        assert response.status_code == 200, response.text
        assert response.json()["raw_text"]


def _seeded_user_id(db_session: Session) -> str:
    from app.models.user import User

    user = db_session.query(User).first()
    assert user is not None
    return user.id
