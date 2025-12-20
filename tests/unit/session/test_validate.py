"""Unit tests for session_validate module.

This module tests session validation functionality including:
- Git status checking
- Work item criteria validation
- Quality gates preview integration
- Tracking update detection
- Full validation workflow
"""

import json
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.exceptions import (
    GitError,
    NotAGitRepoError,
    SessionNotFoundError,
    SpecValidationError,
    ValidationError,
)
from solokit.session.validate import SessionValidator


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary .session directory structure.

    Returns:
        Path: Path to temporary .session directory with tracking subdirectory.
    """
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
    """Create lightweight mock for QualityGates to avoid slow execution.

    Returns:
        Mock: Mock QualityGates instance with basic methods.
    """
    from solokit.core.config import QualityGatesConfig

    mock_qg = Mock()
    mock_qg.config = QualityGatesConfig()  # Uses default values
    mock_qg.run_tests.return_value = (True, {"status": "passed", "reason": "All tests passed"})
    mock_qg.run_linting.return_value = (True, {"status": "passed"})
    mock_qg.run_formatting.return_value = (True, {"status": "passed"})
    return mock_qg


class TestSessionValidatorInit:
    """Test suite for SessionValidator initialization."""

    def test_init_with_default_project_root(self, temp_session_dir):
        """Test SessionValidator initializes with current directory as default project root."""
        # Arrange & Act
        with patch("solokit.session.validate.Path.cwd", return_value=temp_session_dir.parent):
            with patch("solokit.session.validate.QualityGates"):
                validator = SessionValidator()

        # Assert
        assert validator.project_root == temp_session_dir.parent
        assert validator.session_dir == temp_session_dir

    def test_init_with_custom_project_root(self, temp_session_dir):
        """Test SessionValidator initializes with custom project root path."""
        # Arrange
        project_root = temp_session_dir.parent

        # Act
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Assert
        assert validator.project_root == project_root
        assert validator.session_dir == temp_session_dir

    def test_init_creates_quality_gates_instance(self, temp_session_dir):
        """Test SessionValidator creates QualityGates instance with config path."""
        # Arrange
        project_root = temp_session_dir.parent

        # Act
        with patch("solokit.session.validate.QualityGates") as mock_qg_class:
            _validator = SessionValidator(project_root=project_root)

        # Assert
        expected_config_path = temp_session_dir / "config.json"
        mock_qg_class.assert_called_once_with(expected_config_path)


class TestCheckGitStatus:
    """Test suite for check_git_status method."""

    def test_check_git_status_returns_success_for_clean_directory(self, temp_session_dir):
        """Test check_git_status returns passed=True for clean working directory."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

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

        # Act
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is True
        assert "main" in result["message"]
        assert result["details"]["branch"] == "main"
        assert result["details"]["changes"] == 0

    def test_check_git_status_returns_success_with_non_tracking_changes(self, temp_session_dir):
        """Test check_git_status returns passed=True when changes don't include tracking files."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_status = CommandResult(
            returncode=0,
            stdout=" M src/main.py\n M tests/test_foo.py\n",
            stderr="",
            command=["git", "status"],
            duration_seconds=0.1,
        )

        mock_branch = CommandResult(
            returncode=0,
            stdout="feature-branch\n",
            stderr="",
            command=["git", "branch"],
            duration_seconds=0.1,
        )

        # Act
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is True
        assert "feature-branch" in result["message"]
        assert result["details"]["changes"] == 2

    def test_check_git_status_fails_with_uncommitted_tracking_files(self, temp_session_dir):
        """Test check_git_status returns passed=False when tracking files are uncommitted."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_status = CommandResult(
            returncode=0,
            stdout=" M .session/tracking/status_update.json\n M .session/tracking/work_items.json\n",
            stderr="",
            command=["git", "status"],
            duration_seconds=0.1,
        )

        # Act
        with patch.object(validator.runner, "run", return_value=mock_status):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is False
        assert "Uncommitted tracking files" in result["message"]
        assert "2 files" in result["message"]

    def test_check_git_status_fails_when_not_git_repository(self, temp_session_dir):
        """Test check_git_status raises NotAGitRepoError when directory is not a git repo."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_status = CommandResult(
            returncode=128,  # Git error code for "not a git repository"
            stdout="",
            stderr="",
            command=["git", "status"],
            duration_seconds=0.1,
        )

        # Act & Assert
        with patch.object(validator.runner, "run", return_value=mock_status):
            with pytest.raises(NotAGitRepoError) as exc_info:
                validator.check_git_status()

        # Verify exception details
        assert str(temp_session_dir.parent) == exc_info.value.context.get("path")

    def test_check_git_status_raises_git_error_on_branch_failure(self, temp_session_dir):
        """Test check_git_status raises GitError when branch command fails."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_status = CommandResult(
            returncode=0, stdout="", stderr="", command=["git", "status"], duration_seconds=0.1
        )

        mock_branch_fail = CommandResult(
            returncode=1,
            stdout="",
            stderr="fatal: not a valid object name",
            command=["git", "branch"],
            duration_seconds=0.1,
        )

        # Act & Assert
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch_fail]):
            with pytest.raises(GitError) as exc_info:
                validator.check_git_status()

        # Verify exception
        assert "Failed to get current branch" in exc_info.value.message


