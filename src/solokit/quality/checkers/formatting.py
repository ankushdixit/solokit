#!/usr/bin/env python3
"""
Code formatting checker.

Runs formatters like black, prettier, etc.
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


class FormattingChecker(QualityChecker):
    """Code formatting validation."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        language: str | None = None,
        auto_fix: bool | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize formatting checker.

        Args:
            config: Formatting configuration
            project_root: Project root directory
            language: Programming language (python, javascript, typescript)
            auto_fix: Whether to automatically format (overrides config)
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
        return "formatting"

    def is_enabled(self) -> bool:
        """Check if formatting is enabled."""
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
        """Run formatting checks."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        logger.info(f"Running formatting for {self.language}")

        # Get formatting command for language
        commands = self.config.get("commands", {})
        command = commands.get(self.language)
        if not command:
            logger.warning(f"No formatting command configured for language: {self.language}")
            return self._create_skipped_result(reason=f"no command for {self.language}")

        # Add appropriate flags based on auto_fix and language
        if self.language == "python":
            if not self.auto_fix:
                command += " --check"
        elif self.language in ["javascript", "typescript"]:
            if self.auto_fix:
                command += " --write"
            else:
                command += " --check"

        # For Python projects, use venv executables if available
        # Skip venv auto-detection for solokit itself (development tool)
        command_parts = command.split()
        if (
            self.language == "python"
            and command_parts[0] in ["ruff", "black", "autopep8", "yapf"]
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

        # Run formatter
        result = self.runner.run(command_parts, timeout=QUALITY_CHECK_VERY_LONG_TIMEOUT)

        execution_time = time.time() - start_time

        if result.timed_out:
            required = self.config.get("required", False)
            if required:
                return CheckResult(
                    checker_name=self.name(),
                    passed=False,
                    status="failed",
                    errors=[{"message": "Formatting timed out"}],
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
                    errors=[{"message": "Required formatting tool not found"}],
                    warnings=[],
                    info={"reason": "tool not found"},
                    execution_time=execution_time,
                )
            return self._create_skipped_result(reason="formatting tool not available")

        passed = result.returncode == 0

        errors = []
        if not passed:
            errors.append(
                {
                    "message": "Code formatting issues found",
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
                "formatted": self.auto_fix,
                "output": result.stdout[:1000] if result.stdout else "",
            },
            execution_time=execution_time,
        )
