"""
OpenTelemetry tracing middleware
"""

from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add distributed tracing with OpenTelemetry.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add tracing context to request.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response: FastAPI response
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.client": request.client.host if request.client else "unknown",
            },
        ) as span:
            response: Response = await call_next(request)

            # Add response attributes to span
            span.set_attribute("http.status_code", response.status_code)

            return response


def configure_tracing(app: Any) -> None:
    """
    Configure OpenTelemetry tracing for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Only configure tracing in production
    if settings.ENVIRONMENT != "development":
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
