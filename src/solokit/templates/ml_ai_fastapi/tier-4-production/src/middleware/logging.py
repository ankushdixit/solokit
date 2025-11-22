"""
Request/Response logging middleware
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response: FastAPI response
        """
        # Start timer
        start_time = time.time()

        # Extract request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Log incoming request
        logger.info(
            "request_started",
            method=method,
            path=path,
            client=client_host,
        )

        # Process request
        try:
            response: Response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log successful response
            logger.info(
                "request_completed",
                method=method,
                path=path,
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)

            return response  # noqa: TRY300

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                "request_failed",
                method=method,
                path=path,
                duration=f"{duration:.3f}s",
                error=str(e),
                exc_info=True,
            )
            raise
