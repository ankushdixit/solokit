"""Unit tests for scripts/git_integration.py - Git workflow integration."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from solokit.core.command_runner import CommandResult
from solokit.core.config import ConfigManager, GitWorkflowConfig
from solokit.core.exceptions import (
    CommandExecutionError,
    ErrorCode,
    FileOperationError,
    GitError,
    NotAGitRepoError,
    WorkingDirNotCleanError,
)
from solokit.git.integration import GitWorkflow


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for tests that don't need file-based config."""
    mock_manager = MagicMock()
    mock_manager.git_workflow = GitWorkflowConfig()
    with patch("solokit.git.integration.get_config_manager", return_value=mock_manager):
        yield mock_manager


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Reset ConfigManager singleton before each test."""
    ConfigManager._instance = None
    ConfigManager._config = None
    ConfigManager._config_path = None
    yield


# ============================================================================
# Test GitWorkflow Initialization
# ============================================================================


class TestGitWorkflowInit:
    """Tests for GitWorkflow initialization."""

    def test_init_default_root(self):
        """Test GitWorkflow initialization with default root directory."""
        # Arrange & Act
        with (
            patch.object(Path, "cwd", return_value=Path("/test/root")),
            patch("solokit.git.integration.get_config_manager"),
        ):
            workflow = GitWorkflow()

        # Assert
        assert workflow.project_root == Path("/test/root")
        assert workflow.work_items_file == Path("/test/root/.session/tracking/work_items.json")
        assert workflow.config_file == Path("/test/root/.session/config.json")

    def test_init_custom_root(self):
        """Test GitWorkflow initialization with custom root directory."""
        # Arrange
        custom_root = Path("/custom/path")

        # Act
        with patch("solokit.git.integration.get_config_manager"):
            workflow = GitWorkflow(project_root=custom_root)

        # Assert
        assert workflow.project_root == custom_root
        assert workflow.work_items_file == Path("/custom/path/.session/tracking/work_items.json")
        assert workflow.config_file == Path("/custom/path/.session/config.json")

    def test_init_loads_config(self):
        """Test that GitWorkflow initialization loads configuration."""
        # Arrange & Act
        workflow = GitWorkflow(Path("/test"))

        # Assert - config should be a GitWorkflowConfig instance
        assert isinstance(workflow.config, GitWorkflowConfig)
        assert workflow.config.mode == "pr"
        assert workflow.config.auto_push is True


# ============================================================================
# Test Check Git Status
# ============================================================================


class TestCheckGitStatus:
    """Tests for check_git_status method."""

    def test_check_git_status_clean(self, tmp_path):
        """Test check_git_status with clean working directory."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="")

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", return_value=mock_result):
            workflow.check_git_status()  # No exception means clean

    def test_check_git_status_dirty(self, tmp_path):
        """Test check_git_status with uncommitted changes."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout=" M file.txt\n")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(WorkingDirNotCleanError) as exc_info:
                workflow.check_git_status()
            assert "not clean" in str(exc_info.value).lower()

    def test_check_git_status_not_git_repo(self, tmp_path):
        """Test check_git_status when not in git repository."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stdout="")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(NotAGitRepoError) as exc_info:
                workflow.check_git_status()
            assert "not a git repository" in str(exc_info.value).lower()

    def test_check_git_status_timeout(self, tmp_path):
        """Test check_git_status when git command times out."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act & Assert
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
            with pytest.raises(CommandExecutionError) as exc_info:
                workflow.check_git_status()
            # The error is a CommandExecutionError which wraps the timeout
            assert exc_info.value is not None

    def test_check_git_status_git_not_found(self, tmp_path):
        """Test check_git_status when git is not installed."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act & Assert
        with patch.object(
            workflow.runner,
            "run",
            return_value=CommandResult(
                returncode=-1,
                stdout="",
                stderr="git not found",
                command=["git"],
                duration_seconds=0.0,
            ),
        ):
            with pytest.raises(NotAGitRepoError):
                workflow.check_git_status()


