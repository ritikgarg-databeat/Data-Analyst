"""Resume Analyzer tests (Phase 11) — evidence extraction only ever quotes
real resume text (never fabricates a metric/employer/achievement), quality/
clarity/impact scores are deterministic (never AI-generated), and resume gap
analysis compares real evidence against a real target role's skill list."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_resume_with_version(client: TestClient, raw_text: str) -> dict:
    resume = client.post("/api/v1/resume", json={"title": "Test Resume", "is_primary": True}).json()
    version = client.post(
        f"/api/v1/resume/{resume['id']}/versions", json={"source": "PASTED", "raw_text": raw_text}
    ).json()
    return version


class TestEvidenceExtraction:
    def test_evidence_text_is_a_verbatim_line_from_the_resume(self, client: TestClient) -> None:
        raw_text = "Wrote complex SQL Fundamentals queries daily.\nUsed Pandas to clean large datasets."
        version = _create_resume_with_version(client, raw_text)
        evidence = client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence").json()

        assert any(e["skill_slug"] == "sql-fundamentals" for e in evidence)
        for e in evidence:
            assert e["evidence_text"] in raw_text

    def test_no_evidence_for_skills_never_mentioned(self, client: TestClient) -> None:
        version = _create_resume_with_version(client, "Managed spreadsheets in Excel Fundamentals only.")
        evidence = client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence").json()
        slugs = {e["skill_slug"] for e in evidence}
        assert "dbt" not in slugs
        assert "machine-learning-fundamentals" not in slugs

    def test_re_extraction_replaces_not_duplicates(self, client: TestClient) -> None:
        version = _create_resume_with_version(
            client, "SQL Fundamentals expert with years of Pandas experience."
        )
        first = client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence").json()
        second = client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence").json()
        assert len(first) == len(second)


class TestQualityReview:
    def test_clear_measurable_resume_scores_higher_than_vague_one(self, client: TestClient) -> None:
        strong = _create_resume_with_version(
            client,
            "Reduced churn by 12% through targeted analysis.\nBuilt 5 dashboards used by 3 teams weekly.",
        )
        weak = _create_resume_with_version(
            client,
            "Responsible for various things related to data and stuff that needed doing around the "
            "office on most days of the working week without much further specificity provided here.",
        )
        strong_review = client.post(f"/api/v1/resume/versions/{strong['id']}/review").json()
        weak_review = client.post(f"/api/v1/resume/versions/{weak['id']}/review").json()
        assert strong_review["quality_score"] > weak_review["quality_score"]

    def test_quality_score_is_deterministic_not_ai_dependent(self, client: TestClient) -> None:
        version = _create_resume_with_version(client, "Led a project. Increased revenue by 20%.")
        first = client.post(f"/api/v1/resume/versions/{version['id']}/review").json()
        second = client.post(f"/api/v1/resume/versions/{version['id']}/review").json()
        assert first["quality_score"] == second["quality_score"]
        assert first["clarity_score"] == second["clarity_score"]
        assert first["impact_score"] == second["impact_score"]


class TestGapAnalysis:
    def test_gap_analysis_flags_missing_target_role_skills(self, client: TestClient) -> None:
        target_role = client.post(
            "/api/v1/career/target-roles", json={"role_template_slug": "data-analyst"}
        ).json()
        version = _create_resume_with_version(client, "Only SQL Fundamentals mentioned here.")
        client.post(f"/api/v1/resume/versions/{version['id']}/extract-evidence")

        gap_response = client.get(
            f"/api/v1/resume/versions/{version['id']}/gap-analysis",
            params={"target_role_id": target_role["id"]},
        ).json()
        gaps_by_slug = {g["skill_slug"]: g["has_evidence"] for g in gap_response["gaps"]}
        assert gaps_by_slug.get("sql-fundamentals") is True
        assert any(has_evidence is False for has_evidence in gaps_by_slug.values())
