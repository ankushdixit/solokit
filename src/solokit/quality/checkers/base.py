#!/usr/bin/env python3
"""
Base classes for quality checkers.

Defines the abstract interface for all quality checkers and the result structure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    """Result from a quality check execution.

    Attributes:
        checker_name: Name of the checker that produced this result
        passed: Whether the check passed overall
        status: Status string (e.g., "passed", "failed", "skipped")
        errors: List of error messages or error dictionaries
        warnings: List of warning messages or warning dictionaries
        info: Additional information about the check execution
        execution_time: Time taken to run the check in seconds
    """

    checker_name: str
    passed: bool
    status: str
    errors: list[dict[str, Any] | str] = field(default_factory=list)
    warnings: list[dict[str, Any] | str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    @property
    def details(self) -> dict[str, Any]:
        """Return check result as details dict for backward compatibility.

        Returns:
            Dict containing status, passed, and info merged together
        """
        result_dict: dict[str, Any] = {"status": self.status, "passed": self.passed}
        result_dict.update(self.info)
        if self.errors:
            result_dict["errors"] = self.errors
        if self.warnings:
            result_dict["warnings"] = self.warnings
        return result_dict


class QualityChecker(ABC):
    """Abstract base class for quality checkers.

    All quality checkers must inherit from this class and implement
    the abstract methods. This provides a consistent interface for
    the orchestrator to execute different types of quality checks.
    """

    def __init__(self, config: dict[str, Any], project_root: Path | None = None):
        """Initialize the quality checker.

        Args:
            config: Configuration dictionary for this checker
            project_root: Root directory of the project (defaults to current directory)
        """
        self.config = config
        self.project_root = project_root or Path.cwd()

    @abstractmethod
    def name(self) -> str:
        """Return the name of this checker.

        Returns:
            A unique identifier for this checker (e.g., "bandit", "tests")
        """
        pass  # pragma: no cover

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if this checker is enabled in the configuration.

        Returns:
            True if the checker should run, False to skip
        """
        pass  # pragma: no cover

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute the quality check.

        Returns:
            CheckResult containing the outcome of the check
        """
        pass  # pragma: no cover

    def _create_skipped_result(self, reason: str = "disabled") -> CheckResult:
        """Helper to create a skipped result.

        Args:
            reason: Reason why the check was skipped

        Returns:
            CheckResult marked as skipped
        """
        return CheckResult(
            checker_name=self.name(),
            passed=True,
            status="skipped",
            info={"reason": reason},
            execution_time=0.0,
        )
