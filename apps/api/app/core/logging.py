import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Basic structured-ish console logging for local development.

    Kept intentionally simple for Phase 1. Later phases may swap this for
    structured JSON logging, metrics, and tracing without touching callers —
    everything logs through the standard `logging` module.
    """
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))

    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.handlers = [handler]

    # Quiet noisy third-party loggers at INFO.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING if settings.is_test else logging.INFO)
