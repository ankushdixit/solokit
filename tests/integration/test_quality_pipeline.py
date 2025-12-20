"""Integration tests for quality pipeline integration gates.

This module tests the QualityGates class integration test methods which handle
integration test execution, environment validation, and documentation validation.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.quality.gates import QualityGates


class TestQualityGatesInit:
    """Tests for QualityGates initialization with integration test config."""

    def test_init_with_default_config(self):
        """Test that QualityGates initializes with default config when no config file exists."""
        # Arrange
        # No setup needed - using default Path that doesn't exist

        # Act
        gates = QualityGates(config_path=Path("/nonexistent/config.json"))

        # Assert
        assert gates is not None
        assert gates.config is not None
        assert hasattr(gates.config, "test_execution")

    def test_init_with_custom_config(self, temp_dir):
        """Test that QualityGates initializes with custom config from file."""
        # Arrange
        config_file = temp_dir / "config.json"
        custom_config = {
            "quality_gates": {"test_execution": {"enabled": False, "required": False}},
            "integration_tests": {"enabled": True},
        }
        config_file.write_text(json.dumps(custom_config))

        # Act
        gates = QualityGates(config_path=config_file)

        # Assert
        assert gates.config.test_execution.enabled is False

    def test_init_loads_full_config(self, temp_dir):
        """Test that QualityGates stores config path for later access to full config."""
        # Arrange
        config_file = temp_dir / "config.json"
        config_file.write_text(json.dumps({"quality_gates": {}}))

        # Act
        gates = QualityGates(config_path=config_file)

        # Assert
        assert hasattr(gates, "_config_path")
        assert gates._config_path == config_file


class TestIntegrationTestMethods:
    """Tests for integration test method existence and basic functionality."""

    def test_run_integration_tests_method_exists(self):
        """Test that run_integration_tests method exists."""
        # Arrange
        gates = QualityGates()

        # Act & Assert
        assert hasattr(gates, "run_integration_tests")
        assert callable(gates.run_integration_tests)

    def test_validate_integration_environment_method_exists(self):
        """Test that validate_integration_environment method exists."""
        # Arrange
        gates = QualityGates()

        # Act & Assert
        assert hasattr(gates, "validate_integration_environment")
        assert callable(gates.validate_integration_environment)

    def test_validate_integration_documentation_method_exists(self):
        """Test that validate_integration_documentation method exists."""
        # Arrange
        gates = QualityGates()

        # Act & Assert
        assert hasattr(gates, "validate_integration_documentation")
        assert callable(gates.validate_integration_documentation)


class TestIntegrationTestSkipping:
    """Tests for skipping integration tests on non-integration work items."""

    def test_run_integration_tests_skips_non_integration_work_item(self):
        """Test that run_integration_tests skips non-integration work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Regular Feature"}

        # Act
        passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "not integration test"

    def test_run_integration_tests_skips_bug_work_item(self):
        """Test that run_integration_tests skips bug work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "BUG-001", "type": "bug", "title": "Fix Bug"}

        # Act
        passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_run_integration_tests_skips_refactor_work_item(self):
        """Test that run_integration_tests skips refactor work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "REF-001", "type": "refactor", "title": "Refactor Code"}

        # Act
        passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_environment_skips_non_integration_work_item(self):
        """Test that validate_integration_environment skips non-integration work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Feature"}

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_documentation_skips_non_integration_work_item(self):
        """Test that validate_integration_documentation skips non-integration work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Feature"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"


