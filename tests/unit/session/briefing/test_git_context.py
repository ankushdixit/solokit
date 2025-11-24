#!/usr/bin/env python3
"""Unit tests for git_context.py module.

Tests cover:
- Git status checking
- Git branch status determination
- Previous work item git status finalization
- Error handling for git operations
"""

import json
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult
from solokit.core.exceptions import ErrorCode, GitError, SystemError
from solokit.core.types import GitStatus, WorkItemStatus
from solokit.session.briefing.git_context import GitContext


def create_command_result(returncode=0, stdout="", stderr=""):
    """Helper to create CommandResult with default values."""
    return CommandResult(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        command=["git"],
        duration_seconds=0.1,
    )


class TestGitContext:
    """Tests for GitContext class."""

    def test_init(self):
        """Test GitContext initialization."""
        context = GitContext()
        assert context.runner is not None

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_clean(self, mock_workflow_class):
        """Test check_git_status when working directory is clean."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.get_current_branch.return_value = "main"
        mock_workflow.check_git_status.return_value = None  # No exception = clean
        mock_workflow_class.return_value = mock_workflow

        context = GitContext()

        # Act
        result = context.check_git_status()

        # Assert
        assert result["clean"] is True
        assert result["status"] == "Working directory clean"
        assert result["branch"] == "main"

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_not_clean(self, mock_workflow_class):
        """Test check_git_status when working directory has uncommitted changes."""
        # Arrange
        from solokit.core.exceptions import WorkingDirNotCleanError

        mock_workflow = Mock()
        mock_workflow.get_current_branch.return_value = "feature-branch"

        # Create the exception with changes list
        exception = WorkingDirNotCleanError(changes=["file1.py", "file2.py"])
        mock_workflow.check_git_status.side_effect = exception
        mock_workflow_class.return_value = mock_workflow

        context = GitContext()

        # Act
        result = context.check_git_status()

        # Assert
        assert result["clean"] is False
        assert "not clean" in result["status"]
        assert result["branch"] == "feature-branch"

    @patch("solokit.git.integration.GitWorkflow", side_effect=ImportError("Module not found"))
    def test_check_git_status_import_error(self, mock_workflow_class):
        """Test check_git_status when GitWorkflow import fails."""
        # Arrange
        context = GitContext()

        # Act & Assert
        with pytest.raises(SystemError) as exc_info:
            context.check_git_status()

        assert exc_info.value.code == ErrorCode.IMPORT_FAILED
        assert "GitWorkflow" in exc_info.value.message

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_git_error_reraise(self, mock_workflow_class):
        """Test check_git_status re-raises GitError."""
        # Arrange
        mock_workflow = Mock()
        git_error = GitError(
            message="Git command failed",
            code=ErrorCode.GIT_COMMAND_FAILED,
        )
        mock_workflow.get_current_branch.side_effect = git_error
        mock_workflow_class.return_value = mock_workflow

        context = GitContext()

        # Act & Assert
        with pytest.raises(GitError) as exc_info:
            context.check_git_status()

        assert exc_info.value.code == ErrorCode.GIT_COMMAND_FAILED

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_unexpected_error(self, mock_workflow_class):
        """Test check_git_status wraps unexpected errors."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.get_current_branch.side_effect = ValueError("Unexpected error")
        mock_workflow_class.return_value = mock_workflow

        context = GitContext()

        # Act & Assert
        with pytest.raises(GitError) as exc_info:
            context.check_git_status()

        assert "Failed to check git status" in exc_info.value.message

    def test_determine_git_branch_final_status_merged(self):
        """Test determine_git_branch_final_status when branch is merged."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        merged_result = create_command_result(returncode=0, stdout="  feature-branch\n")
        context.runner.run.return_value = merged_result

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.MERGED.value

    def test_determine_git_branch_final_status_pr_merged(self):
        """Test determine_git_branch_final_status when PR is merged."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: PR exists and is merged
        pr_result = create_command_result(
            returncode=0, stdout=json.dumps([{"number": 123, "state": "MERGED"}])
        )

        context.runner.run.side_effect = [not_merged_result, pr_result]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.MERGED.value

    def test_determine_git_branch_final_status_pr_closed(self):
        """Test determine_git_branch_final_status when PR is closed (not merged)."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: PR exists and is closed
        pr_result = create_command_result(
            returncode=0, stdout=json.dumps([{"number": 123, "state": "CLOSED"}])
        )

        context.runner.run.side_effect = [not_merged_result, pr_result]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.PR_CLOSED.value

    def test_determine_git_branch_final_status_pr_open(self):
        """Test determine_git_branch_final_status when PR is open."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: PR exists and is open
        pr_result = create_command_result(
            returncode=0, stdout=json.dumps([{"number": 123, "state": "OPEN"}])
        )

        context.runner.run.side_effect = [not_merged_result, pr_result]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.PR_CREATED.value

    def test_determine_git_branch_final_status_json_decode_error(self):
        """Test determine_git_branch_final_status handles JSON decode errors gracefully."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: Invalid JSON
        pr_result = create_command_result(returncode=0, stdout="invalid json{")

        # Third check: branch exists locally
        local_branch_result = create_command_result(
            returncode=0, stdout="refs/heads/feature-branch"
        )

        context.runner.run.side_effect = [not_merged_result, pr_result, local_branch_result]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.READY_FOR_PR.value

    def test_determine_git_branch_final_status_branch_exists_locally(self):
        """Test determine_git_branch_final_status when branch exists locally."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: No PRs
        no_pr_result = create_command_result(returncode=0)

        # Third check: branch exists locally
        local_branch_result = create_command_result(
            returncode=0, stdout="refs/heads/feature-branch"
        )

        context.runner.run.side_effect = [not_merged_result, no_pr_result, local_branch_result]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.READY_FOR_PR.value

    def test_determine_git_branch_final_status_branch_exists_remotely(self):
        """Test determine_git_branch_final_status when branch exists remotely."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: No PRs
        no_pr_result = create_command_result(returncode=0)

        # Third check: branch doesn't exist locally
        no_local_branch_result = create_command_result(returncode=1)

        # Fourth check: branch exists remotely
        remote_branch_result = create_command_result(
            returncode=0, stdout="abc123 refs/heads/feature-branch"
        )

        context.runner.run.side_effect = [
            not_merged_result,
            no_pr_result,
            no_local_branch_result,
            remote_branch_result,
        ]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.READY_FOR_PR.value

    def test_determine_git_branch_final_status_deleted(self):
        """Test determine_git_branch_final_status when branch is deleted."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        # First check: not in merged branches
        not_merged_result = create_command_result(returncode=0)

        # Second check: No PRs
        no_pr_result = create_command_result(returncode=0)

        # Third check: branch doesn't exist locally
        no_local_branch_result = create_command_result(returncode=1)

        # Fourth check: branch doesn't exist remotely
        no_remote_branch_result = create_command_result(returncode=0)

        context.runner.run.side_effect = [
            not_merged_result,
            no_pr_result,
            no_local_branch_result,
            no_remote_branch_result,
        ]

        git_info = {"parent_branch": "main"}

        # Act
        result = context.determine_git_branch_final_status("feature-branch", git_info)

        # Assert
        assert result == GitStatus.DELETED.value

    def test_determine_git_branch_final_status_git_error_reraise(self):
        """Test determine_git_branch_final_status re-raises GitError."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        git_error = GitError(
            message="Git command failed",
            code=ErrorCode.GIT_COMMAND_FAILED,
        )
        context.runner.run.side_effect = git_error

        git_info = {"parent_branch": "main"}

        # Act & Assert
        with pytest.raises(GitError):
            context.determine_git_branch_final_status("feature-branch", git_info)

    def test_determine_git_branch_final_status_unexpected_error(self):
        """Test determine_git_branch_final_status wraps unexpected errors."""
        # Arrange
        context = GitContext()
        context.runner = Mock()

        context.runner.run.side_effect = ValueError("Unexpected error")

        git_info = {"parent_branch": "main"}

        # Act & Assert
        with pytest.raises(GitError) as exc_info:
            context.determine_git_branch_final_status("feature-branch", git_info)

        assert "Failed to determine git branch status" in exc_info.value.message

    def test_finalize_previous_work_item_git_status_no_previous(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status when no previous work item exists."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        context = GitContext()

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                }
            }
        }

        # Act
        result = context.finalize_previous_work_item_git_status(work_items_data, "WORK-001")

        # Assert
        assert result is None

    def test_finalize_previous_work_item_git_status_no_branch(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status when previous work item has no branch."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        context = GitContext()

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "git": {"status": GitStatus.IN_PROGRESS.value},
                },
                "WORK-002": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                },
            }
        }

        # Act
        result = context.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

        # Assert
        assert result is None

    def test_finalize_previous_work_item_git_status_success(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status successfully finalizes status."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "git": {
                        "status": GitStatus.IN_PROGRESS.value,
                        "branch": "feature-branch",
                        "parent_branch": "main",
                    },
                },
                "WORK-002": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                },
            }
        }

        # Create work_items.json
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        context = GitContext()
        context.runner = Mock()

        # Mock git checks to return merged status
        merged_result = create_command_result(returncode=0, stdout="  feature-branch\n")
        context.runner.run.return_value = merged_result

        # Act
        result = context.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

        # Assert
        assert result == "WORK-001"

        # Verify file was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["work_items"]["WORK-001"]["git"]["status"] == GitStatus.MERGED.value

    def test_finalize_previous_work_item_git_status_file_write_error(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status handles file write errors."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "git": {
                        "status": GitStatus.IN_PROGRESS.value,
                        "branch": "feature-branch",
                        "parent_branch": "main",
                    },
                },
                "WORK-002": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                },
            }
        }

        context = GitContext()
        context.runner = Mock()

        # Mock git checks to return merged status
        merged_result = create_command_result(returncode=0, stdout="  feature-branch\n")
        context.runner.run.return_value = merged_result

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Act & Assert
            with pytest.raises(SystemError) as exc_info:
                context.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

            assert exc_info.value.code == ErrorCode.FILE_OPERATION_FAILED
            assert "Permission denied" in exc_info.value.context["error"]

    def test_finalize_previous_work_item_git_status_git_error_reraise(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status re-raises GitError."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "git": {
                        "status": GitStatus.IN_PROGRESS.value,
                        "branch": "feature-branch",
                        "parent_branch": "main",
                    },
                },
                "WORK-002": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                },
            }
        }

        context = GitContext()
        context.runner = Mock()

        git_error = GitError(
            message="Git command failed",
            code=ErrorCode.GIT_COMMAND_FAILED,
        )
        context.runner.run.side_effect = git_error

        # Act & Assert
        with pytest.raises(GitError):
            context.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

    def test_finalize_previous_work_item_git_status_unexpected_error(self, tmp_path, monkeypatch):
        """Test finalize_previous_work_item_git_status when determine_git_branch_final_status raises error."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "git": {
                        "status": GitStatus.IN_PROGRESS.value,
                        "branch": "feature-branch",
                        "parent_branch": "main",
                    },
                },
                "WORK-002": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "git": {},
                },
            }
        }

        context = GitContext()
        context.runner = Mock()

        # This will cause determine_git_branch_final_status to wrap error as GitError
        context.runner.run.side_effect = ValueError("Unexpected error")

        # Act & Assert
        # determine_git_branch_final_status wraps ValueError as GitError
        with pytest.raises(GitError) as exc_info:
            context.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

        assert "Failed to determine git branch status" in exc_info.value.message
