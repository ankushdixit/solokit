#!/usr/bin/env python3
"""
Test execution and coverage checker.

Runs tests using pytest, Jest, or other test frameworks and validates coverage.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import TEST_RUNNER_TIMEOUT
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class ExecutionChecker(QualityChecker):
    """Test execution and coverage validation."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        language: str | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize test runner.

        Args:
            config: Test execution configuration
            project_root: Project root directory
            language: Programming language (python, javascript, typescript)
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner if runner is not None else CommandRunner(default_timeout=TEST_RUNNER_TIMEOUT)
        )
        self.language = language or self._detect_language()

    def name(self) -> str:
        """Return checker name."""
        return "tests"

    def is_enabled(self) -> bool:
        """Check if test execution is enabled."""
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
        """Run test suite with coverage."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        logger.info(f"Running tests for {self.language}")

        # Get test command for language
        commands = self.config.get("commands", {})
        command = commands.get(self.language)
        if not command:
            logger.warning(f"No test command configured for language: {self.language}")
            return self._create_skipped_result(reason=f"no command for {self.language}")

        # For Python projects, use venv pytest if available
        # Skip venv auto-detection for solokit itself (development tool)
        command_parts = command.split()
        if (
            self.language == "python"
            and command_parts[0] in ["pytest", "python", "python3"]
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

        # Run tests
        result = self.runner.run(command_parts, timeout=TEST_RUNNER_TIMEOUT)

        # pytest exit codes:
        # 0 = all tests passed
        # 1 = tests were collected and run but some failed
        # 2 = test execution was interrupted
        # 3 = internal error
        # 4 = pytest command line usage error
        # 5 = no tests were collected

        if result.timed_out:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=[{"message": "Test execution timed out"}],
                warnings=[],
                info={"reason": "timeout"},
                execution_time=execution_time,
            )

        # Command not found (test tool not available)
        if result.returncode == -1 and "not found" in result.stderr.lower():
            return self._create_skipped_result(reason=f"{command.split()[0]} not available")

        # Treat "no tests collected" (exit code 5) as skipped, not failed
        if result.returncode == 5:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=True,
                status="skipped",
                errors=[],
                warnings=[],
                info={"reason": "no tests collected", "returncode": result.returncode},
                execution_time=execution_time,
            )

        # Parse coverage
        coverage = self._parse_coverage()
        passed = result.returncode == 0

        # Check coverage threshold
        threshold = self.config.get("coverage_threshold", 80)
        if coverage is not None and coverage < threshold:
            passed = False

        execution_time = time.time() - start_time

        errors = []
        if result.returncode != 0:
            errors.append(
                {
                    "message": f"Tests failed with exit code {result.returncode}",
                    "output": (result.stderr[:500] if result.stderr else ""),  # Limit output
                }
            )

        if coverage is not None and coverage < threshold:
            errors.append({"message": f"Coverage {coverage}% below threshold {threshold}%"})

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info={
                "coverage": coverage,
                "threshold": threshold,
                "returncode": result.returncode,
                "output": result.stdout[:1000] if result.stdout else "",  # Limit output
            },
            execution_time=execution_time,
        )

    def _parse_coverage(self) -> float | None:
        """Parse coverage from test results."""
        try:
            if self.language == "python":
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                    return data.get("totals", {}).get("percent_covered", 0)  # type: ignore[no-any-return]

            elif self.language in ["javascript", "typescript"]:
                coverage_file = self.project_root / "coverage" / "coverage-summary.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        data = json.load(f)
                    return data.get("total", {}).get("lines", {}).get("pct", 0)  # type: ignore[no-any-return]

            return None
        except OSError as e:
            logger.debug(f"Failed to read coverage file: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse coverage file: {e}")
            return None