class TestIntegrationTestsDisabled:
    """Tests for skipping integration tests when disabled in config."""

    def test_run_integration_tests_skips_when_disabled(self, temp_dir):
        """Test that run_integration_tests skips when disabled in config."""
        # Arrange
        config_file = temp_dir / "config.json"
        config = {"quality_gates": {}, "integration_tests": {"enabled": False}}
        config_file.write_text(json.dumps(config))
        gates = QualityGates(config_path=config_file)

        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Integration Test",
        }

        # Act
        passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "disabled"

    def test_run_integration_tests_runs_when_enabled(self, temp_dir):
        """Test that run_integration_tests attempts to run when enabled in config."""
        # Arrange
        config_file = temp_dir / "config.json"
        config = {"quality_gates": {}, "integration_tests": {"enabled": True}}
        config_file.write_text(json.dumps(config))
        gates = QualityGates(config_path=config_file)

        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Integration Test",
        }

        # Act
        with patch("solokit.work_items.spec_parser.parse_spec_file") as mock_parse:
            mock_parse.return_value = {"test_scenarios": []}
            with patch(
                "solokit.testing.integration_runner.IntegrationTestRunner"
            ) as mock_runner_class:
                mock_runner = Mock()
                # setup_environment now raises exceptions instead of returning tuple
                mock_runner.setup_environment.return_value = None
                # run_tests now returns dict directly (not tuple)
                mock_runner.run_tests.return_value = {"passed": 5, "failed": 0}
                mock_runner.teardown_environment.return_value = None
                mock_runner_class.return_value = mock_runner

                passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert results.get("reason") != "disabled"


class TestEnvironmentValidation:
    """Tests for integration environment validation logic."""

    @patch("subprocess.run")
    def test_validate_environment_checks_docker_available(self, mock_run):
        """Test that validate_integration_environment checks Docker availability."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "environment_requirements": {},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert "docker_available" in results
        assert isinstance(results["docker_available"], bool)

    @patch("subprocess.run")
    def test_validate_environment_checks_docker_compose_available(self, mock_run):
        """Test that validate_integration_environment checks Docker Compose availability."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "environment_requirements": {},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert "docker_compose_available" in results
        assert isinstance(results["docker_compose_available"], bool)

    def test_validate_environment_detects_missing_compose_file(self):
        """Test that validate_integration_environment detects missing compose file."""
        # Arrange
        gates = QualityGates()
        work_item = {
            "id": "INTEG-002",
            "type": "integration_test",
            "environment_requirements": {"compose_file": "nonexistent-compose.yml"},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert "nonexistent-compose.yml" in results.get("missing_config", [])

    def test_validate_environment_detects_missing_config_files(self):
        """Test that validate_integration_environment detects missing config files."""
        # Arrange
        gates = QualityGates()
        work_item = {
            "id": "INTEG-003",
            "type": "integration_test",
            "environment_requirements": {
                "compose_file": "docker-compose.yml",
                "config_files": ["missing-config.yml", "another-missing.json"],
            },
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        missing = results.get("missing_config", [])
        assert any("missing-config.yml" in f for f in missing)
        assert any("another-missing.json" in f for f in missing)

    def test_validate_environment_results_has_required_keys(self):
        """Test that validate_integration_environment results have correct structure."""
        # Arrange
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "environment_requirements": {},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        expected_keys = [
            "docker_available",
            "docker_compose_available",
            "required_services",
            "missing_config",
            "passed",
        ]
        for key in expected_keys:
            assert key in results

    @patch("subprocess.run")
    def test_validate_environment_passes_when_all_requirements_met(self, mock_run, temp_dir):
        """Test that validate_integration_environment passes when all requirements are met."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        compose_file = temp_dir / "docker-compose.yml"
        compose_file.write_text("version: '3'")

        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "environment_requirements": {"compose_file": str(compose_file)},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is True
        assert results["passed"] is True

    @patch("subprocess.run")
    def test_validate_environment_fails_when_docker_unavailable(self, mock_run):
        """Test that validate_integration_environment fails when Docker is unavailable."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("docker not found")
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "environment_requirements": {},
        }

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is False
        assert results["passed"] is False
        assert results["docker_available"] is False


class TestIntegrationTestExecution:
    """Tests for integration test execution results structure."""

    def test_run_integration_tests_raises_error_when_spec_missing(self):
        """Test that run_integration_tests raises error when spec file is missing."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act & Assert
        from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError

        with pytest.raises(
            SolokitFileNotFoundError, match=r"File not found: .*session[/\\]specs[/\\]INTEG-001\.md"
        ):
            gates.run_integration_tests(work_item)
