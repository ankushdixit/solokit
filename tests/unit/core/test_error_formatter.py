"""Unit tests for error formatter"""

from io import StringIO

from solokit.core.error_formatter import (
    ErrorFormatter,
    format_info_message,
    format_progress_message,
    format_success_message,
    format_validation_errors,
    format_warning_message,
)
from solokit.core.exceptions import (
    ConfigValidationError,
    ErrorCategory,
    ErrorCode,
    GitError,
    ValidationError,
    WorkItemNotFoundError,
)


class TestErrorFormatter:
    """Test ErrorFormatter class"""

    def test_format_solokit_error_basic(self):
        """Test formatting basic SolokitError"""
        error = WorkItemNotFoundError("my_feature")
        formatted = ErrorFormatter.format_error(error, verbose=False)

        assert "🔍" in formatted  # Not found symbol
        assert "my_feature" in formatted
        assert "/work-list" in formatted  # Remediation

    def test_format_solokit_error_verbose(self):
        """Test verbose formatting includes context and error code"""
        error = ValidationError(
            message="Test error",
            code=ErrorCode.INVALID_WORK_ITEM_ID,
            context={"work_item_id": "bad-id", "field": "name"},
        )
        formatted = ErrorFormatter.format_error(error, verbose=True)

        assert "⚠️" in formatted  # Validation symbol
        assert "Context:" in formatted
        assert "work_item_id" in formatted
        assert "bad-id" in formatted
        assert "Error Code:" in formatted
        assert "INVALID_WORK_ITEM_ID" in formatted

    def test_format_error_with_list_context(self):
        """Test formatting error with list in context"""
        error = ConfigValidationError(
            config_path=".session/config.json", errors=["Error 1", "Error 2", "Error 3"]
        )
        formatted = ErrorFormatter.format_error(error, verbose=True)

        assert "validation_errors:" in formatted
        assert "Error 1" in formatted
        assert "Error 2" in formatted

    def test_format_error_with_dict_context(self):
        """Test formatting error with dict in context"""
        error = ValidationError(
            message="Test error", context={"metadata": {"key1": "value1", "key2": "value2"}}
        )
        formatted = ErrorFormatter.format_error(error, verbose=True)

        assert "metadata:" in formatted
        assert "key1" in formatted

    def test_format_error_with_long_list(self):
        """Test formatting limits long lists"""
        errors = [f"Error {i}" for i in range(15)]
        error = ConfigValidationError(config_path=".session/config.json", errors=errors)
        formatted = ErrorFormatter.format_error(error, verbose=True)

        assert "... and 5 more" in formatted

    def test_format_generic_error(self):
        """Test formatting generic exception"""
        error = ValueError("Generic error")
        formatted = ErrorFormatter.format_error(error, verbose=False)

        assert "❌" in formatted
        assert "ValueError" in formatted
        assert "Generic error" in formatted

    def test_format_generic_error_verbose(self):
        """Test verbose formatting of generic exception includes traceback"""
        try:
            raise ValueError("Generic error")
        except ValueError as e:
            formatted = ErrorFormatter.format_error(e, verbose=True)

        assert "ValueError" in formatted
        assert "Generic error" in formatted
        assert "Traceback" in formatted or "File" in formatted

    def test_get_error_symbol(self):
        """Test error symbols map correctly"""
        symbols = {
            ErrorCategory.VALIDATION: "⚠️",
            ErrorCategory.NOT_FOUND: "🔍",
            ErrorCategory.CONFIGURATION: "⚙️",
            ErrorCategory.SYSTEM: "💥",
            ErrorCategory.GIT: "🔀",
            ErrorCategory.DEPENDENCY: "🔗",
            ErrorCategory.SECURITY: "🔒",
            ErrorCategory.TIMEOUT: "⏱️",
            ErrorCategory.ALREADY_EXISTS: "📋",
            ErrorCategory.PERMISSION: "🔐",
        }

        for category, expected_symbol in symbols.items():
            assert ErrorFormatter._get_error_symbol(category) == expected_symbol

    def test_print_error(self):
        """Test printing error to stream"""
        error = WorkItemNotFoundError("my_feature")
        output = StringIO()

        ErrorFormatter.print_error(error, verbose=False, file=output)

        result = output.getvalue()
        assert "my_feature" in result
        assert "🔍" in result

    def test_get_exit_code_solokit_error(self):
        """Test exit code extraction from SolokitError"""
        validation_error = ValidationError("test")
        assert ErrorFormatter.get_exit_code(validation_error) == 2

        not_found_error = WorkItemNotFoundError("test")
        assert ErrorFormatter.get_exit_code(not_found_error) == 3

        git_error = GitError("test", code=ErrorCode.GIT_COMMAND_FAILED)
        assert ErrorFormatter.get_exit_code(git_error) == 6

    def test_get_exit_code_generic_error(self):
        """Test exit code for generic exception"""
        error = ValueError("test")
        assert ErrorFormatter.get_exit_code(error) == 1

    def test_format_error_with_cause(self):
        """Test formatting error with cause chain"""
        original = ValueError("Original error")
        error = ValidationError(message="Validation failed", cause=original)
        formatted = ErrorFormatter.format_error(error, verbose=True)

        assert "Caused by:" in formatted
        assert "Original error" in formatted

    def test_format_error_with_remediation(self):
        """Test remediation always shown"""
        error = ValidationError(message="Test error", remediation="This is how to fix it")
        formatted = ErrorFormatter.format_error(error, verbose=False)

        assert "💡" in formatted
        assert "This is how to fix it" in formatted


