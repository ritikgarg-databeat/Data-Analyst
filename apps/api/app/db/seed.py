"""Idempotent seed script.

Loads foundational taxonomy from `database/seeds/*.yaml` (domains, skills,
modules, datasets, tags), then syncs lesson and
exercise *content* from `content/**/*.yaml` (see app.content.sync — that is
the source of truth for lessons/exercises, not a YAML seed file). Safe to
run repeatedly — re-running upserts by natural key (slug).

Usage:
    uv run python -m app.db.seed
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.content.sync import sync as sync_content
from app.core.database import Base, SessionLocal, engine
from app.models.assessment import Assessment, AssessmentQuestion
from app.models.career import Achievement
from app.models.dataset import Dataset
from app.models.domain import Domain
from app.models.enums import AssessmentRetryPolicy, DifficultyLevel, SkillCategory
from app.models.exercise import Exercise
from app.models.metric import MetricDefinition
from app.models.module import Module
from app.models.skill import Skill
from app.models.tag import Tag
from app.sql.sync import sync as sync_sql_tables

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]
SEEDS_DIR = REPO_ROOT / "database" / "seeds"


def _load_yaml(filename: str) -> list[dict[str, Any]]:
    path = SEEDS_DIR / filename
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _seed_domains(db: Session) -> None:
    rows = _load_yaml("domains.yaml")
    for row in rows:
        domain = db.query(Domain).filter(Domain.slug == row["slug"]).one_or_none()
        if domain is None:
            domain = Domain(slug=row["slug"])
            db.add(domain)
        domain.name = row["name"]
        domain.description = row.get("description")
        domain.icon = row.get("icon")
        domain.display_order = row.get("display_order", 0)
        domain.is_active = True
    logger.info("Seeded %d domains", len(rows))


def _seed_skills(db: Session) -> None:
    rows = _load_yaml("skills.yaml")
    for row in rows:
        skill = db.query(Skill).filter(Skill.slug == row["slug"]).one_or_none()
        if skill is None:
            skill = Skill(slug=row["slug"])
            db.add(skill)
        skill.name = row["name"]
        skill.description = row.get("description")
        skill.category = SkillCategory(row["category"])
        skill.target_level = DifficultyLevel(row.get("target_level", "INTERMEDIATE"))
    logger.info("Seeded %d skills", len(rows))


def _seed_modules(db: Session) -> None:
    rows = _load_yaml("modules.yaml")
    for row in rows:
        domain = db.query(Domain).filter(Domain.slug == row["domain_slug"]).one_or_none()
        if domain is None:
            logger.warning("Skipping module '%s': unknown domain '%s'", row["slug"], row["domain_slug"])
            continue
        module = db.query(Module).filter(Module.slug == row["slug"]).one_or_none()
        if module is None:
            module = Module(slug=row["slug"])
            db.add(module)
        module.domain_id = domain.id
        module.title = row["title"]
        module.description = row.get("description")
        module.difficulty = DifficultyLevel(row.get("difficulty", "BEGINNER"))
        module.estimated_minutes = row.get("estimated_minutes", 15)
        module.display_order = row.get("display_order", 0)
        module.is_active = True
    logger.info("Seeded %d modules", len(rows))


def _seed_datasets(db: Session) -> None:
    rows = _load_yaml("datasets.yaml")
    for row in rows:
        dataset = db.query(Dataset).filter(Dataset.slug == row["slug"]).one_or_none()
        if dataset is None:
            dataset = Dataset(slug=row["slug"])
            db.add(dataset)
        dataset.name = row["name"]
        dataset.description = row.get("description")
        dataset.source = row.get("source")
        dataset.source_url = row.get("source_url")
        dataset.domain = row.get("domain")
        dataset.file_path = row.get("file_path")
        dataset.file_format = row.get("file_format")
        dataset.row_count = row.get("row_count")
        dataset.column_count = row.get("column_count")
        dataset.difficulty = DifficultyLevel(row.get("difficulty", "BEGINNER"))
        dataset.dataset_metadata = row.get("metadata")
    logger.info("Seeded %d datasets", len(rows))


def _seed_tags(db: Session) -> None:
    rows = _load_yaml("tags.yaml")
    for row in rows:
        tag = db.query(Tag).filter(Tag.slug == row["slug"]).one_or_none()
        if tag is None:
            tag = Tag(slug=row["slug"])
            db.add(tag)
        tag.name = row["name"]
    logger.info("Seeded %d tags", len(rows))


def _seed_metrics(db: Session) -> None:
    """The Metrics Library (Phase 6, spec section 42) — reference data,
    independent of lesson/exercise content sync."""
    rows = _load_yaml("metrics.yaml")
    for i, row in enumerate(rows):
        metric = db.query(MetricDefinition).filter(MetricDefinition.slug == row["slug"]).one_or_none()
        if metric is None:
            metric = MetricDefinition(slug=row["slug"])
            db.add(metric)
        metric.name = row["name"]
        metric.category = row["category"]
        metric.definition = row["definition"]
        metric.formula = row.get("formula")
        metric.examples = row.get("examples", [])
        metric.sql_example = row.get("sql_example")
        metric.python_example = row.get("python_example")
        metric.common_mistakes = row.get("common_mistakes", [])
        metric.related_metrics = row.get("related_metrics", [])
        metric.business_questions = row.get("business_questions", [])
        metric.interview_questions = row.get("interview_questions", [])
        metric.display_order = row.get("display_order", i)
    logger.info("Seeded %d metrics", len(rows))


def _seed_achievements(db: Session) -> None:
    """Badge definitions for the Career layer's Achievement System (Phase
    11, spec section 27) — reference data independent of content sync,
    exactly like _seed_metrics. Earning them is decided by
    app.services.achievement_service reading real platform events, never by
    this seed."""
    rows = _load_yaml("achievements.yaml")
    for row in rows:
        achievement = db.query(Achievement).filter(Achievement.slug == row["slug"]).one_or_none()
        if achievement is None:
            achievement = Achievement(slug=row["slug"])
            db.add(achievement)
        achievement.title = row["title"]
        achievement.description = row["description"]
        achievement.icon = row.get("icon")
        achievement.criteria = row.get("criteria", {})
        achievement.is_active = True
    logger.info("Seeded %d achievements", len(rows))


def _seed_assessments(db: Session) -> None:
    """Runs AFTER content sync — exercise_slug references must already exist."""
    rows = _load_yaml("assessments.yaml")
    for row in rows:
        module = db.query(Module).filter(Module.slug == row["module_slug"]).one_or_none()
        if module is None:
            logger.warning("Skipping assessment '%s': unknown module '%s'", row["slug"], row["module_slug"])
            continue

        assessment = db.query(Assessment).filter(Assessment.slug == row["slug"]).one_or_none()
        if assessment is None:
            assessment = Assessment(slug=row["slug"])
            db.add(assessment)
        assessment.module_id = module.id
        assessment.title = row["title"]
        assessment.description = row.get("description")
        assessment.time_limit_minutes = row.get("time_limit_minutes")
        assessment.passing_score = row.get("passing_score", 80)
        assessment.retry_policy = AssessmentRetryPolicy(row.get("retry_policy", "UNLIMITED"))
        assessment.max_attempts = row.get("max_attempts")
        assessment.is_active = True
        db.flush()

        db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).delete()
        for i, question in enumerate(row.get("questions", [])):
            exercise = db.query(Exercise).filter(Exercise.slug == question["exercise_slug"]).one_or_none()
            if exercise is None:
                logger.warning(
                    "Skipping assessment question: unknown exercise '%s'", question["exercise_slug"]
                )
                continue
            db.add(
                AssessmentQuestion(
                    assessment_id=assessment.id,
                    exercise_id=exercise.id,
                    display_order=i + 1,
                    points=question.get("points", 10),
                )
            )
    logger.info("Seeded %d assessments", len(rows))


def seed(db: Session | None = None) -> None:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        _seed_domains(session)
        _seed_skills(session)
        session.flush()  # domains/skills need ids before modules reference them
        _seed_modules(session)
        _seed_datasets(session)
        _seed_tags(session)
        _seed_metrics(session)
        _seed_achievements(session)
        session.commit()
        logger.info("Taxonomy seed complete.")

        sync_sql_tables(session)

        sync_content(session)

        _seed_assessments(session)
        session.commit()
        logger.info("Assessment seed complete.")
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    Base.metadata.create_all(bind=engine)  # convenience for non-Docker/local runs; Alembic is authoritative
    seed()
