"""Backup CLI (Phase 12) — dumps the local user's data to a timestamped JSON
file under `data/backups/`, without needing the API server running.

Usage:
    uv run --project apps/api python -m app.db.backup_cli
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.core.database import SessionLocal
from app.services.backup_service import BackupService
from app.services.user_service import UserService

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKUPS_DIR = REPO_ROOT / "data" / "backups"


def main() -> int:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    session = SessionLocal()
    try:
        user = UserService(session).get_current_user()
        bundle = BackupService(session).export_bundle(user.id)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_path = BACKUPS_DIR / f"backup-{timestamp}.json"
        out_path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
        total_rows = sum(bundle.manifest.counts.values())
        table_count = len(bundle.manifest.counts)
        print(f"Backup written to {out_path} ({total_rows} rows across {table_count} tables).")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
