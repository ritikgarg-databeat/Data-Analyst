"""Request-ID + duration logging middleware (Phase 12) — the one concrete
gap a Phase 12 audit found in an otherwise-clean logging/error-handling
posture: `app/core/logging.py` had no per-request correlation id or
duration, and no middleware existed beyond CORS. This adds both, without
touching the existing plain-text log format or `AppError` handling."""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_current_request_id() -> str | None:
    """Read from anywhere in the current request's call stack (e.g. to
    attach to an error response's `details`) without threading it through
    every function signature."""
    return _request_id_ctx.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request id (reusing an inbound `X-Request-ID` header if the
    caller already provides one — useful when this API sits behind another
    proxy that generates its own), times the request, and logs one line per
    request: method, path, status, duration, request id. Echoes the id back
    as a response header so a caller can correlate it with these logs."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = _request_id_ctx.set(request_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.exception(
                "request_id=%s method=%s path=%s status=500 duration_ms=%s",
                request_id, request.method, request.url.path, duration_ms,
            )
            raise
        else:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id, request.method, request.url.path, response.status_code, duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            _request_id_ctx.reset(token)
