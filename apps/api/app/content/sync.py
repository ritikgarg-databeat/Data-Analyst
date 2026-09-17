"""Content sync CLI — reconciles content/**/*.yaml into PostgreSQL.

Usage:
    uv run --project apps/api python -m app.content.sync

The filesystem (content/) is the source of truth for lesson/exercise
*content*; this command derives the corresponding Lesson/Exercise rows plus
their Tag/Skill/Dataset/Prerequisite/RelatedLesson relationships and upserts
them by slug — safe to re-run. A lesson or exercise previously synced but no
longer present on disk is deactivated (is_active=False), never deleted, so
progress history referencing it is preserved.

Refuses to run against invalid content — run `python -m app.content.validate`
first (this command runs the same validation and aborts on failure).
"""

from __future__ import annotations

import logging
import sys

from sqlalchemy.orm import Session

from app.content.loader import load_all
from app.content.schema import (
    CaseContentFile,
    ExerciseContentFile,
    InterviewQuestionContentFile,
    InterviewTemplateContentFile,
    LessonContentFile,
    ProjectTemplateContentFile,
    RoleTemplateContentFile,
)
from app.content.validate import run as validate_run
from app.core.database import SessionLocal
from app.models.career import RoleTemplate
from app.models.case import Case
from app.models.dataset import Dataset
from app.models.enums import (
    CaseCategory,
    CaseDifficulty,
    DifficultyLevel,
    ExerciseType,
    InterviewQuestionType,
    LessonContentType,
    TargetRoleCategory,
)
from app.models.exercise import Exercise
from app.models.interview import InterviewQuestion, InterviewTemplate
from app.models.lesson import Lesson
from app.models.lesson_relations import LessonDataset, LessonPrerequisite, LessonSkill, RelatedLesson
from app.models.module import Module
from app.models.project import ProjectTemplate
from app.models.skill import Skill
from app.models.tag import ExerciseTag, LessonTag, Tag

logger = logging.getLogger(__name__)

CONTENT_LESSON_PREFIX = "content/lessons/"
CONTENT_EXERCISE_PREFIX = "content/exercises/"
CONTENT_CASE_PREFIX = "content/cases/"
CONTENT_PROJECT_PREFIX = "content/projects/"
CONTENT_INTERVIEW_QUESTION_PREFIX = "content/interview/questions/"
CONTENT_INTERVIEW_TEMPLATE_PREFIX = "content/interview/templates/"
CONTENT_ROLE_TEMPLATE_PREFIX = "content/career/role_templates/"


def _get_or_create_tag(db: Session, slug: str) -> Tag:
    tag = db.query(Tag).filter(Tag.slug == slug).one_or_none()
    if tag is None:
        tag = Tag(slug=slug, name=slug.replace("-", " ").title())
        db.add(tag)
        db.flush()
    return tag


def _sync_lesson(db: Session, content: LessonContentFile) -> Lesson:
    module = db.query(Module).filter(Module.slug == content.module_slug).one()

    lesson = db.query(Lesson).filter(Lesson.slug == content.slug).one_or_none()
    if lesson is None:
        lesson = Lesson(slug=content.slug)
        db.add(lesson)

    lesson.module_id = module.id
    lesson.title = content.title
    lesson.description = content.description
    lesson.content_type = LessonContentType(content.content_type)
    lesson.difficulty = DifficultyLevel(content.difficulty)
    lesson.estimated_minutes = content.estimated_minutes
    lesson.display_order = content.display_order
    lesson.content_reference = content.source_path
    lesson.is_active = True
    lesson.completion_criteria = (
        content.completion_criteria.model_dump() if content.completion_criteria else None
    )
    db.flush()
    return lesson