# ============================================================================
# Test Get Current Branch
# ============================================================================


class TestGetCurrentBranch:
    """Tests for get_current_branch method."""

    def test_get_current_branch_success(self, tmp_path):
        """Test getting current branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="feature-branch\n")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == "feature-branch"

    def test_get_current_branch_main(self, tmp_path):
        """Test getting current branch when on main."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="main\n")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == "main"

    def test_get_current_branch_detached_head(self, tmp_path):
        """Test getting current branch in detached HEAD state."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == ""

    def test_get_current_branch_git_error(self, tmp_path):
        """Test getting current branch when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch is None

    def test_get_current_branch_exception(self, tmp_path):
        """Test getting current branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Git error",
            command=["git", "branch", "--show-current"],
            duration_seconds=0.0,
        )

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch is None


# ============================================================================
# Test Create Branch
# ============================================================================


class TestCreateBranch:
    """Tests for create_branch method."""

    def test_create_branch_success(self, tmp_path):
        """Test creating a new branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            branch_name, parent_branch = workflow.create_branch("feature_foo", 5)

        # Assert
        assert branch_name == "feature_foo"
        assert parent_branch == "main"

    def test_create_branch_naming_convention(self, tmp_path):
        """Test that branch name uses work_item_id directly."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            branch_name, parent = workflow.create_branch("bug_123", 42)

        # Assert
        assert branch_name == "bug_123"

    def test_create_branch_captures_parent(self, tmp_path):
        """Test that create_branch captures parent branch before creating new branch."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="develop")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            branch_name, parent_branch = workflow.create_branch("feature_bar", 10)

        # Assert
        assert parent_branch == "develop"

    def test_create_branch_git_error(self, tmp_path):
        """Test creating branch when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=128, stderr="fatal: branch exists")

        # Act & Assert
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            with pytest.raises(GitError) as exc_info:
                workflow.create_branch("feature_dup", 1)
            assert "failed to create branch" in str(exc_info.value).lower()

    def test_create_branch_exception(self, tmp_path):
        """Test creating branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Git error",
            command=["git", "checkout", "-b", "feature_err"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(GitError) as exc_info:
                workflow.create_branch("feature_err", 1)
            assert "failed to create branch" in str(exc_info.value).lower()


# ============================================================================
# Test Checkout Branch
# ============================================================================


class TestCheckoutBranch:
    """Tests for checkout_branch method."""

    def test_checkout_branch_success(self, tmp_path):
        """Test checking out an existing branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", return_value=mock_result):
            workflow.checkout_branch("feature-branch")

    def test_checkout_branch_not_exists(self, tmp_path):
        """Test checking out a branch that doesn't exist."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="error: pathspec 'missing' did not match")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.checkout_branch("missing-branch")
            assert "failed to checkout" in str(exc_info.value).lower()

    def test_checkout_branch_exception(self, tmp_path):
        """Test checking out branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Git error",
            command=["git", "checkout", "some-branch"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.checkout_branch("some-branch")
            assert "failed to checkout" in str(exc_info.value).lower()


# ============================================================================
# Test Commit Changes
# ============================================================================


class TestCommitChanges:
    """Tests for commit_changes method."""

    def test_commit_changes_success(self, tmp_path):
        """Test committing changes successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=0, stderr="")
        mock_sha = Mock(returncode=0, stdout="abc1234567890\n")

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit, mock_sha]):
            commit_sha = workflow.commit_changes("feat: Add new feature")

        # Assert
        assert commit_sha == "abc1234"

    def test_commit_changes_multiline_message(self, tmp_path):
        """Test committing with multiline commit message."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=0, stderr="")
        mock_sha = Mock(returncode=0, stdout="def5678\n")
        message = "feat: Add feature\n\nDetailed description here"

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit, mock_sha]) as mock_run:
            commit_sha = workflow.commit_changes(message)

        # Assert
        assert commit_sha == "def5678"
        # Verify commit message was passed correctly
        assert mock_run.call_args_list[1][0][0] == ["git", "commit", "-m", message]

    def test_commit_changes_nothing_to_commit(self, tmp_path):
        """Test committing when there are no changes."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=1, stderr="nothing to commit, working tree clean")

        # Act & Assert
        with patch("subprocess.run", side_effect=[mock_add, mock_commit]):
            with pytest.raises(GitError) as exc_info:
                workflow.commit_changes("feat: No changes")
            assert "commit failed" in str(exc_info.value).lower()

    def test_commit_changes_git_error(self, tmp_path):
        """Test committing when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=128, stderr="fatal: unable to commit")

        # Act & Assert
        with patch("subprocess.run", side_effect=[mock_add, mock_commit]):
            with pytest.raises(GitError) as exc_info:
                workflow.commit_changes("fix: Bug fix")
            assert "commit failed" in str(exc_info.value).lower()

    def test_commit_changes_exception(self, tmp_path):
        """Test committing when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Git error",
            command=["git", "add", "."],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch.object(workflow.runner, "run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.commit_changes("feat: Feature")
            assert "staging failed" in str(exc_info.value).lower()


# ============================================================================
# Test Push Branch
# ============================================================================


class TestPushBranch:
    """Tests for push_branch method."""

    def test_push_branch_success(self, tmp_path):
        """Test pushing branch to remote successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", return_value=mock_result):
            workflow.push_branch("feature-branch")

    def test_push_branch_no_remote(self, tmp_path):
        """Test pushing when no remote is configured."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stderr="fatal: No remote repository specified")

        # Act & Assert - Should not raise (logs info instead)
        with patch("subprocess.run", return_value=mock_result):
            workflow.push_branch("feature-branch")  # No exception

    def test_push_branch_no_upstream(self, tmp_path):
        """Test pushing when no upstream is configured."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(
            returncode=128, stderr="fatal: The current branch has no upstream branch"
        )

        # Act & Assert - Should not raise (logs info instead)
        with patch("subprocess.run", return_value=mock_result):
            workflow.push_branch("feature-branch")  # No exception

    def test_push_branch_network_error(self, tmp_path):
        """Test pushing when network error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to access")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.push_branch("feature-branch")
            assert "push failed" in str(exc_info.value).lower()

    def test_push_branch_exception(self, tmp_path):
        """Test pushing when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Network error",
            command=["git", "push", "origin", "feature-branch"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.push_branch("feature-branch")
            assert "push failed" in str(exc_info.value).lower()


# ============================================================================
# Test Delete Remote Branch
# ============================================================================


class TestDeleteRemoteBranch:
    """Tests for delete_remote_branch method."""

    def test_delete_remote_branch_success(self, tmp_path):
        """Test deleting remote branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", return_value=mock_result):
            workflow.delete_remote_branch("feature-branch")

    def test_delete_remote_branch_not_exists(self, tmp_path):
        """Test deleting remote branch that doesn't exist."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="error: remote ref does not exist")

        # Act & Assert - Should not raise (logs info instead)
        with patch("subprocess.run", return_value=mock_result):
            workflow.delete_remote_branch("missing-branch")  # No exception

    def test_delete_remote_branch_error(self, tmp_path):
        """Test deleting remote branch when error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to delete")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.delete_remote_branch("feature-branch")
            assert "failed to delete" in str(exc_info.value).lower()

    def test_delete_remote_branch_exception(self, tmp_path):
        """Test deleting remote branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Network error",
            command=["git", "push", "origin", "--delete", "feature-branch"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.delete_remote_branch("feature-branch")
            assert "failed to delete" in str(exc_info.value).lower()


# ============================================================================
# Test Push Main to Remote
# ============================================================================


class TestPushMainToRemote:
    """Tests for push_main_to_remote method."""

    def test_push_main_to_remote_success(self, tmp_path):
        """Test pushing main to remote successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", return_value=mock_result):
            workflow.push_main_to_remote()

    def test_push_main_to_remote_custom_branch(self, tmp_path):
        """Test pushing custom branch to remote."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            workflow.push_main_to_remote("develop")
        assert mock_run.call_args[0][0] == ["git", "push", "origin", "develop"]

    def test_push_main_to_remote_error(self, tmp_path):
        """Test pushing main to remote when error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to push")

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.push_main_to_remote()
            assert "failed to push" in str(exc_info.value).lower()

    def test_push_main_to_remote_exception(self, tmp_path):
        """Test pushing main to remote when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Network error",
            command=["git", "push", "origin", "main"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.push_main_to_remote()
            assert "failed to push" in str(exc_info.value).lower()


# ============================================================================
# Test Create Pull Request
# ============================================================================


class TestCreatePullRequest:
    """Tests for create_pull_request method."""

    def test_create_pull_request_success(self, tmp_path):
        """Test creating pull request successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "feature_1",
            "type": "feature",
            "title": "New Feature",
            "description": "Desc",
        }
        mock_gh_check = Mock(returncode=0)
        mock_pr_create = Mock(returncode=0, stdout="https://github.com/user/repo/pull/42\n")

        # Act
        with patch("subprocess.run", side_effect=[mock_gh_check, mock_pr_create]):
            pr_url = workflow.create_pull_request(
                "feature_1", "session-001-feature_1", work_item, 1
            )

        # Assert
        assert "github.com" in pr_url

    def test_create_pull_request_gh_not_installed(self, tmp_path):
        """Test creating PR when gh CLI is not installed."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}
        mock_gh_check = Mock(returncode=127)

        # Act & Assert
        with patch("subprocess.run", return_value=mock_gh_check):
            with pytest.raises(GitError) as exc_info:
                workflow.create_pull_request("feature_1", "session-001-feature_1", work_item, 1)
            assert "gh cli not installed" in str(exc_info.value).lower()

    def test_create_pull_request_gh_error(self, tmp_path):
        """Test creating PR when gh command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}
        mock_gh_check = Mock(returncode=0)
        mock_pr_create = Mock(returncode=1, stderr="error: authentication failed")

        # Act & Assert
        with patch("subprocess.run", side_effect=[mock_gh_check, mock_pr_create]):
            with pytest.raises(GitError) as exc_info:
                workflow.create_pull_request("feature_1", "session-001-feature_1", work_item, 1)
            assert "failed to create pr" in str(exc_info.value).lower()

    def test_create_pull_request_exception(self, tmp_path):
        """Test creating PR when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Network error",
            command=["gh", "version"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch.object(workflow.runner, "run", return_value=mock_result):
            with pytest.raises(GitError):
                workflow.create_pull_request("feature_1", "session-001-feature_1", work_item, 1)


# ============================================================================
# Test Format PR Title
# ============================================================================


class TestFormatPRTitle:
    """Tests for _format_pr_title method."""

    def test_format_pr_title_default_template(self, tmp_path):
        """Test formatting PR title with default template."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "feature", "title": "Add user authentication"}

        # Act
        title = workflow._format_pr_title(work_item, 5)

        # Assert
        assert "Feature:" in title
        assert "Add user authentication" in title

    def test_format_pr_title_custom_template(self, tmp_path):
        """Test formatting PR title with custom template."""
        # Arrange
        config_data = {"git_workflow": {"pr_title_template": "[{session_num}] {type}: {title}"}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "bug", "title": "Fix login issue"}

        # Act
        title = workflow._format_pr_title(work_item, 10)

        # Assert
        assert "[10]" in title
        assert "bug" in title.lower()
        assert "Fix login issue" in title

    def test_format_pr_title_missing_fields(self, tmp_path):
        """Test formatting PR title with missing work item fields."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {}  # Empty work item

        # Act
        title = workflow._format_pr_title(work_item, 1)

        # Assert
        assert "Feature:" in title  # Default type
        assert "Work Item" in title  # Default title


# ============================================================================
# Test Format PR Body
# ============================================================================


class TestFormatPRBody:
    """Tests for _format_pr_body method."""

    def test_format_pr_body_default_template(self, tmp_path):
        """Test formatting PR body with default template."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "feature_1",
            "description": "Add authentication feature",
            "git": {"commits": ["abc1234", "def5678"]},
        }

        # Act
        body = workflow._format_pr_body(work_item, "feature_1", 5)

        # Assert
        assert "Work Item: feature_1" in body
        assert "Add authentication feature" in body
        assert "Claude Code" in body

    def test_format_pr_body_with_commits(self, tmp_path):
        """Test formatting PR body with commit messages in custom template."""
        # Arrange
        config_data = {
            "git_workflow": {"pr_body_template": "## {work_item_id}\n\nCommits:\n{commit_messages}"}
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "bug_1",
            "description": "Fix bug",
            "git": {"commits": ["abc1234", "def5678"]},
        }

        # Act
        body = workflow._format_pr_body(work_item, "bug_1", 3)

        # Assert
        assert "- abc1234" in body
        assert "- def5678" in body

    def test_format_pr_body_no_commits(self, tmp_path):
        """Test formatting PR body with no commits uses default text in custom template."""
        # Arrange
        config_data = {
            "git_workflow": {"pr_body_template": "## {work_item_id}\n\n{commit_messages}"}
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "description": "Feature"}

        # Act
        body = workflow._format_pr_body(work_item, "feature_1", 1)

        # Assert
        assert "See commits for details" in body

    def test_format_pr_body_custom_template(self, tmp_path):
        """Test formatting PR body with custom template."""
        # Arrange
        config_data = {
            "git_workflow": {
                "pr_body_template": "## {work_item_id}\n\nType: {type}\n\n{description}"
            }
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "refactor", "description": "Refactor code"}

        # Act
        body = workflow._format_pr_body(work_item, "refactor_1", 2)

        # Assert
        assert "## refactor_1" in body
        assert "Type: refactor" in body
        assert "Refactor code" in body


