#!/usr/bin/env python3
"""
Specification completeness checker.

Validates that work item specification files are complete and properly formatted.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.exceptions import SpecValidationError
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker
from solokit.work_items.spec_validator import validate_spec_file

logger = get_logger(__name__)


class SpecCompletenessChecker(QualityChecker):
    """Specification file completeness validation."""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        work_item: dict[str, Any] | None = None,
    ):
        """Initialize spec completeness checker.

        Args:
            config: Spec completeness configuration
            project_root: Project root directory
            work_item: Work item dictionary with 'id' and 'type' fields
        """
        super().__init__(config, project_root)
        self.work_item = work_item or {}

    def name(self) -> str:
        """Return checker name."""
        return "spec_completeness"

    def is_enabled(self) -> bool:
        """Check if spec completeness validation is enabled."""
        return bool(self.config.get("enabled", True))

    def run(self) -> CheckResult:
        """Run spec completeness validation."""
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result()

        work_item_id = self.work_item.get("id")
        work_item_type = self.work_item.get("type")

        if not work_item_id or not work_item_type:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=[{"message": "Work item missing 'id' or 'type' field"}],
                warnings=[],
                info={},
                execution_time=execution_time,
            )

        logger.info(f"Validating spec file for work item: {work_item_id}")

        # Validate spec file
        try:
            validate_spec_file(work_item_id, work_item_type)
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=True,
                status="passed",
                errors=[],
                warnings=[],
                info={"message": f"Spec file for '{work_item_id}' is complete"},
                execution_time=execution_time,
            )
        except SpecValidationError as e:
            execution_time = time.time() - start_time
            validation_errors = e.context.get("validation_errors", [])
            errors = [{"message": error} for error in validation_errors]
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=cast(list[dict[str, Any] | str], errors),
                warnings=[],
                info={
                    "message": f"Spec file for '{work_item_id}' is incomplete",
                    "suggestion": e.remediation
                    or f"Edit .session/specs/{work_item_id}.md to add missing sections",
                },
                execution_time=execution_time,
            )
        except SolokitFileNotFoundError as e:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=[{"message": e.message}],
                warnings=[],
                info={"suggestion": e.remediation},
                execution_time=execution_time,
            )
        except (OSError, ValueError) as e:
            execution_time = time.time() - start_time
            return CheckResult(
                checker_name=self.name(),
                passed=False,
                status="failed",
                errors=[{"message": f"Error validating spec file: {str(e)}"}],
                warnings=[],
                info={"suggestion": "Check spec file format and validator configuration"},
                execution_time=execution_time,
            )
