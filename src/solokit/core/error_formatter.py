"""
Format exceptions for CLI display.

Separates presentation concerns from business logic. Business logic raises
structured exceptions, CLI layer formats them for user display.

Usage:
    from solokit.core.error_formatter import ErrorFormatter

    try:
        # Business logic
        do_something()
    except SolokitError as e:
        ErrorFormatter.print_error(e, verbose=args.verbose)
        sys.exit(e.exit_code)
"""

import sys
from typing import Any

from solokit.core.exceptions import ErrorCategory, SolokitError


class ErrorFormatter:
    """Format exceptions for CLI output"""

    @staticmethod
    def format_error(error: Exception, verbose: bool = False) -> str:
        """
        Format exception for display.

        Args:
            error: Exception to format
            verbose: Include full context and stack trace

        Returns:
            Formatted error message

        Example:
            >>> from solokit.core.exceptions import WorkItemNotFoundError
            >>> error = WorkItemNotFoundError("my_feature")
            >>> print(ErrorFormatter.format_error(error))
            🔍 Work item 'my_feature' not found
            💡 Use '/work-list' to see available work items
        """
        if isinstance(error, SolokitError):
            return ErrorFormatter._format_solokit_error(error, verbose)
        else:
            return ErrorFormatter._format_generic_error(error, verbose)

    @staticmethod
    def _format_solokit_error(error: SolokitError, verbose: bool) -> str:
        """Format SolokitError with structured data"""
        lines = []

        # Error symbol based on category
        symbol = ErrorFormatter._get_error_symbol(error.category)
        lines.append(f"{symbol} {error.message}")

        # Context (if verbose or critical info)
        if verbose and error.context:
            lines.append("\nContext:")
            for key, value in error.context.items():
                # Format lists and dicts nicely
                if isinstance(value, list):
                    lines.append(f"  {key}:")
                    for item in value[:10]:  # Limit to 10 items
                        lines.append(f"    - {item}")
                    if len(value) > 10:
                        lines.append(f"    ... and {len(value) - 10} more")
                elif isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in list(value.items())[:10]:
                        lines.append(f"    {k}: {v}")
                    if len(value) > 10:
                        lines.append(f"    ... and {len(value) - 10} more items")
                else:
                    lines.append(f"  {key}: {value}")

        # Remediation (always show if available)
        if error.remediation:
            lines.append(f"\n💡 {error.remediation}")

        # Error code (if verbose)
        if verbose:
            lines.append(f"\nError Code: {error.code.name} ({error.code.value})")
            lines.append(f"Category: {error.category.value}")

        # Cause (if present)
        if verbose and error.cause:
            lines.append(f"\nCaused by: {error.cause}")

        return "\n".join(lines)

    @staticmethod
    def _format_generic_error(error: Exception, verbose: bool) -> str:
        """Format generic exception"""
        if verbose:
            import traceback

            return f"❌ {type(error).__name__}: {error}\n\n{traceback.format_exc()}"
        else:
            return f"❌ {type(error).__name__}: {error}"

    @staticmethod
    def _get_error_symbol(category: ErrorCategory) -> str:
        """Get emoji symbol for error category"""
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
        return symbols.get(category, "❌")

    @staticmethod
    def print_error(error: Exception, verbose: bool = False, file: Any = None) -> None:
        """
        Print formatted error to stderr.

        Args:
            error: Exception to print
            verbose: Include full context
            file: Output stream (default: stderr)

        Example:
            >>> try:
            ...     raise ValidationError("Invalid input")
            ... except SolokitError as e:
            ...     ErrorFormatter.print_error(e)
        """
        import logging

        if file is None:
            file = sys.stderr

        formatted = ErrorFormatter.format_error(error, verbose)
        logger = logging.getLogger(__name__)

        try:
            print(formatted, file=file)
        except (ValueError, OSError) as e:
            # Handle closed file (e.g., in tests with capsys)
            logger.warning(f"Could not write to stderr: {e}, trying stdout")
            try:
                print(formatted, file=sys.stdout)
            except (ValueError, OSError) as e2:
                # Both are closed - log the error instead of silently suppressing
                logger.error(f"Could not write error to stderr or stdout: {e2}")
                logger.error(f"Original error message: {formatted}")

    @staticmethod
    def get_exit_code(error: Exception) -> int:
        """
        Get appropriate exit code for error.

        Args:
            error: Exception to get exit code for

        Returns:
            Exit code (0 for success, >0 for errors)

        Example:
            >>> from solokit.core.exceptions import ValidationError, ErrorCode
            >>> error = ValidationError("test", code=ErrorCode.INVALID_WORK_ITEM_ID)
            >>> ErrorFormatter.get_exit_code(error)
            2
        """
        if isinstance(error, SolokitError):
            return error.exit_code
        else:
            return 1  # Generic error


def format_validation_errors(errors: list[str], header: str | None = None) -> str:
    """
    Format a list of validation errors for display.

    Args:
        errors: List of error messages
        header: Optional header to display before errors

    Returns:
        Formatted error message

    Example:
        >>> errors = ["Missing field 'name'", "Invalid value for 'age'"]
        >>> print(format_validation_errors(errors, "Validation failed"))
        ⚠️ Validation failed

          1. Missing field 'name'
          2. Invalid value for 'age'
    """
    lines = []

    if header:
        lines.append(f"⚠️ {header}")
        lines.append("")

    for i, error in enumerate(errors, 1):
        lines.append(f"  {i}. {error}")

    return "\n".join(lines)


def format_progress_message(current: int, total: int, message: str) -> str:
    """
    Format a progress message with count.

    Args:
        current: Current item number
        total: Total number of items
        message: Progress message

    Returns:
        Formatted progress message

    Example:
        >>> print(format_progress_message(3, 10, "Processing files"))
        [3/10] Processing files...
    """
    return f"[{current}/{total}] {message}..."


def format_success_message(message: str) -> str:
    """
    Format a success message.

    Args:
        message: Success message

    Returns:
        Formatted success message with checkmark

    Example:
        >>> print(format_success_message("Work item created"))
        ✅ Work item created
    """
    return f"✅ {message}"


def format_warning_message(message: str) -> str:
    """
    Format a warning message.

    Args:
        message: Warning message

    Returns:
        Formatted warning message with icon

    Example:
        >>> print(format_warning_message("Config file not found, using defaults"))
        ⚠️ Config file not found, using defaults
    """
    return f"⚠️ {message}"


def format_info_message(message: str) -> str:
    """
    Format an info message.

    Args:
        message: Info message

    Returns:
        Formatted info message with icon

    Example:
        >>> print(format_info_message("Loading configuration"))
        ℹ️ Loading configuration
    """
    return f"ℹ️ {message}"
