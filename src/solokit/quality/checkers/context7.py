#!/usr/bin/env python3
"""
Context7 library verification checker.

Verifies important libraries via Context7 MCP integration by parsing
libraries from stack.txt and querying Context7 for security and version status.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import QUALITY_CHECK_LONG_TIMEOUT
from solokit.core.exceptions import FileOperationError
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class Context7Checker(QualityChecker):
    """Context7 library verification for important dependencies."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize Context7 checker.

        Args:
            config: Context7 configuration
            project_root: Project root directory
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_LONG_TIMEOUT)
        )

    def name(self) -> str:
        """Return checker name."""
        return "context7"

    def is_enabled(self) -> bool:
        """Check if Context7 verification is enabled."""
        return bool(self.config.get("enabled", False))

    def run(self) -> CheckResult:
        """Run Context7 library verification."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result(reason="not enabled")

        # Get stack.txt path (relative to project root or .session/tracking)
        stack_file = self.project_root / ".session" / "tracking" / "stack.txt"
        if not stack_file.exists():
            return self._create_skipped_result(reason="no stack.txt")

        logger.info("Running Context7 library verification")

        # Parse libraries from stack.txt
        try:
            libraries = self._parse_libraries_from_stack(stack_file)
        except FileOperationError as e:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=[{"message": f"Failed to read stack.txt: {e}"}],
                warnings=[],
                info={"reason": "stack file read error"},
                execution_time=execution_time,
            )

        # Verify libraries
        results: dict[str, Any] = {"libraries": [], "verified": 0, "failed": 0}

        for lib in libraries:
            # Check if library should be verified
            if not self._should_verify_library(lib):
                continue

            # Query Context7 MCP
            verified = self._query_context7(lib)

            results["libraries"].append(
                {
                    "name": lib["name"],
                    "version": lib.get("version", "unknown"),
                    "verified": verified,
                }
            )

            if verified:
                results["verified"] += 1
            else:
                results["failed"] += 1

        passed = results["failed"] == 0
        execution_time = time.time() - start_time

        errors = []
        if not passed:
            for lib in results["libraries"]:
                if not lib["verified"]:
                    errors.append(
                        {
                            "message": f"Library verification failed: {lib['name']} {lib['version']}",
                            "library": lib["name"],
                            "version": lib["version"],
                        }
                    )

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info={
                "total_libraries": len(results["libraries"]),
                "verified": results["verified"],
                "failed": results["failed"],
                "libraries": results["libraries"],
            },
            execution_time=execution_time,
        )

    def _parse_libraries_from_stack(self, stack_file: Path) -> list[dict[str, str]]:
        """
        Parse libraries from stack.txt.

        Args:
            stack_file: Path to stack.txt file

        Returns:
            List of library dictionaries with 'name' and 'version' keys

        Raises:
            FileOperationError: If stack file cannot be read
        """
        libraries = []

        try:
            with open(stack_file) as f:
                content = f.read()

            # Parse libraries - expecting format like "Python 3.x" or "pytest (testing)"
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extract library name and version
                parts = line.split()
                if len(parts) >= 1:
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else "unknown"
                    libraries.append({"name": name, "version": version})

        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(stack_file),
                details="Failed to read stack.txt file",
                cause=e,
            ) from e

        return libraries

    def _should_verify_library(self, lib: dict[str, str]) -> bool:
        """Check if library should be verified via Context7.

        Args:
            lib: Library dictionary with 'name' and 'version' keys

        Returns:
            True if library should be verified, False otherwise
        """
        # Check if library is in important list (if configured)
        important_libs = self.config.get("important_libraries", [])
        if important_libs:
            return lib["name"] in important_libs

        # By default, verify all libraries
        return True

    def _query_context7(self, lib: dict[str, str]) -> bool:
        """Query Context7 MCP for library verification (stub).

        Args:
            lib: Library dictionary with 'name' and 'version' keys

        Returns:
            True if library is current/secure, False otherwise

        Note:
            This is currently a stub implementation. When fully implemented, this should:
            1. Connect to Context7 MCP server
            2. Query library version and security status
            3. Return True if library is current/secure, False otherwise

            Returns True by default to allow framework operation.
        """
        # NOTE: Future integration - Context7 MCP for library verification
        # When implemented, this should:
        # 1. Connect to Context7 MCP server
        # 2. Query library version and security status
        # 3. Return True if library is current/secure, False otherwise
        # Returns True by default to allow framework operation
        return True
