#!/usr/bin/env python3
"""
Integration test validation checker.

Validates integration test environment, documentation, and execution.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, cast

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import DOCKER_COMMAND_TIMEOUT, QUALITY_CHECK_STANDARD_TIMEOUT
from solokit.core.exceptions import CommandExecutionError
from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
from solokit.core.logging_config import get_logger
from solokit.core.types import WorkItemType
from solokit.quality.checkers.base import CheckResult, QualityChecker
from solokit.quality.scaffolding import has_integration_test_files
from solokit.work_items import spec_parser

logger = get_logger(__name__)


class IntegrationChecker(QualityChecker):
    """Integration test requirements validation."""

    def __init__(
        self,
        work_item: dict[str, Any],
        config: dict[str, Any],
        runner: CommandRunner | None = None,
        config_path: Path | None = None,
    ):
        """Initialize integration checker.

        Args:
            work_item: Work item dictionary (must be integration_test type)
            config: Integration test configuration
            runner: Optional CommandRunner instance (for testing)
            config_path: Path to full config file (for loading documentation settings)
        """
        super().__init__(config)
        self.work_item = work_item
        self.runner = (
            runner
            if runner is not None
            else CommandRunner(default_timeout=QUALITY_CHECK_STANDARD_TIMEOUT)
        )
        self.config_path = config_path if config_path is not None else Path(".session/config.json")

    def name(self) -> str:
        """Return checker name."""
        return "integration"

    def is_enabled(self) -> bool:
        """Check if integration validation is enabled."""
        return bool(self.config.get("enabled", True))

    def run(self) -> CheckResult:
        """Execute integration test validation (full orchestration).

        Returns:
            CheckResult with orchestrated validation outcome
        """
        start_time = time.time()

        # Only run for integration_test work items
        if self.work_item.get("type") != WorkItemType.INTEGRATION_TEST.value:
            return self._create_skipped_result("not integration test")

        if not self.is_enabled():
            return self._create_skipped_result("disabled")

        # Skip if no integration test files exist (minimal scaffolding case)
        if not has_integration_test_files():
            logger.info("No integration test files found - skipping integration tests")
            return self._create_skipped_result("no integration test files found")

        logger.info("Running integration test quality gates...")

        results: dict[str, Any] = {
            "integration_tests": {},
            "performance_benchmarks": {},
            "api_contracts": {},
        }

        errors = []
        warnings = []

        # Import here to avoid circular imports
        from solokit.core.exceptions import (
            EnvironmentSetupError,
            IntegrationExecutionError,
            IntegrationTestError,
        )
        from solokit.testing.integration_runner import IntegrationTestRunner

        runner_instance = IntegrationTestRunner(self.work_item)

        try:
            # Setup environment (now raises exceptions instead of returning tuple)
            runner_instance.setup_environment()

            # Execute integration tests (now returns dict and raises exceptions on failure)
            test_results = runner_instance.run_tests()
            results["integration_tests"] = test_results

            # Check if tests passed
            if test_results.get("failed", 0) > 0:
                logger.error("Integration tests failed")
                errors.append(
                    {"message": f"{test_results.get('failed', 0)} integration tests failed"}
                )

            logger.info(f"Integration tests passed ({test_results.get('passed', 0)} tests)")

            # 2. Run performance benchmarks
            if self.work_item.get("performance_benchmarks"):
                from solokit.testing.performance import PerformanceBenchmark

                benchmark = PerformanceBenchmark(self.work_item)
                benchmarks_passed, benchmark_results = benchmark.run_benchmarks()
                results["performance_benchmarks"] = benchmark_results

                if not benchmarks_passed:
                    logger.error("Performance benchmarks failed")
                    if self.config.get("performance_benchmarks", {}).get("required", True):
                        errors.append({"message": "Performance benchmarks failed"})
                    else:
                        warnings.append({"message": "Performance benchmarks failed (optional)"})
                else:
                    logger.info("Performance benchmarks passed")

            # 3. Validate API contracts
            if self.work_item.get("api_contracts"):
                from solokit.quality.api_validator import APIContractValidator

                validator = APIContractValidator(self.work_item)
                contracts_passed, contract_results = validator.validate_contracts()
                results["api_contracts"] = contract_results

                if not contracts_passed:
                    logger.error("API contract validation failed")
                    if self.config.get("api_contracts", {}).get("required", True):
                        errors.append({"message": "API contract validation failed"})
                    else:
                        warnings.append({"message": "API contract validation failed (optional)"})
                else:
                    logger.info("API contracts validated")

        except SolokitFileNotFoundError as e:
            # Spec file not found - skip gracefully for minimal scaffolding
            logger.info(f"Spec file not found, skipping integration tests: {e}")
            file_path = (
                e.context.get("file_path", "unknown") if hasattr(e, "context") else "unknown"
            )
            return self._create_skipped_result(f"spec file not found: {file_path}")

        except (
            EnvironmentSetupError,
            IntegrationExecutionError,
            IntegrationTestError,
        ) as e:
            # Integration test setup or execution failed
            logger.error(f"Integration test error: {e}")
            errors.append({"message": str(e)})

        finally:
            # Always teardown environment
            try:
                runner_instance.teardown_environment()
            except (OSError, CommandExecutionError) as e:
                # Log teardown failures but don't fail the gate
                logger.warning(f"Environment teardown failed: {e}")
                warnings.append({"message": f"Environment teardown failed: {e}"})

        execution_time = time.time() - start_time
        passed = len(errors) == 0

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=cast(list[dict[str, Any] | str], warnings),
            info=results,
            execution_time=execution_time,
        )

    def validate_environment(self) -> CheckResult:
        """Validate integration test environment requirements.

        Returns:
            CheckResult with environment validation outcome
        """
        start_time = time.time()

        if self.work_item.get("type") != WorkItemType.INTEGRATION_TEST.value:
            return self._create_skipped_result("not integration test")

        env_requirements = self.work_item.get("environment_requirements", {})
        results: dict[str, Any] = {
            "docker_available": False,
            "docker_compose_available": False,
            "required_services": [],
            "missing_config": [],
        }

        errors = []

        # Check Docker available
        result = self.runner.run(["docker", "--version"], timeout=DOCKER_COMMAND_TIMEOUT)
        results["docker_available"] = result.success

        if not result.success:
            errors.append({"message": "Docker not available"})

        # Check Docker Compose available
        result = self.runner.run(["docker-compose", "--version"], timeout=DOCKER_COMMAND_TIMEOUT)
        results["docker_compose_available"] = result.success

        if not result.success:
            errors.append({"message": "Docker Compose not available"})

        # Check compose file exists
        compose_file = env_requirements.get("compose_file", "docker-compose.integration.yml")
        if not Path(compose_file).exists():
            results["missing_config"].append(compose_file)
            errors.append({"message": f"Missing compose file: {compose_file}"})

        # Check config files exist
        config_files = env_requirements.get("config_files", [])
        for config_file in config_files:
            if not Path(config_file).exists():
                results["missing_config"].append(config_file)
                errors.append({"message": f"Missing config file: {config_file}"})

        execution_time = time.time() - start_time
        passed = (
            results["docker_available"]
            and results["docker_compose_available"]
            and len(results["missing_config"]) == 0
        )

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info=results,
            execution_time=execution_time,
        )

    def validate_documentation(self) -> CheckResult:
        """Validate integration test documentation requirements.

        Returns:
            CheckResult with documentation validation outcome
        """
        start_time = time.time()

        if self.work_item.get("type") != WorkItemType.INTEGRATION_TEST.value:
            return self._create_skipped_result("not integration test")

        # Get integration documentation config
        full_config: dict[str, Any] = {}
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    full_config = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.debug(f"Failed to load config: {e}")

        config = full_config.get("integration_tests", {}).get("documentation", {})
        if not config.get("enabled", True):
            return self._create_skipped_result("documentation validation disabled")

        results: dict[str, Any] = {"checks": [], "missing": []}

        # 1. Check for integration architecture diagram
        if config.get("architecture_diagrams", True):
            diagram_paths = [
                "docs/architecture/integration-architecture.md",
                "docs/integration-architecture.md",
                ".session/specs/integration-architecture.md",
            ]

            diagram_found = any(Path(p).exists() for p in diagram_paths)
            results["checks"].append(
                {"name": "Integration architecture diagram", "passed": diagram_found}
            )

            if not diagram_found:
                results["missing"].append("Integration architecture diagram")

        # 2. Check for sequence diagrams (using spec_parser)
        if config.get("sequence_diagrams", True):
            # Parse spec file to get test scenarios
            try:
                parsed_spec = spec_parser.parse_spec_file(self.work_item)
                scenarios = parsed_spec.get("test_scenarios", [])
            except (OSError, ValueError, KeyError) as e:
                logger.debug(f"Failed to parse spec file for scenarios: {e}")
                scenarios = []

            if scenarios:
                # Check if any scenario content contains sequence diagrams
                has_sequence = False
                for scenario in scenarios:
                    content = scenario.get("content", "")
                    if "```mermaid" in content or "sequenceDiagram" in content:
                        has_sequence = True
                        break

                results["checks"].append({"name": "Sequence diagrams", "passed": has_sequence})

                if not has_sequence:
                    results["missing"].append("Sequence diagrams for test scenarios")

        # 3. Check for API contract documentation (using spec_parser)
        if config.get("contract_documentation", True):
            # Parse spec file to get API contracts
            try:
                parsed_spec = spec_parser.parse_spec_file(self.work_item)
                api_contracts = parsed_spec.get("api_contracts", "")
                # API contracts should be documented in the spec
                has_contracts = api_contracts and len(api_contracts.strip()) > 20
            except (OSError, ValueError, KeyError) as e:
                logger.debug(f"Failed to parse spec file for API contracts: {e}")
                has_contracts = False

            results["checks"].append(
                {
                    "name": "API contracts documented",
                    "passed": has_contracts,
                }
            )

            if not has_contracts:
                results["missing"].append("API contract documentation")

        # 4. Check for performance baseline documentation (using spec_parser)
        if config.get("performance_baseline_docs", True):
            # Parse spec file to get performance benchmarks
            try:
                parsed_spec = spec_parser.parse_spec_file(self.work_item)
                benchmarks = parsed_spec.get("performance_benchmarks", "")
                has_benchmarks = benchmarks and len(benchmarks.strip()) > 20
            except (OSError, ValueError, KeyError) as e:
                logger.debug(f"Failed to parse spec file for performance benchmarks: {e}")
                has_benchmarks = False

            if has_benchmarks:
                baseline_file = Path(".session/tracking/performance_baselines.json")
                baseline_exists = baseline_file.exists()

                results["checks"].append(
                    {
                        "name": "Performance baseline documented",
                        "passed": baseline_exists,
                    }
                )

                if not baseline_exists:
                    results["missing"].append("Performance baseline documentation")

        # 5. Check for integration point documentation (using spec_parser)
        try:
            parsed_spec = spec_parser.parse_spec_file(self.work_item.get("id"))
            scope = parsed_spec.get("scope", "")
            # Check if scope has meaningful content
            documented = scope and len(scope.strip()) > 20
        except (OSError, ValueError, KeyError) as e:
            logger.debug(f"Failed to parse spec file for integration points: {e}")
            documented = False

        results["checks"].append({"name": "Integration points documented", "passed": documented})

        if not documented:
            results["missing"].append("Integration points documentation")

        # Determine overall pass/fail
        passed_checks = sum(1 for check in results["checks"] if check["passed"])
        total_checks = len(results["checks"])

        # Pass if all required checks pass
        passed = len(results["missing"]) == 0
        results["summary"] = f"{passed_checks}/{total_checks} documentation requirements met"

        execution_time = time.time() - start_time

        errors = []
        for missing in results["missing"]:
            errors.append({"message": f"Missing: {missing}"})

        return CheckResult(
            checker_name=self.name(),
            passed=passed,
            status="passed" if passed else "failed",
            errors=cast(list[dict[str, Any] | str], errors),
            warnings=[],
            info=results,
            execution_time=execution_time,
        )
