"""Data Integrity Audit CLI (Phase 12, spec section 78).

Usage:
    uv run --project apps/api python -m app.db.integrity_check_cli
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.services.data_integrity_service import DataIntegrityService


def main() -> int:
    session = SessionLocal()
    try:
        results = DataIntegrityService(session).check_all()
        print("Data Integrity Audit\n")
        exit_code = 0
        for result in results:
            icon = "[OK]" if result.orphaned_count == 0 else "[FAIL]"
            print(f"  {icon:8s} {result.name}: {result.detail}")
            if result.orphaned_count:
                exit_code = 1
        return exit_code
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