# ============================================================================
# Test Merge to Parent
# ============================================================================


class TestMergeToParent:
    """Tests for merge_to_parent method."""

    def test_merge_to_parent_success(self, tmp_path):
        """Test merging branch to parent successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=0, stderr="")
        mock_delete = Mock(returncode=0)

        # Act & Assert - Should not raise any exception
        with patch("subprocess.run", side_effect=[mock_checkout, mock_merge, mock_delete]):
            workflow.merge_to_parent("feature-branch", "main")

    def test_merge_to_parent_custom_parent(self, tmp_path):
        """Test merging to custom parent branch."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=0, stderr="")
        mock_delete = Mock(returncode=0)

        # Act & Assert
        with patch(
            "subprocess.run", side_effect=[mock_checkout, mock_merge, mock_delete]
        ) as mock_run:
            workflow.merge_to_parent("feature-branch", "develop")
        # Verify checkout called with correct parent
        assert mock_run.call_args_list[0][0][0] == ["git", "checkout", "develop"]

    def test_merge_to_parent_merge_conflict(self, tmp_path):
        """Test merging when merge conflict occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=1, stderr="CONFLICT: merge conflict in file.txt")

        # Act & Assert
        with patch("subprocess.run", side_effect=[mock_checkout, mock_merge]):
            with pytest.raises(GitError) as exc_info:
                workflow.merge_to_parent("feature-branch", "main")
            assert "merge failed" in str(exc_info.value).lower()

    def test_merge_to_parent_exception(self, tmp_path):
        """Test merging when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = CommandResult(
            returncode=-1,
            stdout="",
            stderr="Git error",
            command=["git", "checkout", "main"],
            duration_seconds=0.0,
        )

        # Act & Assert
        with patch.object(workflow.runner, "run", return_value=mock_result):
            with pytest.raises(GitError) as exc_info:
                workflow.merge_to_parent("feature-branch", "main")
            assert "failed to checkout" in str(exc_info.value).lower()


