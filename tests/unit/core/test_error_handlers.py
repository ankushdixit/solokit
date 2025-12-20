"""Unit tests for error handlers"""

import subprocess
import sys
import time

import pytest

from solokit.core.error_handlers import (
    ErrorContext,
    convert_file_errors,
    convert_subprocess_errors,
    log_errors,
    safe_execute,
    with_retry,
    with_timeout,
)
from solokit.core.exceptions import (
    ErrorCode,
    GitError,
    SubprocessError,
    SystemError,
    ValidationError,
)
from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
from solokit.core.exceptions import TimeoutError as SolokitTimeoutError


class TestWithRetryDecorator:
    """Test retry decorator"""

    def test_successful_first_attempt(self):
        """Test function succeeds on first attempt"""
        call_count = 0

        @with_retry(max_attempts=3, delay_seconds=0.01)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_until_success(self):
        """Test function succeeds after retries"""
        attempt_count = 0

        @with_retry(max_attempts=3, delay_seconds=0.01)
        def eventual_success():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = eventual_success()
        assert result == "success"
        assert attempt_count == 3

    def test_all_attempts_fail(self):
        """Test function fails after all attempts"""
        attempt_count = 0

        @with_retry(max_attempts=3, delay_seconds=0.01)
        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            always_fails()

        assert attempt_count == 3

    def test_retry_with_backoff(self):
        """Test retry uses exponential backoff"""
        timestamps = []

        @with_retry(max_attempts=3, delay_seconds=0.1, backoff_multiplier=2.0)
        def failing_function():
            timestamps.append(time.time())
            raise ValueError("Error")

        with pytest.raises(ValueError):
            failing_function()

        # Check that delays increased (approximately)
        assert len(timestamps) == 3
        delay1 = timestamps[1] - timestamps[0]
        delay2 = timestamps[2] - timestamps[1]
        assert delay2 > delay1  # Second delay should be longer

    def test_retry_specific_exceptions_only(self):
        """Test retry only catches specified exceptions"""

        @with_retry(max_attempts=3, delay_seconds=0.01, exceptions=(ValueError,))
        def raise_type_error():
            raise TypeError("Should not retry")

        with pytest.raises(TypeError):
            raise_type_error()


class TestWithTimeoutDecorator:
    """Test timeout decorator"""

    @pytest.mark.skipif(not hasattr(subprocess, "run"), reason="Requires subprocess module")
    def test_function_completes_within_timeout(self):
        """Test function completes before timeout"""

        @with_timeout(seconds=2, operation_name="quick_operation")
        def quick_function():
            time.sleep(0.1)
            return "completed"

        result = quick_function()
        assert result == "completed"

    @pytest.mark.skipif(sys.platform == "win32", reason="Timeout not supported on Windows")
    def test_function_times_out(self):
        """Test function raises timeout error"""

        @with_timeout(seconds=1, operation_name="slow_operation")
        def slow_function():
            time.sleep(3)
            return "should not reach here"

        with pytest.raises(SolokitTimeoutError) as exc_info:
            slow_function()

        assert "slow_operation" in str(exc_info.value)
        assert exc_info.value.context["timeout_seconds"] == 1


class TestLogErrorsDecorator:
    """Test log errors decorator"""

    def test_logs_solokit_error(self, caplog):
        """Test logging of SolokitError at ERROR level (system errors)"""
        from solokit.core.exceptions import SystemError

        @log_errors()
        def raises_solokit_error():
            raise SystemError(
                message="Test system error",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={"component": "test"},
            )

        with pytest.raises(SystemError):
            raises_solokit_error()

        assert "raises_solokit_error failed" in caplog.text
        assert "Test system error" in caplog.text

    def test_logs_validation_error_at_debug(self, caplog):
        """Test logging of ValidationError at DEBUG level (user input errors)"""
        import logging

        caplog.set_level(logging.DEBUG)

        @log_errors()
        def raises_validation_error():
            raise ValidationError(
                message="Test validation error",
                code=ErrorCode.INVALID_WORK_ITEM_ID,
                context={"item_id": "test"},
            )

        with pytest.raises(ValidationError):
            raises_validation_error()

        assert "raises_validation_error failed" in caplog.text
        assert "Test validation error" in caplog.text

    def test_logs_notfound_error_at_debug(self, caplog):
        """Test logging of NotFoundError at DEBUG level (user input errors)"""
        import logging

        from solokit.core.exceptions import WorkItemNotFoundError

        caplog.set_level(logging.DEBUG)

        @log_errors()
        def raises_notfound_error():
            raise WorkItemNotFoundError("nonexistent_item")

        with pytest.raises(WorkItemNotFoundError):
            raises_notfound_error()

        assert "raises_notfound_error failed" in caplog.text

    def test_logs_generic_error(self, caplog):
        """Test logging of generic exception"""

        @log_errors()
        def raises_generic_error():
            raise ValueError("Generic error")

        with pytest.raises(ValueError):
            raises_generic_error()

        assert "raises_generic_error failed with unexpected error" in caplog.text

    def test_successful_function_not_logged(self, caplog):
        """Test successful execution doesn't log errors"""

        @log_errors()
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"
        assert "failed" not in caplog.text


