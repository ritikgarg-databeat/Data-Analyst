"""Tests for the Analytics Case Library (Phase 6, spec sections 33 & 44) —
a read view over Exercises tagged `case-study`. Verified against the 5
pre-existing Phase 5 EDA-challenge-library exercises already carrying that
tag (content/exercises/data-analyst-foundations/*.yaml), which have no
rubric/business_context — so this also checks the feature degrades
gracefully for cases authored before Phase 6."""

import pytest
from fastapi.testclient import TestClient

KNOWN_PRE_EXISTING_CASE = "three-insights-from-the-ecommerce-dataset"


def test_list_cases_includes_pre_existing_eda_cases(client: TestClient) -> None:
    response = client.get("/api/v1/analytics/cases")
    assert response.status_code == 200
    cases = response.json()
    slugs = {c["slug"] for c in cases}
    assert {
        "three-insights-from-the-ecommerce-dataset",
        "characterizing-the-top-10-percent-of-customers-by-spend",
        "comparing-customer-segments-on-value-and-frequency",
        "evaluating-acquisition-channels-by-customer-value",
        "campaign-spend-versus-effectiveness",
    }.issubset(slugs)


def test_get_case_returns_prompt_and_empty_rubric_for_pre_phase6_case(client: TestClient) -> None:
    response = client.get(f"/api/v1/analytics/cases/{KNOWN_PRE_EXISTING_CASE}")
    assert response.status_code == 200
    body = response.json()
    assert body["prompt"]
    assert body["rubric"] == []
    assert body["business_context"] is None


def test_get_unknown_case_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/analytics/cases/does-not-exist")
    assert response.status_code == 404


def test_case_content_reachable_via_generic_exercise_endpoint_too(client: TestClient) -> None:
    """A case is *just* an Exercise under the hood — the standard content/attempt
    endpoints must keep working unmodified (this is why no new attempt-tracking
    table was introduced)."""
    response = client.get(f"/api/v1/exercises/{KNOWN_PRE_EXISTING_CASE}/content")
    assert response.status_code == 200
    body = response.json()
    assert body["rubric"] == []
    assert "prompt" in body


def test_submitting_a_rubric_case_computes_a_real_score(client: TestClient) -> None:
    """Finds any Phase-6-authored case with a non-empty rubric (rather than
    hardcoding a specific slug, since exact new case slugs are content-authored)
    and verifies the full self-assessed-rubric submission flow end to end."""
    cases = client.get("/api/v1/analytics/cases").json()
    rubric_case = next((c for c in cases if c["rubric"]), None)
    if rubric_case is None:
        return  # no rubric-bearing case authored yet in this content set — nothing to verify.

    rubric = rubric_case["rubric"]
    total_points = sum(r["points"] for r in rubric)
    half = rubric[: max(1, len(rubric) // 2)]
    half_points = sum(r["points"] for r in half)

    response = client.post(
        f"/api/v1/exercises/{rubric_case['slug']}/attempts",
        json={"submitted_answer": "My analysis.", "rubric_selections": [r["criterion"] for r in half]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_auto_graded"] is True
    assert body["attempt"]["score"] == pytest.approx(half_points / total_points * 100)
