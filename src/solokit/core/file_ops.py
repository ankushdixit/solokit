"""File operations utilities

Centralized file I/O operations with consistent error handling and atomicity guarantees.
"""

import json
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from solokit.core.exceptions import (
    ErrorCode,
    FileOperationError,
    SystemError,
)
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)

logger = logging.getLogger(__name__)


class JSONFileOperations:
    """Centralized JSON file I/O with atomic writes and error handling"""

    @staticmethod
    def load_json(
        file_path: Path,
        default: dict[str, Any] | None = None,
        validator: Callable[[dict], bool] | None = None,
    ) -> dict[str, Any]:
        """
        Load JSON file with optional default and validation

        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist (None raises error)
            validator: Optional validation function that returns True if data is valid

        Returns:
            Loaded JSON data as dict

        Raises:
            FileOperationError: If file not found and no default provided
            FileOperationError: If JSON is invalid
            FileOperationError: If validation fails

        Examples:
            >>> # Load required file (raises if missing)
            >>> data = JSONFileOperations.load_json(Path("config.json"))
            >>> # Load with default
            >>> data = JSONFileOperations.load_json(Path("optional.json"), default={})
            >>> # Load with validation
            >>> validator = lambda d: "version" in d
            >>> data = JSONFileOperations.load_json(Path("config.json"), validator=validator)
        """
        if not file_path.exists():
            if default is not None:
                logger.debug(f"File not found, using default: {file_path}")
                return default
            raise FileOperationError(
                operation="read",
                file_path=str(file_path),
                details="File does not exist",
            )

        try:
            with open(file_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            raise FileOperationError(
                operation="parse",
                file_path=str(file_path),
                details=f"Invalid JSON: {e}",
                cause=e,
            ) from e
        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(file_path),
                details=str(e),
                cause=e,
            ) from e
        except Exception as e:
            raise SystemError(
                message=f"Unexpected error reading {file_path}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={"file_path": str(file_path), "operation": "read"},
                cause=e,
            ) from e

        if validator and not validator(data):
            raise FileOperationError(
                operation="validate",
                file_path=str(file_path),
                details="Validation function returned False",
            )

        logger.debug(f"Loaded JSON from {file_path}")
        return data

    @staticmethod
    def save_json(
        file_path: Path,
        data: dict[str, Any],
        indent: int = 2,
        atomic: bool = True,
        create_dirs: bool = True,
    ) -> None:
        """
        Save data to JSON file with atomic write option

        Args:
            file_path: Path to JSON file
            data: Data to save
            indent: JSON indentation (default 2)
            atomic: Use atomic write via temp file (default True)
            create_dirs: Create parent directories if needed (default True)

        Raises:
            FileOperationError: If save fails

        Examples:
            >>> # Save with atomic write (default)
            >>> JSONFileOperations.save_json(Path("data.json"), {"key": "value"})
            >>> # Save without atomic write
            >>> JSONFileOperations.save_json(Path("data.json"), data, atomic=False)
            >>> # Save with custom indent
            >>> JSONFileOperations.save_json(Path("data.json"), data, indent=4)
        """
        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            if atomic:
                # Atomic write via temp file
                temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=indent, default=str)
                temp_path.replace(file_path)
            else:
                # Direct write
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=indent, default=str)

            logger.debug(f"Saved JSON to {file_path}")

        except OSError as e:
            raise FileOperationError(
                operation="write",
                file_path=str(file_path),
                details=str(e),
                cause=e,
            ) from e
        except Exception as e:
            raise SystemError(
                message=f"Unexpected error saving to {file_path}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={
                    "file_path": str(file_path),
                    "operation": "write",
                    "atomic": atomic,
                },
                cause=e,
            ) from e

    @staticmethod
    def load_json_safe(file_path: Path, default: dict[str, Any]) -> dict[str, Any]:
        """
        Load JSON with guaranteed return (never raises)

        Logs errors but always returns a value.
        Convenience method for cases where failures should be silent.

        Args:
            file_path: Path to JSON file
            default: Default value to return if load fails

        Returns:
            Loaded JSON data or default value

        Examples:
            >>> # Always returns a dict, never raises
            >>> data = JSONFileOperations.load_json_safe(Path("config.json"), {})
        """
        try:
            return JSONFileOperations.load_json(file_path)
        except FileOperationError as e:
            logger.warning(f"Using default for {file_path}: {e}")
            return default


# Convenience functions for backward compatibility
def load_json(file_path: Path) -> dict[str, Any]:
    """Load JSON file

    Backward compatibility wrapper. Raises FileOperationError if file not found.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded JSON data

    Raises:
        FileOperationError: If file not found or JSON is invalid
    """
    return JSONFileOperations.load_json(file_path)


def save_json(file_path: Path, data: dict[str, Any], indent: int = 2) -> None:
    """Save data to JSON file with atomic write

    Backward compatibility wrapper.

    Args:
        file_path: Path to JSON file
        data: Data to save
        indent: JSON indentation (default 2)

    Raises:
        FileOperationError: If save fails
    """
    JSONFileOperations.save_json(file_path, data, indent=indent)


def ensure_directory(path: Path) -> None:
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)


def backup_file(file_path: Path) -> Path:
    """Create backup of a file

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file

    Raises:
        SolokitFileNotFoundError: If source file doesn't exist
        FileOperationError: If backup operation fails
    """
    if not file_path.exists():
        raise SolokitFileNotFoundError(file_path=str(file_path), file_type="backup source")

    try:
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        shutil.copy2(file_path, backup_path)
        return backup_path
    except OSError as e:
        raise FileOperationError(
            operation="backup",
            file_path=str(file_path),
            details=str(e),
            cause=e,
        ) from e


def read_file(file_path: Path) -> str:
    """Read file contents

    Args:
        file_path: Path to file to read

    Returns:
        File contents as string

    Raises:
        SolokitFileNotFoundError: If file doesn't exist
        FileOperationError: If read operation fails
    """
    if not file_path.exists():
        raise SolokitFileNotFoundError(file_path=str(file_path), file_type="text file")

    try:
        with open(file_path) as f:
            return f.read()
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(file_path),
            details=str(e),
            cause=e,
        ) from e


def write_file(file_path: Path, content: str) -> None:
    """Write content to file

    Args:
        file_path: Path to file to write
        content: Content to write

    Raises:
        FileOperationError: If write operation fails
    """
    try:
        with open(file_path, "w") as f:
            f.write(content)
    except OSError as e:
        raise FileOperationError(
            operation="write",
            file_path=str(file_path),
            details=str(e),
            cause=e,
        ) from e
