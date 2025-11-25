#!/usr/bin/env python3
"""
Unit tests for session_complete.py

Tests cover:
- Status and work item loading
- Quality gates integration
- Tracking updates (subprocess calls)
- Learning management (extraction, curation)
- Git workflow completion
- Summary generation
- Uncommitted changes check
- Main function workflow
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from solokit.core.command_runner import CommandResult
from solokit.session.complete import (
    auto_extract_learnings,
    check_uncommitted_changes,
    complete_git_workflow,
    extract_learnings_from_session,
    generate_commit_message,
    generate_deployment_summary,
    generate_integration_test_summary,
    generate_summary,
    # load_curation_config,  # Removed - now in ConfigManager (tested in test_config.py)
    load_status,
    load_work_items,
    main,
    record_session_commits,
    run_quality_gates,
    trigger_curation_if_needed,
    update_all_tracking,
)


class TestLoadStatus:
    """Tests for load_status function."""

    def test_load_status_success(self, tmp_path, monkeypatch):
        """Test successful loading of session status."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        status_file = session_dir / "status_update.json"

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        status_file.write_text(json.dumps(status_data))

        # Act
        result = load_status()

        # Assert
        assert result == status_data
        assert result["current_session"] == 5
        assert result["current_work_item"] == "feature-001"

    def test_load_status_file_not_found(self, tmp_path, monkeypatch):
        """Test load_status returns None when file doesn't exist."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Act
        result = load_status()

        # Assert
        assert result is None

    def test_load_status_invalid_json(self, tmp_path, monkeypatch):
        """Test load_status raises error for invalid JSON."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        status_file = session_dir / "status_update.json"
        status_file.write_text("invalid json{")

        # Act & Assert
        with pytest.raises(FileOperationError, match="File parse operation failed"):
            load_status()


