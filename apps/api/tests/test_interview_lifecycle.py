"""Integration tests for the Phase 9 Interview Engine's live session lifecycle
(`/api/v1/interviews*`), exercised through the real API against authored
content (the `sql-discount-percent-revenue` interview question, the
`interview-dau-decline-investigation` interview case, and the
`mock-analyst-quick` template) — real SQL grading, real Case Study Engine
reuse, real deterministic scoring, all through actual HTTP calls."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

CORRECT_SQL = (
    "SELECT ROUND(SUM(quantity * unit_price * (1 - discount / 100.0)), 2) AS total_revenue FROM order_items;"
)


@pytest.fixture(autouse=True)
def _only_discount_sql_question_is_selectable(db_session: Session):
    """This whole test file is written against ONE specific, known SQL
    question (`sql-discount-percent-revenue`) so its exact correct-answer
    query and skill can be asserted on. The adaptive-selection pool now has
    dozens of real SQL questions (Phase 9's authored question bank), so
    without this, `select_next_question` could deterministically-but-
    unpredictably pick any of them. Deactivating every other SQL question for
    the duration of this file's tests keeps selection pinned to the one this
    file actually knows about, and restores everything afterward since the
    test DB is shared across the whole session."""
    from app.models.interview import InterviewQuestion

    sql_questions = db_session.query(InterviewQuestion).filter(InterviewQuestion.interview_type == "SQL").all()
    originally_active = {q.id: q.is_active for q in sql_questions}
    for q in sql_questions:
        q.is_active = q.slug == "sql-discount-percent-revenue"
    db_session.commit()
    yield
    for q in sql_questions:
        q.is_active = originally_active[q.id]
    db_session.commit()


@pytest.fixture
def _only_dau_case_is_selectable(db_session: Session):
    """Pins Case Study round selection to one specific, known case
    (`interview-dau-decline-investigation`) so a test can submit it and
    assert on the result — mirrors `_only_discount_sql_question_is_
    selectable` above, but for Cases: `_pick_interview_case` picks the first
    not-yet-used case tagged "interview" ordered by title, and there are now
    15 real ones, so without this the choice is deterministic-but-
    unpredictable from a test's perspective. Function-scoped (not autouse)
    since only one test below needs it."""
    from app.models.case import Case

    interview_cases = [c for c in db_session.query(Case).all() if "interview" in c.tags]
    originally_active = {c.id: c.is_active for c in interview_cases}
    for c in interview_cases:
        c.is_active = c.slug == "interview-dau-decline-investigation"
    db_session.commit()
    yield
    for c in interview_cases:
        c.is_active = originally_active[c.id]
    db_session.commit()


def _create_practice_sql_interview(client: TestClient, question_count: int = 1) -> dict:
    response = client.post(
        "/api/v1/interviews",
        json={"mode": "PRACTICE", "interview_type": "SQL", "time_limit_seconds": 600, "question_count": question_count},
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestAdHocPracticeInterview:
    def test_create_start_answer_completes_a_single_question_interview(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        assert interview["status"] == "NOT_STARTED"
        assert interview["sections"][0]["interview_type"] == "SQL"

        started = client.post(f"/api/v1/interviews/{interview['id']}/start").json()
        assert started["status"] == "IN_PROGRESS"
        current = started["current_question"]
        assert current is not None
        assert current["question"]["exercise_type"] == "SQL"
        assert "sql_solution_query" not in current["question"] or current["question"].get("sql_solution_query") is None

        answered = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        assert answered["score"] == 100.0
        assert answered["is_auto_graded"] is True
        assert answered["interview"]["status"] == "COMPLETED"
        assert answered["interview"]["score"]["overall"] > 0
        dims = {d["dimension"]: d["score"] for d in answered["interview"]["score"]["dimensions"]}
        assert dims["Technical Correctness"] == 100.0

    def test_wrong_answer_still_completes_but_scores_low(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        answered = client.post(
            f"/api/v1/interviews/{interview['id']}/answer",
            json={"submitted_query": "SELECT 1 AS total_revenue"},
        ).json()
        assert answered["score"] is not None
        assert answered["score"] < 70.0

    def test_answering_before_starting_is_rejected(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        response = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        )
        assert response.status_code == 400

    def test_hidden_answer_fields_never_reach_the_client(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        started = client.post(f"/api/v1/interviews/{interview['id']}/start").json()
        question = started["current_question"]["question"]
        assert "sql_solution_query" not in question
        assert "reference_solution" not in question
        assert "solution" not in question


class TestTimerEnforcement:
    """Server-side-only timer validation (spec sections 34/58) — the backend
    must compute elapsed time from its own stored timestamps and never trust
    a client-reported duration, cutting the interview off with an automatic
    submission once the real elapsed time exceeds the limit."""

    def test_answering_past_the_time_limit_auto_submits_instead_of_grading(
        self, client: TestClient, db_session
    ) -> None:
        from datetime import UTC, datetime, timedelta

        from app.models.interview import Interview

        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        row = db_session.get(Interview, interview["id"])
        row.total_time_limit_seconds = 60
        row.started_at = datetime.now(UTC) - timedelta(seconds=120)
        db_session.commit()

        response = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        )
        assert response.status_code == 400

        after = client.get(f"/api/v1/interviews/{interview['id']}").json()
        assert after["status"] == "COMPLETED"

    def test_a_stale_get_request_alone_auto_submits_a_timed_out_interview(
        self, client: TestClient, db_session
    ) -> None:
        from datetime import UTC, datetime, timedelta

        from app.models.interview import Interview

        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        row = db_session.get(Interview, interview["id"])
        row.total_time_limit_seconds = 60
        row.started_at = datetime.now(UTC) - timedelta(seconds=120)
        db_session.commit()

        after = client.get(f"/api/v1/interviews/{interview['id']}").json()
        assert after["status"] == "COMPLETED"
        assert after["score"] is not None  # scored from whatever was answered so far (nothing, here)


class TestPauseResume:
    def test_pause_then_resume_accumulates_real_elapsed_time_and_keeps_progressing(
        self, client: TestClient
    ) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        paused = client.post(f"/api/v1/interviews/{interview['id']}/pause").json()
        assert paused["status"] == "PAUSED"

        resumed = client.post(f"/api/v1/interviews/{interview['id']}/resume").json()
        assert resumed["status"] == "IN_PROGRESS"

        answered = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        assert answered["interview"]["status"] == "COMPLETED"

    def test_cannot_pause_an_interview_that_has_not_started(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        response = client.post(f"/api/v1/interviews/{interview['id']}/pause")
        assert response.status_code == 400


class TestAbandon:
    def test_abandon_marks_status_and_blocks_further_actions(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        abandoned = client.post(f"/api/v1/interviews/{interview['id']}/abandon").json()
        assert abandoned["status"] == "ABANDONED"

        response = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        )
        assert response.status_code == 400


class TestMockTemplateWithCaseStudyRound:
    def test_two_round_mock_interview_advances_through_sql_then_a_real_case_attempt(
        self, client: TestClient
    ) -> None:
        templates = client.get("/api/v1/interviews/templates").json()
        assert any(t["slug"] == "mock-analyst-quick" for t in templates)

        created = client.post(
            "/api/v1/interviews", json={"mode": "MOCK", "template_slug": "mock-analyst-quick"}
        ).json()
        assert [s["interview_type"] for s in created["sections"]] == ["SQL", "CASE_STUDY"]

        started = client.post(f"/api/v1/interviews/{created['id']}/start").json()
        assert started["current_question"]["question"]["interview_type"] == "SQL"

        answered = client.post(
            f"/api/v1/interviews/{created['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        interview = answered["interview"]
        assert interview["status"] == "IN_PROGRESS"  # one round left
        current = interview["current_question"]
        assert current["case_attempt_id"] is not None
        assert current["case_attempt_status"] == "IN_PROGRESS"

        # Complete the Case Study round through the REAL, separate Case Study
        # Engine (exactly like the frontend redirecting to the Case Workspace).
        case_attempt_id = current["case_attempt_id"]
        client.patch(f"/api/v1/cases/attempts/{case_attempt_id}/clarification", json={"questions": "What changed?"})
        client.patch(
            f"/api/v1/cases/attempts/{case_attempt_id}/framing",
            json={
                "framing": {
                    "problem": "Confirm and localize the DAU decline.",
                    "objective": "Determine if the drop is real.",
                    "primary_metric": "DAU",
                    "scope": "Last 14 days",
                    "hypotheses": "Tracking artifact vs. real decline",
                }
            },
        )
        client.patch(
            f"/api/v1/cases/attempts/{case_attempt_id}/datasets", json={"dataset_slugs": ["saas-product"]}
        )
        client.patch(
            f"/api/v1/cases/attempts/{case_attempt_id}/recommendation",
            json={
                "recommendation": {
                    "recommendation": "Investigate further",
                    "why": "Confirmed via raw events",
                    "expected_impact": "Faster resolution",
                    "risks": "Single bad day",
                    "implementation_considerations": "Segment by platform",
                    "next_steps": "Segment by platform",
                }
            },
        )
        client.patch(
            f"/api/v1/cases/attempts/{case_attempt_id}/executive-summary",
            json={
                "executive_summary": {
                    "problem": "DAU dropped 18%",
                    "key_findings": "Confirmed, localized",
                    "business_impact": "Avoid overreacting",
                    "recommendation": "Investigate segment",
                    "next_steps": "Open investigation",
                }
            },
        )
        submitted = client.post(f"/api/v1/cases/attempts/{case_attempt_id}/submit", json={"rubric_selections": {}})
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "COMPLETED"

        # The interview only notices via its own GET (spec-consistent: the
        # frontend returns here after the Case Workspace finishes).
        refreshed = client.get(f"/api/v1/interviews/{created['id']}").json()
        assert refreshed["status"] == "COMPLETED"
        assert refreshed["score"]["overall"] > 0


class TestReadinessAndPlan:
    def test_readiness_weaknesses_and_plan_are_reachable_after_a_completed_interview(
        self, client: TestClient
    ) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")
        answered = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        # A single-question interview auto-completes on its last answer — a
        # readiness snapshot is taken then, without needing an explicit /submit.
        assert answered["interview"]["status"] == "COMPLETED"

        readiness = client.get("/api/v1/interview/readiness")
        assert readiness.status_code == 200
        assert 0.0 <= readiness.json()["overall_score"] <= 100.0

        history = client.get("/api/v1/interview/readiness/history")
        assert history.status_code == 200
        assert len(history.json()) >= 1

        weaknesses = client.get("/api/v1/interview/recommendations/weaknesses")
        assert weaknesses.status_code == 200

        plan = client.post("/api/v1/interview/recommendations/plan")
        assert plan.status_code == 201
        body = plan.json()
        assert len(body["days"]) == 7
        assert body["days"][-2]["task_type"] == "MOCK_INTERVIEW"
        assert body["days"][-1]["task_type"] == "REVIEW"

        fetched_plan = client.get("/api/v1/interview/recommendations/plan")
        assert fetched_plan.status_code == 200
        assert fetched_plan.json()["id"] == body["id"]

    def test_a_completed_case_study_round_contributes_to_the_readiness_breakdown(
        self, client: TestClient, _only_dau_case_is_selectable
    ) -> None:
        """Case Study rounds score via `case_attempt_id`, not
        `exercise_attempt_id` — a real, previously-latent gap let every other
        round type feed the per-type breakdown while Case Study never did."""
        interview = client.post(
            "/api/v1/interviews",
            json={"mode": "PRACTICE", "interview_type": "CASE_STUDY", "question_count": 1},
        ).json()
        started = client.post(f"/api/v1/interviews/{interview['id']}/start").json()
        case_attempt_id = started["current_question"]["case_attempt_id"]
        assert case_attempt_id

        submitted = client.post(f"/api/v1/cases/attempts/{case_attempt_id}/submit", json={"rubric_selections": {}})
        assert submitted.status_code == 200, submitted.text

        # The interview self-heals to COMPLETED on its next GET, once it
        # notices the Case Study round's case attempt is done.
        finished = client.get(f"/api/v1/interviews/{interview['id']}").json()
        assert finished["status"] == "COMPLETED"

        readiness = client.get("/api/v1/interview/readiness").json()
        assert "CASE_STUDY" in readiness["breakdown"]
        assert 0.0 <= readiness["breakdown"]["CASE_STUDY"] <= 100.0


class TestQuestionCatalogBookmarksAndNotes:
    def test_list_and_get_question_catalog(self, client: TestClient) -> None:
        listing = client.get("/api/v1/interview/questions", params={"interview_type": "SQL"}).json()
        assert any(q["slug"] == "sql-discount-percent-revenue" for q in listing)

        detail = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()
        assert detail["prompt"]
        assert "sql_solution_query" not in detail

    def test_bookmark_create_list_delete(self, client: TestClient) -> None:
        question = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()

        created = client.post(
            "/api/v1/interview/bookmarks", json={"target_type": "QUESTION", "target_id": question["id"]}
        )
        assert created.status_code == 201
        bookmark_id = created.json()["id"]

        listed = client.get("/api/v1/interview/bookmarks").json()
        assert any(b["id"] == bookmark_id for b in listed)

        detail_after = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()
        assert detail_after["is_bookmarked"] is True

        deleted = client.delete(f"/api/v1/interview/bookmarks/{bookmark_id}")
        assert deleted.status_code == 204

    def test_note_create_update_delete(self, client: TestClient) -> None:
        question = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()

        created = client.post(
            "/api/v1/interview/notes",
            json={"target_type": "QUESTION", "target_id": question["id"], "note": "Remember: check MIN/MAX first."},
        )
        assert created.status_code == 201
        note_id = created.json()["id"]

        updated = client.patch(f"/api/v1/interview/notes/{note_id}", json={"note": "Updated note."})
        assert updated.status_code == 200
        assert updated.json()["note"] == "Updated note."

        deleted = client.delete(f"/api/v1/interview/notes/{note_id}")
        assert deleted.status_code == 204

    def test_review_queue_endpoint_is_reachable_and_excludes_a_just_attempted_question(
        self, client: TestClient
    ) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")
        client.post(f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": "SELECT 1"})

        response = client.get("/api/v1/interview/questions/review-queue")
        assert response.status_code == 200
        # A question answered moments ago hasn't reached even its shortest
        # (1-day, for a miss) rest interval yet -> not due for review yet.
        assert not any(item["slug"] == "sql-discount-percent-revenue" for item in response.json())


class TestReview:
    def test_review_is_rejected_before_the_interview_is_finished(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")

        response = client.get(f"/api/v1/interviews/{interview['id']}/review")
        assert response.status_code == 400

    def test_review_after_completion_reveals_answer_details_and_test_outcomes(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")
        client.post(f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL})

        response = client.get(f"/api/v1/interviews/{interview['id']}/review")
        assert response.status_code == 200
        body = response.json()
        assert body["interview"]["status"] == "COMPLETED"
        assert len(body["questions"]) == 1

        q = body["questions"][0]
        assert q["question_slug"] == "sql-discount-percent-revenue"
        assert q["score"] == 100.0
        assert q["passed"] is True
        assert q["explanation"]
        assert q["submitted_answer"] == CORRECT_SQL
        assert q["skill_slug"] == "data-quality-engineering"
        assert any(t["name"] for t in q["test_outcomes"])

    def test_review_of_a_case_study_round_shows_the_case_title_and_score(
        self, client: TestClient, _only_dau_case_is_selectable
    ) -> None:
        created = client.post(
            "/api/v1/interviews", json={"mode": "MOCK", "template_slug": "mock-analyst-quick"}
        ).json()
        client.post(f"/api/v1/interviews/{created['id']}/start")
        answered = client.post(
            f"/api/v1/interviews/{created['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        case_attempt_id = answered["interview"]["current_question"]["case_attempt_id"]

        client.patch(f"/api/v1/cases/attempts/{case_attempt_id}/framing", json={
            "framing": {
                "problem": "p", "objective": "o", "primary_metric": "m", "scope": "s", "hypotheses": "h",
            }
        })
        client.post(f"/api/v1/cases/attempts/{case_attempt_id}/submit", json={"rubric_selections": {}})
        client.get(f"/api/v1/interviews/{created['id']}")  # let the interview self-heal to COMPLETED

        review = client.get(f"/api/v1/interviews/{created['id']}/review").json()
        case_review = next(q for q in review["questions"] if q["interview_type"] == "CASE_STUDY")
        assert case_review["title"] == "Why Did Daily Active Users Drop 18% This Week?"
        assert case_review["case_slug"] == "interview-dau-decline-investigation"
        assert case_review["score"] is not None


class TestRetry:
    def test_retry_full_creates_a_new_interview_and_preserves_the_original(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")
        original_completed = client.post(
            f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()["interview"]
        assert original_completed["status"] == "COMPLETED"

        retried = client.post(f"/api/v1/interviews/{interview['id']}/retry", json={"scope": "FULL"})
        assert retried.status_code == 201
        new_interview = retried.json()
        assert new_interview["id"] != interview["id"]
        assert new_interview["status"] == "NOT_STARTED"

        # The original attempt's history and score must survive untouched.
        original_after = client.get(f"/api/v1/interviews/{interview['id']}").json()
        assert original_after["status"] == "COMPLETED"
        assert original_after["score"]["overall"] == original_completed["score"]["overall"]


class TestCreateInterviewPinnedToQuestion:
    def test_question_id_pins_the_exact_question_and_auto_starts(self, client: TestClient) -> None:
        question = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()

        created = client.post("/api/v1/interviews", json={"mode": "PRACTICE", "question_id": question["id"]})
        assert created.status_code == 201
        body = created.json()
        assert body["status"] == "IN_PROGRESS"
        assert body["current_question"]["question"]["slug"] == "sql-discount-percent-revenue"

        answered = client.post(
            f"/api/v1/interviews/{body['id']}/answer", json={"submitted_query": CORRECT_SQL}
        ).json()
        assert answered["interview"]["status"] == "COMPLETED"

    def test_retry_question_pins_the_exact_same_question(self, client: TestClient) -> None:
        interview = _create_practice_sql_interview(client)
        client.post(f"/api/v1/interviews/{interview['id']}/start")
        client.post(f"/api/v1/interviews/{interview['id']}/answer", json={"submitted_query": CORRECT_SQL})

        question = client.get("/api/v1/interview/questions/sql-discount-percent-revenue").json()
        retried = client.post(
            f"/api/v1/interviews/{interview['id']}/retry",
            json={"scope": "QUESTION", "interview_question_id": question["id"]},
        )
        assert retried.status_code == 201
        new_interview = retried.json()
        assert new_interview["mode"] == "PRACTICE"
        assert new_interview["status"] == "IN_PROGRESS"
        assert new_interview["current_question"]["question"]["slug"] == "sql-discount-percent-revenue"

    def test_retry_section_of_a_template_interview(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/interviews", json={"mode": "MOCK", "template_slug": "mock-analyst-quick"}
        ).json()
        sql_section_id = created["sections"][0]["id"]

        retried = client.post(
            f"/api/v1/interviews/{created['id']}/retry",
            json={"scope": "SECTION", "section_id": sql_section_id},
        )
        assert retried.status_code == 201
        new_interview = retried.json()
        assert [s["interview_type"] for s in new_interview["sections"]] == ["SQL"]


class TestWeaknessDrill:
    def test_weakness_drill_with_no_interview_type_auto_targets_something_real(self, client: TestClient) -> None:
        response = client.post("/api/v1/interviews", json={"mode": "WEAKNESS_DRILL"})
        assert response.status_code == 201
        body = response.json()
        assert body["sections"][0]["interview_type"]  # a real, non-empty interview_type was chosen


class TestContentAdmin:
    def test_list_and_toggle_question_admin(self, client: TestClient) -> None:
        listing = client.get("/api/v1/interview/questions/admin")
        assert listing.status_code == 200
        question = next(q for q in listing.json() if q["slug"] == "sql-discount-percent-revenue")
        assert question["exercise_slug"] == "de-sql-discount-percent-revenue"
        assert question["is_active"] is True

        deactivated = client.patch(
            f"/api/v1/interview/questions/admin/{question['id']}", json={"is_active": False}
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["is_active"] is False

        catalog_after = client.get("/api/v1/interview/questions").json()
        assert not any(q["slug"] == "sql-discount-percent-revenue" for q in catalog_after)

        # restore, so later tests in this module still see the question active
        client.patch(f"/api/v1/interview/questions/admin/{question['id']}", json={"is_active": True})

    def test_list_and_toggle_template_admin(self, client: TestClient) -> None:
        listing = client.get("/api/v1/interviews/templates/admin")
        assert listing.status_code == 200
        template = next(t for t in listing.json() if t["slug"] == "mock-analyst-quick")
        assert template["section_count"] == 2

        deactivated = client.patch(
            f"/api/v1/interviews/templates/admin/{template['id']}", json={"is_active": False}
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["is_active"] is False

        public_listing = client.get("/api/v1/interviews/templates").json()
        assert not any(t["slug"] == "mock-analyst-quick" for t in public_listing)

        client.patch(f"/api/v1/interviews/templates/admin/{template['id']}", json={"is_active": True})
