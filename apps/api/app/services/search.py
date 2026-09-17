"""Application-wide content search.

Phase 2 uses a portable case-insensitive substring match (SQLAlchemy
`.ilike()`, which works identically on SQLite and PostgreSQL) across
title/name/description, rather than PostgreSQL `tsvector`/GIN indexes —
this keeps the exact same search code path exercised by the fast SQLite
test suite as by production Postgres (see docs/architecture.md). The
service's public interface (`SearchService.search`) doesn't leak this
choice to callers, so swapping in `tsvector` full-text (or, later,
semantic/vector search) behind the same method signature is a drop-in
upgrade, not a rewrite.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.domain import Domain
from app.models.exercise import Exercise
from app.models.interview import InterviewQuestion
from app.models.lesson import Lesson
from app.models.metric import MetricDefinition
from app.models.module import Module
from app.models.project import ProjectTemplate
from app.models.skill import Skill

SearchKind = Literal[
    "domain", "module", "lesson", "skill", "exercise", "case", "project", "interview_question", "metric"
]
ALL_KINDS: tuple[SearchKind, ...] = (
    "domain", "module", "lesson", "skill", "exercise", "case", "project", "interview_question", "metric",
)


@dataclass
class SearchResult:
    kind: SearchKind
    id: str
    slug: str
    title: str
    description: str | None
    url_path: str


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self, query: str, kinds: tuple[SearchKind, ...] = ALL_KINDS, limit: int = 25
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []
        pattern = f"%{query}%"
        results: list[SearchResult] = []

        if "domain" in kinds:
            for d in (
                self.db.query(Domain)
                .filter(Domain.name.ilike(pattern) | Domain.description.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult("domain", d.id, d.slug, d.name, d.description, f"/learn/{d.slug}")
                )

        if "module" in kinds:
            for m in (
                self.db.query(Module)
                .filter(Module.title.ilike(pattern) | Module.description.ilike(pattern))
                .limit(limit)
            ):
                domain = self.db.get(Domain, m.domain_id)
                url = f"/learn/{domain.slug}/{m.slug}" if domain else f"/learn/{m.slug}"
                results.append(SearchResult("module", m.id, m.slug, m.title, m.description, url))

        if "lesson" in kinds:
            for lesson_row in (
                self.db.query(Lesson)
                .filter(Lesson.title.ilike(pattern) | Lesson.description.ilike(pattern))
                .limit(limit)
            ):
                module = self.db.get(Module, lesson_row.module_id)
                domain = self.db.get(Domain, module.domain_id) if module else None
                url = (
                    f"/learn/{domain.slug}/{module.slug}/{lesson_row.slug}"
                    if domain and module
                    else f"/learn/{lesson_row.slug}"
                )
                results.append(
                    SearchResult(
                        "lesson",
                        lesson_row.id,
                        lesson_row.slug,
                        lesson_row.title,
                        lesson_row.description,
                        url,
                    )
                )

        if "skill" in kinds:
            for s in (
                self.db.query(Skill)
                .filter(Skill.name.ilike(pattern) | Skill.description.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult("skill", s.id, s.slug, s.name, s.description, f"/skills#{s.slug}")
                )

        if "exercise" in kinds:
            for e in (
                self.db.query(Exercise)
                .filter(Exercise.title.ilike(pattern) | Exercise.description.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult("exercise", e.id, e.slug, e.title, e.description, f"/practice/{e.slug}")
                )

        if "case" in kinds:
            for c in (
                self.db.query(Case)
                .filter(Case.title.ilike(pattern) | Case.problem_statement.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult(
                        "case", c.id, c.slug, c.title, c.problem_statement, f"/case-studies/{c.slug}"
                    )
                )

        if "project" in kinds:
            for p in (
                self.db.query(ProjectTemplate)
                .filter(ProjectTemplate.title.ilike(pattern) | ProjectTemplate.objective.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult(
                        "project", p.id, p.slug, p.title, p.objective, f"/projects/templates/{p.slug}"
                    )
                )

        if "interview_question" in kinds:
            for q, exercise_row in (
                self.db.query(InterviewQuestion, Exercise)
                .join(Exercise, Exercise.id == InterviewQuestion.exercise_id)
                .filter(Exercise.title.ilike(pattern) | Exercise.description.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult(
                        "interview_question",
                        q.id,
                        q.slug,
                        exercise_row.title,
                        exercise_row.description,
                        f"/interview/questions/{q.slug}",
                    )
                )

        if "metric" in kinds:
            for m in (
                self.db.query(MetricDefinition)
                .filter(MetricDefinition.name.ilike(pattern) | MetricDefinition.definition.ilike(pattern))
                .limit(limit)
            ):
                results.append(
                    SearchResult("metric", m.id, m.slug, m.name, m.definition, f"/metrics#{m.slug}")
                )

        return results[:limit]