class TestConvertSubprocessErrors:
    """Test subprocess error conversion"""

    def test_converts_timeout_expired(self):
        """Test TimeoutExpired converted to SolokitTimeoutError"""

        @convert_subprocess_errors
        def timeout_command():
            raise subprocess.TimeoutExpired(
                cmd=["git", "fetch"], timeout=30, output=b"output", stderr=b"error"
            )

        with pytest.raises(SolokitTimeoutError) as exc_info:
            timeout_command()

        assert exc_info.value.code == ErrorCode.OPERATION_TIMEOUT
        assert "git fetch" in str(exc_info.value)

    def test_converts_file_not_found(self):
        """Test FileNotFoundError converted to GitError"""

        @convert_subprocess_errors
        def missing_command():
            raise FileNotFoundError(2, "No such file", "git")

        with pytest.raises(GitError) as exc_info:
            missing_command()

        assert exc_info.value.code == ErrorCode.GIT_NOT_FOUND

    def test_converts_called_process_error(self):
        """Test CalledProcessError converted to SubprocessError"""

        @convert_subprocess_errors
        def failed_command():
            raise subprocess.CalledProcessError(
                returncode=1, cmd=["pytest", "tests/"], output=b"test output", stderr=b"test failed"
            )

        with pytest.raises(SubprocessError) as exc_info:
            failed_command()

        assert exc_info.value.code == ErrorCode.SUBPROCESS_FAILED
        assert exc_info.value.context["returncode"] == 1

    def test_successful_command_not_converted(self):
        """Test successful execution not affected"""

        @convert_subprocess_errors
        def successful_command():
            return "success"

        result = successful_command()
        assert result == "success"


class TestConvertFileErrors:
    """Test file error conversion"""

    def test_converts_io_error(self):
        """Test IOError converted to SystemError"""

        @convert_file_errors
        def file_operation():
            error = OSError("Permission denied")
            error.filename = "/path/to/file"
            raise error

        with pytest.raises(SystemError) as exc_info:
            file_operation()

        assert exc_info.value.code == ErrorCode.FILE_OPERATION_FAILED

    def test_converts_file_not_found(self):
        """Test FileNotFoundError converted to SolokitFileNotFoundError"""

        @convert_file_errors
        def missing_file():
            raise FileNotFoundError(2, "No such file", "/path/to/file")

        with pytest.raises(SolokitFileNotFoundError) as exc_info:
            missing_file()

        assert exc_info.value.code == ErrorCode.FILE_NOT_FOUND


class TestErrorContext:
    """Test ErrorContext context manager"""

    def test_context_runs_cleanup_on_success(self):
        """Test cleanup runs on successful execution"""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with ErrorContext("test operation", cleanup=cleanup, item_id="123"):
            pass

        assert cleanup_called

    def test_context_runs_cleanup_on_error(self):
        """Test cleanup runs even when error occurs"""
        cleanup_called = False

        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with pytest.raises(ValueError):
            with ErrorContext("test operation", cleanup=cleanup):
                raise ValueError("Test error")

        assert cleanup_called

    def test_context_adds_data_to_solokit_error(self):
        """Test context data added to SolokitError"""
        try:
            with ErrorContext("test operation", work_item_id="123", file="test.py"):
                raise ValidationError("Test error")
        except ValidationError as e:
            assert e.context["work_item_id"] == "123"
            assert e.context["file"] == "test.py"

    def test_context_cleanup_error_logged(self, caplog):
        """Test cleanup errors are logged"""

        def failing_cleanup():
            raise ValueError("Cleanup failed")

        with pytest.raises(ValidationError):
            with ErrorContext("test operation", cleanup=failing_cleanup):
                raise ValidationError("Test error")

        assert "Cleanup failed" in caplog.text


class TestSafeExecute:
    """Test safe_execute utility"""

    def test_successful_execution(self):
        """Test successful function returns result"""

        def successful_func():
            return "success"

        result = safe_execute(successful_func, default="default")
        assert result == "success"

    def test_failed_execution_returns_default(self):
        """Test failed function returns default"""

        def failing_func():
            raise ValueError("Error")

        result = safe_execute(failing_func, default="default")
        assert result == "default"

    def test_failed_execution_logs_error(self, caplog):
        """Test failed execution logs error"""
        import logging

        def failing_func():
            raise ValueError("Error")

        with caplog.at_level(logging.WARNING, logger="solokit.core.error_handlers"):
            safe_execute(failing_func, default=None, log_errors=True)
        assert "Optional operation failed" in caplog.text

    def test_failed_execution_no_log(self, caplog):
        """Test failed execution doesn't log when disabled"""

        def failing_func():
            raise ValueError("Error")

        safe_execute(failing_func, default=None, log_errors=False)
        assert "Optional operation failed" not in caplog.text

    def test_with_arguments(self):
        """Test safe_execute with function arguments"""

        def add(a, b):
            return a + b

        result = safe_execute(add, 2, 3, default=0)
        assert result == 5

    def test_with_kwargs(self):
        """Test safe_execute with keyword arguments"""

        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}"

        result = safe_execute(greet, name="World", greeting="Hi", default="Error")
        assert result == "Hi, World"