class TestLoadWorkItems:
    """Tests for load_work_items function."""

    def test_load_work_items_success(self, tmp_path, monkeypatch):
        """Test successful loading of work items."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"

        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test Feature", "type": "feature", "status": "in_progress"}
            },
            "metadata": {},
        }
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        result = load_work_items()

        # Assert
        assert result == work_items_data
        assert "feature-001" in result["work_items"]

    def test_load_work_items_file_not_found(self, tmp_path, monkeypatch):
        """Test load_work_items raises error when file doesn't exist."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        monkeypatch.chdir(tmp_path)

        # Act & Assert
        with pytest.raises(FileOperationError, match="File read operation failed"):
            load_work_items()

    def test_load_work_items_invalid_json(self, tmp_path, monkeypatch):
        """Test load_work_items raises error for invalid JSON."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text("not valid json")

        # Act & Assert
        with pytest.raises(FileOperationError, match="File parse operation failed"):
            load_work_items()


class TestRunQualityGates:
    """Tests for run_quality_gates function."""

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_all_pass(self, mock_gates_class):
        """Test run_quality_gates when all gates pass."""
        # Arrange
        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        mock_gates.config = {
            "test_execution": {"required": True},
            "security": {"required": True},
            "linting": {"required": True},
            "formatting": {"required": True},
            "documentation": {"required": True},
            "context7": {"required": True},
        }

        # All gates pass
        mock_gates.run_tests.return_value = (True, {"status": "passed", "coverage": 85})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "All gates passed"

        # Act
        results, all_passed, failed_gates = run_quality_gates()

        # Assert
        assert all_passed is True
        assert failed_gates == []
        assert "tests" in results
        assert "security" in results
        assert mock_gates.run_tests.called
        assert mock_gates.run_security_scan.called

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_test_failure(self, mock_gates_class):
        """Test run_quality_gates when tests fail."""
        # Arrange
        from solokit.core.config import QualityGatesConfig

        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        mock_gates.config = QualityGatesConfig()  # Uses default values with all required=True

        mock_gates.run_tests.return_value = (False, {"status": "failed", "failed": 5})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "Tests failed"
        mock_gates.get_remediation_guidance.return_value = "Fix failing tests"

        # Act
        results, all_passed, failed_gates = run_quality_gates()

        # Assert
        assert all_passed is False
        assert "tests" in failed_gates
        assert mock_gates.get_remediation_guidance.called

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_security_failure(self, mock_gates_class):
        """Test run_quality_gates when security scan fails."""
        # Arrange
        from solokit.core.config import QualityGatesConfig

        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        mock_gates.config = QualityGatesConfig()  # Uses default values with all required=True

        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (False, {"status": "failed", "issues": 3})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "Security issues found"
        mock_gates.get_remediation_guidance.return_value = "Fix security issues"

        # Act
        results, all_passed, failed_gates = run_quality_gates()

        # Assert
        assert all_passed is False
        assert "security" in failed_gates
        assert results["security"]["issues"] == 3

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_multiple_failures(self, mock_gates_class):
        """Test run_quality_gates with multiple gate failures."""
        # Arrange
        from dataclasses import replace

        from solokit.core.config import QualityGatesConfig

        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        # Make linting and formatting required for this test
        config = QualityGatesConfig()
        config = replace(
            config,
            linting=replace(config.linting, required=True),
            formatting=replace(config.formatting, required=True),
        )
        mock_gates.config = config

        mock_gates.run_tests.return_value = (False, {"status": "failed"})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (False, {"status": "failed"})
        mock_gates.run_formatting.return_value = (False, {"status": "failed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "Multiple failures"
        mock_gates.get_remediation_guidance.return_value = "Fix all issues"

        # Act
        results, all_passed, failed_gates = run_quality_gates()

        # Assert
        assert all_passed is False
        assert len(failed_gates) == 3
        assert "tests" in failed_gates
        assert "linting" in failed_gates
        assert "formatting" in failed_gates

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_with_work_item(self, mock_gates_class):
        """Test run_quality_gates with work item for custom validations."""
        # Arrange
        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        mock_gates.config = {
            "test_execution": {"required": True},
            "security": {"required": True},
            "linting": {"required": True},
            "formatting": {"required": True},
            "documentation": {"required": True},
            "context7": {"required": True},
        }

        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.run_custom_validations.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "All passed"

        work_item = {"type": "integration_test", "title": "Test"}

        # Act
        results, all_passed, failed_gates = run_quality_gates(work_item)

        # Assert
        assert all_passed is True
        assert "custom" in results
        mock_gates.run_custom_validations.assert_called_once_with(work_item)

    @patch("solokit.session.complete.QualityGates")
    def test_run_quality_gates_non_required_gate_failure(self, mock_gates_class):
        """Test run_quality_gates when non-required gate fails."""
        # Arrange
        from dataclasses import replace

        from solokit.core.config import QualityGatesConfig

        mock_gates = MagicMock()
        mock_gates_class.return_value = mock_gates
        # Make security not required for this test
        config = QualityGatesConfig()
        config = replace(config, security=replace(config.security, required=False))
        mock_gates.config = config

        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (
            False,
            {"status": "failed"},
        )  # Fails but not required
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "All required gates passed"

        # Act
        results, all_passed, failed_gates = run_quality_gates()

        # Assert
        assert all_passed is True  # Should still pass since security not required
        assert failed_gates == []


class TestUpdateAllTracking:
    """Tests for update_all_tracking function."""

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.session.complete.Path")
    def test_update_tracking_success(self, mock_path, mock_run):
        """Test successful tracking update."""
        # Arrange
        mock_path.return_value.parent = Path("/fake/scripts")
        mock_result = CommandResult(
            returncode=0,
            stdout="Stack updated successfully",
            stderr="",
            command=["python"],
            duration_seconds=0.1,
        )
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = update_all_tracking(5)

        # Assert
        assert result is True
        assert mock_runner.run.call_count == 2  # stack and tree

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.session.complete.Path")
    def test_update_tracking_stack_failure(self, mock_path, mock_run):
        """Test tracking update when stack update fails."""
        # Arrange
        mock_path.return_value.parent = Path("/fake/scripts")

        def run_side_effect(*args, **kwargs):
            if "generate_stack.py" in str(args[0]):
                result = CommandResult(
                    returncode=1,
                    stdout="",
                    stderr="Stack update error",
                    command=["python"],
                    duration_seconds=0.1,
                )
                return result
            else:
                result = CommandResult(
                    returncode=0,
                    stdout="Tree updated",
                    stderr="",
                    command=["python"],
                    duration_seconds=0.1,
                )
                return result

        mock_runner = Mock()

        mock_runner.run.side_effect = run_side_effect

        mock_run.return_value = mock_runner

        # Act
        result = update_all_tracking(5)

        # Assert
        assert result is True  # Function returns True even on failure

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.session.complete.Path")
    def test_update_tracking_tree_failure(self, mock_path, mock_run):
        """Test tracking update when tree update fails."""
        # Arrange
        mock_path.return_value.parent = Path("/fake/scripts")

        def run_side_effect(*args, **kwargs):
            if "generate_tree.py" in str(args[0]):
                result = CommandResult(
                    returncode=1,
                    stdout="",
                    stderr="Tree update error",
                    command=["python"],
                    duration_seconds=0.1,
                )
                return result
            else:
                result = CommandResult(
                    returncode=0,
                    stdout="Stack updated",
                    stderr="",
                    command=["python"],
                    duration_seconds=0.1,
                )
                return result

        mock_runner = Mock()

        mock_runner.run.side_effect = run_side_effect

        mock_run.return_value = mock_runner

        # Act
        result = update_all_tracking(5)

        # Assert
        assert result is True

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.session.complete.Path")
    def test_update_tracking_timeout(self, mock_path, mock_run):
        """Test tracking update handles timeout exception."""
        # Arrange
        mock_path.return_value.parent = Path("/fake/scripts")
        mock_runner = Mock()

        mock_runner.run.return_value = CommandResult(
            returncode=124,
            stdout="",
            stderr="Timeout",
            command=["python"],
            duration_seconds=30.0,
            timed_out=True,
        )

        mock_run.return_value = mock_runner

        # Act
        result = update_all_tracking(5)

        # Assert
        assert result is True  # Function continues despite exception


class TestTriggerCurationIfNeeded:
    """Tests for trigger_curation_if_needed function."""

    @patch("solokit.core.config.get_config_manager")
    def test_trigger_curation_disabled(self, mock_get_config_manager):
        """Test trigger_curation_if_needed when auto_curate is disabled."""
        # Arrange
        from solokit.core.config import CurationConfig

        mock_config_manager = MagicMock()
        mock_config_manager.curation = CurationConfig(auto_curate=False)
        mock_get_config_manager.return_value = mock_config_manager

        # Act
        trigger_curation_if_needed(5)

        # Assert - should return early, no subprocess call
        mock_config_manager.load_config.assert_called_once()

    @patch("solokit.learning.curator.LearningsCurator")
    @patch("solokit.core.config.get_config_manager")
    def test_trigger_curation_triggered(self, mock_get_config_manager, mock_curator_class):
        """Test trigger_curation_if_needed triggers curation."""
        # Arrange
        from solokit.core.config import CurationConfig

        mock_config_manager = MagicMock()
        mock_config_manager.curation = CurationConfig(auto_curate=True, frequency=5)
        mock_get_config_manager.return_value = mock_config_manager

        mock_curator = Mock()
        mock_curator_class.return_value = mock_curator

        # Act
        trigger_curation_if_needed(5)  # 5 % 5 == 0

        # Assert
        mock_curator_class.assert_called_once()
        mock_curator.curate.assert_called_once_with(dry_run=False)

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.core.config.get_config_manager")
    def test_trigger_curation_not_time_yet(self, mock_get_config_manager, mock_run):
        """Test trigger_curation_if_needed when not time to curate."""
        # Arrange
        from solokit.core.config import CurationConfig

        mock_config_manager = MagicMock()
        mock_config_manager.curation = CurationConfig(auto_curate=True, frequency=5)
        mock_get_config_manager.return_value = mock_config_manager

        mock_runner = Mock()
        mock_run.return_value = mock_runner

        # Act
        trigger_curation_if_needed(3)  # 3 % 5 != 0

        # Assert
        mock_runner.run.assert_not_called()

    @patch("solokit.learning.curator.LearningsCurator")
    @patch("solokit.core.config.get_config_manager")
    def test_trigger_curation_failure(self, mock_get_config_manager, mock_curator_class):
        """Test trigger_curation_if_needed handles curation failure."""
        # Arrange
        from solokit.core.config import CurationConfig

        mock_config_manager = MagicMock()
        mock_config_manager.curation = CurationConfig(auto_curate=True, frequency=5)
        mock_get_config_manager.return_value = mock_config_manager

        mock_curator = Mock()
        mock_curator.curate.side_effect = Exception("Curation error")
        mock_curator_class.return_value = mock_curator

        # Act
        trigger_curation_if_needed(5)

        # Assert - should not raise exception
        mock_curator_class.assert_called_once()
        mock_curator.curate.assert_called_once_with(dry_run=False)

    @patch("solokit.session.complete.CommandRunner")
    @patch("solokit.core.config.get_config_manager")
    def test_trigger_curation_exception(self, mock_get_config_manager, mock_run):
        """Test trigger_curation_if_needed handles exceptions gracefully."""
        # Arrange
        from solokit.core.config import CurationConfig

        mock_config_manager = MagicMock()
        mock_config_manager.curation = CurationConfig(auto_curate=True, frequency=5)
        mock_get_config_manager.return_value = mock_config_manager

        mock_runner = Mock()

        mock_runner.run.return_value = CommandResult(
            returncode=124,
            stdout="",
            stderr="Timeout",
            command=["python"],
            duration_seconds=30.0,
            timed_out=True,
        )

        mock_run.return_value = mock_runner

        # Act
        trigger_curation_if_needed(5)

        # Assert - should not raise exception


class TestAutoExtractLearnings:
    """Tests for auto_extract_learnings function."""

    def test_auto_extract_from_summary(self, tmp_path, monkeypatch):
        """Test auto-extraction from session summary."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        summary_file = tmp_path / ".session" / "history" / "session_005_summary.md"
        summary_file.parent.mkdir(parents=True)
        summary_file.write_text("Session summary content")

        mock_curator = MagicMock()
        mock_curator.extract_from_session_summary.return_value = [
            {"content": "Learning 1"},
            {"content": "Learning 2"},
        ]
        mock_curator.add_learning_if_new.side_effect = [True, True]
        mock_curator.extract_from_git_commits.return_value = []
        mock_curator.extract_from_code_comments.return_value = []

        # Mock the LearningsCurator class
        with patch("solokit.learning.curator.LearningsCurator", return_value=mock_curator):
            # Act
            result = auto_extract_learnings(5)

        # Assert
        assert result == 2

    def test_auto_extract_from_commits(self, tmp_path, monkeypatch):
        """Test auto-extraction from git commits."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_curator = MagicMock()
        mock_curator.extract_from_session_summary.return_value = []
        mock_curator.extract_from_git_commits.return_value = [{"content": "Commit learning"}]
        mock_curator.add_learning_if_new.return_value = True
        mock_curator.extract_from_code_comments.return_value = []

        # Mock the LearningsCurator class
        with patch("solokit.learning.curator.LearningsCurator", return_value=mock_curator):
            # Act
            result = auto_extract_learnings(5)

        # Assert
        assert result == 1

    def test_auto_extract_from_code(self, tmp_path, monkeypatch):
        """Test auto-extraction from code comments."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_curator = MagicMock()
        mock_curator.extract_from_session_summary.return_value = []
        mock_curator.extract_from_git_commits.return_value = []
        mock_curator.extract_from_code_comments.return_value = [
            {"content": "Code comment learning"}
        ]
        mock_curator.add_learning_if_new.return_value = True

        # Mock the LearningsCurator class
        with patch("solokit.learning.curator.LearningsCurator", return_value=mock_curator):
            # Act
            result = auto_extract_learnings(5)

        # Assert
        assert result == 1

    def test_auto_extract_no_new_learnings(self, tmp_path, monkeypatch):
        """Test auto-extraction when all learnings are duplicates."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_curator = MagicMock()
        mock_curator.extract_from_session_summary.return_value = [{"content": "Dup"}]
        mock_curator.add_learning_if_new.return_value = False  # Duplicate
        mock_curator.extract_from_git_commits.return_value = []
        mock_curator.extract_from_code_comments.return_value = []

        # Use sys.modules patching instead of __import__ to avoid recursion issues
        mock_module = MagicMock()
        mock_module.LearningsCurator = lambda: mock_curator

        with patch.dict("sys.modules", {"learning_curator": mock_module}):
            # Act
            result = auto_extract_learnings(5)

        # Assert
        assert result == 0

    def test_auto_extract_failure(self, tmp_path, monkeypatch):
        """Test auto-extraction handles import failure."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Create a mock that raises ImportError when LearningsCurator is accessed
        mock_module = MagicMock()
        mock_module.LearningsCurator = MagicMock(side_effect=ImportError("Module not found"))

        # Use sys.modules patching - when the module exists but class instantiation fails
        with patch.dict("sys.modules", {"learning_curator": mock_module}):
            # Act
            result = auto_extract_learnings(5)

        # Assert - should return 0 on failure (graceful handling)
        assert result == 0


