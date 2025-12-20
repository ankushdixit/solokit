"""Integration tests for work item git status finalization.

This module tests the integration between work items and git operations,
particularly the automatic finalization of git branch status when switching
between work items (Bug #24 fix).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from solokit.session.briefing import (
    determine_git_branch_final_status,
    finalize_previous_work_item_git_status,
)


@pytest.fixture(autouse=True)
def mock_shutil_which():
    """Mock shutil.which to return None by default to prevent path resolution."""
    with patch("shutil.which", return_value=None):
        yield


@pytest.fixture
def mock_work_item_environment(tmp_path):
    """Create mock .session environment with completed work items and git tracking.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Returns:
        Path: Root project directory with .session structure.
    """
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"
    briefings_dir = session_dir / "briefings"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()
    briefings_dir.mkdir()

    # Create mock work items with various git states
    work_items = {
        "work_items": {
            "item_completed_with_stale_git": {
                "id": "item_completed_with_stale_git",
                "title": "Completed Item With Stale Git Status",
                "type": "feature",
                "status": "completed",
                "priority": "high",
                "dependencies": [],
                "git": {
                    "branch": "session-001-item_completed_with_stale_git",
                    "parent_branch": "main",
                    "status": "in_progress",  # Stale - should be updated
                },
                "sessions": [{"session_num": 1, "started_at": "2025-01-01T00:00:00"}],
            },
            "item_new": {
                "id": "item_new",
                "title": "New Item to Start",
                "type": "bug",
                "status": "not_started",
                "priority": "medium",
                "dependencies": [],
            },
            "item_in_progress": {
                "id": "item_in_progress",
                "title": "In Progress Item",
                "type": "feature",
                "status": "in_progress",
                "priority": "high",
                "dependencies": [],
                "git": {
                    "branch": "session-002-item_in_progress",
                    "parent_branch": "main",
                    "status": "in_progress",  # Should NOT be finalized
                },
                "sessions": [{"session_num": 2, "started_at": "2025-01-02T00:00:00"}],
            },
            "item_completed_no_git": {
                "id": "item_completed_no_git",
                "title": "Completed Item Without Git",
                "type": "bug",
                "status": "completed",
                "priority": "low",
                "dependencies": [],
            },
        },
        "metadata": {
            "total_items": 4,
            "completed": 2,
            "in_progress": 1,
            "blocked": 0,
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(work_items, f, indent=2)

    # Create mock learnings
    learnings = {"learnings": []}
    learnings_file = tracking_dir / "learnings.json"
    with open(learnings_file, "w") as f:
        json.dump(learnings, f, indent=2)

    # Create mock stack and tree files
    (tracking_dir / "stack.txt").write_text("Test Stack")
    (tracking_dir / "tree.txt").write_text("Test Tree")

    # Create spec files for all work items
    for item_id in work_items["work_items"].keys():
        spec_file = specs_dir / f"{item_id}.md"
        spec_file.write_text(f"# {item_id}\n\nTest specification")

    return tmp_path


class TestGitBranchStatusDetection:
    """Test suite for git branch status detection functionality."""

    def test_detect_merged_branch_status(self):
        """Test that merged branch is correctly detected via git branch --merged."""
        # Arrange
        branch_name = "session-001-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = f"  {branch_name}\n  another-branch\n"
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "merged"

    def test_detect_open_pr_status(self):
        """Test that open PR status is detected when branch not merged but PR exists."""
        # Arrange
        branch_name = "session-002-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                result.returncode = 0
                result.stdout = '[{"number": 123, "state": "OPEN"}]'
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "pr_created"

    def test_detect_closed_pr_status(self):
        """Test that closed PR status is detected when PR is closed without merge."""
        # Arrange
        branch_name = "session-003-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                result.returncode = 0
                result.stdout = '[{"number": 124, "state": "CLOSED"}]'
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "pr_closed"

    def test_detect_merged_pr_via_gh_cli(self):
        """Test that merged state is detected via GitHub CLI when PR shows MERGED."""
        # Arrange
        branch_name = "session-004-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                result.returncode = 0
                result.stdout = '[{"number": 125, "state": "MERGED"}]'
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "merged"

    def test_detect_ready_for_pr_local_branch(self):
        """Test that local branch without PR is detected as ready_for_pr."""
        # Arrange
        branch_name = "session-005-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                raise FileNotFoundError()
            elif "show-ref" in cmd:
                result.returncode = 0
                result.stdout = f"abc123 refs/heads/{branch_name}"
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "ready_for_pr"

    def test_detect_ready_for_pr_remote_branch(self):
        """Test that remote branch without PR is detected as ready_for_pr."""
        # Arrange
        branch_name = "session-006-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                raise FileNotFoundError()
            elif "show-ref" in cmd:
                result.returncode = 1  # Not found locally
            elif "ls-remote" in cmd:
                result.returncode = 0
                result.stdout = f"def456 refs/heads/{branch_name}"
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "ready_for_pr"

    def test_detect_deleted_branch(self):
        """Test that deleted branch (not found locally or remotely) is detected."""
        # Arrange
        branch_name = "session-007-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd and "pr" in cmd:
                raise FileNotFoundError()
            elif "show-ref" in cmd:
                result.returncode = 1  # Not found locally
            elif "ls-remote" in cmd:
                result.returncode = 0
                result.stdout = ""  # Not found remotely
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "deleted"

    def test_graceful_fallback_when_gh_cli_unavailable(self):
        """Test graceful handling when GitHub CLI is not installed or available."""
        # Arrange
        branch_name = "session-008-feature_test"
        git_info = {"parent_branch": "main"}

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = ""
            elif "gh" in cmd:
                raise FileNotFoundError("gh command not found")
            elif "show-ref" in cmd:
                result.returncode = 0
                result.stdout = f"abc123 refs/heads/{branch_name}"
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            status = determine_git_branch_final_status(branch_name, git_info)

        # Assert
        assert status == "ready_for_pr"


class TestWorkItemGitStatusFinalization:
    """Test suite for work item git status finalization when switching items."""

    def test_finalize_completed_work_item_git_status(
        self, mock_work_item_environment, capsys, monkeypatch
    ):
        """Test that completed work item git status is finalized when starting new work item."""
        # Arrange
        monkeypatch.chdir(mock_work_item_environment)
        work_items_file = mock_work_item_environment / ".session" / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "branch" in cmd and "--merged" in cmd:
                result.returncode = 0
                result.stdout = "  session-001-item_completed_with_stale_git\n"
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            finalize_previous_work_item_git_status(work_items_data, "item_new")

        # Assert
        captured = capsys.readouterr()
        assert "Finalized git status for previous work item" in captured.out
        assert "item_completed_with_stale_git → merged" in captured.out

        with open(work_items_file) as f:
            updated_data = json.load(f)
        assert (
            updated_data["work_items"]["item_completed_with_stale_git"]["git"]["status"] == "merged"
        )

    def test_only_finalize_completed_work_items(self, mock_work_item_environment, monkeypatch):
        """Test that only completed work items are finalized, in-progress items unchanged."""
        # Arrange
        monkeypatch.chdir(mock_work_item_environment)
        work_items_file = mock_work_item_environment / ".session" / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        original_status = work_items_data["work_items"]["item_in_progress"]["git"]["status"]

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            finalize_previous_work_item_git_status(work_items_data, "item_new")

        # Assert
        with open(work_items_file) as f:
            updated_data = json.load(f)

        assert updated_data["work_items"]["item_in_progress"]["git"]["status"] == original_status

    def test_skip_work_items_without_git_branch(
        self, mock_work_item_environment, capsys, monkeypatch
    ):
        """Test that finalization gracefully skips work items without git branch info."""
        # Arrange
        monkeypatch.chdir(mock_work_item_environment)
        work_items_file = mock_work_item_environment / ".session" / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        # Remove git info from completed item
        del work_items_data["work_items"]["item_completed_with_stale_git"]["git"]
        with open(work_items_file, "w") as f:
            json.dump(work_items_data, f, indent=2)

        # Reload
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        # Act
        finalize_previous_work_item_git_status(work_items_data, "item_new")

        # Assert
        captured = capsys.readouterr()
        assert "Finalized git status" not in captured.out

    def test_does_not_finalize_when_resuming_same_work_item(
        self, mock_work_item_environment, capsys, monkeypatch
    ):
        """Test that finalization does not run when resuming the same work item."""
        # Arrange
        monkeypatch.chdir(mock_work_item_environment)
        work_items_file = mock_work_item_environment / ".session" / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        original_status = work_items_data["work_items"]["item_completed_with_stale_git"]["git"][
            "status"
        ]

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        # Act
        with patch("subprocess.run", side_effect=mock_run):
            # Try to finalize when "starting" the same completed item
            finalize_previous_work_item_git_status(work_items_data, "item_completed_with_stale_git")

        # Assert
        captured = capsys.readouterr()
        assert "Finalized git status" not in captured.out

        with open(work_items_file) as f:
            updated_data = json.load(f)
        assert (
            updated_data["work_items"]["item_completed_with_stale_git"]["git"]["status"]
            == original_status
        )
