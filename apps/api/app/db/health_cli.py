"""System Health CLI (Phase 12) — the same dependency-aware checks the
`/api/v1/platform/health` endpoint exposes, runnable without the API server
up (useful right after a fresh clone, before anything is running).

Usage:
    uv run --project apps/api python -m app.db.health_cli
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.services.system_health_service import SystemHealthService

_STATUS_ICON = {
    "ok": "[OK]", "degraded": "[DEGRADED]", "unavailable": "[UNAVAILABLE]", "not_configured": "[-]",
}


def main() -> int:
    session = SessionLocal()
    try:
        report = SystemHealthService(session).check_all()
        print(f"System Health - checked at {report.checked_at.isoformat()}\n")
        exit_code = 0
        for service in report.services:
            icon = _STATUS_ICON.get(service.status, "[?]")
            line = f"  {icon:14s} {service.name}"
            print(line)
            if service.detail:
                print(f"                 {service.detail}")
            if service.status == "unavailable":
                exit_code = 1
        return exit_code
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