class TestExtractLearningsFromSession:
    """Tests for extract_learnings_from_session function."""

    def test_extract_from_file_success(self, tmp_path):
        """Test extraction from learnings file."""
        # Arrange
        learnings_file = tmp_path / "learnings.txt"
        learnings_file.write_text("Learning 1\nLearning 2\nLearning 3\n")

        # Act
        result = extract_learnings_from_session(str(learnings_file))

        # Assert
        assert len(result) == 3
        assert "Learning 1" in result
        assert not learnings_file.exists()  # File should be deleted

    def test_extract_from_file_not_found(self, tmp_path):
        """Test extraction when learnings file doesn't exist."""
        # Arrange
        learnings_file = tmp_path / "missing.txt"

        # Act
        with patch("sys.stdin.isatty", return_value=False):
            result = extract_learnings_from_session(str(learnings_file))

        # Assert
        assert result == []

    def test_extract_from_file_with_empty_lines(self, tmp_path):
        """Test extraction filters empty lines from file."""
        # Arrange
        learnings_file = tmp_path / "learnings.txt"
        learnings_file.write_text("Learning 1\n\n\nLearning 2\n  \n")

        # Act
        result = extract_learnings_from_session(str(learnings_file))

        # Assert
        assert len(result) == 2
        assert "Learning 1" in result
        assert "Learning 2" in result

    @patch("builtins.input", side_effect=["Learning 1", "Learning 2", "done"])
    @patch("sys.stdin.isatty", return_value=True)
    def test_extract_manual_interactive(self, mock_isatty, mock_input):
        """Test manual extraction in interactive mode."""
        # Act
        result = extract_learnings_from_session()

        # Assert
        assert len(result) == 2
        assert "Learning 1" in result
        assert "Learning 2" in result

    @patch("sys.stdin.isatty", return_value=False)
    def test_extract_manual_non_interactive(self, mock_isatty):
        """Test manual extraction in non-interactive mode skips input."""
        # Act
        result = extract_learnings_from_session()

        # Assert
        assert result == []

    @patch("builtins.input", side_effect=["skip"])
    @patch("sys.stdin.isatty", return_value=True)
    def test_extract_manual_skip_command(self, mock_isatty, mock_input):
        """Test skip command returns empty list."""
        # Act
        result = extract_learnings_from_session()

        # Assert
        assert result == []

    @patch("builtins.input", side_effect=["", "", "done"])
    @patch("sys.stdin.isatty", return_value=True)
    def test_extract_manual_filters_empty(self, mock_isatty, mock_input):
        """Test manual extraction filters empty strings."""
        # Act
        result = extract_learnings_from_session()

        # Assert
        assert result == []

    @patch("builtins.input", side_effect=EOFError)
    @patch("sys.stdin.isatty", return_value=True)
    def test_extract_manual_handles_eof(self, mock_isatty, mock_input):
        """Test manual extraction handles EOF gracefully."""
        # Act
        result = extract_learnings_from_session()

        # Assert
        assert result == []


