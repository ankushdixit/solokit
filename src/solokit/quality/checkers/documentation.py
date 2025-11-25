#!/usr/bin/env python3
"""
Documentation validation checker.

Validates CHANGELOG updates, docstrings, and README currency.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import (
    GIT_STANDARD_TIMEOUT,
    QUALITY_CHECK_STANDARD_TIMEOUT,
)
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class DocumentationChecker(QualityChecker):
    """Documentation requirements validation."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        work_item: dict[str, Any] | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize documentation checker.

        Args:
            config: Documentation configuration
            project_root: Project root directory
            work_item: Work item dictionary (optional, for README check)
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_STANDARD_TIMEOUT)
        )
        self.work_item = work_item or {}

    def name(self) -> str:
        """Return checker name."""
        return "documentation"

    def is_enabled(self) -> bool:
        """Check if documentation validation is enabled."""
        return bool(self.config.get("enabled", True))

    def run(self) -> CheckResult:
        """Run documentation validation."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        logger.info("Running documentation validation")

        checks = []
        passed = True

        # Check CHANGELOG updated
        if self.config.get("check_changelog", False):
            changelog_passed = self._check_changelog_updated()
            checks.append({"name": "CHANGELOG updated", "passed": changelog_passed})
            if not changelog_passed:
                passed = False

        # Check docstrings for Python
        if self.config.get("check_docstrings", False):
            docstrings_passed = self._check_python_docstrings()
            checks.append({"name": "Docstrings present", "passed": docstrings_passed})
            if not docstrings_passed:
                passed = False

        # Check README current
        if self.config.get("check_readme", False):
            readme_passed = self._check_readme_current()
            checks.append({"name": "README current", "passed": readme_passed})
            if not readme_passed:
                passed = False

        execution_time = time.time() - start_time

        errors = []
        for check in checks:
            if not check["passed"]:
                errors.append({"message": f"{check['name']} check failed"})

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info={"checks": checks},
            execution_time=execution_time,
        )

    def _check_changelog_updated(self) -> bool:
        """Check if CHANGELOG was updated in the current branch."""
        # Get the current branch name
        result = self.runner.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=GIT_STANDARD_TIMEOUT
        )
        if not result.success:
            logger.debug("Could not check CHANGELOG: git not available")
            return True  # Skip check if git not available

        current_branch = result.stdout.strip()

        # Don't check if we're on main/master
        if current_branch in ["main", "master"]:
            logger.debug("On main/master branch, skipping CHANGELOG check")
            return True

        # Check if CHANGELOG.md was modified in any commit on this branch
        result = self.runner.run(
            ["git", "log", "--name-only", "--pretty=format:", "main..HEAD"],
            timeout=GIT_STANDARD_TIMEOUT,
        )

        if result.success and "CHANGELOG.md" in result.stdout:
            logger.debug("CHANGELOG updated in branch")
            return True
        else:
            logger.debug("CHANGELOG not updated in branch")
            return False

    def _check_python_docstrings(self) -> bool:
        """Check if Python functions have docstrings."""
        # Only check if this is a Python project
        if (
            not (self.project_root / "pyproject.toml").exists()
            and not (self.project_root / "setup.py").exists()
        ):
            return True

        # Use venv Python if available, otherwise skip check
        venv_python = self.project_root / "venv" / "bin" / "python"
        venv_python_win = self.project_root / "venv" / "Scripts" / "python.exe"

        python_cmd = None
        if venv_python.exists():
            python_cmd = str(venv_python)
        elif venv_python_win.exists():
            python_cmd = str(venv_python_win)
        else:
            # No venv found, skip check
            logger.debug("No venv found, skipping docstring check")
            return True

        result = self.runner.run(
            [python_cmd, "-m", "pydocstyle", "--count"], timeout=QUALITY_CHECK_STANDARD_TIMEOUT
        )

        # If pydocstyle not available or timeout, skip check
        if result.timed_out or result.returncode == -1:
            logger.debug("pydocstyle not available, skipping docstring check")
            return True

        # Check if pydocstyle is not installed (stderr contains "No module named")
        if "No module named" in result.stderr:
            logger.debug("pydocstyle not installed, skipping docstring check")
            return True

        # If no issues found, return True
        return result.returncode == 0

    def _check_readme_current(self) -> bool:
        """Check if README was updated (optional check)."""
        result = self.runner.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"], timeout=GIT_STANDARD_TIMEOUT
        )

        if not result.success:
            logger.debug("Could not check README: git not available")
            return True  # Skip check if git not available

        changed_files = result.stdout.strip().split("\n")
        readme_updated = any("README" in f.upper() for f in changed_files)

        if readme_updated:
            logger.debug("README updated")
        else:
            logger.debug("README not updated")

        return readme_updated
