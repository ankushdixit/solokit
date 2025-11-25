#!/usr/bin/env python3
"""
Custom validation checker.

Runs user-defined validation rules.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import QUALITY_CHECK_LONG_TIMEOUT, QUALITY_CHECK_STANDARD_TIMEOUT
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class CustomValidationChecker(QualityChecker):
    """Custom validation rules execution."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        work_item: dict[str, Any] | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize custom validation checker.

        Args:
            config: Custom validations configuration
            project_root: Project root directory
            work_item: Work item dictionary (for work-item-specific rules)
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_LONG_TIMEOUT)
        )
        self.work_item = work_item or {}

    def name(self) -> str:
        """Return checker name."""
        return "custom_validations"

    def is_enabled(self) -> bool:
        """Check if custom validations are enabled."""
        # Custom validations are enabled if there are any rules defined
        work_item_rules = self.work_item.get("validation_rules", [])
        project_rules = self.config.get("rules", [])
        return len(work_item_rules) > 0 or len(project_rules) > 0

    def run(self) -> CheckResult:
        """Run custom validation rules."""
        start_time = time.time()

        # Get rules from both work item and project config
        work_item_rules = self.work_item.get("validation_rules", [])
        project_rules = self.config.get("rules", [])
        all_rules = work_item_rules + project_rules

        if not all_rules:
            return self._create_skipped_result(reason="no custom rules defined")

        logger.info(f"Running {len(all_rules)} custom validation rules")

        validations = []
        passed = True

        for rule in all_rules:
            rule_type = rule.get("type")
            required = rule.get("required", False)

            # Execute rule based on type
            if rule_type == "command":
                rule_passed = self._run_command_validation(rule)
            elif rule_type == "file_exists":
                rule_passed = self._check_file_exists(rule)
            elif rule_type == "grep":
                rule_passed = self._run_grep_validation(rule)
            else:
                logger.warning(f"Unknown validation rule type: {rule_type}")
                rule_passed = True

            validations.append(
                {
                    "name": rule.get("name", "unknown"),
                    "passed": rule_passed,
                    "required": required,
                    "type": rule_type,
                }
            )

            if not rule_passed and required:
                passed = False

        execution_time = time.time() - start_time

        errors = []
        for validation in validations:
            if not validation["passed"] and validation["required"]:
                errors.append({"message": f"Required validation failed: {validation['name']}"})

        warnings = []
        for validation in validations:
            if not validation["passed"] and not validation["required"]:
                warnings.append({"message": f"Optional validation failed: {validation['name']}"})

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=cast(list[dict[str, Any] | str], warnings),
            info={"validations": validations},
            execution_time=execution_time,
        )

    def _run_command_validation(self, rule: dict[str, Any]) -> bool:
        """Run command validation rule."""
        command = rule.get("command")
        if not command:
            logger.warning("Command validation missing 'command' field")
            return True

        logger.debug(f"Running command validation: {command}")
        result = self.runner.run(command.split(), timeout=QUALITY_CHECK_LONG_TIMEOUT)
        return result.success

    def _check_file_exists(self, rule: dict[str, Any]) -> bool:
        """Check if file exists at path."""
        file_path = rule.get("path")
        if not file_path:
            logger.warning("File exists validation missing 'path' field")
            return True

        path = self.project_root / file_path
        exists = path.exists()
        logger.debug(f"Checking file exists: {file_path} -> {exists}")
        return bool(exists)

    def _run_grep_validation(self, rule: dict[str, Any]) -> bool:
        """Run grep validation rule."""
        pattern = rule.get("pattern")
        files = rule.get("files", ".")

        if not pattern:
            logger.warning("Grep validation missing 'pattern' field")
            return True

        logger.debug(f"Running grep validation: pattern={pattern}, files={files}")
        result = self.runner.run(
            ["grep", "-r", pattern, files], timeout=QUALITY_CHECK_STANDARD_TIMEOUT
        )
        # grep returns 0 if pattern found
        return result.success