# ============================================================================
# Test Start Work Item
# ============================================================================


class TestStartWorkItem:
    """Tests for start_work_item method."""

    def test_start_work_item_create_new_branch(self, tmp_path):
        """Test starting work item with new branch creation."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {"id": "feature_1", "title": "New Feature", "status": "in_progress"}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(
            workflow, "create_branch", return_value=("session-001-feature_1", "main")
        ):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "created"
        assert result["branch"] == "session-001-feature_1"
        assert result["success"] is True

        # Verify work item was updated
        with open(work_items_file) as f:
            data = json.load(f)
            assert "git" in data["work_items"]["feature_1"]
            assert data["work_items"]["feature_1"]["git"]["branch"] == "session-001-feature_1"
            assert data["work_items"]["feature_1"]["git"]["parent_branch"] == "main"
            assert data["work_items"]["feature_1"]["git"]["status"] == "in_progress"

    def test_start_work_item_resume_existing_branch(self, tmp_path):
        """Test starting work item with existing branch."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "git": {"branch": "session-001-feature_1", "status": "in_progress"},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(workflow, "checkout_branch", return_value=None):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "resumed"
        assert result["branch"] == "session-001-feature_1"
        assert result["success"] is True

    def test_start_work_item_create_branch_failure(self, tmp_path):
        """Test starting work item when branch creation fails."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {"work_items": {"feature_1": {"id": "feature_1"}}}
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(
            workflow,
            "create_branch",
            side_effect=GitError("Branch exists", ErrorCode.GIT_COMMAND_FAILED),
        ):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "created"
        assert result["success"] is False
        assert "Branch exists" in result["message"]


# ============================================================================
# Test Complete Work Item
# ============================================================================


class TestCompleteWorkItem:
    """Tests for complete_work_item method."""

    def test_complete_work_item_commit_and_push(self, tmp_path):
        """Test completing work item with commit and push."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete feature", False, 1)

        # Assert
        assert result["success"] is True
        assert result["commit"] == "abc1234"
        assert result["pushed"] is True

        # Verify work item was updated
        with open(work_items_file) as f:
            data = json.load(f)
            assert "abc1234" in data["work_items"]["feature_1"]["git"]["commits"]

    def test_complete_work_item_with_pr_mode(self, tmp_path):
        """Test completing work item with PR creation in pr mode."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "pr", "auto_create_pr": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(
                workflow,
                "create_pull_request",
                return_value="https://github.com/user/repo/pull/1",
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True

        # Verify work item git status updated to pr_created
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "pr_created"

    def test_complete_work_item_with_local_merge(self, tmp_path):
        """Test completing work item with local merge in local mode."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local", "delete_branch_after_merge": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(workflow, "merge_to_parent", return_value=None),
            patch.object(workflow, "push_main_to_remote", return_value=None),
            patch.object(workflow, "delete_remote_branch", return_value=None),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True

        # Verify work item git status updated to merged
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "merged"

    def test_complete_work_item_no_git_tracking(self, tmp_path):
        """Test completing work item without git tracking."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {"work_items": {"feature_1": {"id": "feature_1", "status": "completed"}}}
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        assert "no git tracking" in result["message"].lower()

    def test_complete_work_item_nothing_to_commit_with_existing_commits(self, tmp_path):
        """Test completing work item when nothing to commit but existing commits exist."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        mock_git_log = Mock(returncode=0, stdout="abc1234\ndef5678\n")

        # Act
        with (
            patch.object(
                workflow,
                "commit_changes",
                side_effect=GitError(
                    "Commit failed: nothing to commit", ErrorCode.GIT_COMMAND_FAILED
                ),
            ),
            patch.object(workflow, "push_branch", return_value=None),
            patch("subprocess.run", return_value=mock_git_log),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is True
        assert "Found 2 existing commit(s)" in result["commit"]

        # Verify commits were added to work item
        with open(work_items_file) as f:
            data = json.load(f)
            assert "abc1234" in data["work_items"]["feature_1"]["git"]["commits"]
            assert "def5678" in data["work_items"]["feature_1"]["git"]["commits"]

    def test_complete_work_item_commit_failure(self, tmp_path):
        """Test completing work item when commit fails."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "git": {
                        "branch": "session-001-feature_1",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(
            workflow,
            "commit_changes",
            side_effect=GitError("fatal: error", ErrorCode.GIT_COMMAND_FAILED),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        assert "commit failed" in result["message"].lower()


# ============================================================================
# Test Main Function
# ============================================================================


class TestMain:
    """Tests for main function."""

    def test_main_logs_status(self, tmp_path):
        """Test main function logs git status and current branch."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.check_git_status.return_value = None
        mock_workflow.get_current_branch.return_value = "main"

        # Act
        with patch("solokit.git.integration.GitWorkflow", return_value=mock_workflow):
            from solokit.git.integration import main

            main()

        # Assert
        mock_workflow.check_git_status.assert_called_once()
        mock_workflow.get_current_branch.assert_called_once()


# ============================================================================
# Test Error Handling Paths
# ============================================================================


class TestErrorHandlingPaths:
    """Tests for error handling and exception paths."""

    def test_start_work_item_checkout_failure(self, tmp_path):
        """Test start_work_item when checkout fails (line 372-373)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "git": {"branch": "session-001-feature_1", "status": "in_progress"},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act - Mock checkout to raise GitError
        with patch.object(
            workflow,
            "checkout_branch",
            side_effect=GitError("Branch not found", ErrorCode.GIT_COMMAND_FAILED),
        ):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "resumed"
        assert result["success"] is False
        assert "Branch not found" in result["message"]

    def test_start_work_item_create_branch_saves_work_items(self, tmp_path):
        """Test start_work_item saves work items after creating branch (line 397-398)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {"work_items": {"feature_1": {"id": "feature_1"}}}
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Mock file write failure
        original_open = open

        def mock_open(*args, **kwargs):
            mode = kwargs.get("mode", args[1] if len(args) > 1 else "r")
            if "work_items.json" in str(args[0]) and "w" in mode:
                raise OSError("Disk full")
            return original_open(*args, **kwargs)

        # Act
        with (
            patch.object(workflow, "create_branch", return_value=("branch-1", "main")),
            patch("builtins.open", side_effect=mock_open),
        ):
            with pytest.raises(FileOperationError) as exc_info:
                workflow.start_work_item("feature_1", 1)

            assert "Failed to save work items" in str(exc_info.value)

    def test_complete_work_item_read_failure(self, tmp_path):
        """Test complete_work_item when reading work items fails (line 444-445)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        # Create corrupted JSON
        work_items_file.write_text("{invalid json")
        workflow = GitWorkflow(project_root=tmp_path)

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            workflow.complete_work_item("feature_1", "commit message", False, 1)

        assert "Failed to load work items" in str(exc_info.value)

    def test_complete_work_item_nothing_to_commit_no_existing_commits(self, tmp_path):
        """Test complete_work_item with nothing to commit and no existing commits (line 495-497)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        mock_git_log = Mock(returncode=0, stdout="")  # No commits found

        # Act
        with (
            patch.object(
                workflow,
                "commit_changes",
                side_effect=GitError("nothing to commit", ErrorCode.GIT_COMMAND_FAILED),
            ),
            patch("subprocess.run", return_value=mock_git_log),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        # The error message contains "nothing to commit" which is in the git error
        assert "No commits found" in result["message"] or "nothing to commit" in result["message"]

    def test_complete_work_item_nothing_to_commit_git_log_fails(self, tmp_path):
        """Test complete_work_item when git log fails after nothing to commit (line 495-497)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        mock_git_log = Mock(returncode=1, stdout="", stderr="fatal: error")

        # Act
        with (
            patch.object(
                workflow,
                "commit_changes",
                side_effect=GitError("nothing to commit", ErrorCode.GIT_COMMAND_FAILED),
            ),
            patch("subprocess.run", return_value=mock_git_log),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        assert "Failed to retrieve commits" in result["message"]

    def test_complete_work_item_push_failure(self, tmp_path):
        """Test complete_work_item when push fails (line 508-510)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {"branch": "branch-1", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(
                workflow,
                "push_branch",
                side_effect=GitError("Network error", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is True
        assert result["pushed"] is False

    def test_complete_work_item_pr_mode_create_pr_failure(self, tmp_path):
        """Test complete_work_item in PR mode when PR creation fails (line 526-527)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {
                        "branch": "branch-1",
                        "parent_branch": "main",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "pr", "auto_create_pr": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(
                workflow,
                "create_pull_request",
                side_effect=GitError("gh auth required", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True
        # Verify work item git status updated to ready_for_pr instead of pr_created
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "ready_for_pr"

    def test_complete_work_item_pr_mode_auto_create_pr_disabled(self, tmp_path):
        """Test complete_work_item in PR mode with auto_create_pr disabled (line 533)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {"branch": "branch-1", "parent_branch": "main", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "pr", "auto_create_pr": False}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True
        assert "PR creation skipped" in result["message"]
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "ready_for_pr"

    def test_complete_work_item_local_mode_merge_failure(self, tmp_path):
        """Test complete_work_item in local mode when merge fails (line 546-548)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {"branch": "branch-1", "parent_branch": "main", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local"}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(
                workflow,
                "merge_to_parent",
                side_effect=GitError("Merge conflict", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True
        assert "Merge conflict" in result["message"]
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "ready_to_merge"

    def test_complete_work_item_local_mode_push_main_failure(self, tmp_path):
        """Test complete_work_item in local mode when pushing main fails (line 555-556)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {"branch": "branch-1", "parent_branch": "main", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local", "delete_branch_after_merge": False}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(workflow, "merge_to_parent", return_value=None),
            patch.object(
                workflow,
                "push_main_to_remote",
                side_effect=GitError("Network error", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True
        assert "Failed to push main" in result["message"]

    def test_complete_work_item_local_mode_delete_remote_branch_failure(self, tmp_path):
        """Test complete_work_item when deleting remote branch fails (line 563-566)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {"branch": "branch-1", "parent_branch": "main", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local", "delete_branch_after_merge": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(workflow, "merge_to_parent", return_value=None),
            patch.object(workflow, "push_main_to_remote", return_value=None),
            patch.object(
                workflow,
                "delete_remote_branch",
                side_effect=GitError("Network error", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True
        assert "Failed to delete remote branch" in result["message"]

    def test_complete_work_item_local_mode_merge_failure_sets_ready_to_merge(self, tmp_path):
        """Test complete_work_item sets status to ready_to_merge on merge failure (line 571-572)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {"branch": "branch-1", "parent_branch": "main", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local"}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch.object(
                workflow,
                "merge_to_parent",
                side_effect=GitError("Merge conflict", ErrorCode.GIT_COMMAND_FAILED),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "ready_to_merge"
            assert "Manual merge required" in result["message"]

    def test_complete_work_item_save_failure_at_end(self, tmp_path):
        """Test complete_work_item when saving work items fails at the end (line 587-588)."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {"branch": "branch-1", "commits": []},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        original_open = open

        def mock_open(*args, **kwargs):
            # Allow first read, fail on write
            mode = kwargs.get("mode", args[1] if len(args) > 1 else "r")
            if "work_items.json" in str(args[0]):
                if "w" in mode:
                    raise OSError("Disk full")
            return original_open(*args, **kwargs)

        # Act & Assert
        with (
            patch.object(workflow, "commit_changes", return_value="abc1234"),
            patch.object(workflow, "push_branch", return_value=None),
            patch("builtins.open", side_effect=mock_open),
        ):
            with pytest.raises(FileOperationError) as exc_info:
                workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

            assert "Failed to save work items" in str(exc_info.value)

    def test_main_handles_git_errors(self, tmp_path):
        """Test main function handles git errors gracefully (line 611-612)."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.check_git_status.side_effect = NotAGitRepoError("Not a git repository")
        mock_workflow.get_current_branch.return_value = None

        # Act - Should not raise exception
        with patch("solokit.git.integration.GitWorkflow", return_value=mock_workflow):
            from solokit.git.integration import main

            main()

        # Assert - Should complete without raising
        assert True