def _sync_lesson_relations(db: Session, content: LessonContentFile, lesson: Lesson) -> None:
    db.query(LessonTag).filter(LessonTag.lesson_id == lesson.id).delete()
    db.query(LessonSkill).filter(LessonSkill.lesson_id == lesson.id).delete()
    db.query(LessonDataset).filter(LessonDataset.lesson_id == lesson.id).delete()
    db.query(LessonPrerequisite).filter(LessonPrerequisite.lesson_id == lesson.id).delete()
    db.query(RelatedLesson).filter(RelatedLesson.lesson_id == lesson.id).delete()

    for tag_slug in content.tags:
        tag = _get_or_create_tag(db, tag_slug)
        db.add(LessonTag(lesson_id=lesson.id, tag_id=tag.id))

    for skill_slug in content.skills:
        skill = db.query(Skill).filter(Skill.slug == skill_slug).one()
        db.add(LessonSkill(lesson_id=lesson.id, skill_id=skill.id))

    for dataset_slug in content.datasets:
        dataset = db.query(Dataset).filter(Dataset.slug == dataset_slug).one()
        db.add(LessonDataset(lesson_id=lesson.id, dataset_id=dataset.id))

    for prereq_slug in content.prerequisites:
        prereq = db.query(Lesson).filter(Lesson.slug == prereq_slug).one()
        db.add(
            LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=prereq.id, is_hard_blocker=True)
        )

    for prereq_slug in content.soft_prerequisites:
        prereq = db.query(Lesson).filter(Lesson.slug == prereq_slug).one()
        db.add(
            LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=prereq.id, is_hard_blocker=False)
        )

    for related_slug in content.related_lessons:
        related = db.query(Lesson).filter(Lesson.slug == related_slug).one()
        db.add(RelatedLesson(lesson_id=lesson.id, related_lesson_id=related.id))


def _sync_exercise(db: Session, content: ExerciseContentFile) -> Exercise:
    exercise = db.query(Exercise).filter(Exercise.slug == content.slug).one_or_none()
    if exercise is None:
        exercise = Exercise(slug=content.slug)
        db.add(exercise)

    exercise.title = content.title
    exercise.description = content.description
    exercise.exercise_type = ExerciseType(content.exercise_type)
    exercise.difficulty = DifficultyLevel(content.difficulty)
    exercise.points = content.points
    exercise.content_reference = content.source_path
    exercise.is_active = True

    exercise.lesson_id = None
    if content.lesson_slug:
        lesson = db.query(Lesson).filter(Lesson.slug == content.lesson_slug).one()
        exercise.lesson_id = lesson.id

    exercise.skill_id = None
    if content.skill:
        skill = db.query(Skill).filter(Skill.slug == content.skill).one()
        exercise.skill_id = skill.id

    exercise.dataset_id = None
    if content.dataset:
        dataset = db.query(Dataset).filter(Dataset.slug == content.dataset).one()
        exercise.dataset_id = dataset.id

    db.flush()
    return exercise


def _sync_exercise_tags(db: Session, content: ExerciseContentFile, exercise: Exercise) -> None:
    db.query(ExerciseTag).filter(ExerciseTag.exercise_id == exercise.id).delete()
    for tag_slug in content.tags:
        tag = _get_or_create_tag(db, tag_slug)
        db.add(ExerciseTag(exercise_id=exercise.id, tag_id=tag.id))


def _sync_case(db: Session, content: CaseContentFile) -> Case:
    case = db.query(Case).filter(Case.slug == content.slug).one_or_none()
    if case is None:
        case = Case(slug=content.slug)
        db.add(case)
    else:
        # A content edit bumps the version so in-progress/completed attempts keep
        # the version they were actually scored against (spec section 48).
        if case.version != content.version:
            logger.info("Case '%s' content version changed %d -> %d", content.slug, case.version, content.version)

    case.title = content.title
    case.category = CaseCategory(content.category)
    case.difficulty = CaseDifficulty(content.difficulty)
    case.estimated_minutes = content.estimated_minutes
    case.company_context = content.company_context
    case.stakeholder_name = content.stakeholder_name
    case.stakeholder_role = content.stakeholder_role
    case.problem_statement = content.problem_statement
    case.business_context = content.business_context
    case.objective = content.objective
    case.initial_information = content.initial_information
    case.constraints = content.constraints
    case.available_datasets = content.available_datasets
    case.expected_deliverables = content.expected_deliverables
    case.learning_objectives = content.learning_objectives
    case.stages = content.stages
    case.required_exercise_slugs = content.required_exercise_slugs
    case.tags = content.tags
    case.skills = content.skills
    case.clarification_guidance = content.clarification_guidance
    case.rubric = [cat.model_dump() for cat in content.rubric]
    case.hints = content.hints
    case.reference_solution = content.reference_solution.model_dump()
    case.version = content.version
    case.content_reference = content.source_path
    case.is_active = True
    db.flush()
    return case


def _sync_project_template(db: Session, content: ProjectTemplateContentFile) -> ProjectTemplate:
    template = db.query(ProjectTemplate).filter(ProjectTemplate.slug == content.slug).one_or_none()
    if template is None:
        template = ProjectTemplate(slug=content.slug)
        db.add(template)

    template.title = content.title
    template.category = CaseCategory(content.category)
    template.business_context = content.business_context
    template.objective = content.objective
    template.requirements = content.requirements
    template.suggested_datasets = content.suggested_datasets
    template.milestones = [m.model_dump() for m in content.milestones]
    template.required_skills = content.required_skills
    template.rubric = [cat.model_dump() for cat in content.rubric]
    template.learning_objectives = content.learning_objectives
    template.estimated_hours = content.estimated_hours
    template.tags = content.tags
    template.version = content.version
    template.content_reference = content.source_path
    template.is_active = True
    db.flush()
    return template