class TestFormatHelpers:
    """Test formatting helper functions"""

    def test_format_validation_errors(self):
        """Test formatting validation errors"""
        errors = ["Missing field 'name'", "Invalid value for 'age'"]
        formatted = format_validation_errors(errors, header="Validation failed")

        assert "⚠️ Validation failed" in formatted
        assert "1. Missing field 'name'" in formatted
        assert "2. Invalid value for 'age'" in formatted

    def test_format_validation_errors_no_header(self):
        """Test formatting validation errors without header"""
        errors = ["Error 1", "Error 2"]
        formatted = format_validation_errors(errors)

        assert "1. Error 1" in formatted
        assert "2. Error 2" in formatted
        assert "⚠️" not in formatted

    def test_format_progress_message(self):
        """Test formatting progress message"""
        formatted = format_progress_message(3, 10, "Processing files")
        assert formatted == "[3/10] Processing files..."

    def test_format_success_message(self):
        """Test formatting success message"""
        formatted = format_success_message("Work item created")
        assert formatted == "✅ Work item created"

    def test_format_warning_message(self):
        """Test formatting warning message"""
        formatted = format_warning_message("Config file not found, using defaults")
        assert formatted == "⚠️ Config file not found, using defaults"

    def test_format_info_message(self):
        """Test formatting info message"""
        formatted = format_info_message("Loading configuration")
        assert formatted == "ℹ️ Loading configuration"


class TestErrorFormatterEdgeCases:
    """Edge case tests for error formatting"""

    def test_format_error_with_large_dict_context(self):
        """Test formatting error with dict context > 10 items shows truncation message"""
        # Create a dict with more than 10 items
        large_dict = {f"key{i}": f"value{i}" for i in range(15)}
        error = ValidationError(message="Test error", context={"large_data": large_dict})
        formatted = ErrorFormatter.format_error(error, verbose=True)

        # Should show truncation message for large dicts
        assert "... and 5 more items" in formatted

    def test_print_error_with_closed_file(self):
        """Test printing error when file is closed falls back to stdout"""
        from io import StringIO

        error = WorkItemNotFoundError("my_feature")
        closed_file = StringIO()
        closed_file.close()

        # Should not raise - should handle gracefully
        # The function will try stdout as fallback
        ErrorFormatter.print_error(error, verbose=False, file=closed_file)

    def test_print_error_both_streams_closed(self):
        """Test printing error when both stderr and stdout fail handles gracefully"""
        from unittest.mock import MagicMock, patch

        error = WorkItemNotFoundError("my_feature")

        # Mock the logger to capture logging calls without writing to streams
        mock_logger = MagicMock()

        with (
            patch("builtins.print", side_effect=ValueError("stream closed")),
            patch("logging.getLogger", return_value=mock_logger),
        ):
            # Should not raise - handles gracefully
            ErrorFormatter.print_error(error, verbose=False)

        # Verify the error was logged (logger.error was called)
        assert mock_logger.error.called or mock_logger.warning.called


class TestErrorFormatterIntegration:
    """Integration tests for error formatting"""

    def test_complete_error_flow(self):
        """Test complete error formatting flow"""
        # Create error with all attributes
        error = ValidationError(
            message="Work item validation failed",
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context={
                "work_item_id": "my_feature",
                "errors": ["Missing section", "Invalid format"],
                "file_path": ".session/specs/my_feature.md",
            },
            remediation="Edit the spec file to fix validation errors",
        )

        # Format in normal mode
        normal = ErrorFormatter.format_error(error, verbose=False)
        assert "⚠️" in normal
        assert "Work item validation failed" in normal
        assert "Edit the spec file" in normal
        assert "Context:" not in normal  # Not in normal mode

        # Format in verbose mode
        verbose = ErrorFormatter.format_error(error, verbose=True)
        assert "⚠️" in verbose
        assert "Context:" in verbose
        assert "work_item_id" in verbose
        assert "my_feature" in verbose
        assert "Error Code:" in verbose
        assert "SPEC_VALIDATION_FAILED" in verbose

    def test_nested_context_formatting(self):
        """Test formatting of nested context structures"""
        error = ValidationError(
            message="Complex validation error",
            context={
                "simple": "value",
                "list": ["item1", "item2", "item3"],
                "dict": {"key1": "val1", "key2": "val2"},
                "number": 42,
                "boolean": True,
            },
        )

        formatted = ErrorFormatter.format_error(error, verbose=True)

        # Check all context items are present
        assert "simple: value" in formatted
        assert "list:" in formatted
        assert "item1" in formatted
        assert "dict:" in formatted
        assert "key1: val1" in formatted
        assert "number: 42" in formatted
        assert "boolean: True" in formatted
