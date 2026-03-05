"""Request Tracing — UUID per-request for latency profiling.

Adds trace_id to every request via FastAPI middleware.
Requirements: 34.1, 34.2, 34.3
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logging import get_logger

logger = get_logger("tracing")


class TracingMiddleware(BaseHTTPMiddleware):
    """Adds trace_id header to every request and logs latency.

    Headers:
        X-Trace-ID: UUID v4 — injected into request and response
        X-Response-Time-Ms: Latency in milliseconds
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        # Store trace_id in request state for downstream use
        request.state.trace_id = trace_id

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

        logger.info(
            "request_completed",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=elapsed_ms,
        )

        return response


def get_trace_id(request: Request) -> str:
    """Helper to extract trace_id from request state."""
    return getattr(request.state, "trace_id", "no-trace")
