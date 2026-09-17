"""Regression test for a Phase 12 performance fix — the Career Skill Matrix
computed evidence for all 38 skills via `compute_skill_evidence` in a loop
(~5 queries per skill, re-fetching the same "all completed projects"/"all
completed case attempts" rows every time). `compute_all_skill_evidence`
fetches each source table once and must produce IDENTICAL results."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.services.career_evidence import compute_all_skill_evidence, compute_skill_evidence


def test_batch_evidence_matches_per_skill_evidence_exactly(client: TestClient, db_session: Session) -> None:
    user_id = client.get("/api/v1/users/me").json()["id"]
    # Touch a few real signals so the comparison isn't over an all-zero matrix.
    client.get("/api/v1/career/skill-matrix")

    slugs = [s.slug for s in db_session.query(Skill).all()]
    batch = compute_all_skill_evidence(db_session, user_id)

    assert set(batch.keys()) == set(slugs)
    for slug in slugs:
        individual = compute_skill_evidence(db_session, user_id, slug)
        assert batch[slug].mastery_score == individual.mastery_score
        assert batch[slug].exercises_passed == individual.exercises_passed
        assert batch[slug].projects_count == individual.projects_count
        assert batch[slug].cases_count == individual.cases_count
        assert batch[slug].mock_interview_score == individual.mock_interview_score
        assert batch[slug].evidence_level == individual.evidence_level