class TestCompleteGitWorkflow:
    """Tests for complete_git_workflow function."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"work_items": {"feature-001": {"status": "completed"}}}',
    )
    @patch("solokit.git.integration.GitWorkflow")
    def test_complete_git_workflow_success(self, mock_git_workflow_class, mock_file, tmp_path):
        """Test successful git workflow completion."""
        # Arrange
        mock_workflow = MagicMock()
        mock_workflow.complete_work_item.return_value = {
            "success": True,
            "message": "Work item completed",
        }
        mock_git_workflow_class.return_value = mock_workflow

        # Act
        result = complete_git_workflow("feature-001", "Commit message", 5)

        # Assert
        assert result["success"] is True

    @patch("solokit.git.integration.GitWorkflow")
    def test_complete_git_workflow_module_not_found(self, mock_git_workflow_class):
        """Test git workflow when import fails."""
        # Arrange
        mock_git_workflow_class.side_effect = ImportError("Module not found")

        # Act
        result = complete_git_workflow("feature-001", "Commit message", 5)

        # Assert
        assert result["success"] is False
        assert "error" in result["message"].lower()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"work_items": {"feature-001": {"status": "completed"}}}',
    )
    @patch("solokit.git.integration.GitWorkflow")
    def test_complete_git_workflow_with_merge(self, mock_git_workflow_class, mock_file, tmp_path):
        """Test git workflow with merge when work item completed."""
        # Arrange
        mock_workflow = MagicMock()
        mock_workflow.complete_work_item.return_value = {"success": True}
        mock_git_workflow_class.return_value = mock_workflow

        # Act
        complete_git_workflow("feature-001", "Commit", 5)

        # Assert
        mock_workflow.complete_work_item.assert_called_once()
        call_args = mock_workflow.complete_work_item.call_args
        assert call_args[1]["merge"] is True

    @patch("solokit.session.complete.Path")
    def test_complete_git_workflow_exception(self, mock_path_class):
        """Test git workflow handles exceptions."""
        # Arrange
        mock_path_class.side_effect = Exception("Unexpected error")

        # Act
        result = complete_git_workflow("feature-001", "Commit", 5)

        # Assert
        assert result["success"] is False
        assert "error" in result["message"].lower()


class TestRecordSessionCommits:
    """Tests for record_session_commits function."""

    @patch("solokit.session.complete.CommandRunner")
    def test_record_commits_success(self, mock_run, tmp_path, monkeypatch):
        """Test successful recording of session commits."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"

        work_items_data = {
            "work_items": {
                "feature-001": {"git": {"branch": "session-001-feature", "parent_branch": "main"}}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123|Commit message|2025-01-15 10:00:00"
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        record_session_commits("feature-001")

        # Assert
        with open(work_items_file) as f:
            updated_data = json.load(f)
        assert "commits" in updated_data["work_items"]["feature-001"]["git"]
        assert len(updated_data["work_items"]["feature-001"]["git"]["commits"]) == 1

    @patch("solokit.session.complete.CommandRunner")
    def test_record_commits_no_branch(self, mock_run, tmp_path, monkeypatch):
        """Test record_session_commits when work item has no git branch."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"

        work_items_data = {
            "work_items": {
                "feature-001": {
                    "git": {}  # No branch
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        mock_runner = Mock()
        mock_run.return_value = mock_runner

        # Act
        record_session_commits("feature-001")

        # Assert - should return silently without calling git
        mock_runner.run.assert_not_called()

    @patch("solokit.session.complete.CommandRunner")
    def test_record_commits_git_error(self, mock_run, tmp_path, monkeypatch):
        """Test record_session_commits handles git errors silently."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"

        work_items_data = {
            "work_items": {
                "feature-001": {"git": {"branch": "session-001", "parent_branch": "main"}}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        record_session_commits("feature-001")

        # Assert - should not raise exception

    @patch("solokit.session.complete.CommandRunner")
    def test_record_commits_parsing(self, mock_run, tmp_path, monkeypatch):
        """Test record_session_commits parses multiple commits correctly."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"

        work_items_data = {
            "work_items": {
                "feature-001": {"git": {"branch": "session-001", "parent_branch": "main"}}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "abc123|Commit 1|2025-01-15 10:00:00\ndef456|Commit 2|2025-01-15 11:00:00"
        )
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        record_session_commits("feature-001")

        # Assert
        with open(work_items_file) as f:
            updated_data = json.load(f)
        commits = updated_data["work_items"]["feature-001"]["git"]["commits"]
        assert len(commits) == 2
        assert commits[0]["sha"] == "abc123"
        assert commits[1]["message"] == "Commit 2"


class TestGenerateCommitMessage:
    """Tests for generate_commit_message function."""

    @patch("solokit.session.complete.parse_spec_file")
    def test_generate_commit_message_completed(self, mock_parse):
        """Test commit message generation for completed work item."""
        # Arrange
        status = {"current_session": 5}
        work_item = {"type": "feature", "title": "Add user authentication", "status": "completed"}
        mock_parse.return_value = {"rationale": "Users need secure login"}

        # Act
        result = generate_commit_message(status, work_item)

        # Assert
        assert "Session 005: Feature - Add user authentication" in result
        assert "✅ Work item completed" in result
        assert "Users need secure login" in result
        assert "Claude Code" in result

    @patch("solokit.session.complete.parse_spec_file")
    def test_generate_commit_message_in_progress(self, mock_parse):
        """Test commit message generation for in-progress work item."""
        # Arrange
        status = {"current_session": 3}
        work_item = {"type": "bug", "title": "Fix login error", "status": "in_progress"}
        mock_parse.return_value = {"rationale": "Login fails on mobile"}

        # Act
        result = generate_commit_message(status, work_item)

        # Assert
        assert "Session 003: Bug - Fix login error" in result
        assert "🚧 Work in progress" in result
        assert "Login fails on mobile" in result

    @patch("solokit.session.complete.parse_spec_file")
    def test_generate_commit_message_with_long_rationale(self, mock_parse):
        """Test commit message truncates long rationale."""
        # Arrange
        status = {"current_session": 1}
        work_item = {"type": "refactor", "title": "Refactor database layer", "status": "completed"}
        long_rationale = "A" * 250  # Longer than 200 chars
        mock_parse.return_value = {"rationale": long_rationale}

        # Act
        result = generate_commit_message(status, work_item)

        # Assert
        assert "..." in result  # Should be truncated
        assert len(result.split("\n\n")[1]) < 210  # Should be trimmed

    @patch("solokit.session.complete.parse_spec_file")
    def test_generate_commit_message_no_spec(self, mock_parse):
        """Test commit message when spec file not found."""
        # Arrange
        status = {"current_session": 2}
        work_item = {"type": "feature", "title": "Add feature", "status": "completed"}
        mock_parse.side_effect = FileNotFoundError

        # Act
        result = generate_commit_message(status, work_item)

        # Assert
        assert "Session 002: Feature - Add feature" in result
        assert "✅ Work item completed" in result
        # No rationale section


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_generate_summary_basic(self):
        """Test basic summary generation."""
        # Arrange
        status = {"current_session": 5, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {"feature-001": {"title": "Test Feature", "status": "completed"}}
        }
        gate_results = {
            "tests": {"status": "passed", "coverage": 85},
            "security": {"status": "passed"},
        }

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Session 5 Summary" in result
        assert "feature-001" in result
        assert "Test Feature" in result
        assert "Tests: ✓ PASSED" in result
        assert "Coverage: 85%" in result

    def test_generate_summary_with_learnings(self):
        """Test summary generation with learnings."""
        # Arrange
        status = {"current_session": 3, "current_work_item": "bug-001"}
        work_items_data = {"work_items": {"bug-001": {"title": "Fix bug", "status": "completed"}}}
        gate_results = {"tests": {"status": "passed"}}
        learnings = ["Learning 1", "Learning 2"]

        # Act
        result = generate_summary(status, work_items_data, gate_results, learnings)

        # Assert
        assert "Learnings Captured" in result
        assert "Learning 1" in result
        assert "Learning 2" in result

    def test_generate_summary_with_security_issues(self):
        """Test summary includes security issue counts."""
        # Arrange
        status = {"current_session": 2, "current_work_item": "feature-002"}
        work_items_data = {
            "work_items": {
                "feature-002": {"title": "Feature", "status": "in_progress", "type": "feature"}
            }
        }
        gate_results = {
            "tests": {"status": "passed"},
            "security": {"status": "failed", "by_severity": {"high": 2, "medium": 5}},
        }

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Security: ✗ FAILED" in result
        assert "high: 2" in result
        assert "medium: 5" in result

    def test_generate_summary_with_skipped_gate(self):
        """Test summary handles skipped gates."""
        # Arrange
        status = {"current_session": 1, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {"feature-001": {"title": "Feature", "status": "completed"}}
        }
        gate_results = {"tests": {"status": "passed"}, "linting": {"status": "skipped"}}

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Linting: ⊘ SKIPPED" in result

    @patch("solokit.session.complete.CommandRunner")
    def test_generate_summary_with_commits(self, mock_run):
        """Test summary includes commit details (Enhancement #11)."""
        # Arrange
        status = {"current_session": 1, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {
                "feature-001": {
                    "title": "Feature",
                    "status": "completed",
                    "git": {
                        "commits": [
                            {
                                "sha": "abc1234567890",
                                "message": "feat: Add feature X",
                                "timestamp": "2025-10-26T10:00:00",
                            }
                        ]
                    },
                }
            }
        }
        gate_results = {"tests": {"status": "passed"}}

        # Mock git diff --stat
        mock_runner = Mock()
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout=" file1.py | 10 +++++-----\n 1 file changed, 5 insertions(+), 5 deletions(-)",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )
        mock_run.return_value = mock_runner

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Commits Made" in result
        assert "abc1234" in result  # Short SHA
        assert "feat: Add feature X" in result
        assert "Files changed:" in result
        assert "file1.py" in result

    @patch("solokit.session.complete.CommandRunner")
    def test_generate_summary_with_multiline_commit(self, mock_run):
        """Test summary preserves multi-line commit messages (Enhancement #11)."""
        # Arrange
        status = {"current_session": 1, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {
                "feature-001": {
                    "title": "Feature",
                    "status": "completed",
                    "git": {
                        "commits": [
                            {
                                "sha": "abc1234567890",
                                "message": "feat: Add feature X\n\nAdded comprehensive implementation\nwith tests and documentation",
                                "timestamp": "2025-10-26T10:00:00",
                            }
                        ]
                    },
                }
            }
        }
        gate_results = {"tests": {"status": "passed"}}
        mock_runner = Mock()
        mock_runner.run.return_value = CommandResult(
            returncode=0, stdout="", stderr="", command=["git"], duration_seconds=0.1
        )
        mock_run.return_value = mock_runner

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Commits Made" in result
        assert "feat: Add feature X" in result
        assert "Added comprehensive implementation" in result
        assert "with tests and documentation" in result

    def test_generate_summary_no_commits(self):
        """Test summary works when no commits present (Enhancement #11)."""
        # Arrange
        status = {"current_session": 1, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {"feature-001": {"title": "Feature", "status": "completed", "git": {}}}
        }
        gate_results = {"tests": {"status": "passed"}}

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert
        assert "Commits Made" not in result
        assert "Session 1 Summary" in result  # Summary still generated

    @patch("solokit.session.complete.CommandRunner")
    def test_generate_summary_git_diff_fails_gracefully(self, mock_run):
        """Test summary handles git diff failure gracefully (Enhancement #11)."""
        # Arrange
        status = {"current_session": 1, "current_work_item": "feature-001"}
        work_items_data = {
            "work_items": {
                "feature-001": {
                    "title": "Feature",
                    "status": "completed",
                    "git": {
                        "commits": [
                            {
                                "sha": "abc1234567890",
                                "message": "feat: Add feature X",
                                "timestamp": "2025-10-26T10:00:00",
                            }
                        ]
                    },
                }
            }
        }
        gate_results = {"tests": {"status": "passed"}}

        # Mock git diff failure
        mock_runner = Mock()
        mock_runner.run.return_value = CommandResult(
            returncode=1, stdout="", stderr="", command=["git"], duration_seconds=0.1
        )
        mock_run.return_value = mock_runner

        # Act
        result = generate_summary(status, work_items_data, gate_results, None)

        # Assert - Should still include commit but no file stats
        assert "Commits Made" in result
        assert "abc1234" in result
        assert "feat: Add feature X" in result
        # File stats section should not crash, just be omitted


class TestGenerateIntegrationTestSummary:
    """Tests for generate_integration_test_summary function."""

    def test_integration_summary_not_integration_test(self):
        """Test integration summary returns empty for non-integration work items."""
        # Arrange
        work_item = {"type": "feature", "title": "Regular feature"}
        gate_results = {}

        # Act
        result = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert result == ""

    def test_integration_summary_with_results(self):
        """Test integration summary with test results."""
        # Arrange
        work_item = {"type": "integration_test", "title": "API Tests"}
        gate_results = {
            "integration_tests": {
                "integration_tests": {
                    "passed": 25,
                    "failed": 2,
                    "skipped": 1,
                    "total_duration": 45.5,
                }
            }
        }

        # Act
        result = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "Integration Test Results" in result
        assert "Passed: 25" in result
        assert "Failed: 2" in result
        assert "Duration: 45.50s" in result

    def test_integration_summary_with_performance(self):
        """Test integration summary with performance benchmarks."""
        # Arrange
        work_item = {"type": "integration_test"}
        gate_results = {
            "integration_tests": {
                "performance_benchmarks": {
                    "load_test": {
                        "latency": {"p50": 100, "p95": 250, "p99": 500},
                        "throughput": {"requests_per_sec": 1000},
                    },
                    "regression_detected": True,
                }
            }
        }

        # Act
        result = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "Performance Benchmarks" in result
        assert "p50 latency: 100ms" in result
        assert "p95 latency: 250ms" in result
        assert "Throughput: 1000 req/s" in result
        assert "Performance regression detected" in result

    def test_integration_summary_with_api_contracts(self):
        """Test integration summary with API contract validation."""
        # Arrange
        work_item = {"type": "integration_test"}
        gate_results = {
            "integration_tests": {
                "api_contracts": {
                    "contracts_validated": 15,
                    "breaking_changes": [
                        {"message": "Field removed from User API"},
                        {"message": "Endpoint /v1/old deprecated"},
                    ],
                }
            }
        }

        # Act
        result = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "API Contract Validation" in result
        assert "Contracts validated: 15" in result
        assert "Breaking changes detected: 2" in result
        assert "Field removed from User API" in result


class TestGenerateDeploymentSummary:
    """Tests for generate_deployment_summary function."""

    def test_deployment_summary_not_deployment(self):
        """Test deployment summary returns empty for non-deployment work items."""
        # Arrange
        work_item = {"type": "feature"}
        gate_results = {}

        # Act
        result = generate_deployment_summary(work_item, gate_results)

        # Assert
        assert result == ""

    def test_deployment_summary_with_results(self):
        """Test deployment summary includes framework sections."""
        # Arrange
        work_item = {"type": "deployment"}
        gate_results = {"gates": [{"name": "Environment Validation", "passed": True}]}

        # Act
        result = generate_deployment_summary(work_item, gate_results)

        # Assert
        assert "DEPLOYMENT RESULTS" in result
        assert "Deployment Execution" in result
        assert "Smoke Tests" in result
        assert "Environment Validation" in result
        assert "✓ PASSED" in result

    def test_deployment_summary_validation_failed(self):
        """Test deployment summary shows failed validation."""
        # Arrange
        work_item = {"type": "deployment"}
        gate_results = {"gates": [{"name": "Environment Validation", "passed": False}]}

        # Act
        result = generate_deployment_summary(work_item, gate_results)

        # Assert
        assert "✗ FAILED" in result


class TestCheckUncommittedChanges:
    """Tests for check_uncommitted_changes function."""

    @patch("solokit.session.complete.CommandRunner")
    def test_no_uncommitted_changes(self, mock_run):
        """Test check_uncommitted_changes returns True when no changes."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is True

    @patch("builtins.input", return_value="y")
    @patch("sys.stdin.isatty", return_value=True)
    @patch("solokit.session.complete.CommandRunner")
    def test_uncommitted_changes_user_override(self, mock_run, mock_isatty, mock_input):
        """Test user can override uncommitted changes check."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = " M src/main.py\n"
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is True

    @patch("builtins.input", return_value="n")
    @patch("sys.stdin.isatty", return_value=True)
    @patch("solokit.session.complete.CommandRunner")
    def test_uncommitted_changes_user_abort(self, mock_run, mock_isatty, mock_input):
        """Test user can abort on uncommitted changes."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = " M src/main.py\n"
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is False

    @patch("sys.stdin.isatty", return_value=False)
    @patch("solokit.session.complete.CommandRunner")
    def test_uncommitted_changes_non_interactive(self, mock_run, mock_isatty):
        """Test non-interactive mode returns False on uncommitted changes."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = " M src/main.py\n"
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is False

    @patch("solokit.session.complete.CommandRunner")
    def test_uncommitted_changes_only_session_tracking(self, mock_run):
        """Test check passes when only session tracking files changed."""
        # Arrange
        mock_result = MagicMock()
        mock_result.stdout = (
            " M .session/tracking/status_update.json\n M .session/briefings/session_005.md\n"
        )
        mock_runner = Mock()

        mock_runner.run.return_value = mock_result

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is True

    @patch("solokit.session.complete.CommandRunner")
    def test_uncommitted_changes_exception(self, mock_run):
        """Test check returns True on exception."""
        # Arrange
        mock_runner = Mock()

        mock_runner.run.side_effect = Exception("Git error")

        mock_run.return_value = mock_runner

        # Act
        result = check_uncommitted_changes()

        # Assert
        assert result is True  # Don't block on errors


# Interactive mode tests removed for Claude Code integration
# Interactive completion prompt is now handled by /end slash command using AskUserQuestion
# Removed tests:
# - test_prompt_choice_complete
# - test_prompt_choice_incomplete
# - test_prompt_choice_cancel
# - test_prompt_default_choice
# - test_prompt_invalid_input_retry
# - test_prompt_non_interactive_defaults_true
# - test_prompt_displays_work_item_title


class TestMain:
    """Tests for main function."""

    @patch("solokit.session.complete.load_status")
    def test_main_no_active_session(self, mock_load_status):
        """Test main exits when no active session."""
        # Arrange
        mock_load_status.return_value = None

        # Act
        with patch("sys.argv", ["session_complete.py"]):
            result = main()

        # Assert
        assert result == 1

    @patch("solokit.session.complete.auto_extract_learnings")
    @patch("solokit.session.complete.record_session_commits")
    @patch("solokit.session.complete.complete_git_workflow")
    @patch("solokit.session.complete.generate_commit_message")
    @patch("solokit.session.complete.extract_learnings_from_session")
    @patch("solokit.session.complete.trigger_curation_if_needed")
    @patch("solokit.session.complete.update_all_tracking")
    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    @patch("builtins.input", return_value="1")  # Changed from "y" to "1" for new prompt
    @patch("sys.stdin.isatty", return_value=True)
    def test_main_success_complete(
        self,
        mock_isatty,
        mock_input,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        mock_update_tracking,
        mock_trigger_curation,
        mock_extract_learnings,
        mock_generate_commit,
        mock_complete_git,
        mock_record_commits,
        mock_auto_extract,
        tmp_path,
        monkeypatch,
    ):
        """Test successful main execution with work item completion."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        history_dir = session_dir / "history"
        tracking_dir.mkdir(parents=True)
        history_dir.mkdir(parents=True)

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test Feature", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        # Write work_items.json
        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        status_file = tracking_dir / "status_update.json"
        status_file.write_text(json.dumps(status_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        mock_run_gates.return_value = ({"tests": {"status": "passed"}}, True, [])
        mock_extract_learnings.return_value = []
        mock_generate_commit.return_value = "Commit message"
        mock_complete_git.return_value = {"success": True, "message": "Success"}
        mock_auto_extract.return_value = 0

        # Act
        with patch("sys.argv", ["session_complete.py", "--complete"]):
            result = main()

        # Assert
        assert result == 0
        assert mock_run_gates.called
        assert mock_update_tracking.called

    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_uncommitted_changes_abort(
        self, mock_load_status, mock_load_work_items, mock_check_changes
    ):
        """Test main aborts when user doesn't commit changes."""
        # Arrange
        mock_load_status.return_value = {"current_session": 5, "current_work_item": "feature-001"}
        mock_load_work_items.return_value = {
            "work_items": {"feature-001": {"title": "Test", "status": "in_progress"}}
        }
        mock_check_changes.return_value = False

        # Act
        with patch("sys.argv", ["session_complete.py"]):
            result = main()

        # Assert
        assert result == 1

    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_quality_gates_fail(
        self, mock_load_status, mock_load_work_items, mock_check_changes, mock_run_gates
    ):
        """Test main exits when quality gates fail."""
        # Arrange
        mock_load_status.return_value = {"current_session": 5, "current_work_item": "feature-001"}
        mock_load_work_items.return_value = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            }
        }
        mock_check_changes.return_value = True
        mock_run_gates.return_value = ({"tests": {"status": "failed"}}, False, ["tests"])

        # Act
        with patch("sys.argv", ["session_complete.py"]):
            result = main()

        # Assert
        assert result == 1

    @patch("solokit.session.complete.auto_extract_learnings")
    @patch("solokit.session.complete.record_session_commits")
    @patch("solokit.session.complete.complete_git_workflow")
    @patch("solokit.session.complete.generate_commit_message")
    @patch("solokit.session.complete.extract_learnings_from_session")
    @patch("solokit.session.complete.trigger_curation_if_needed")
    @patch("solokit.session.complete.update_all_tracking")
    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_with_learnings_file(
        self,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        mock_update_tracking,
        mock_trigger_curation,
        mock_extract_learnings,
        mock_generate_commit,
        mock_complete_git,
        mock_record_commits,
        mock_auto_extract,
        tmp_path,
        monkeypatch,
    ):
        """Test main with learnings file argument."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        history_dir = session_dir / "history"
        tracking_dir.mkdir(parents=True)
        history_dir.mkdir(parents=True)

        learnings_file = tmp_path / "learnings.txt"
        learnings_file.write_text("Learning 1\nLearning 2")

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        status_file = tracking_dir / "status_update.json"
        status_file.write_text(json.dumps(status_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        mock_run_gates.return_value = ({"tests": {"status": "passed"}}, True, [])
        mock_extract_learnings.return_value = ["Learning 1", "Learning 2"]
        mock_generate_commit.return_value = "Commit"
        mock_complete_git.return_value = {"success": True}
        mock_auto_extract.return_value = 0

        # Mock LearningsCurator
        mock_curator = MagicMock()
        mock_curator.create_learning_entry.side_effect = lambda **kwargs: kwargs
        mock_curator.add_learning_if_new.side_effect = [True, True]

        # Use a simpler approach - just patch the module after import
        import sys as system

        mock_learning_module = MagicMock()
        mock_learning_module.LearningsCurator = lambda: mock_curator

        # Act
        with patch(
            "sys.argv",
            ["session_complete.py", "--learnings-file", str(learnings_file), "--complete"],
        ):
            with patch.dict(system.modules, {"learning_curator": mock_learning_module}):
                with patch("sys.stdin.isatty", return_value=False):
                    result = main()

        # Assert
        assert result == 0
        mock_extract_learnings.assert_called_once_with(str(learnings_file))

    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_missing_completion_flag(
        self,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        tmp_path,
        monkeypatch,
    ):
        """Test main requires --complete or --incomplete flag."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        mock_run_gates.return_value = ({"tests": {"status": "passed"}}, True, [])

        # Act - call without --complete or --incomplete flag
        with patch("sys.argv", ["session_complete.py"]):
            result = main()

        # Assert - should return error code 1
        assert result == 1

    @patch("solokit.session.complete.auto_extract_learnings")
    @patch("solokit.session.complete.record_session_commits")
    @patch("solokit.session.complete.complete_git_workflow")
    @patch("solokit.session.complete.generate_commit_message")
    @patch("solokit.session.complete.extract_learnings_from_session")
    @patch("solokit.session.complete.trigger_curation_if_needed")
    @patch("solokit.session.complete.update_all_tracking")
    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_complete_flag(
        self,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        mock_update_tracking,
        mock_trigger_curation,
        mock_extract_learnings,
        mock_generate_commit,
        mock_complete_git,
        mock_record_commits,
        mock_auto_extract,
        tmp_path,
        monkeypatch,
    ):
        """Test main with --complete flag marks work item as complete."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        history_dir = session_dir / "history"
        tracking_dir.mkdir(parents=True)
        history_dir.mkdir(parents=True)

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        status_file = tracking_dir / "status_update.json"
        status_file.write_text(json.dumps(status_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        mock_run_gates.return_value = ({"tests": {"status": "passed"}}, True, [])
        mock_extract_learnings.return_value = []
        mock_generate_commit.return_value = "Commit"
        mock_complete_git.return_value = {"success": True}
        mock_auto_extract.return_value = 0

        # Act
        with patch("sys.argv", ["session_complete.py", "--complete"]):
            result = main()

        # Assert
        assert result == 0
        # Check work item was marked complete
        with open(work_items_file) as f:
            updated_data = json.load(f)
        assert updated_data["work_items"]["feature-001"]["status"] == "completed"

    @patch("solokit.session.complete.auto_extract_learnings")
    @patch("solokit.session.complete.record_session_commits")
    @patch("solokit.session.complete.complete_git_workflow")
    @patch("solokit.session.complete.generate_commit_message")
    @patch("solokit.session.complete.extract_learnings_from_session")
    @patch("solokit.session.complete.trigger_curation_if_needed")
    @patch("solokit.session.complete.update_all_tracking")
    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_incomplete_flag_skips_quality_gate_enforcement(
        self,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        mock_update_tracking,
        mock_trigger_curation,
        mock_extract_learnings,
        mock_generate_commit,
        mock_complete_git,
        mock_record_commits,
        mock_auto_extract,
        tmp_path,
        monkeypatch,
    ):
        """Test main with --incomplete flag skips quality gate enforcement."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        history_dir = session_dir / "history"
        tracking_dir.mkdir(parents=True)
        history_dir.mkdir(parents=True)

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        status_file = tracking_dir / "status_update.json"
        status_file.write_text(json.dumps(status_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        # Quality gates FAIL but should not block with --incomplete
        mock_run_gates.return_value = ({"tests": {"status": "failed"}}, False, ["tests"])
        mock_extract_learnings.return_value = []
        mock_generate_commit.return_value = "Commit"
        mock_complete_git.return_value = {"success": True}
        mock_auto_extract.return_value = 0

        # Act
        with patch("sys.argv", ["session_complete.py", "--incomplete"]):
            result = main()

        # Assert - Should succeed even though quality gates failed
        assert result == 0
        # Check work item was kept as in-progress
        with open(work_items_file) as f:
            updated_data = json.load(f)
        assert updated_data["work_items"]["feature-001"]["status"] == "in_progress"

    @patch("solokit.session.complete.run_quality_gates")
    @patch("solokit.session.complete.check_uncommitted_changes")
    @patch("solokit.session.complete.load_work_items")
    @patch("solokit.session.complete.load_status")
    def test_main_complete_flag_enforces_quality_gates(
        self,
        mock_load_status,
        mock_load_work_items,
        mock_check_changes,
        mock_run_gates,
        tmp_path,
        monkeypatch,
    ):
        """Test main with --complete flag enforces quality gates (fails if gates fail)."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        status_data = {"current_session": 5, "current_work_item": "feature-001", "status": "active"}
        work_items_data = {
            "work_items": {
                "feature-001": {"title": "Test", "type": "feature", "status": "in_progress"}
            },
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }

        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        mock_load_status.return_value = status_data
        mock_load_work_items.return_value = work_items_data
        mock_check_changes.return_value = True
        # Quality gates FAIL and should block with --complete
        mock_run_gates.return_value = ({"tests": {"status": "failed"}}, False, ["tests"])

        # Act
        with patch("sys.argv", ["session_complete.py", "--complete"]):
            result = main()

        # Assert - Should fail because quality gates failed
        assert result == 1


class TestAdditionalCoverage:
    """Additional tests to increase coverage for uncovered lines."""

    def test_load_status_oserror(self, tmp_path, monkeypatch):
        """Test load_status handles OSError (lines 66-67)."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        status_file = session_dir / "status_update.json"
        status_file.write_text("{}")

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError, match="File read operation failed"):
                load_status()

    def test_load_work_items_oserror(self, tmp_path, monkeypatch):
        """Test load_work_items handles OSError (lines 104-105)."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError, match="File read operation failed"):
                load_work_items()

    def test_run_quality_gates_documentation_failure(self, tmp_path, monkeypatch):
        """Test run_quality_gates adds documentation to failed gates (lines 163-164)."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        mock_gates = MagicMock()
        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (False, {"status": "failed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.run_custom_validations.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "Report"
        mock_gates.get_remediation_guidance.return_value = "Guidance"
        mock_gates.config.test_execution.required = True
        mock_gates.config.security.required = True
        mock_gates.config.linting.required = True
        mock_gates.config.formatting.required = True
        mock_gates.config.documentation.required = True

        with patch("solokit.session.complete.QualityGates", return_value=mock_gates):
            results, all_passed, failed_gates = run_quality_gates({})

        assert "documentation" in failed_gates
        assert not all_passed

    def test_run_quality_gates_context7_failure_warning(self, tmp_path, monkeypatch, caplog):
        """Test run_quality_gates logs warning for Context7 failure (line 172)."""
        import logging
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)

        mock_gates = MagicMock()
        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (False, {"status": "failed"})
        mock_gates.run_custom_validations.return_value = (True, {"status": "passed"})
        mock_gates.generate_report.return_value = "Report"
        mock_gates.get_remediation_guidance.return_value = ""
        mock_gates.config.test_execution.required = True
        mock_gates.config.security.required = True
        mock_gates.config.linting.required = True
        mock_gates.config.formatting.required = True
        mock_gates.config.documentation.required = True

        with patch("solokit.session.complete.QualityGates", return_value=mock_gates):
            with caplog.at_level(logging.WARNING):
                results, all_passed, failed_gates = run_quality_gates({})

        # Context7 failure should be warning, not a failed gate
        assert "context7" not in failed_gates
        assert all_passed  # Should still pass

    def test_run_quality_gates_custom_validation_failure(self, tmp_path, monkeypatch):
        """Test run_quality_gates adds custom to failed gates (lines 179-180)."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)

        mock_gates = MagicMock()
        mock_gates.run_tests.return_value = (True, {"status": "passed"})
        mock_gates.run_security_scan.return_value = (True, {"status": "passed"})
        mock_gates.run_linting.return_value = (True, {"status": "passed"})
        mock_gates.run_formatting.return_value = (True, {"status": "passed"})
        mock_gates.validate_documentation.return_value = (True, {"status": "passed"})
        mock_gates.verify_context7_libraries.return_value = (True, {"status": "passed"})
        mock_gates.run_custom_validations.return_value = (False, {"status": "failed"})
        mock_gates.generate_report.return_value = "Report"
        mock_gates.get_remediation_guidance.return_value = "Guidance"
        mock_gates.config.test_execution.required = True
        mock_gates.config.security.required = True
        mock_gates.config.linting.required = True
        mock_gates.config.formatting.required = True
        mock_gates.config.documentation.required = True

        work_item = {"id": "test"}
        with patch("solokit.session.complete.QualityGates", return_value=mock_gates):
            results, all_passed, failed_gates = run_quality_gates(work_item)

        assert "custom" in failed_gates
        assert not all_passed

    def test_update_all_tracking_stack_exception(self, tmp_path, monkeypatch, capsys):
        """Test update_all_tracking handles stack update exception (lines 240-242)."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)

        with patch("solokit.session.complete.CommandRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.run.side_effect = RuntimeError("Stack script failed")
            mock_runner_class.return_value = mock_runner

            update_all_tracking(session_num=1)

        # Should continue despite exception
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()

    def test_extract_learnings_from_session_os_error(self, tmp_path, monkeypatch, capsys):
        """Test extract_learnings_from_session handles OSError (lines 403-406)."""
        from unittest.mock import patch

        monkeypatch.chdir(tmp_path)

        learnings_file = tmp_path / "learnings.txt"
        learnings_file.write_text("Learning 1\nLearning 2")

        # Mock open to raise OSError
        original_open = open

        def mock_open_func(path, *args, **kwargs):
            if str(learnings_file) in str(path):
                raise OSError("Permission denied")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", mock_open_func):
            result = extract_learnings_from_session(learnings_file)

        # Should return empty list on error
        assert result == []
        captured = capsys.readouterr()
        assert "Failed to read" in captured.out

    def test_complete_git_workflow_load_work_items_error(self, tmp_path, monkeypatch):
        """Test complete_git_workflow handles work items load error (lines 468-470)."""
        from unittest.mock import patch

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        # Create invalid work_items.json
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text("{invalid json}")

        with patch("solokit.git.integration.GitWorkflow"):
            result = complete_git_workflow("test_item", "Test commit", 1)

        assert result["success"] is False
        assert "Failed to load" in result["message"]

    def test_complete_git_workflow_work_item_not_found(self, tmp_path, monkeypatch):
        """Test complete_git_workflow handles work item not found (lines 473-474)."""
        from unittest.mock import patch

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text(json.dumps({"work_items": {}}))

        with patch("solokit.git.integration.GitWorkflow"):
            result = complete_git_workflow("nonexistent_item", "Test commit", 1)

        assert result["success"] is False
        assert "not found" in result["message"]

    def test_record_session_commits_work_item_not_found(self, tmp_path, monkeypatch, caplog):
        """Test record_session_commits handles missing work item (lines 507-508)."""
        import logging

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text(json.dumps({"work_items": {}}))

        with caplog.at_level(logging.WARNING):
            record_session_commits("nonexistent_item")

        # Should log warning about missing work item
        assert "not found" in caplog.text.lower()

    def test_record_session_commits_git_log_failure(self, tmp_path, monkeypatch, caplog):
        """Test record_session_commits handles git log failure (lines 530-531)."""
        import logging
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        work_items_data = {
            "work_items": {
                "test_item": {
                    "id": "test_item",
                    "status": "in_progress",
                    "git": {"branch": "feature/test", "parent_branch": "main"},
                }
            }
        }
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        with patch("solokit.session.complete.CommandRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.run.return_value = MagicMock(
                success=False, returncode=128, stderr="fatal: not a git repository"
            )
            mock_runner_class.return_value = mock_runner

            with caplog.at_level(logging.DEBUG):
                record_session_commits("test_item")

        # Should handle silently
        # No assertion needed, just verify no exception raised

    def test_record_session_commits_exception_handling(self, tmp_path, monkeypatch, caplog):
        """Test record_session_commits handles exceptions (lines 548-550)."""
        import logging

        monkeypatch.chdir(tmp_path)

        # Don't create the work_items.json file to trigger FileNotFoundError
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        with caplog.at_level(logging.DEBUG):
            # This should not raise, just log
            record_session_commits("test_item")

        # Should silently handle exception

    def test_auto_extract_learnings_no_new_learnings(self, tmp_path, monkeypatch, capsys):
        """Test auto_extract_learnings when no new learnings found (lines 367-368)."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        mock_curator = MagicMock()
        mock_curator.add_learning_if_new.return_value = False

        mock_extractor = MagicMock()
        mock_extractor.extract_from_git_diff.return_value = []
        mock_extractor.extract_from_spec_file.return_value = []

        with patch("solokit.learning.curator.LearningsCurator", return_value=mock_curator):
            with patch("solokit.learning.extractor.LearningExtractor", return_value=mock_extractor):
                # auto_extract_learnings takes only session_num parameter
                result = auto_extract_learnings(1)

        assert result == 0
        captured = capsys.readouterr()
        assert "No new learnings" in captured.out
