"""Discovers and parses content/lessons/**/*.yaml and content/exercises/**/*.yaml.

Deliberately tolerant: a malformed file does not raise here — it's collected
as a `ContentLoadError` so `validate.py` can report every problem in one
pass instead of stopping at the first bad file.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.content.schema import (
    CaseContentFile,
    ExerciseContentFile,
    InterviewQuestionContentFile,
    InterviewTemplateContentFile,
    LessonContentFile,
    ProjectTemplateContentFile,
    RoleTemplateContentFile,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
LESSONS_DIR = REPO_ROOT / "content" / "lessons"
EXERCISES_DIR = REPO_ROOT / "content" / "exercises"
CASES_DIR = REPO_ROOT / "content" / "cases"
PROJECTS_DIR = REPO_ROOT / "content" / "projects"
INTERVIEW_QUESTIONS_DIR = REPO_ROOT / "content" / "interview" / "questions"
INTERVIEW_TEMPLATES_DIR = REPO_ROOT / "content" / "interview" / "templates"
ROLE_TEMPLATES_DIR = REPO_ROOT / "content" / "career" / "role_templates"


@dataclass
class ContentLoadError:
    path: str
    message: str


@dataclass
class LoadResult:
    lessons: list[LessonContentFile]
    exercises: list[ExerciseContentFile]
    cases: list[CaseContentFile]
    project_templates: list[ProjectTemplateContentFile]
    interview_questions: list[InterviewQuestionContentFile]
    interview_templates: list[InterviewTemplateContentFile]
    role_templates: list[RoleTemplateContentFile]
    errors: list[ContentLoadError]


def _relpath(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _load_one(path: Path, model: type) -> tuple[object | None, ContentLoadError | None]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, ContentLoadError(_relpath(path), f"invalid YAML: {exc}")

    if not isinstance(raw, dict):
        return None, ContentLoadError(_relpath(path), "file must contain a YAML mapping at the top level")

    try:
        instance = model(**raw, source_path=_relpath(path))
    except ValidationError as exc:
        messages = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        return None, ContentLoadError(_relpath(path), messages)

    return instance, None


def load_lesson_file(content_reference: str) -> LessonContentFile:
    """Loads a single already-validated lesson content file by its stored content_reference."""
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return LessonContentFile(**raw, source_path=content_reference)


def load_exercise_file(content_reference: str) -> ExerciseContentFile:
    """Loads a single already-validated exercise content file by its stored content_reference."""
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ExerciseContentFile(**raw, source_path=content_reference)


def load_case_file(content_reference: str) -> CaseContentFile:
    """Loads a single already-validated case content file by its stored content_reference."""
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CaseContentFile(**raw, source_path=content_reference)


def load_project_template_file(content_reference: str) -> ProjectTemplateContentFile:
    """Loads a single already-validated project template content file by its stored content_reference."""
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ProjectTemplateContentFile(**raw, source_path=content_reference)


def load_interview_question_file(content_reference: str) -> InterviewQuestionContentFile:
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return InterviewQuestionContentFile(**raw, source_path=content_reference)


def load_interview_template_file(content_reference: str) -> InterviewTemplateContentFile:
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return InterviewTemplateContentFile(**raw, source_path=content_reference)


def load_role_template_file(content_reference: str) -> RoleTemplateContentFile:
    path = REPO_ROOT / content_reference
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return RoleTemplateContentFile(**raw, source_path=content_reference)


def load_all() -> LoadResult:
    lessons: list[LessonContentFile] = []
    exercises: list[ExerciseContentFile] = []
    cases: list[CaseContentFile] = []
    project_templates: list[ProjectTemplateContentFile] = []
    interview_questions: list[InterviewQuestionContentFile] = []
    interview_templates: list[InterviewTemplateContentFile] = []
    role_templates: list[RoleTemplateContentFile] = []
    errors: list[ContentLoadError] = []

    for path in sorted(LESSONS_DIR.rglob("*.yaml")):
        lesson, error = _load_one(path, LessonContentFile)
        if error:
            errors.append(error)
        else:
            lessons.append(lesson)  # type: ignore[arg-type]

    for path in sorted(EXERCISES_DIR.rglob("*.yaml")):
        exercise, error = _load_one(path, ExerciseContentFile)
        if error:
            errors.append(error)
        else:
            exercises.append(exercise)  # type: ignore[arg-type]

    for path in sorted(CASES_DIR.rglob("*.yaml")) if CASES_DIR.exists() else []:
        case, error = _load_one(path, CaseContentFile)
        if error:
            errors.append(error)
        else:
            cases.append(case)  # type: ignore[arg-type]

    for path in sorted(PROJECTS_DIR.rglob("*.yaml")) if PROJECTS_DIR.exists() else []:
        project_template, error = _load_one(path, ProjectTemplateContentFile)
        if error:
            errors.append(error)
        else:
            project_templates.append(project_template)  # type: ignore[arg-type]

    for path in sorted(INTERVIEW_QUESTIONS_DIR.rglob("*.yaml")) if INTERVIEW_QUESTIONS_DIR.exists() else []:
        question, error = _load_one(path, InterviewQuestionContentFile)
        if error:
            errors.append(error)
        else:
            interview_questions.append(question)  # type: ignore[arg-type]

    for path in sorted(INTERVIEW_TEMPLATES_DIR.rglob("*.yaml")) if INTERVIEW_TEMPLATES_DIR.exists() else []:
        template, error = _load_one(path, InterviewTemplateContentFile)
        if error:
            errors.append(error)
        else:
            interview_templates.append(template)  # type: ignore[arg-type]

    for path in sorted(ROLE_TEMPLATES_DIR.rglob("*.yaml")) if ROLE_TEMPLATES_DIR.exists() else []:
        role_template, error = _load_one(path, RoleTemplateContentFile)
        if error:
            errors.append(error)
        else:
            role_templates.append(role_template)  # type: ignore[arg-type]

    return LoadResult(
        lessons=lessons,
        exercises=exercises,
        cases=cases,
        project_templates=project_templates,
        interview_questions=interview_questions,
        interview_templates=interview_templates,
        role_templates=role_templates,
        errors=errors,
    )
