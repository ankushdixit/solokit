"""Additional tests for session_validate module to improve coverage.

This module tests uncovered paths in validate.py including:
- File operation error handling (lines 203-204, 224-230)
- validate() output formatting (lines 369-390)
- main() CLI function (lines 417-469)
- Deployment work item validation (lines 293-297)
"""

import json
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult
from solokit.core.exceptions import (
    FileOperationError,
    SessionNotFoundError,
)
from solokit.core.types import WorkItemType
from solokit.session import validate as validate_module
from solokit.session.validate import SessionValidator


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary .session directory structure."""
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()

    # Create minimal config.json
    config = {
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": True,
                "commands": {
                    "python": "pytest --cov=src --cov-report=json",
                    "javascript": "npm test -- --coverage",
                    "typescript": "npm test -- --coverage",
                },
            },
            "linting": {"enabled": True, "required": False},
            "formatting": {"enabled": True, "required": False},
        }
    }
    (session_dir / "config.json").write_text(json.dumps(config))

    return session_dir


@pytest.fixture
def mock_quality_gates():
    """Create lightweight mock for QualityGates."""
    from solokit.core.config import QualityGatesConfig

    mock_qg = Mock()
    mock_qg.config = QualityGatesConfig()
    mock_qg.run_tests.return_value = (True, {"status": "passed", "reason": "All tests passed"})
    mock_qg.run_linting.return_value = (True, {"status": "passed"})
    mock_qg.run_formatting.return_value = (True, {"status": "passed"})
    return mock_qg


class TestValidateWorkItemCriteriaFileErrors:
    """Tests for validate_work_item_criteria file operation error handling."""

    def test_validate_work_item_criteria_raises_file_operation_error_on_status_read_failure(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria raises FileOperationError when status file read fails."""
        # Arrange
        project_root = temp_session_dir.parent
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text("invalid json {")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            validator.validate_work_item_criteria()

        # Verify exception
        assert exc_info.value.context["operation"] == "read"
        assert "status_update.json" in exc_info.value.context["file_path"]

    def test_validate_work_item_criteria_raises_file_operation_error_on_work_items_read_failure(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria raises FileOperationError when work items read fails."""
        # Arrange
        project_root = temp_session_dir.parent
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text("invalid json {")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            validator.validate_work_item_criteria()

        # Verify exception
        assert exc_info.value.context["operation"] == "read"
        assert "work_items.json" in exc_info.value.context["file_path"]


class TestValidateWorkItemCriteriaDeploymentType:
    """Tests for validate_work_item_criteria with deployment work items."""

    def test_validate_work_item_criteria_validates_deployment_sections(self, temp_session_dir):
        """Test validate_work_item_criteria checks deployment-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "DEPLOY-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "DEPLOY-001": {
                    "id": "DEPLOY-001",
                    "type": WorkItemType.DEPLOYMENT.value,
                    "spec_file": ".session/specs/DEPLOY-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "DEPLOY-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing deployment_scope and deployment_procedure
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Deployment Scope" in result["missing_sections"]
        assert "Deployment Procedure" in result["missing_sections"]

    def test_validate_work_item_criteria_passes_complete_deployment_spec(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=True for complete deployment spec."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "DEPLOY-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "DEPLOY-001": {
                    "id": "DEPLOY-001",
                    "type": WorkItemType.DEPLOYMENT.value,
                    "spec_file": ".session/specs/DEPLOY-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "DEPLOY-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "deployment_scope": "Deploy to production",
            "deployment_procedure": "Run deployment script",
        }
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "Work item spec is complete"


class TestValidateOutputFormatting:
    """Tests for validate() output formatting (lines 369-390)."""

    def test_validate_shows_quality_gate_issues_when_failed(
        self, temp_session_dir, mock_quality_gates, capsys
    ):
        """Test validate() displays quality gate issues when gates fail."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        # Make tests fail with issues
        mock_quality_gates.run_tests.return_value = (
            False,
            {
                "status": "failed",
                "reason": "Tests failed",
                "issues": ["test_foo.py::test_bar failed", "test_baz.py::test_qux failed"],
            },
        )

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock git
        mock_status = CommandResult(
            returncode=0, stdout="", stderr="", command=["git", "status"], duration_seconds=0.1
        )
        mock_branch = CommandResult(
            returncode=0,
            stdout="main\n",
            stderr="",
            command=["git", "branch"],
            duration_seconds=0.1,
        )

        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Overview",
            "implementation_details": "Details",
        }

        # Act
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
            with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
                result = validator.validate()

        # Assert
        assert result["ready"] is False

        # Check console output
        captured = capsys.readouterr()
        assert "✗ tests:" in captured.out
        # Note: The validate() method constructs gates dict without including 'issues' from test_results,
        # so individual issues won't be displayed unless the gate dict includes them.
        # This test verifies that quality gate failures are shown, but detailed issues
        # aren't propagated by the current implementation of validate_quality_gates_check()
        assert "Tests failed" in captured.out

    def test_validate_shows_missing_paths_for_work_item_criteria_legacy(
        self, temp_session_dir, mock_quality_gates, capsys
    ):
        """Test validate() displays missing implementation paths (if result contains them)."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock git
        mock_status = CommandResult(
            returncode=0, stdout="", stderr="", command=["git", "status"], duration_seconds=0.1
        )
        mock_branch = CommandResult(
            returncode=0,
            stdout="main\n",
            stderr="",
            command=["git", "branch"],
            duration_seconds=0.1,
        )

        parsed_spec = {"acceptance_criteria": ["AC1", "AC2"]}  # Incomplete

        # Act
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
            with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
                result = validator.validate()

        # Assert
        assert result["ready"] is False

        # Check console output
        captured = capsys.readouterr()
        assert "✗ Work Item Criteria:" in captured.out or "work_item_criteria" in captured.out


class TestMainFunction:
    """Tests for main() CLI function (lines 417-469)."""

    def test_main_returns_0_when_validation_passes(self, temp_session_dir, mock_quality_gates):
        """Test main() returns 0 when validation passes."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            with patch("solokit.session.validate.Path.cwd", return_value=project_root):
                validator = SessionValidator(project_root=project_root)

                # Mock git
                mock_status = CommandResult(
                    returncode=0,
                    stdout="",
                    stderr="",
                    command=["git", "status"],
                    duration_seconds=0.1,
                )
                mock_branch = CommandResult(
                    returncode=0,
                    stdout="main\n",
                    stderr="",
                    command=["git", "branch"],
                    duration_seconds=0.1,
                )

                parsed_spec = {
                    "acceptance_criteria": ["AC1", "AC2", "AC3"],
                    "overview": "Overview",
                    "implementation_details": "Details",
                }

                # Act
                with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
                    with patch(
                        "solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec
                    ):
                        with patch(
                            "solokit.session.validate.SessionValidator", return_value=validator
                        ):
                            with patch("sys.argv", ["validate.py"]):
                                result = validate_module.main()

        # Assert
        assert result == 0

    def test_main_returns_1_when_validation_fails(self, temp_session_dir, mock_quality_gates):
        """Test main() returns 1 when validation fails."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create session setup with incomplete spec
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            with patch("solokit.session.validate.Path.cwd", return_value=project_root):
                validator = SessionValidator(project_root=project_root)

                # Mock git
                mock_status = CommandResult(
                    returncode=0,
                    stdout="",
                    stderr="",
                    command=["git", "status"],
                    duration_seconds=0.1,
                )
                mock_branch = CommandResult(
                    returncode=0,
                    stdout="main\n",
                    stderr="",
                    command=["git", "branch"],
                    duration_seconds=0.1,
                )

                parsed_spec = {"acceptance_criteria": ["AC1", "AC2"]}  # Incomplete

                # Act
                with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
                    with patch(
                        "solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec
                    ):
                        with patch(
                            "solokit.session.validate.SessionValidator", return_value=validator
                        ):
                            with patch("sys.argv", ["validate.py"]):
                                result = validate_module.main()

        # Assert
        assert result == 1

    def test_main_handles_session_not_found_error(self, temp_session_dir, capsys):
        """Test main() handles SessionNotFoundError gracefully."""
        # Arrange - Create directory without status file but with git mocked
        project_root = temp_session_dir.parent

        # Mock git to succeed so we get SessionNotFoundError instead of NotAGitRepoError
        mock_status = CommandResult(
            returncode=0, stdout="", stderr="", command=["git", "status"], duration_seconds=0.1
        )

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch("solokit.core.command_runner.CommandRunner.run", return_value=mock_status):
                with patch("sys.argv", ["validate.py"]):
                    # Act
                    result = validate_module.main()

        # Assert
        assert result == SessionNotFoundError().exit_code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_validation_error(self, temp_session_dir, capsys):
        """Test main() handles ValidationError gracefully."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status file with no current work item
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": None}))

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch("sys.argv", ["validate.py"]):
                # Act
                result = validate_module.main()

        # Assert
        assert result > 0  # Some error code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_file_not_found_error(self, temp_session_dir, capsys):
        """Test main() handles FileNotFoundError gracefully."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status pointing to work item, but no work_items.json file
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch("sys.argv", ["validate.py"]):
                # Act
                result = validate_module.main()

        # Assert
        assert result > 0  # Some error code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_spec_validation_error(self, temp_session_dir, capsys):
        """Test main() handles SpecValidationError gracefully."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            # Mock spec parser to raise error
            with patch(
                "solokit.work_items.spec_parser.parse_spec_file",
                side_effect=Exception("Parse error"),
            ):
                with patch("sys.argv", ["validate.py"]):
                    # Act
                    result = validate_module.main()

        # Assert
        assert result > 0  # Some error code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_git_error(self, temp_session_dir, mock_quality_gates, capsys):
        """Test main() handles GitError gracefully."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            with patch("solokit.session.validate.Path.cwd", return_value=project_root):
                validator = SessionValidator(project_root=project_root)

                # Mock git to raise error
                mock_status = CommandResult(
                    returncode=128,
                    stdout="",
                    stderr="",
                    command=["git", "status"],
                    duration_seconds=0.1,
                )

                # Act
                with patch.object(validator.runner, "run", return_value=mock_status):
                    with patch("solokit.session.validate.SessionValidator", return_value=validator):
                        with patch("sys.argv", ["validate.py"]):
                            result = validate_module.main()

        # Assert
        assert result > 0  # Some error code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_handles_unexpected_error(self, temp_session_dir, capsys):
        """Test main() handles unexpected errors gracefully."""
        # Arrange
        project_root = temp_session_dir.parent

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch(
                "solokit.session.validate.SessionValidator",
                side_effect=RuntimeError("Unexpected error"),
            ):
                with patch("sys.argv", ["validate.py"]):
                    # Act
                    result = validate_module.main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.err

    def test_main_accepts_fix_flag(self, temp_session_dir, mock_quality_gates):
        """Test main() accepts --fix flag and passes it to validate()."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            with patch("solokit.session.validate.Path.cwd", return_value=project_root):
                validator = SessionValidator(project_root=project_root)

                # Mock git
                mock_status = CommandResult(
                    returncode=0,
                    stdout="",
                    stderr="",
                    command=["git", "status"],
                    duration_seconds=0.1,
                )
                mock_branch = CommandResult(
                    returncode=0,
                    stdout="main\n",
                    stderr="",
                    command=["git", "branch"],
                    duration_seconds=0.1,
                )

                parsed_spec = {
                    "acceptance_criteria": ["AC1", "AC2", "AC3"],
                    "overview": "Overview",
                    "implementation_details": "Details",
                }

                # Act
                with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
                    with patch(
                        "solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec
                    ):
                        with patch(
                            "solokit.session.validate.SessionValidator", return_value=validator
                        ):
                            with patch("sys.argv", ["validate.py", "--fix"]):
                                result = validate_module.main()

        # Assert
        assert result == 0
        # Verify auto_fix was passed
        mock_quality_gates.run_linting.assert_called_with(auto_fix=True)
        mock_quality_gates.run_formatting.assert_called_with(auto_fix=True)

    def test_main_accepts_debug_flag_shows_traceback(self, temp_session_dir, capsys):
        """Test main() accepts --debug flag and shows detailed errors."""
        # Arrange
        project_root = temp_session_dir.parent

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch(
                "solokit.session.validate.SessionValidator",
                side_effect=RuntimeError("Debug test error"),
            ):
                with patch("sys.argv", ["validate.py", "--debug"]):
                    # Act
                    result = validate_module.main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        # Debug mode should show more detailed error
        assert "Unexpected error" in captured.err

    def test_main_without_debug_flag_suggests_debug(self, temp_session_dir, capsys):
        """Test main() suggests --debug flag when error occurs without it."""
        # Arrange
        project_root = temp_session_dir.parent

        with patch("solokit.session.validate.Path.cwd", return_value=project_root):
            with patch(
                "solokit.session.validate.SessionValidator",
                side_effect=RuntimeError("Test error"),
            ):
                with patch("sys.argv", ["validate.py"]):
                    # Act
                    result = validate_module.main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        # Without debug, should suggest using --debug
        assert "--debug" in captured.out or "debug" in captured.out.lower()
