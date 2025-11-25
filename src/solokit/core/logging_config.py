"""Centralized logging configuration for Solokit."""

import json
import logging
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Format logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Format logs for human reading."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record for console.

        Args:
            record: Log record to format

        Returns:
            Human-readable log string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        name = record.name.split(".")[-1]  # Extract last component only
        message = record.getMessage()

        # Color code by level
        level_colors = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
        }
        color = level_colors.get(level, "")
        reset = "\033[0m"

        formatted = f"{timestamp} {color}{level:8}{reset} {name} - {message}"

        # Add exception if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    structured: bool = False,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        structured: Use structured JSON logging (default: False)
    """
    root_logger = logging.getLogger("solokit")
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(HumanReadableFormatter())
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"solokit.{name}")


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, logger: logging.Logger, **context: Any):
        """
        Initialize with logger and context data.

        Args:
            logger: Logger instance to add context to
            **context: Key-value pairs to add as context
        """
        self.logger = logger
        self.context = context
        self.old_factory: Callable[..., logging.LogRecord] | None = None

    def __enter__(self) -> "LogContext":
        """Add context to log records."""
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = old_factory(*args, **kwargs)
            record.context = self.context
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, *args: Any) -> None:
        """Restore original factory."""
        if self.old_factory is not None:
            logging.setLogRecordFactory(self.old_factory)
