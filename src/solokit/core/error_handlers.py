"""
Error handling decorators and utilities.

Provides decorators for common error handling patterns like retry,
timeout, and logging. Separates error handling concerns from business logic.

Usage:
    from solokit.core.error_handlers import with_retry, log_errors

    @log_errors()
    @with_retry(max_attempts=3)
    def load_config(path: str) -> dict:
        return json.load(open(path))
"""

from __future__ import annotations

import functools
import logging
import subprocess
import time
from collections.abc import Callable
from typing import Any, Literal, TypeVar

from solokit.core.exceptions import ErrorCode, GitError, SolokitError, SubprocessError, SystemError
from solokit.core.exceptions import TimeoutError as SolokitTimeoutError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_timeout(
    seconds: int, operation_name: str
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add timeout to function execution.

    Note: This uses signal.alarm which only works on Unix systems.
    On Windows, the timeout is not enforced but the function still runs.

    Args:
        seconds: Timeout in seconds
        operation_name: Name of operation for error message

    Returns:
        Decorator function

    Raises:
        TimeoutError: If function exceeds timeout

    Example:
        >>> @with_timeout(seconds=5, operation_name="fetch data")
        ... def fetch_data():
        ...     time.sleep(10)  # Will timeout
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                import signal

                def timeout_handler(signum: int, frame: Any) -> None:
                    raise SolokitTimeoutError(operation=operation_name, timeout_seconds=seconds)

                # Set up timeout signal (Unix only)
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                try:
                    return func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            except AttributeError:
                # Windows doesn't have SIGALRM, just run without timeout
                logger.warning(f"Timeout not supported on this platform for {operation_name}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


def with_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between attempts
        backoff_multiplier: Multiply delay by this after each attempt
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorator function

    Example:
        >>> @with_retry(max_attempts=3, delay_seconds=2.0)
        ... def load_file(path: Path) -> dict:
        ...     return json.load(open(path))
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = delay_seconds
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")

            # Re-raise the last exception
            if last_exception:
                raise last_exception
            # This should never happen, but mypy needs it
            raise RuntimeError(f"{func.__name__} completed without returning or raising")

        return wrapper

    return decorator


def log_errors(
    logger_instance: logging.Logger | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to log exceptions with structured data.

    Args:
        logger_instance: Logger to use (defaults to function's module logger)

    Returns:
        Decorator function

    Example:
        >>> @log_errors()
        ... def process_work_item(item_id: str):
        ...     # Business logic that may raise SolokitError
        ...     pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            log = logger_instance or logging.getLogger(func.__module__)

            try:
                return func(*args, **kwargs)
            except SolokitError as e:
                # Import here to avoid circular dependency
                from solokit.core.exceptions import NotFoundError, ValidationError

                # User input errors (ValidationError, NotFoundError) should be DEBUG level
                # System/integration errors should be ERROR level
                if isinstance(e, (ValidationError, NotFoundError)):
                    log.debug(
                        f"{func.__name__} failed: {e.message}",
                        extra={
                            "error_code": e.code.value,
                            "error_category": e.category.value,
                            "context": e.context,
                            "function": func.__name__,
                        },
                    )
                else:
                    # Log system/integration errors at ERROR level
                    log.error(
                        f"{func.__name__} failed: {e.message}",
                        extra={
                            "error_code": e.code.value,
                            "error_category": e.category.value,
                            "context": e.context,
                            "function": func.__name__,
                        },
                    )
                raise
            except Exception as e:  # noqa: BLE001 - Logging decorator catches all for observability
                # Log unexpected errors
                log.exception(
                    f"{func.__name__} failed with unexpected error: {e}",
                    extra={"function": func.__name__},
                )
                raise

        return wrapper

    return decorator


def convert_subprocess_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to convert subprocess exceptions to SolokitError.

    Converts FileNotFoundError and subprocess exceptions to structured errors.

    Example:
        >>> @convert_subprocess_errors
        ... def run_git_command(args: list[str]) -> str:
        ...     result = subprocess.run(["git"] + args, check=True, capture_output=True, text=True)
        ...     return result.stdout
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except subprocess.TimeoutExpired as e:
            raise SolokitTimeoutError(
                operation=f"subprocess: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}",
                timeout_seconds=int(e.timeout),
                context={"stdout": e.stdout, "stderr": e.stderr},
            ) from e
        except FileNotFoundError as e:
            # Command not found (e.g., git not installed)
            cmd_name = e.filename or "unknown command"
            raise GitError(
                message=f"Command not found: {cmd_name}",
                code=ErrorCode.GIT_NOT_FOUND,
                remediation=f"Install {cmd_name} or ensure it's in your PATH",
                cause=e,
            ) from e
        except subprocess.CalledProcessError as e:
            raise SubprocessError(
                command=" ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd),
                returncode=e.returncode,
                stderr=e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr,
                stdout=e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout,
            ) from e

    return wrapper


def convert_file_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to convert file operation exceptions to SolokitError.

    Converts IOError, OSError, FileNotFoundError, etc. to structured errors.

    Example:
        >>> @convert_file_errors
        ... def read_config(path: str) -> dict:
        ...     with open(path) as f:
        ...         return json.load(f)
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        import builtins

        from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError

        try:
            return func(*args, **kwargs)
        except builtins.FileNotFoundError as e:
            # Catch FileNotFoundError first (it's a subclass of OSError)
            file_path = getattr(e, "filename", "unknown")
            raise SolokitFileNotFoundError(file_path=file_path) from e
        except OSError as e:
            # Extract file path from exception if available
            file_path = getattr(e, "filename", "unknown")
            raise SystemError(
                message=f"File operation failed: {e}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={"file_path": file_path, "error": str(e)},
                cause=e,
            ) from e

    return wrapper


class ErrorContext:
    """
    Context manager for handling errors with cleanup.

    Example:
        >>> with ErrorContext("processing work item", work_item_id=item_id):
        ...     # Do work that may raise errors
        ...     process_item(item_id)
    """

    def __init__(
        self, operation: str, cleanup: Callable[[], None] | None = None, **context_data: Any
    ) -> None:
        self.operation = operation
        self.cleanup = cleanup
        self.context_data = context_data

    def __enter__(self) -> ErrorContext:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        # Run cleanup regardless of success/failure
        if self.cleanup:
            try:
                self.cleanup()
            except Exception as e:  # noqa: BLE001 - Cleanup must not fail the main operation
                logger.error(f"Cleanup failed for {self.operation}: {e}")

        # Add context to SolokitError if present
        if exc_type and issubclass(exc_type, SolokitError):
            exc_val.context.update(self.context_data)

        # Don't suppress exception
        return False


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T | None = None,
    log_errors: bool = True,
    **kwargs: Any,
) -> T | None:
    """
    Execute function and return default value on error instead of raising.

    Useful for optional operations where failure should not stop execution.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        default: Value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for func

    Returns:
        Function result or default value

    Example:
        >>> result = safe_execute(
        ...     load_optional_config,
        ...     "/path/to/config.json",
        ...     default={}
        ... )
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 - safe_execute is designed to catch all errors
        if log_errors:
            logger.warning(
                f"Optional operation failed: {func.__name__}: {e}",
                extra={"function": func.__name__, "error": str(e)},
            )
        return default
