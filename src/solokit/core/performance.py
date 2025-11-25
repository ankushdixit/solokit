"""Performance monitoring and profiling"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from solokit.core.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def measure_time(operation: str | None = None) -> Callable[[F], F]:
    """Decorator to measure function execution time"""

    def decorator(func: F) -> F:
        op_name = operation or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if duration > 1.0:  # Warn if > 1s
                    logger.warning(f"Slow operation: {op_name} took {duration:.3f}s")
                elif duration > 0.1:  # Log if > 100ms
                    logger.info(f"Performance: {op_name} took {duration:.3f}s")

        return cast(F, wrapper)

    return decorator


class Timer:
    """Context manager for timing code blocks"""

    def __init__(self, name: str):
        """Initialize timer with name"""
        self.name = name
        self.start: float | None = None
        self.duration: float | None = None

    def __enter__(self) -> "Timer":
        """Start timer"""
        self.start = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        """End timer and log"""
        if self.start is not None:
            self.duration = time.time() - self.start
            if self.duration > 0.1:
                logger.info(f"Performance: {self.name} took {self.duration:.3f}s")
