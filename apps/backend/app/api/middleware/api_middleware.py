"""API Runtime Enhancements - Correlation ID and Global Error middleware."""

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Injects a correlation ID into every request/response for distributed tracing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        request.state.request_id = str(uuid.uuid4())
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        logger.info(
            f"[{request.method}] {request.url.path} "
            f"correlation={correlation_id} "
            f"duration={duration_ms:.2f}ms "
            f"status={response.status_code}"
        )
        return response


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns structured error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.error(
                f"Unhandled exception: {e} correlation={correlation_id}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(e),
                    "correlation_id": correlation_id,
                },
            )