def _sync_interview_question(db: Session, content: InterviewQuestionContentFile) -> InterviewQuestion:
    question = db.query(InterviewQuestion).filter(InterviewQuestion.slug == content.slug).one_or_none()
    if question is None:
        question = InterviewQuestion(slug=content.slug)
        db.add(question)

    exercise = db.query(Exercise).filter(Exercise.slug == content.exercise_slug).one()
    question.exercise_id = exercise.id
    question.interview_type = InterviewQuestionType(content.interview_type)
    question.time_limit_seconds = content.time_limit_seconds
    question.company_archetypes = content.company_archetypes
    question.version = content.version
    question.content_reference = content.source_path
    question.is_active = True
    db.flush()
    return question


def _sync_interview_question_follow_ups(db: Session, content: InterviewQuestionContentFile) -> None:
    """Second pass — `follow_up_slugs` may reference a question that hadn't
    been created yet in file-scan order (same reasoning as lesson
    prerequisites' two-pass sync above)."""
    question = db.query(InterviewQuestion).filter(InterviewQuestion.slug == content.slug).one()
    follow_up_ids = []
    for follow_up_slug in content.follow_up_slugs:
        follow_up = db.query(InterviewQuestion).filter(InterviewQuestion.slug == follow_up_slug).one()
        follow_up_ids.append(follow_up.id)
    question.follow_up_question_ids = follow_up_ids
    db.flush()


def _sync_interview_template(db: Session, content: InterviewTemplateContentFile) -> InterviewTemplate:
    template = db.query(InterviewTemplate).filter(InterviewTemplate.slug == content.slug).one_or_none()
    if template is None:
        template = InterviewTemplate(slug=content.slug)
        db.add(template)

    template.title = content.title
    template.target_profile = content.target_profile
    template.description = content.description
    template.sections = [s.model_dump() for s in content.sections]
    template.rubric_weights = content.rubric_weights
    template.tags = content.tags
    template.version = content.version
    template.content_reference = content.source_path
    template.is_active = True
    db.flush()
    return template


def _sync_role_template(db: Session, content: RoleTemplateContentFile) -> RoleTemplate:
    template = db.query(RoleTemplate).filter(RoleTemplate.slug == content.slug).one_or_none()
    if template is None:
        template = RoleTemplate(slug=content.slug)
        db.add(template)

    template.title = content.title
    template.category = TargetRoleCategory(content.category)
    template.description = content.description
    template.core_skills = content.core_skills
    template.preferred_skills = content.preferred_skills
    template.nice_to_have_skills = content.nice_to_have_skills
    template.typical_responsibilities = content.typical_responsibilities
    template.version = content.version
    template.content_reference = content.source_path
    template.is_active = True
    db.flush()
    return template


