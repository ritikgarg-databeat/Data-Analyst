"""Restore CLI (Phase 12) — restores a backup JSON file (see
`app.db.backup_cli`) without needing the API server running. Always prints
a preview and requires an explicit `--yes` flag before writing anything —
never destructive by default.

Usage:
    uv run --project apps/api python -m app.db.restore_cli <account-email> <path-to-backup.json> [--yes]
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.platform import BackupBundle
from app.services.backup_service import BackupService


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: python -m app.db.restore_cli <account-email> <path-to-backup.json> [--yes]",
            file=sys.stderr,
        )
        return 1

    account_email = sys.argv[1].strip().lower()
    backup_path = Path(sys.argv[2])
    confirmed = "--yes" in sys.argv[3:]
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}", file=sys.stderr)
        return 1

    bundle = BackupBundle.model_validate_json(backup_path.read_text(encoding="utf-8"))

    session = SessionLocal()
    try:
        service = BackupService(session)
        preview = service.preview_restore(bundle)
        print(f"Backup created: {preview.manifest.created_at} (schema {preview.manifest.schema_version})")
        table_count = len(preview.manifest.counts)
        print(f"Tables: {sum(preview.manifest.counts.values())} rows across {table_count} tables")
        for issue in preview.issues:
            print(f"  [!] {issue}")
        if not preview.compatible:
            print("Preview reported compatibility issues — re-run with --yes to attempt it anyway.")
        if not confirmed:
            print("\nThis was a DRY RUN. Re-run with --yes to actually restore.")
            return 0

        user = session.scalar(select(User).where(User.email == account_email))
        if not user:
            print("Account not found.", file=sys.stderr)
            return 1
        restored = service.restore_bundle(user.id, bundle)
        total = sum(restored.values())
        print(f"\nRestored {total} new row(s) (rows already present were left untouched):")
        for name, count in restored.items():
            if count:
                print(f"  {name}: +{count}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
