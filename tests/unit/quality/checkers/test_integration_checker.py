"""Unit tests for integration.py IntegrationChecker.

Tests for the IntegrationChecker class which validates integration test environment,
documentation, and execution.
"""

from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult, CommandRunner
from solokit.core.exceptions import (
    EnvironmentSetupError,
    IntegrationExecutionError,
    IntegrationTestError,
)
from solokit.core.types import WorkItemType
from solokit.quality.checkers.integration import IntegrationChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def integration_config():
    """Standard integration test config."""
    return {
        "enabled": True,
        "performance_benchmarks": {"required": True},
        "api_contracts": {"required": True},
    }


@pytest.fixture
def integration_work_item():
    """Standard integration test work item."""
    return {
        "id": "WI-001",
        "type": WorkItemType.INTEGRATION_TEST.value,
        "title": "Test Integration",
        "spec_file": ".session/specs/WI-001.md",
        "environment_requirements": {
            "compose_file": "docker-compose.integration.yml",
            "config_files": ["config/integration.json"],
        },
    }


@pytest.fixture
def feature_work_item():
    """Feature work item (not integration test)."""
    return {
        "id": "WI-002",
        "type": WorkItemType.FEATURE.value,
        "title": "Feature",
    }


class TestIntegrationCheckerInit:
    """Tests for IntegrationChecker initialization."""

    def test_init_with_defaults(self, integration_config, integration_work_item):
        """Test initialization with default parameters."""
        checker = IntegrationChecker(integration_work_item, integration_config)

        assert checker.config == integration_config
        assert checker.work_item == integration_work_item
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)

    def test_init_with_custom_runner(self, integration_config, integration_work_item, mock_runner):
        """Test initialization with custom runner."""
        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_work_item(self, integration_config, integration_work_item):
        """Test initialization stores work item."""
        checker = IntegrationChecker(integration_work_item, integration_config)

        assert checker.work_item == integration_work_item
        assert checker.work_item["type"] == WorkItemType.INTEGRATION_TEST.value


class TestIntegrationCheckerInterface:
    """Tests for IntegrationChecker interface methods."""

    def test_name_returns_integration(self, integration_config, integration_work_item):
        """Test name() returns 'integration'."""
        checker = IntegrationChecker(integration_work_item, integration_config)

        assert checker.name() == "integration"

    def test_is_enabled_returns_true_by_default(self, integration_work_item):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = IntegrationChecker(integration_work_item, config)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, integration_work_item):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = IntegrationChecker(integration_work_item, config)

        assert checker.is_enabled() is False


