"""Backup / Restore tests (Phase 12) — verifies the exported bundle never
includes secrets, restore is idempotent (never duplicates an existing row),
and restore genuinely recreates a row that's missing from the target
database (the real disaster-recovery scenario)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress


class TestBackupExport:
    def test_backup_never_contains_a_secret_field(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        serialized = str(bundle).lower()
        for forbidden in ("api_key", "ai_api_key", "openai_api_key", "anthropic_api_key", "database_url"):
            assert forbidden not in serialized

    def test_manifest_reports_real_counts(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        assert bundle["manifest"]["created_at"]
        assert bundle["manifest"]["schema_version"]
        assert isinstance(bundle["manifest"]["counts"], dict)
        assert sum(bundle["manifest"]["counts"].values()) >= 0

    def test_career_note_created_now_appears_in_a_fresh_export(self, client: TestClient) -> None:
        before = client.get("/api/v1/platform/backup").json()["manifest"]["counts"]["career_notes"]
        client.post("/api/v1/career/notes", json={"topic": "Backup probe", "body": "test note"})
        after = client.get("/api/v1/platform/backup").json()["manifest"]["counts"]["career_notes"]
        assert after == before + 1


class TestBackupHandlesCompositeKeyEntities:
    def test_export_preview_and_restore_round_trip_a_composite_key_row_without_crashing(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Regression test — LessonProgress has a composite (user_id,
        lesson_id) primary key, not a synthetic `id` column like every other
        backed-up entity. `export_bundle` used to assume `.id` unconditionally
        and crashed with AttributeError the moment any LessonProgress row
        existed; `preview_restore` separately flagged every LessonProgress row
        as corrupted for the same "no id" reason; and `restore_bundle`'s
        idempotency check crashed on `row["id"]` too. All three now work off
        the row's real primary key columns instead of assuming `id`."""
        user_id = client.get("/api/v1/users/me").json()["id"]
        lesson = db_session.execute(select(Lesson)).scalars().first()
        db_session.merge(LessonProgress(user_id=user_id, lesson_id=lesson.id, progress_percent=100.0))
        db_session.commit()

        bundle = client.get("/api/v1/platform/backup").json()
        assert bundle["manifest"]["counts"]["lesson_progress"] >= 1
        assert any(row["lesson_id"] == lesson.id for row in bundle["data"]["lesson_progress"])

        preview = client.post("/api/v1/platform/restore/preview", json=bundle).json()
        assert preview["compatible"] is True
        assert preview["issues"] == []

        result = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True})
        assert result.status_code == 200
        assert result.json()["restored"]["lesson_progress"] == 0  # already present — idempotent no-op


class TestRestore:
    def test_preview_reports_compatible_for_a_freshly_exported_bundle(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        preview = client.post("/api/v1/platform/restore/preview", json=bundle).json()
        assert preview["compatible"] is True
        assert preview["issues"] == []

    def test_restore_requires_explicit_confirmation(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        response = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": False})
        assert response.status_code == 400

    def test_restoring_an_already_present_bundle_is_a_no_op(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        result = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True}).json()
        assert all(count == 0 for count in result["restored"].values())

    def test_restoring_an_unchanged_singleton_row_is_a_no_op(self, client: TestClient) -> None:
        """Regression test: the singleton-row (unique_per_user) restore path
        used to unconditionally count a match as "restored" even when every
        field was already identical — so restoring an unchanged backup falsely
        reported a change whenever a CareerProfile/AISettings/Portfolio row
        already existed (a common case — many endpoints lazily auto-create
        one). Deterministic regardless of test execution order, unlike the
        no-op test above, which only exercises this when an earlier test in
        the same run happened to create one of these rows first."""
        client.get("/api/v1/platform/next-best-actions")  # lazily creates a CareerProfile
        bundle = client.get("/api/v1/platform/backup").json()
        assert bundle["data"]["career_profiles"], "expected a CareerProfile row in the bundle"

        result = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True}).json()
        assert result["restored"]["career_profiles"] == 0

    def test_restore_recreates_a_row_missing_from_the_target(self, client: TestClient) -> None:
        note = client.post(
            "/api/v1/career/notes", json={"topic": "Restore probe", "body": "will be deleted"}
        ).json()
        bundle = client.get("/api/v1/platform/backup").json()

        client.delete(f"/api/v1/career/notes/{note['id']}")
        notes_after_delete = {n["id"] for n in client.get("/api/v1/career/notes").json()}
        assert note["id"] not in notes_after_delete

        result = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True}).json()
        assert result["restored"]["career_notes"] >= 1

        notes_after_restore = {n["id"] for n in client.get("/api/v1/career/notes").json()}
        assert note["id"] in notes_after_restore

    def test_restore_of_a_singleton_row_under_a_different_id_updates_in_place_without_crashing(
        self, client: TestClient
    ) -> None:
        """Regression test: AISettings/CareerProfile/Portfolio are lazily
        auto-created (with a fresh id) the first time their feature is used —
        e.g. simply loading the dashboard's Next Best Action card creates a
        CareerProfile. A backup taken on another install (or before that
        auto-create ever ran) can carry the SAME logical row under a
        DIFFERENT id. Restoring it must update the existing row in place,
        never insert a second row and crash on the real `UniqueConstraint(
        "user_id")` — this used to abort the ENTIRE restore with zero rows
        restored."""
        client.get("/api/v1/platform/next-best-actions")  # lazily creates a CareerProfile
        current = client.get("/api/v1/career/profile").json()

        bundle = client.get("/api/v1/platform/backup").json()
        profile_row = dict(bundle["data"]["career_profiles"][0])
        assert profile_row["id"] == current["id"]
        profile_row["id"] = str(uuid.uuid4())  # simulate an older backup's different id
        profile_row["headline"] = "Restored from an old backup"
        bundle["data"]["career_profiles"] = [profile_row]

        response = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True})
        assert response.status_code == 200
        assert response.json()["restored"]["career_profiles"] == 1

        profile_after = client.get("/api/v1/career/profile").json()
        assert profile_after["id"] == current["id"], "must update the existing row, not insert a duplicate"
        assert profile_after["headline"] == "Restored from an old backup"

    def test_restore_ignores_unrecognized_tables_without_crashing(self, client: TestClient) -> None:
        bundle = client.get("/api/v1/platform/backup").json()
        bundle["data"]["some_future_table"] = [{"id": str(uuid.uuid4())}]
        preview = client.post("/api/v1/platform/restore/preview", json=bundle).json()
        assert any("unrecognized" in issue.lower() for issue in preview["issues"])
        result = client.post("/api/v1/platform/restore", json={"bundle": bundle, "confirm": True})
        assert result.status_code == 200
