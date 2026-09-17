"""Findings, hypotheses, and evidence (Phase 8, spec sections 15-18, 52) —
shared by the Case Study Engine and the Project Engine (exactly one of
`case_attempt_id`/`project_id` is set on each row) rather than two
near-duplicate services, the same reasoning Phase 7 used to unify the Data
Modeler/Architecture/Pipeline graph schema.

Every mutation here first verifies the parent CaseAttempt/Project actually
belongs to `user_id` — like the rest of this codebase, an unauthorized
target 404s rather than leaking whether it exists.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models.case import CaseAttempt
from app.models.enums import EvidenceType, FindingConfidence, HypothesisStatus
from app.models.finding import Evidence, Finding, Hypothesis
from app.models.project import Project


class FindingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Ownership checks ------------------------------------------------

    def _assert_case_attempt_owned(self, user_id: str, case_attempt_id: str) -> None:
        attempt = self.db.get(CaseAttempt, case_attempt_id)
        if attempt is None or attempt.user_id != user_id:
            raise NotFoundError(f"Case attempt '{case_attempt_id}' not found.")

    def _assert_project_owned(self, user_id: str, project_id: str) -> None:
        project = self.db.get(Project, project_id)
        if project is None or project.user_id != user_id:
            raise NotFoundError(f"Project '{project_id}' not found.")

    def _assert_owner(self, user_id: str, *, case_attempt_id: str | None, project_id: str | None) -> None:
        if bool(case_attempt_id) == bool(project_id):
            raise AppError("Exactly one of case_attempt_id/project_id must be set.")
        if case_attempt_id:
            self._assert_case_attempt_owned(user_id, case_attempt_id)
        if project_id:
            self._assert_project_owned(user_id, project_id)

    def _get_owned_finding(self, user_id: str, finding_id: str) -> Finding:
        finding = self.db.get(Finding, finding_id)
        if finding is None:
            raise NotFoundError(f"Finding '{finding_id}' not found.")
        self._assert_owner(user_id, case_attempt_id=finding.case_attempt_id, project_id=finding.project_id)
        return finding

    def _get_owned_hypothesis(self, user_id: str, hypothesis_id: str) -> Hypothesis:
        hypothesis = self.db.get(Hypothesis, hypothesis_id)
        if hypothesis is None:
            raise NotFoundError(f"Hypothesis '{hypothesis_id}' not found.")
        self._assert_owner(user_id, case_attempt_id=hypothesis.case_attempt_id, project_id=hypothesis.project_id)
        return hypothesis

    # --- Findings ----------------------------------------------------------

    def list_findings(
        self, user_id: str, *, case_attempt_id: str | None = None, project_id: str | None = None
    ) -> list[Finding]:
        self._assert_owner(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        stmt = select(Finding).order_by(Finding.display_order, Finding.created_at)
        stmt = stmt.where(Finding.case_attempt_id == case_attempt_id) if case_attempt_id else stmt.where(
            Finding.project_id == project_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_finding(
        self,
        user_id: str,
        *,
        case_attempt_id: str | None = None,
        project_id: str | None = None,
        observation: str,
        evidence_text: str | None = None,
        impact: str | None = None,
        confidence: FindingConfidence | None = None,
        related_analysis: str | None = None,
    ) -> Finding:
        self._assert_owner(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        existing_count = len(
            self.list_findings(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        )
        finding = Finding(
            case_attempt_id=case_attempt_id,
            project_id=project_id,
            observation=observation,
            evidence_text=evidence_text,
            impact=impact,
            confidence=confidence,
            related_analysis=related_analysis,
            display_order=existing_count,
        )
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def update_finding(
        self,
        user_id: str,
        finding_id: str,
        *,
        observation: str | None = None,
        evidence_text: str | None = None,
        impact: str | None = None,
        confidence: FindingConfidence | None = None,
        related_analysis: str | None = None,
    ) -> Finding:
        finding = self._get_owned_finding(user_id, finding_id)
        if observation is not None:
            finding.observation = observation
        if evidence_text is not None:
            finding.evidence_text = evidence_text
        if impact is not None:
            finding.impact = impact
        if confidence is not None:
            finding.confidence = confidence
        if related_analysis is not None:
            finding.related_analysis = related_analysis
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def delete_finding(self, user_id: str, finding_id: str) -> None:
        finding = self._get_owned_finding(user_id, finding_id)
        self.db.delete(finding)
        self.db.commit()

    def add_finding_evidence(
        self,
        user_id: str,
        finding_id: str,
        *,
        evidence_type: EvidenceType,
        ref_id: str | None,
        label: str,
        snapshot: str | None,
    ) -> Evidence:
        self._get_owned_finding(user_id, finding_id)  # ownership check
        evidence = Evidence(
            finding_id=finding_id, evidence_type=evidence_type, ref_id=ref_id, label=label, snapshot=snapshot
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    # --- Hypotheses ----------------------------------------------------------

    def list_hypotheses(
        self, user_id: str, *, case_attempt_id: str | None = None, project_id: str | None = None
    ) -> list[Hypothesis]:
        self._assert_owner(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        stmt = select(Hypothesis).order_by(Hypothesis.display_order, Hypothesis.created_at)
        stmt = stmt.where(Hypothesis.case_attempt_id == case_attempt_id) if case_attempt_id else stmt.where(
            Hypothesis.project_id == project_id
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_hypothesis(
        self,
        user_id: str,
        *,
        case_attempt_id: str | None = None,
        project_id: str | None = None,
        statement: str,
    ) -> Hypothesis:
        self._assert_owner(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        existing_count = len(
            self.list_hypotheses(user_id, case_attempt_id=case_attempt_id, project_id=project_id)
        )
        hypothesis = Hypothesis(
            case_attempt_id=case_attempt_id,
            project_id=project_id,
            statement=statement,
            display_order=existing_count,
        )
        self.db.add(hypothesis)
        self.db.commit()
        self.db.refresh(hypothesis)
        return hypothesis

    def update_hypothesis(
        self,
        user_id: str,
        hypothesis_id: str,
        *,
        statement: str | None = None,
        status: HypothesisStatus | None = None,
        evidence_text: str | None = None,
    ) -> Hypothesis:
        hypothesis = self._get_owned_hypothesis(user_id, hypothesis_id)
        if statement is not None:
            hypothesis.statement = statement
        if status is not None:
            hypothesis.status = status
        if evidence_text is not None:
            hypothesis.evidence_text = evidence_text
        self.db.commit()
        self.db.refresh(hypothesis)
        return hypothesis

    def delete_hypothesis(self, user_id: str, hypothesis_id: str) -> None:
        hypothesis = self._get_owned_hypothesis(user_id, hypothesis_id)
        self.db.delete(hypothesis)
        self.db.commit()

    def add_hypothesis_evidence(
        self,
        user_id: str,
        hypothesis_id: str,
        *,
        evidence_type: EvidenceType,
        ref_id: str | None,
        label: str,
        snapshot: str | None,
    ) -> Evidence:
        self._get_owned_hypothesis(user_id, hypothesis_id)  # ownership check
        evidence = Evidence(
            hypothesis_id=hypothesis_id, evidence_type=evidence_type, ref_id=ref_id, label=label, snapshot=snapshot
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def delete_evidence(self, user_id: str, evidence_id: str) -> None:
        evidence = self.db.get(Evidence, evidence_id)
        if evidence is None:
            raise NotFoundError(f"Evidence '{evidence_id}' not found.")
        if evidence.finding_id:
            self._get_owned_finding(user_id, evidence.finding_id)
        else:
            self._get_owned_hypothesis(user_id, evidence.hypothesis_id)  # type: ignore[arg-type]
        self.db.delete(evidence)
        self.db.commit()
