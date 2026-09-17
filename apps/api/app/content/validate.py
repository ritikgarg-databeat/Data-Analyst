"""Content validation CLI.

Usage:
    uv run --project apps/api python -m app.content.validate

Discovers every content file, validates it against the Pydantic schema,
then cross-checks references (module/skill/dataset/tag/prerequisite/
lesson_slug) against the seed taxonomies and the other content files —
entirely without a database connection, so content can be validated before
touching Postgres at all. Prints every problem found (not just the first)
and exits non-zero if anything is wrong.
"""

from __future__ import annotations

import sys
from collections import Counter

import yaml

from app.content.loader import REPO_ROOT, load_all
from app.content.schema import AUTO_GRADABLE_EXERCISE_TYPES

SEEDS_DIR = REPO_ROOT / "database" / "seeds"


def _seed_slugs(filename: str) -> set[str]:
    path = SEEDS_DIR / filename
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return {row["slug"] for row in rows}


def _sql_tables_by_dataset() -> dict[str, set[str]]:
    path = SEEDS_DIR / "sql_tables.yaml"
    if not path.exists():
        return {}
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    by_dataset: dict[str, set[str]] = {}
    for row in rows:
        by_dataset.setdefault(row["dataset_slug"], set()).add(row["table_name"])
    return by_dataset