class TestIntegrationCheckerRun:
    """Tests for IntegrationChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, integration_work_item):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = IntegrationChecker(integration_work_item, config)

        result = checker.run()

        assert result.checker_name == "integration"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info.get("reason") == "disabled"

    def test_run_returns_skipped_for_non_integration_work_item(
        self, integration_config, feature_work_item
    ):
        """Test run() returns skipped for non-integration work item."""
        checker = IntegrationChecker(feature_work_item, integration_config)

        result = checker.run()

        assert result.passed is True
        assert result.status == "skipped"
        assert result.info.get("reason") == "not integration test"

    def test_run_returns_skipped_when_no_integration_test_files(
        self, integration_config, integration_work_item
    ):
        """Test run() returns skipped when no integration test files exist."""
        # Mock has_integration_test_files to return False
        with patch(
            "solokit.quality.checkers.integration.has_integration_test_files"
        ) as mock_has_files:
            mock_has_files.return_value = False

            checker = IntegrationChecker(integration_work_item, integration_config)
            result = checker.run()

            assert result.passed is True
            assert result.status == "skipped"
            assert "no integration test files found" in result.info.get("reason", "")

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_passes_when_tests_pass(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() passes when integration tests pass."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert result.info["integration_tests"]["passed"] == 5

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_fails_when_tests_fail(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() fails when integration tests fail."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 3, "failed": 2}

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert "2 integration tests failed" in result.errors[0]["message"]

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_handles_environment_setup_error(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() handles environment setup errors."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.setup_environment.side_effect = EnvironmentSetupError(
            "Docker not available"
        )

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert "Docker not available" in result.errors[0]["message"]

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_handles_integration_execution_error(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() handles integration execution errors."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.side_effect = IntegrationExecutionError(
            "Test execution failed"
        )

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert "Test execution failed" in result.errors[0]["message"]

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_handles_integration_test_error(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() handles integration test errors."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.setup_environment.side_effect = IntegrationTestError("Generic error")

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_tears_down_environment_on_success(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() tears down environment on success."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        checker = IntegrationChecker(integration_work_item, integration_config)
        checker.run()

        mock_runner_instance.teardown_environment.assert_called_once()

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_tears_down_environment_on_failure(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() tears down environment even on failure."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.setup_environment.side_effect = EnvironmentSetupError("Error")

        checker = IntegrationChecker(integration_work_item, integration_config)
        checker.run()

        mock_runner_instance.teardown_environment.assert_called_once()

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_logs_teardown_failure_as_warning(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() logs teardown failures as warnings."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}
        mock_runner_instance.teardown_environment.side_effect = OSError("Cleanup failed")

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        # Should still pass, but have a warning
        assert result.passed is True
        assert len(result.warnings) > 0
        assert "Environment teardown failed" in result.warnings[0]["message"]

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    @patch("solokit.testing.performance.PerformanceBenchmark")
    def test_run_includes_performance_benchmarks(
        self,
        mock_benchmark_class,
        mock_runner_class,
        integration_config,
        integration_work_item,
    ):
        """Test run() includes performance benchmarks."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        mock_benchmark_instance = Mock()
        mock_benchmark_class.return_value = mock_benchmark_instance
        mock_benchmark_instance.run_benchmarks.return_value = (
            True,
            {"latency": "100ms"},
        )

        integration_work_item["performance_benchmarks"] = True

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is True
        assert result.info["performance_benchmarks"]["latency"] == "100ms"

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    @patch("solokit.testing.performance.PerformanceBenchmark")
    def test_run_fails_when_required_benchmarks_fail(
        self,
        mock_benchmark_class,
        mock_runner_class,
        integration_config,
        integration_work_item,
    ):
        """Test run() fails when required benchmarks fail."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        mock_benchmark_instance = Mock()
        mock_benchmark_class.return_value = mock_benchmark_instance
        mock_benchmark_instance.run_benchmarks.return_value = (
            False,
            {"error": "Too slow"},
        )

        integration_work_item["performance_benchmarks"] = True

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert any("Performance benchmarks failed" in e["message"] for e in result.errors)

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    @patch("solokit.testing.performance.PerformanceBenchmark")
    def test_run_warns_when_optional_benchmarks_fail(
        self, mock_benchmark_class, mock_runner_class, integration_work_item
    ):
        """Test run() warns when optional benchmarks fail."""
        config = {"enabled": True, "performance_benchmarks": {"required": False}}

        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        mock_benchmark_instance = Mock()
        mock_benchmark_class.return_value = mock_benchmark_instance
        mock_benchmark_instance.run_benchmarks.return_value = (
            False,
            {"error": "Too slow"},
        )

        integration_work_item["performance_benchmarks"] = True

        checker = IntegrationChecker(integration_work_item, config)
        result = checker.run()

        assert result.passed is True
        assert any(
            "Performance benchmarks failed (optional)" in w["message"] for w in result.warnings
        )

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    @patch("solokit.quality.api_validator.APIContractValidator")
    def test_run_includes_api_contracts(
        self,
        mock_validator_class,
        mock_runner_class,
        integration_config,
        integration_work_item,
    ):
        """Test run() includes API contract validation."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        mock_validator_instance = Mock()
        mock_validator_class.return_value = mock_validator_instance
        mock_validator_instance.validate_contracts.return_value = (
            True,
            {"contracts": 3},
        )

        integration_work_item["api_contracts"] = True

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is True
        assert result.info["api_contracts"]["contracts"] == 3

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    @patch("solokit.quality.api_validator.APIContractValidator")
    def test_run_fails_when_required_contracts_fail(
        self,
        mock_validator_class,
        mock_runner_class,
        integration_config,
        integration_work_item,
    ):
        """Test run() fails when required API contracts fail."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        mock_validator_instance = Mock()
        mock_validator_class.return_value = mock_validator_instance
        mock_validator_instance.validate_contracts.return_value = (
            False,
            {"error": "Contract mismatch"},
        )

        integration_work_item["api_contracts"] = True

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.passed is False
        assert any("API contract validation failed" in e["message"] for e in result.errors)

    @patch("solokit.testing.integration_runner.IntegrationTestRunner")
    def test_run_includes_execution_time(
        self, mock_runner_class, integration_config, integration_work_item
    ):
        """Test run() includes execution time in result."""
        mock_runner_instance = Mock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.run_tests.return_value = {"passed": 5, "failed": 0}

        checker = IntegrationChecker(integration_work_item, integration_config)
        result = checker.run()

        assert result.execution_time > 0


class TestIntegrationCheckerValidateEnvironment:
    """Tests for validate_environment() method."""

    def test_validate_environment_returns_skipped_for_non_integration(
        self, integration_config, feature_work_item, mock_runner
    ):
        """Test validate_environment() skips non-integration work items."""
        checker = IntegrationChecker(feature_work_item, integration_config, runner=mock_runner)

        result = checker.validate_environment()

        assert result.passed is True
        assert result.status == "skipped"

    def test_validate_environment_passes_when_all_requirements_met(
        self, integration_config, integration_work_item, mock_runner, tmp_path
    ):
        """Test validate_environment() passes when all requirements met."""
        # Create required files
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.touch()
        config_file = tmp_path / "config" / "integration.json"
        config_file.parent.mkdir()
        config_file.touch()

        integration_work_item["environment_requirements"]["compose_file"] = str(compose_file)
        integration_work_item["environment_requirements"]["config_files"] = [str(config_file)]

        # Mock Docker commands to succeed
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Docker version 20.10",
            stderr="",
            command=["docker"],
            duration_seconds=0.1,
        )

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.passed is True
        assert result.status == "passed"
        assert result.info["docker_available"] is True
        assert result.info["docker_compose_available"] is True
        assert len(result.info["missing_config"]) == 0

    def test_validate_environment_fails_when_docker_unavailable(
        self, integration_config, integration_work_item, mock_runner, tmp_path
    ):
        """Test validate_environment() fails when Docker unavailable."""
        # Create required files
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.touch()
        integration_work_item["environment_requirements"]["compose_file"] = str(compose_file)

        # Mock Docker command to fail
        mock_runner.run.side_effect = [
            CommandResult(
                returncode=1,
                stdout="",
                stderr="command not found",
                command=["docker"],
                duration_seconds=0.1,
            ),
            CommandResult(
                returncode=0,
                stdout="docker-compose version 1.29",
                stderr="",
                command=["docker-compose"],
                duration_seconds=0.1,
            ),
        ]

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.passed is False
        assert result.status == "failed"
        assert result.info["docker_available"] is False
        assert any("Docker not available" in e["message"] for e in result.errors)

    def test_validate_environment_fails_when_docker_compose_unavailable(
        self, integration_config, integration_work_item, mock_runner, tmp_path
    ):
        """Test validate_environment() fails when Docker Compose unavailable."""
        # Create required files
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.touch()
        integration_work_item["environment_requirements"]["compose_file"] = str(compose_file)

        # Mock Docker Compose command to fail
        mock_runner.run.side_effect = [
            CommandResult(
                returncode=0,
                stdout="Docker version 20.10",
                stderr="",
                command=["docker"],
                duration_seconds=0.1,
            ),
            CommandResult(
                returncode=1,
                stdout="",
                stderr="command not found",
                command=["docker-compose"],
                duration_seconds=0.1,
            ),
        ]

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.passed is False
        assert result.status == "failed"
        assert result.info["docker_compose_available"] is False
        assert any("Docker Compose not available" in e["message"] for e in result.errors)

    def test_validate_environment_fails_when_compose_file_missing(
        self, integration_config, integration_work_item, mock_runner
    ):
        """Test validate_environment() fails when compose file missing."""
        integration_work_item["environment_requirements"]["compose_file"] = "missing-compose.yml"

        # Mock Docker commands to succeed
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="version",
            stderr="",
            command=["docker"],
            duration_seconds=0.1,
        )

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.passed is False
        assert result.status == "failed"
        assert "missing-compose.yml" in result.info["missing_config"]
        assert any("Missing compose file" in e["message"] for e in result.errors)

    def test_validate_environment_fails_when_config_files_missing(
        self, integration_config, integration_work_item, mock_runner, tmp_path
    ):
        """Test validate_environment() fails when config files missing."""
        # Create compose file but not config files
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.touch()
        integration_work_item["environment_requirements"]["compose_file"] = str(compose_file)
        integration_work_item["environment_requirements"]["config_files"] = [
            "missing1.json",
            "missing2.json",
        ]

        # Mock Docker commands to succeed
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="version",
            stderr="",
            command=["docker"],
            duration_seconds=0.1,
        )

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.passed is False
        assert result.status == "failed"
        assert "missing1.json" in result.info["missing_config"]
        assert "missing2.json" in result.info["missing_config"]
        assert len([e for e in result.errors if "Missing config file" in e["message"]]) == 2

    def test_validate_environment_includes_execution_time(
        self, integration_config, integration_work_item, mock_runner
    ):
        """Test validate_environment() includes execution time."""
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="version",
            stderr="",
            command=["docker"],
            duration_seconds=0.1,
        )

        checker = IntegrationChecker(integration_work_item, integration_config, runner=mock_runner)
        result = checker.validate_environment()

        assert result.execution_time > 0


class TestIntegrationCheckerValidateDocumentation:
    """Tests for validate_documentation() method."""

    def test_validate_documentation_returns_skipped_for_non_integration(
        self, integration_config, feature_work_item
    ):
        """Test validate_documentation() skips non-integration work items."""
        checker = IntegrationChecker(feature_work_item, integration_config)

        result = checker.validate_documentation()

        assert result.passed is True
        assert result.status == "skipped"

    def test_validate_documentation_returns_skipped_when_disabled(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() skips when disabled in config."""
        # Create config file with documentation disabled
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text('{"integration_tests": {"documentation": {"enabled": false}}}')

        monkeypatch.chdir(tmp_path)

        checker = IntegrationChecker(integration_work_item, {"enabled": True})
        result = checker.validate_documentation()

        assert result.passed is True
        assert result.status == "skipped"

    def test_validate_documentation_passes_when_all_requirements_met(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() passes when all requirements met."""
        monkeypatch.chdir(tmp_path)

        # Create architecture diagram
        docs_dir = tmp_path / "docs" / "architecture"
        docs_dir.mkdir(parents=True)
        (docs_dir / "integration-architecture.md").write_text("# Architecture")

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": true,
                    "sequence_diagrams": false,
                    "contract_documentation": false,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser to return integration points
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {
                "scope": "This is a detailed scope with integration points documented here."
            }

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is True
            assert result.status == "passed"
            assert len(result.info["missing"]) == 0

    def test_validate_documentation_fails_when_architecture_diagram_missing(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() fails when architecture diagram missing."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": true,
                    "sequence_diagrams": false,
                    "contract_documentation": false,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {"scope": "Detailed scope with integration points."}

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is False
            assert result.status == "failed"
            assert "Integration architecture diagram" in result.info["missing"]

    def test_validate_documentation_checks_sequence_diagrams(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() checks for sequence diagrams."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": false,
                    "sequence_diagrams": true,
                    "contract_documentation": false,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser with sequence diagrams
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {
                "scope": "Integration scope with detailed integration points documentation.",
                "test_scenarios": [
                    {"content": "```mermaid\nsequenceDiagram\nUser->API: Request\n```"},
                ],
            }

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is True
            assert any(
                c["name"] == "Sequence diagrams" and c["passed"] for c in result.info["checks"]
            )

    def test_validate_documentation_fails_when_sequence_diagrams_missing(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() fails when sequence diagrams missing."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": false,
                    "sequence_diagrams": true,
                    "contract_documentation": false,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser without sequence diagrams
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {
                "scope": "Integration scope",
                "test_scenarios": [
                    {"content": "No diagrams here"},
                ],
            }

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is False
            assert "Sequence diagrams for test scenarios" in result.info["missing"]

    def test_validate_documentation_checks_api_contracts(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() checks for API contract documentation."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": false,
                    "sequence_diagrams": false,
                    "contract_documentation": true,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser with API contracts
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {
                "scope": "Integration scope with detailed integration points documentation.",
                "api_contracts": "API contracts are documented here with endpoints and schemas.",
            }

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is True
            assert any(
                c["name"] == "API contracts documented" and c["passed"]
                for c in result.info["checks"]
            )

    def test_validate_documentation_checks_performance_baseline(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() checks for performance baseline."""
        monkeypatch.chdir(tmp_path)

        # Create baseline file
        tracking_dir = tmp_path / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)
        (tracking_dir / "performance_baselines.json").write_text("{}")

        # Create config
        config_file = tmp_path / ".session" / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": false,
                    "sequence_diagrams": false,
                    "contract_documentation": false,
                    "performance_baseline_docs": true
                }
            }
        }"""
        )

        # Mock spec parser with performance benchmarks
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {
                "scope": "Integration scope with detailed integration points documentation.",
                "performance_benchmarks": "Performance benchmarks are documented here with latency targets.",
            }

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.passed is True
            assert any(
                c["name"] == "Performance baseline documented" and c["passed"]
                for c in result.info["checks"]
            )

    def test_validate_documentation_handles_spec_parser_errors(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() handles spec parser errors gracefully."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "sequence_diagrams": true
                }
            }
        }"""
        )

        # Mock spec parser to raise error
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.side_effect = ValueError("Spec file not found")

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            # Should handle error gracefully and continue
            assert result.status in ["passed", "failed"]

    def test_validate_documentation_includes_summary(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() includes summary in results."""
        monkeypatch.chdir(tmp_path)

        # Create config
        config_dir = tmp_path / ".session"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text(
            """{
            "integration_tests": {
                "documentation": {
                    "enabled": true,
                    "architecture_diagrams": false,
                    "sequence_diagrams": false,
                    "contract_documentation": false,
                    "performance_baseline_docs": false
                }
            }
        }"""
        )

        # Mock spec parser
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {"scope": "Integration points documented here."}

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert "summary" in result.info
            assert "/" in result.info["summary"]

    def test_validate_documentation_includes_execution_time(
        self, integration_work_item, tmp_path, monkeypatch
    ):
        """Test validate_documentation() includes execution time."""
        monkeypatch.chdir(tmp_path)

        # Mock spec parser
        with patch(
            "solokit.quality.checkers.integration.spec_parser.parse_spec_file"
        ) as mock_parse:
            mock_parse.return_value = {"scope": "Integration scope"}

            checker = IntegrationChecker(integration_work_item, {"enabled": True})
            result = checker.validate_documentation()

            assert result.execution_time > 0