class TestPreviewQualityGates:
    """Test suite for preview_quality_gates method."""

    def test_preview_quality_gates_all_pass(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates returns passed=True when all gates pass."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "All quality gates pass"
        assert "tests" in result["gates"]
        assert result["gates"]["tests"]["passed"] is True

    def test_preview_quality_gates_tests_fail(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates returns passed=False when tests fail."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.run_tests.return_value = (
            False,
            {"status": "failed", "reason": "2 tests failed"},
        )

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["passed"] is False
        assert result["message"] == "Some quality gates fail"
        assert result["gates"]["tests"]["passed"] is False
        assert "2 tests failed" in result["gates"]["tests"]["message"]

    def test_preview_quality_gates_skips_tests_when_auto_fix_enabled(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates skips tests when auto_fix=True."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        assert "tests" not in result["gates"]  # Tests should be skipped
        mock_quality_gates.run_tests.assert_not_called()

    def test_preview_quality_gates_handles_optional_tests(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates marks optional tests as passed even if they fail."""
        # Arrange
        from dataclasses import replace

        project_root = temp_session_dir.parent
        # Make test_execution not required
        mock_quality_gates.config = replace(
            mock_quality_gates.config,
            test_execution=replace(mock_quality_gates.config.test_execution, required=False),
        )
        mock_quality_gates.run_tests.return_value = (False, {"status": "failed"})

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["gates"]["tests"]["passed"] is True
        assert "not required" in result["gates"]["tests"]["message"]

    def test_preview_quality_gates_handles_disabled_gates(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates skips disabled quality gates."""
        # Arrange
        from dataclasses import replace

        project_root = temp_session_dir.parent
        # Disable test_execution
        mock_quality_gates.config = replace(
            mock_quality_gates.config,
            test_execution=replace(mock_quality_gates.config.test_execution, enabled=False),
        )

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert "tests" not in result["gates"]
        mock_quality_gates.run_tests.assert_not_called()

    def test_preview_quality_gates_auto_fix_linting(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates passes auto_fix parameter to linting."""
        # Arrange
        from dataclasses import replace

        project_root = temp_session_dir.parent
        # Make linting required to see auto-fix message
        mock_quality_gates.config = replace(
            mock_quality_gates.config,
            linting=replace(mock_quality_gates.config.linting, required=True),
        )
        mock_quality_gates.run_linting.return_value = (True, {"status": "passed", "fixed": True})

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        mock_quality_gates.run_linting.assert_called_once_with(auto_fix=True)
        assert "auto-fixed" in result["gates"]["linting"]["message"]

    def test_preview_quality_gates_auto_fix_formatting(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates passes auto_fix parameter to formatting."""
        # Arrange
        from dataclasses import replace

        project_root = temp_session_dir.parent
        # Make formatting required to see auto-fix message
        mock_quality_gates.config = replace(
            mock_quality_gates.config,
            formatting=replace(mock_quality_gates.config.formatting, required=True),
        )
        mock_quality_gates.run_formatting.return_value = (
            True,
            {"status": "passed", "formatted": True},
        )

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        mock_quality_gates.run_formatting.assert_called_once_with(auto_fix=True)
        assert "auto-formatted" in result["gates"]["formatting"]["message"]


class TestValidateWorkItemCriteria:
    """Test suite for validate_work_item_criteria method."""

    def test_validate_work_item_criteria_fails_when_no_active_session(self, temp_session_dir):
        """Test validate_work_item_criteria raises SessionNotFoundError when status file doesn't exist."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with pytest.raises(SessionNotFoundError) as exc_info:
            validator.validate_work_item_criteria()

        # Verify exception
        assert "No active session" in exc_info.value.message

    def test_validate_work_item_criteria_fails_when_no_current_work_item(self, temp_session_dir):
        """Test validate_work_item_criteria raises ValidationError when no current work item set."""
        # Arrange
        project_root = temp_session_dir.parent
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": None}))

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_work_item_criteria()

        # Verify exception
        assert "No current work item" in exc_info.value.message

    def test_validate_work_item_criteria_fails_when_spec_file_missing(self, temp_session_dir):
        """Test validate_work_item_criteria raises FileNotFoundError when spec file doesn't exist."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
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

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with pytest.raises(SolokitFileNotFoundError) as exc_info:
            validator.validate_work_item_criteria()

        # Verify exception
        assert "WORK-001.md" in exc_info.value.message
        assert exc_info.value.context.get("file_type") == "spec"

    def test_validate_work_item_criteria_fails_when_spec_file_invalid(self, temp_session_dir):
        """Test validate_work_item_criteria raises SpecValidationError when spec parsing fails."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
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
        spec_file.write_text("Invalid spec content")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act & Assert
        with patch(
            "solokit.work_items.spec_parser.parse_spec_file", side_effect=Exception("Parse error")
        ):
            with pytest.raises(SpecValidationError) as exc_info:
                validator.validate_work_item_criteria()

        # Verify exception
        assert "WORK-001" in exc_info.value.message
        assert "Parse error" in str(exc_info.value.context.get("validation_errors"))

    def test_validate_work_item_criteria_fails_when_acceptance_criteria_insufficient(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria returns passed=False when fewer than 3 acceptance criteria."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
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

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch(
            "solokit.work_items.spec_parser.parse_spec_file",
            return_value={"acceptance_criteria": ["AC1", "AC2"]},
        ):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Spec file incomplete" in result["message"]
        assert "Acceptance Criteria (at least 3 items)" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_feature_sections(self, temp_session_dir):
        """Test validate_work_item_criteria checks feature-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
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

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing overview and implementation_details
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Overview" in result["missing_sections"]
        assert "Implementation Details" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_bug_sections(self, temp_session_dir):
        """Test validate_work_item_criteria checks bug-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "BUG-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "BUG-001": {
                    "id": "BUG-001",
                    "type": "bug",
                    "spec_file": ".session/specs/BUG-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "BUG-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing description and fix_approach
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Description" in result["missing_sections"]
        assert "Fix Approach" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_integration_test_sections(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria checks integration test-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "TEST-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "TEST-001": {
                    "id": "TEST-001",
                    "type": "integration_test",
                    "spec_file": ".session/specs/TEST-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "TEST-001.md"
        spec_file.write_text("# Spec")

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing scope and test_scenarios
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Scope" in result["missing_sections"]
        assert "Test Scenarios (at least 1)" in result["missing_sections"]

    def test_validate_work_item_criteria_passes_complete_feature_spec(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=True for complete feature spec."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
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

        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Feature overview",
            "implementation_details": "Details",
        }
        with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "Work item spec is complete"


class TestCheckTrackingUpdates:
    """Test suite for check_tracking_updates method."""

    def test_check_tracking_updates_returns_no_changes(self, temp_session_dir):
        """Test check_tracking_updates returns passed=True with no changes message."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.check_tracking_updates()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "No tracking updates"
        assert result["changes"]["stack"]["has_changes"] is False
        assert result["changes"]["tree"]["has_changes"] is False

    def test_check_tracking_updates_detects_changes(self, temp_session_dir):
        """Test check_tracking_updates detects changes when stack or tree modified."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("solokit.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch.object(
            validator,
            "_check_stack_changes",
            return_value={"has_changes": True, "message": "Stack updated"},
        ):
            result = validator.check_tracking_updates()

        # Assert
        assert result["passed"] is True  # Always passes
        assert result["message"] == "Tracking updates detected"
        assert result["changes"]["stack"]["has_changes"] is True


class TestValidate:
    """Test suite for full validate workflow."""

    def test_validate_all_checks_pass(self, temp_session_dir, mock_quality_gates, capsys):
        """Test validate returns ready=True when all checks pass."""
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

        # Mock all checks to pass
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
        assert result["ready"] is True
        assert all(check["passed"] for check in result["checks"].values())

        # Check console output
        captured = capsys.readouterr()
        assert "Session ready to complete!" in captured.out

    def test_validate_raises_exception_on_git_error(self, temp_session_dir, mock_quality_gates):
        """Test validate raises exception when git check fails."""
        # Arrange
        project_root = temp_session_dir.parent

        with patch("solokit.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock git check to fail
        mock_status = CommandResult(
            returncode=128, stdout="", stderr="", command=["git", "status"], duration_seconds=0.1
        )

        # Act & Assert
        with patch.object(validator.runner, "run", return_value=mock_status):
            with pytest.raises(NotAGitRepoError):
                validator.validate()

    def test_validate_passes_auto_fix_parameter(self, temp_session_dir, mock_quality_gates):
        """Test validate passes auto_fix parameter to quality gates preview."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create minimal session setup
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

        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Overview",
            "implementation_details": "Details",
        }

        # Act
        with patch.object(validator.runner, "run", side_effect=[mock_status, mock_branch]):
            with patch("solokit.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
                validator.validate(auto_fix=True)

        # Assert
        mock_quality_gates.run_linting.assert_called_with(auto_fix=True)
        mock_quality_gates.run_formatting.assert_called_with(auto_fix=True)