def run() -> list[str]:
    """Returns a list of human-readable error strings; empty means valid."""
    errors: list[str] = []

    result = load_all()
    for e in result.errors:
        errors.append(f"{e.path}: {e.message}")

    known_modules = _seed_slugs("modules.yaml")
    known_skills = _seed_slugs("skills.yaml")
    known_datasets = _seed_slugs("datasets.yaml")
    known_tags = _seed_slugs("tags.yaml")
    known_lessons = {lesson.slug for lesson in result.lessons}
    known_exercises = {exercise.slug for exercise in result.exercises}
    known_interview_questions = {q.slug for q in result.interview_questions}
    known_sql_tables_by_dataset = _sql_tables_by_dataset()

    # Duplicate slugs.
    for kind, items in (
        ("lesson", result.lessons),
        ("exercise", result.exercises),
        ("case", result.cases),
        ("project template", result.project_templates),
        ("interview question", result.interview_questions),
        ("interview template", result.interview_templates),
        ("role template", result.role_templates),
    ):
        counts = Counter(item.slug for item in items)
        for slug, count in counts.items():
            if count > 1:
                errors.append(f"duplicate {kind} slug '{slug}' ({count} files)")

    # Lesson reference checks.
    for lesson in result.lessons:
        loc = lesson.source_path
        if lesson.module_slug not in known_modules:
            errors.append(
                f"{loc}: module_slug '{lesson.module_slug}' is not defined in database/seeds/modules.yaml"
            )
        for prereq in [*lesson.prerequisites, *lesson.soft_prerequisites]:
            if prereq not in known_lessons:
                errors.append(f"{loc}: prerequisite lesson '{prereq}' does not exist")
        if lesson.slug in lesson.prerequisites or lesson.slug in lesson.soft_prerequisites:
            errors.append(f"{loc}: lesson cannot be its own prerequisite")
        for skill in lesson.skills:
            if skill not in known_skills:
                errors.append(f"{loc}: skill '{skill}' is not defined in database/seeds/skills.yaml")
        for dataset in lesson.datasets:
            if dataset not in known_datasets:
                errors.append(f"{loc}: dataset '{dataset}' is not defined in database/seeds/datasets.yaml")
        for tag in lesson.tags:
            if tag not in known_tags:
                errors.append(f"{loc}: tag '{tag}' is not defined in database/seeds/tags.yaml")
        for related in lesson.related_lessons:
            if related not in known_lessons:
                errors.append(f"{loc}: related_lessons entry '{related}' does not exist")

    # Exercise reference checks.
    for exercise in result.exercises:
        loc = exercise.source_path
        if exercise.lesson_slug and exercise.lesson_slug not in known_lessons:
            errors.append(f"{loc}: lesson_slug '{exercise.lesson_slug}' does not exist")
        if exercise.skill and exercise.skill not in known_skills:
            errors.append(f"{loc}: skill '{exercise.skill}' is not defined in database/seeds/skills.yaml")
        if exercise.dataset and exercise.dataset not in known_datasets:
            errors.append(
                f"{loc}: dataset '{exercise.dataset}' is not defined in database/seeds/datasets.yaml"
            )
        for tag in exercise.tags:
            if tag not in known_tags:
                errors.append(f"{loc}: tag '{tag}' is not defined in database/seeds/tags.yaml")
        if exercise.exercise_type in AUTO_GRADABLE_EXERCISE_TYPES and not exercise.correct_answer:
            errors.append(f"{loc}: exercise_type '{exercise.exercise_type}' requires correct_answer")
        if exercise.exercise_type == "MULTIPLE_CHOICE":
            if not exercise.choices:
                errors.append(f"{loc}: MULTIPLE_CHOICE requires choices")
            elif exercise.correct_answer not in exercise.choices:
                errors.append(f"{loc}: correct_answer must exactly match one entry in choices")
        if exercise.exercise_type == "SQL":
            if not exercise.dataset:
                errors.append(f"{loc}: SQL exercises require a dataset")
            if not exercise.sql_solution_query:
                errors.append(f"{loc}: SQL exercises require sql_solution_query")
            dataset_tables = known_sql_tables_by_dataset.get(exercise.dataset or "", set())
            for table in exercise.sql_tables:
                if table not in dataset_tables:
                    errors.append(
                        f"{loc}: sql_tables entry '{table}' is not a table in dataset '{exercise.dataset}' "
                        "(database/seeds/sql_tables.yaml)"
                    )
            for hidden_test in exercise.sql_hidden_tests:
                if not hidden_test.query.strip():
                    errors.append(f"{loc}: hidden test '{hidden_test.name}' has an empty query")
        if exercise.exercise_type == "PYTHON":
            if not exercise.dataset:
                errors.append(f"{loc}: PYTHON exercises require a dataset")
            if not exercise.python_solution_code:
                errors.append(f"{loc}: PYTHON exercises require python_solution_code")
            if not exercise.python_result_variable.strip():
                errors.append(f"{loc}: python_result_variable cannot be empty")
            # Only checkable statically for datasets that register SqlTable rows
            # (e.g. ecommerce) — a dataset with no such registry (e.g. a lone
            # CSV) has nothing to validate python_datasets entries against
            # without a DB connection, so those are skipped, not rejected.
            dataset_files = known_sql_tables_by_dataset.get(exercise.dataset or "")
            if dataset_files:
                for label in exercise.python_datasets:
                    if label not in dataset_files:
                        errors.append(
                            f"{loc}: python_datasets entry '{label}' is not a table in dataset "
                            f"'{exercise.dataset}' (database/seeds/sql_tables.yaml)"
                        )
            for hidden_test in exercise.python_hidden_tests:
                if not hidden_test.code.strip():
                    errors.append(f"{loc}: hidden test '{hidden_test.name}' has empty code")

    # Case reference checks.
    for case in result.cases:
        loc = case.source_path
        for skill in case.skills:
            if skill not in known_skills:
                errors.append(f"{loc}: skill '{skill}' is not defined in database/seeds/skills.yaml")
        for dataset in case.available_datasets:
            if dataset not in known_datasets:
                errors.append(f"{loc}: dataset '{dataset}' is not defined in database/seeds/datasets.yaml")
        for tag in case.tags:
            if tag not in known_tags:
                errors.append(f"{loc}: tag '{tag}' is not defined in database/seeds/tags.yaml")
        for exercise_slug in case.required_exercise_slugs:
            if exercise_slug not in known_exercises:
                errors.append(f"{loc}: required_exercise_slugs entry '{exercise_slug}' does not exist")
        total_weight = sum(cat.weight for cat in case.rubric)
        if abs(total_weight - 100) > 0.01:
            errors.append(f"{loc}: rubric category weights sum to {total_weight}, not 100")

    # Project template reference checks.
    for template in result.project_templates:
        loc = template.source_path
        for skill in template.required_skills:
            if skill not in known_skills:
                errors.append(f"{loc}: skill '{skill}' is not defined in database/seeds/skills.yaml")
        for dataset in template.suggested_datasets:
            if dataset not in known_datasets:
                errors.append(f"{loc}: dataset '{dataset}' is not defined in database/seeds/datasets.yaml")
        for tag in template.tags:
            if tag not in known_tags:
                errors.append(f"{loc}: tag '{tag}' is not defined in database/seeds/tags.yaml")
        if template.rubric:
            total_weight = sum(cat.weight for cat in template.rubric)
            if abs(total_weight - 100) > 0.01:
                errors.append(f"{loc}: rubric category weights sum to {total_weight}, not 100")

    # Interview question reference checks.
    for question in result.interview_questions:
        loc = question.source_path
        if question.exercise_slug not in known_exercises:
            errors.append(f"{loc}: exercise_slug '{question.exercise_slug}' does not exist")
        for follow_up_slug in question.follow_up_slugs:
            if follow_up_slug not in known_interview_questions:
                errors.append(f"{loc}: follow_up_slugs entry '{follow_up_slug}' does not exist")
            if follow_up_slug == question.slug:
                errors.append(f"{loc}: an interview question cannot be its own follow-up")

    # Interview template reference checks.
    for template in result.interview_templates:
        loc = template.source_path
        total_weight = sum(template.rubric_weights.values())
        if abs(total_weight - 100) > 0.01:
            errors.append(f"{loc}: rubric_weights sum to {total_weight}, not 100")

    # Role template reference checks.
    for role_template in result.role_templates:
        loc = role_template.source_path
        for skill_list_name in ("core_skills", "preferred_skills", "nice_to_have_skills"):
            for skill in getattr(role_template, skill_list_name):
                if skill not in known_skills:
                    errors.append(f"{loc}: skill '{skill}' is not defined in database/seeds/skills.yaml")

    # Detect lesson slugs referenced by content that don't exist anywhere (broken prereq chains
    # already covered above); additionally warn on modules with zero lessons.
    lessons_per_module: Counter[str] = Counter(lesson.module_slug for lesson in result.lessons)
    for module_slug in known_modules:
        if lessons_per_module[module_slug] == 0:
            errors.append(
                f"module '{module_slug}' (database/seeds/modules.yaml) has no lesson content files yet"
            )

    return errors


def main() -> int:
    errors = run()
    result = load_all()
    if errors:
        print(f"Content validation FAILED - {len(errors)} problem(s):\n", file=sys.stderr)
        for err in errors:
            print(f"  [FAIL] {err}", file=sys.stderr)
        return 1

    print(
        f"Content validation passed: {len(result.lessons)} lessons, "
        f"{len(result.exercises)} exercises, {len(result.cases)} cases, "
        f"{len(result.project_templates)} project templates, "
        f"{len(result.interview_questions)} interview questions, "
        f"{len(result.interview_templates)} interview templates, "
        f"{len(result.role_templates)} role templates, 0 problems."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
