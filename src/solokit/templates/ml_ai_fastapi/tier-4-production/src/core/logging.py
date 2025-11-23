"""
Structured logging configuration using structlog
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.core.config import settings


def add_app_context(_logger: Any, _method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log events.

    Args:
        _logger: Logger instance (required by structlog processor protocol, unused)
        _method_name: Method name (required by structlog processor protocol, unused)
        event_dict: Event dictionary

    Returns:
        EventDict: Updated event dictionary
    """
    event_dict["app"] = settings.APP_NAME
    event_dict["env"] = settings.ENVIRONMENT
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging with structlog.
    """
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Add JSON or console rendering based on settings
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logging
configure_logging()

# Create logger instance
logger = structlog.get_logger()
