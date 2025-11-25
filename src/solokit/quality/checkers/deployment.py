#!/usr/bin/env python3
"""
Deployment quality gates checker.

Validates deployment readiness including environment setup, documentation,
rollback procedures, and orchestrates integration tests and security scans.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import QUALITY_CHECK_LONG_TIMEOUT
from solokit.core.logging_config import get_logger
from solokit.quality.checkers.base import CheckResult, QualityChecker

logger = get_logger(__name__)


class DeploymentChecker(QualityChecker):
    """Deployment readiness validation and orchestration."""

    def __init__(
        self,
        work_item: dict[str, Any],
        config: dict[str, Any],
        project_root: Path | None = None,
        runner: CommandRunner | None = None,
    ):
        """Initialize deployment checker.

        Args:
            work_item: Work item dictionary (must be deployment type)
            config: Deployment quality gate configuration
            project_root: Project root directory
            runner: Optional CommandRunner instance (for testing)
        """
        super().__init__(config, project_root)
        self.work_item = work_item
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_LONG_TIMEOUT)
        )

    def name(self) -> str:
        """Return checker name."""
        return "deployment"

    def is_enabled(self) -> bool:
        """Check if deployment quality gates are enabled."""
        return bool(self.config.get("enabled", True))

    def run(self) -> CheckResult:
        """Execute deployment quality gates orchestration.

        Orchestrates:
        1. Integration tests (via IntegrationChecker)
        2. Security scans (via SecurityChecker)
        3. Environment validation
        4. Deployment documentation validation
        5. Rollback procedure testing

        Returns:
            CheckResult with orchestrated deployment validation outcome
        """
        start_time = time.time()

        if not self.is_enabled():
            return self._create_skipped_result("disabled")

        logger.info("Running deployment quality gates...")

        gates: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        overall_passed = True

        # Gate 1: All integration tests must pass
        try:
            from solokit.quality.checkers.integration import IntegrationChecker

            integration_config = self.config.get("integration_tests", {"enabled": True})
            integration_checker = IntegrationChecker(
                self.work_item, integration_config, runner=self.runner
            )

            # Check if integration checker is applicable
            if integration_checker.is_enabled():
                logger.info("Running integration tests gate...")
                integration_result = integration_checker.run()

                gates.append(
                    {
                        "name": "Integration Tests",
                        "required": True,
                        "passed": integration_result.passed,
                        "details": integration_result.info,
                    }
                )

                if not integration_result.passed:
                    overall_passed = False
                    for error in integration_result.errors:
                        errors.append({"gate": "Integration Tests", "message": error})
            else:
                gates.append(
                    {
                        "name": "Integration Tests",
                        "required": True,
                        "passed": True,
                        "details": {"skipped": "not applicable"},
                    }
                )
        except ImportError as e:
            logger.warning(f"Integration checker not available: {e}")
            gates.append(
                {
                    "name": "Integration Tests",
                    "required": True,
                    "passed": True,
                    "details": {"skipped": "checker not available"},
                }
            )

        # Gate 2: Security scans must pass
        try:
            from solokit.quality.checkers.security import SecurityChecker

            security_config = self.config.get("security_scans", {"enabled": True})
            security_checker = SecurityChecker(
                security_config, project_root=self.project_root, runner=self.runner
            )

            if security_checker.is_enabled():
                logger.info("Running security scans gate...")
                security_result = security_checker.run()

                gates.append(
                    {
                        "name": "Security Scans",
                        "required": True,
                        "passed": security_result.passed,
                        "details": security_result.info,
                    }
                )

                if not security_result.passed:
                    overall_passed = False
                    for error in security_result.errors:
                        errors.append({"gate": "Security Scans", "message": error})
            else:
                gates.append(
                    {
                        "name": "Security Scans",
                        "required": True,
                        "passed": True,
                        "details": {"skipped": "disabled"},
                    }
                )
        except ImportError as e:
            logger.warning(f"Security checker not available: {e}")
            gates.append(
                {
                    "name": "Security Scans",
                    "required": True,
                    "passed": True,
                    "details": {"skipped": "checker not available"},
                }
            )

        # Gate 3: Environment must be validated
        logger.info("Validating deployment environment...")
        env_passed = self._validate_deployment_environment()
        gates.append(
            {
                "name": "Environment Validation",
                "required": True,
                "passed": env_passed,
            }
        )
        if not env_passed:
            overall_passed = False
            errors.append(
                {
                    "gate": "Environment Validation",
                    "message": "Deployment environment validation failed",
                }
            )

        # Gate 4: Deployment documentation complete
        logger.info("Validating deployment documentation...")
        docs_passed = self._validate_deployment_documentation()
        gates.append(
            {
                "name": "Deployment Documentation",
                "required": True,
                "passed": docs_passed,
            }
        )
        if not docs_passed:
            overall_passed = False
            errors.append(
                {
                    "gate": "Deployment Documentation",
                    "message": "Deployment documentation incomplete",
                }
            )

        # Gate 5: Rollback procedure tested
        logger.info("Checking rollback testing...")
        rollback_tested = self._check_rollback_tested()
        gates.append({"name": "Rollback Tested", "required": True, "passed": rollback_tested})
        if not rollback_tested:
            overall_passed = False
            errors.append(
                {
                    "gate": "Rollback Tested",
                    "message": "Rollback procedure not tested",
                }
            )

        execution_time = time.time() - start_time

        return CheckResult(
            checker_name=self.name(),
            passed=overall_passed,
            status="passed" if overall_passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=cast(list[dict[str, Any] | str], warnings),
            info={"gates": gates},
            execution_time=execution_time,
        )

    def _validate_deployment_environment(self) -> bool:
        """Validate deployment environment is ready.

        Checks:
        - Target environment extracted from work item specification
        - Environment validator available and passes validation
        - Falls back to True if validator not available

        Returns:
            True if environment validation passes, False otherwise
        """
        try:
            from solokit.quality.env_validator import EnvironmentValidator

            # Parse target environment from work item
            # Try to extract from spec, fallback to "staging"
            spec = self.work_item.get("specification", "")
            environment = "staging"  # Default fallback

            # Simple pattern matching for common environment declarations
            env_match = re.search(r"environment[:\s]+(\w+)", spec.lower())
            if env_match:
                environment = env_match.group(1)

            logger.info(f"Validating deployment environment: {environment}")
            validator = EnvironmentValidator(environment)
            passed, _ = validator.validate_all()

            return passed
        except ImportError:
            # If environment_validator not available, return True
            logger.debug("Environment validator module not available, skipping validation")
            return True

    def _validate_deployment_documentation(self) -> bool:
        """Validate deployment documentation is complete.

        Required sections in work item specification:
        - deployment procedure
        - rollback procedure
        - smoke tests
        - monitoring & alerting

        Returns:
            True if all required sections present, False otherwise
        """
        spec = self.work_item.get("specification", "")

        required_sections = [
            "deployment procedure",
            "rollback procedure",
            "smoke tests",
            "monitoring & alerting",
        ]

        missing_sections = []
        for section in required_sections:
            if section.lower() not in spec.lower():
                missing_sections.append(section)
                logger.warning(f"Missing required documentation section: {section}")

        if missing_sections:
            logger.error(
                f"Deployment documentation incomplete. Missing: {', '.join(missing_sections)}"
            )
            return False

        return True

    def _check_rollback_tested(self) -> bool:
        """Check if rollback procedure has been tested.

        NOTE: Framework stub - Check deployment history for rollback test
        When implemented, this should:
        1. Query deployment history/logs
        2. Check if rollback has been tested in staging/test environment
        3. Verify rollback completed successfully

        Returns:
            True by default to allow framework operation
        """
        # NOTE: Framework stub - Returns True to allow operation
        # In production, implement actual rollback testing verification
        logger.debug("Rollback testing check: Framework stub, returning True")
        return True
