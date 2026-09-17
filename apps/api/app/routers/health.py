from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health_check() -> HealthStatus:
    settings = get_settings()
    return HealthStatus(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )
