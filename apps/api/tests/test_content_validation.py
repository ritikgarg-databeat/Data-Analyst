import pytest
from pydantic import ValidationError

from app.content import loader, validate
from app.content.schema import ExerciseContentFile, LessonContentFile

MINIMAL_LESSON = {
    "slug": "a",
    "module_slug": "how-to-use-this-lab",
    "title": "A",
    "description": "d",
    "difficulty": "BEGINNER",
    "estimated_minutes": 5,
    "display_order": 1,
    "objectives": ["do a thing"],
    "key_takeaways": ["a takeaway"],
    "blocks": [{"type": "text", "body": "hello"}],
}


def test_real_repository_content_validates_with_zero_errors() -> None:
    errors = validate.run()

    assert errors == []


def test_real_content_has_the_expected_lesson_and_exercise_counts() -> None:
    result = loader.load_all()

    assert len(result.lessons) == 325
    assert len(result.exercises) == 354
    assert len(result.cases) == 35
    assert len(result.interview_questions) == 335
    assert len(result.interview_templates) == 6
    assert result.errors == []


def test_lesson_content_file_requires_at_least_one_block() -> None:
    with pytest.raises(ValidationError):
        LessonContentFile(**{**MINIMAL_LESSON, "blocks": []})


def test_lesson_content_file_rejects_an_unknown_block_type() -> None:
    with pytest.raises(ValidationError):
        LessonContentFile(**{**MINIMAL_LESSON, "blocks": [{"type": "not-a-real-block-type"}]})


def test_multiple_choice_exercise_content_file_parses_without_choices() -> None:
    # Pydantic only enforces per-field *shape* — cross-field semantic rules
    # like "MULTIPLE_CHOICE needs choices/correct_answer" are validate.py's
    # job (see the next test), so the bare model must NOT reject this.
    exercise = ExerciseContentFile(
        slug="x",
        title="X",
        description="d",
        exercise_type="MULTIPLE_CHOICE",
        difficulty="BEGINNER",
        points=10,
        prompt="p",
        explanation="e",
    )
    assert exercise.choices is None


def test_validator_rejects_a_multiple_choice_exercise_missing_choices(tmp_path, monkeypatch) -> None:
    lessons_dir = tmp_path / "lessons"
    exercises_dir = tmp_path / "exercises"
    lessons_dir.mkdir()
    exercises_dir.mkdir()

    (exercises_dir / "bad.yaml").write_text(
        "slug: bad-mcq\ntitle: Bad\ndescription: d\nexercise_type: MULTIPLE_CHOICE\n"
        "difficulty: BEGINNER\npoints: 10\nprompt: p\nexplanation: e\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "LESSONS_DIR", lessons_dir)
    monkeypatch.setattr(loader, "EXERCISES_DIR", exercises_dir)
    monkeypatch.setattr(validate, "SEEDS_DIR", loader.REPO_ROOT / "database" / "seeds")

    errors = validate.run()

    joined = "\n".join(errors)
    assert "MULTIPLE_CHOICE requires choices" in joined
    assert "requires correct_answer" in joined


def test_validator_detects_duplicate_slugs_and_broken_references(tmp_path, monkeypatch) -> None:
    lessons_dir = tmp_path / "lessons"
    exercises_dir = tmp_path / "exercises"
    lessons_dir.mkdir()
    exercises_dir.mkdir()

    (lessons_dir / "a.yaml").write_text(
        "slug: dup\nmodule_slug: nonexistent-module\ntitle: A\ndescription: d\n"
        "difficulty: BEGINNER\nestimated_minutes: 5\ndisplay_order: 1\n"
        "objectives: [x]\nkey_takeaways: [y]\nprerequisites: [ghost-lesson]\n"
        "blocks:\n  - type: text\n    body: hi\n",
        encoding="utf-8",
    )
    (lessons_dir / "b.yaml").write_text(
        "slug: dup\nmodule_slug: nonexistent-module\ntitle: B\ndescription: d\n"
        "difficulty: BEGINNER\nestimated_minutes: 5\ndisplay_order: 2\n"
        "objectives: [x]\nkey_takeaways: [y]\n"
        "blocks:\n  - type: text\n    body: hi\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "LESSONS_DIR", lessons_dir)
    monkeypatch.setattr(loader, "EXERCISES_DIR", exercises_dir)
    monkeypatch.setattr(validate, "SEEDS_DIR", loader.REPO_ROOT / "database" / "seeds")

    errors = validate.run()

    joined = "\n".join(errors)
    assert "duplicate lesson slug 'dup'" in joined
    assert "module_slug 'nonexistent-module'" in joined
    assert "prerequisite lesson 'ghost-lesson' does not exist" in joined