def _deactivate_removed(
    db: Session,
    synced_lesson_slugs: set[str],
    synced_exercise_slugs: set[str],
    synced_case_slugs: set[str],
    synced_project_template_slugs: set[str],
    synced_interview_question_slugs: set[str],
    synced_interview_template_slugs: set[str],
    synced_role_template_slugs: set[str],
) -> None:
    stale_lessons = (
        db.query(Lesson)
        .filter(Lesson.content_reference.like(f"{CONTENT_LESSON_PREFIX}%"))
        .filter(~Lesson.slug.in_(synced_lesson_slugs) if synced_lesson_slugs else True)
        .all()
    )
    for lesson in stale_lessons:
        if lesson.is_active:
            logger.warning("Deactivating lesson '%s' — no longer present in content/", lesson.slug)
        lesson.is_active = False

    stale_exercises = (
        db.query(Exercise)
        .filter(Exercise.content_reference.like(f"{CONTENT_EXERCISE_PREFIX}%"))
        .filter(~Exercise.slug.in_(synced_exercise_slugs) if synced_exercise_slugs else True)
        .all()
    )
    for exercise in stale_exercises:
        if exercise.is_active:
            logger.warning("Deactivating exercise '%s' — no longer present in content/", exercise.slug)
        exercise.is_active = False

    stale_cases = (
        db.query(Case)
        .filter(Case.content_reference.like(f"{CONTENT_CASE_PREFIX}%"))
        .filter(~Case.slug.in_(synced_case_slugs) if synced_case_slugs else True)
        .all()
    )
    for case in stale_cases:
        if case.is_active:
            logger.warning("Deactivating case '%s' — no longer present in content/", case.slug)
        case.is_active = False

    stale_templates = (
        db.query(ProjectTemplate)
        .filter(ProjectTemplate.content_reference.like(f"{CONTENT_PROJECT_PREFIX}%"))
        .filter(~ProjectTemplate.slug.in_(synced_project_template_slugs) if synced_project_template_slugs else True)
        .all()
    )
    for template in stale_templates:
        if template.is_active:
            logger.warning("Deactivating project template '%s' — no longer present in content/", template.slug)
        template.is_active = False

    stale_questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.content_reference.like(f"{CONTENT_INTERVIEW_QUESTION_PREFIX}%"))
        .filter(~InterviewQuestion.slug.in_(synced_interview_question_slugs) if synced_interview_question_slugs else True)
        .all()
    )
    for question in stale_questions:
        if question.is_active:
            logger.warning("Deactivating interview question '%s' — no longer present in content/", question.slug)
        question.is_active = False

    stale_interview_templates = (
        db.query(InterviewTemplate)
        .filter(InterviewTemplate.content_reference.like(f"{CONTENT_INTERVIEW_TEMPLATE_PREFIX}%"))
        .filter(
            ~InterviewTemplate.slug.in_(synced_interview_template_slugs) if synced_interview_template_slugs else True
        )
        .all()
    )
    for template in stale_interview_templates:
        if template.is_active:
            logger.warning("Deactivating interview template '%s' — no longer present in content/", template.slug)
        template.is_active = False

    stale_role_templates = (
        db.query(RoleTemplate)
        .filter(RoleTemplate.content_reference.like(f"{CONTENT_ROLE_TEMPLATE_PREFIX}%"))
        .filter(~RoleTemplate.slug.in_(synced_role_template_slugs) if synced_role_template_slugs else True)
        .all()
    )
    for template in stale_role_templates:
        if template.is_active:
            logger.warning("Deactivating role template '%s' — no longer present in content/", template.slug)
        template.is_active = False


def sync(db: Session | None = None) -> None:
    errors = validate_run()
    if errors:
        raise RuntimeError(
            f"Refusing to sync: {len(errors)} content validation error(s). "
            "Run `python -m app.content.validate` for details."
        )

    result = load_all()
    owns_session = db is None
    session = db or SessionLocal()
    try:
        # Two passes over lessons: create/update all lesson rows first (pass 1),
        # then wire up relations (pass 2) — prerequisites/related_lessons may
        # reference a lesson slug that hasn't been created yet in file-scan order.
        for lesson_content in result.lessons:
            _sync_lesson(session, lesson_content)
        session.flush()
        for lesson_content in result.lessons:
            lesson = session.query(Lesson).filter(Lesson.slug == lesson_content.slug).one()
            _sync_lesson_relations(session, lesson_content, lesson)

        for exercise_content in result.exercises:
            exercise = _sync_exercise(session, exercise_content)
            _sync_exercise_tags(session, exercise_content, exercise)

        for case_content in result.cases:
            _sync_case(session, case_content)

        for project_template_content in result.project_templates:
            _sync_project_template(session, project_template_content)

        # Two passes, same reasoning as lessons: an interview question's
        # follow_up_slugs may reference a question not yet created in
        # file-scan order.
        for question_content in result.interview_questions:
            _sync_interview_question(session, question_content)
        session.flush()
        for question_content in result.interview_questions:
            _sync_interview_question_follow_ups(session, question_content)

        for template_content in result.interview_templates:
            _sync_interview_template(session, template_content)

        for role_template_content in result.role_templates:
            _sync_role_template(session, role_template_content)

        _deactivate_removed(
            session,
            {lc.slug for lc in result.lessons},
            {ec.slug for ec in result.exercises},
            {cc.slug for cc in result.cases},
            {pc.slug for pc in result.project_templates},
            {qc.slug for qc in result.interview_questions},
            {tc.slug for tc in result.interview_templates},
            {rc.slug for rc in result.role_templates},
        )

        session.commit()
        logger.info(
            "Content sync complete: %d lessons, %d exercises, %d cases, %d project templates, "
            "%d interview questions, %d interview templates, %d role templates.",
            len(result.lessons),
            len(result.exercises),
            len(result.cases),
            len(result.project_templates),
            len(result.interview_questions),
            len(result.interview_templates),
            len(result.role_templates),
        )
    finally:
        if owns_session:
            session.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
    try:
        sync()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
