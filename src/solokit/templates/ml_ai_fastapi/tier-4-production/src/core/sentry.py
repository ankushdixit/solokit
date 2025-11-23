"""
Sentry error tracking integration
"""

from typing import Any

import sentry_sdk  # pyright: ignore[reportMissingImports]
from sentry_sdk.integrations.fastapi import (  # pyright: ignore[reportMissingImports]
    FastApiIntegration,
)
from sentry_sdk.integrations.sqlalchemy import (  # pyright: ignore[reportMissingImports]
    SqlalchemyIntegration,
)

from src.core.config import settings

# HTTP status codes
HTTP_NOT_FOUND = 404


def initialize_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking.
    Only initializes in non-development environments.
    """
    # Only initialize Sentry in production/staging
    if settings.ENVIRONMENT == "development":
        return

    # Check if Sentry DSN is configured
    sentry_dsn = getattr(settings, "SENTRY_DSN", None)
    if not sentry_dsn:
        return

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=settings.ENVIRONMENT,
        release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% of transactions for profiling
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions
        # Adjust this value in production to reduce overhead
        send_default_pii=False,  # Don't send personally identifiable information
        before_send=before_send_filter,
    )


def before_send_filter(event: Any, hint: dict[str, Any]) -> Any:
    """
    Filter events before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        dict | None: Event to send or None to skip
    """
    # Filter out specific exceptions or add custom logic
    # Example: Don't send 404 errors
    if "exc_info" in hint:
        exc_type, exc_value, _tb = hint["exc_info"]
        if (
            exc_type.__name__ == "HTTPException"
            and hasattr(exc_value, "status_code")
            and exc_value.status_code == HTTP_NOT_FOUND
        ):
            return None

    return event
