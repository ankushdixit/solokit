"""Protocol definitions for structural subtyping in Solokit.

This module defines protocols (structural types) that allow for
duck-typing with type safety. Protocols define interfaces that
classes can satisfy implicitly.
"""

from __future__ import annotations

from typing import Any, Protocol


class JSONSerializable(Protocol):
    """Protocol for objects that can be serialized to JSON.

    Any class that implements a to_dict method returning a dictionary
    satisfies this protocol.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert object to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        ...  # pragma: no cover


class Validatable(Protocol):
    """Protocol for objects that can be validated.

    Any class that implements a validate method satisfies this protocol.
    """

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the object.

        Returns:
            Tuple of (is_valid, list of error messages)
            - is_valid: True if validation passed, False otherwise
            - error messages: List of validation error messages (empty if valid)
        """
        ...  # pragma: no cover


class Configurable(Protocol):
    """Protocol for objects that can be configured.

    Any class that implements load_config and save_config methods
    satisfies this protocol.
    """

    def load_config(self, config: dict[str, Any]) -> None:
        """Load configuration from dictionary.

        Args:
            config: Configuration dictionary
        """
        ...  # pragma: no cover

    def save_config(self) -> dict[str, Any]:
        """Save configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        ...  # pragma: no cover


class Executor(Protocol):
    """Protocol for objects that can execute operations.

    Any class that implements an execute method satisfies this protocol.
    """

    def execute(self) -> tuple[bool, str]:
        """Execute the operation.

        Returns:
            Tuple of (success, message)
            - success: True if execution succeeded, False otherwise
            - message: Status or error message
        """
        ...  # pragma: no cover


class SupportsComparison(Protocol):
    """Protocol for objects that support comparison operations.

    Any class that implements comparison methods satisfies this protocol.
    """

    def __lt__(self, other: Any) -> bool:
        """Less than comparison."""
        ...  # pragma: no cover

    def __le__(self, other: Any) -> bool:
        """Less than or equal comparison."""
        ...  # pragma: no cover

    def __gt__(self, other: Any) -> bool:
        """Greater than comparison."""
        ...  # pragma: no cover

    def __ge__(self, other: Any) -> bool:
        """Greater than or equal comparison."""
        ...  # pragma: no cover


class FileReader(Protocol):
    """Protocol for objects that can read files.

    Any class that implements a read method satisfies this protocol.
    """

    def read(self, file_path: str) -> str:
        """Read content from file.

        Args:
            file_path: Path to file to read

        Returns:
            File content as string
        """
        ...  # pragma: no cover


class FileWriter(Protocol):
    """Protocol for objects that can write files.

    Any class that implements a write method satisfies this protocol.
    """

    def write(self, file_path: str, content: str) -> None:
        """Write content to file.

        Args:
            file_path: Path to file to write
            content: Content to write
        """
        ...  # pragma: no cover
