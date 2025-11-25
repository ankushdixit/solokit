#!/usr/bin/env python3
"""
Code linting checker.

Runs linters like ruff, flake8, eslint, etc.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import QUALITY_CHECK_VERY_LONG_TIMEOUT
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class LintingChecker(QualityChecker):
    """Code linting validation."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        language: str | None = None,
        auto_fix: bool | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize linting checker.

        Args:
            config: Linting configuration
            project_root: Project root directory
            language: Programming language (python, javascript, typescript)
            auto_fix: Whether to automatically fix issues (overrides config)
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_VERY_LONG_TIMEOUT)
        )
        self.language = language or self._detect_language()
        self.auto_fix = auto_fix if auto_fix is not None else self.config.get("auto_fix", False)

    def name(self) -> str:
        """Return checker name."""
        return "linting"

    def is_enabled(self) -> bool:
        """Check if linting is enabled."""
        return bool(self.config.get("enabled", True))

    def _detect_language(self) -> str:
        """Detect primary project language."""
        if (self.project_root / "pyproject.toml").exists() or (
            self.project_root / "setup.py"
        ).exists():
            return "python"
        elif (self.project_root / "package.json").exists():
            if (self.project_root / "tsconfig.json").exists():
                return "typescript"
            return "javascript"
        return "python"  # default

    def _is_solokit_project(self) -> bool:
        """Check if we're running on the solokit project itself."""
        # Solokit has a specific directory structure with src/solokit/
        solokit_marker = self.project_root / "src" / "solokit"
        return solokit_marker.exists() and solokit_marker.is_dir()

    def run(self) -> CheckResult:
        """Run linting checks."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        logger.info(f"Running linting for {self.language}")

        # Get linting command for language
        commands = self.config.get("commands", {})
        command = commands.get(self.language)
        if not command:
            logger.warning(f"No linting command configured for language: {self.language}")
            return self._create_skipped_result(reason=f"no command for {self.language}")

        # Add auto-fix flag if supported
        if self.auto_fix:
            if self.language == "python":
                command += " --fix"
            elif self.language in ["javascript", "typescript"]:
                command += " --fix"

        # For Python projects, use venv executables if available
        # Skip venv auto-detection for solokit itself (development tool)
        command_parts = command.split()
        if (
            self.language == "python"
            and command_parts[0] in ["ruff", "pylint", "flake8", "mypy", "pyright"]
            and not self._is_solokit_project()
        ):
            venv_bin = self.project_root / "venv" / "bin" / command_parts[0]
            venv_scripts = self.project_root / "venv" / "Scripts" / f"{command_parts[0]}.exe"

            if venv_bin.exists():
                command_parts[0] = str(venv_bin)
                logger.debug(f"Using venv executable: {venv_bin}")
            elif venv_scripts.exists():
                command_parts[0] = str(venv_scripts)
                logger.debug(f"Using venv executable: {venv_scripts}")

        # Run linter
        result = self.runner.run(command_parts, timeout=QUALITY_CHECK_VERY_LONG_TIMEOUT)

        execution_time = time.time() - start_time

        if result.timed_out:
            required = self.config.get("required", False)
            if required:
                return CheckResult(
                    checker_name=self.name(),
                    passed=False,
                    status="failed",
                    errors=[{"message": "Linting timed out"}],
                    warnings=[],
                    info={"reason": "timeout"},
                    execution_time=execution_time,
                )
            return CheckResult(
                checker_name=self.name(),
                passed=True,
                status="skipped",
                errors=[],
                warnings=[],
                info={"reason": "timeout"},
                execution_time=execution_time,
            )

        # Tool not found
        if result.returncode == -1:
            required = self.config.get("required", False)
            if required:
                return CheckResult(
                    checker_name=self.name(),
                    passed=False,
                    status="failed",
                    errors=[{"message": "Required linting tool not found"}],
                    warnings=[],
                    info={"reason": "tool not found"},
                    execution_time=execution_time,
                )
            return self._create_skipped_result(reason="linting tool not available")

        passed = result.returncode == 0

        errors = []
        if not passed:
            errors.append(
                {
                    "message": f"Linting found {result.returncode} issue(s)",
                    "output": result.stdout[:500] if result.stdout else "",
                }
            )

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info={
                "issues_found": result.returncode,
                "auto_fixed": self.auto_fix,
                "output": result.stdout[:1000] if result.stdout else "",
            },
            execution_time=execution_time,
        )
