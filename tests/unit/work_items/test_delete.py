"""Unit tests for work item deletion module.

This module tests the delete_work_item function and find_dependents helper,
ensuring safe deletion with dependency checking and metadata updates.
"""

import json

import pytest

from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.exceptions import (
    WorkItemNotFoundError,
)
from solokit.work_items.delete import delete_work_item, find_dependents


@pytest.fixture
def sample_work_items_data():
    """Provide sample work items data structure for testing."""
    return {
        "work_items": {
            "feature_foundation": {
                "id": "feature_foundation",
                "title": "Foundation Module",
                "type": "feature",
                "status": "completed",
                "priority": "critical",
                "dependencies": [],
                "milestone": "v1.0",
                "spec_file": ".session/specs/feature_foundation.md",
                "created_at": "2025-01-01T00:00:00",
                "sessions": [],
            },
            "feature_auth": {
                "id": "feature_auth",
                "title": "User Authentication",
                "type": "feature",
                "status": "in_progress",
                "priority": "high",
                "dependencies": ["feature_foundation"],
                "milestone": "v1.0",
                "spec_file": ".session/specs/feature_auth.md",
                "created_at": "2025-01-02T00:00:00",
                "sessions": [],
            },
            "bug_login_issue": {
                "id": "bug_login_issue",
                "title": "Login Issue",
                "type": "bug",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["feature_auth"],
                "milestone": "",
                "spec_file": ".session/specs/bug_login_issue.md",
                "created_at": "2025-01-03T00:00:00",
                "sessions": [],
            },
            "feature_isolated": {
                "id": "feature_isolated",
                "title": "Isolated Feature",
                "type": "feature",
                "status": "not_started",
                "priority": "low",
                "dependencies": [],
                "milestone": "",
                "spec_file": ".session/specs/feature_isolated.md",
                "created_at": "2025-01-04T00:00:00",
                "sessions": [],
            },
        },
        "metadata": {
            "total_items": 4,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
            "last_updated": "2025-01-04T00:00:00",
        },
    }


@pytest.fixture
def project_with_work_items(tmp_path, sample_work_items_data):
    """Set up a temporary project with work items."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()
    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

    # Create work_items.json
    work_items_file = tracking_dir / "work_items.json"
    work_items_file.write_text(json.dumps(sample_work_items_data, indent=2))

    # Create spec files
    for work_id in sample_work_items_data["work_items"].keys():
        spec_file = specs_dir / f"{work_id}.md"
        spec_file.write_text(f"# Spec for {work_id}\n\nTest spec content.")

    return project_root


class TestFindDependents:
    """Tests for find_dependents helper function."""

    def test_find_dependents_with_one_dependent(self, sample_work_items_data):
        """Test finding dependents when one work item depends on target."""
        work_items = sample_work_items_data["work_items"]
        dependents = find_dependents(work_items, "feature_foundation")

        assert dependents == ["feature_auth"]

    def test_find_dependents_with_multiple_dependents(self):
        """Test finding dependents when multiple work items depend on target."""
        work_items = {
            "feature_a": {"dependencies": []},
            "feature_b": {"dependencies": ["feature_a"]},
            "feature_c": {"dependencies": ["feature_a"]},
            "feature_d": {"dependencies": ["feature_b"]},
        }
        dependents = find_dependents(work_items, "feature_a")

        assert set(dependents) == {"feature_b", "feature_c"}

    def test_find_dependents_with_no_dependents(self, sample_work_items_data):
        """Test finding dependents when no work items depend on target."""
        work_items = sample_work_items_data["work_items"]
        dependents = find_dependents(work_items, "bug_login_issue")

        assert dependents == []

    def test_find_dependents_with_empty_work_items(self):
        """Test finding dependents with empty work items dict."""
        dependents = find_dependents({}, "any_id")

        assert dependents == []

    def test_find_dependents_chain(self, sample_work_items_data):
        """Test finding immediate dependents only (not transitive)."""
        work_items = sample_work_items_data["work_items"]
        # feature_auth depends on feature_foundation
        # bug_login_issue depends on feature_auth
        # So feature_foundation should have only feature_auth as dependent
        dependents = find_dependents(work_items, "feature_foundation")

        assert dependents == ["feature_auth"]
        assert "bug_login_issue" not in dependents


class TestDeleteWorkItem:
    """Tests for delete_work_item function."""

    def test_delete_work_item_nonexistent(self, project_with_work_items):
        """Test deleting a work item that doesn't exist."""
        with pytest.raises(WorkItemNotFoundError) as exc_info:
            delete_work_item(
                "nonexistent_item", delete_spec=False, project_root=project_with_work_items
            )

        assert "nonexistent_item" in str(exc_info.value)
        assert exc_info.value.context["work_item_id"] == "nonexistent_item"

    def test_delete_work_item_keep_spec(self, project_with_work_items):
        """Test deleting work item while keeping spec file."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"

        # Verify initial state
        assert spec_file.exists()
        initial_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" in initial_data["work_items"]
        assert initial_data["metadata"]["total_items"] == 4

        # Delete work item, keep spec
        result = delete_work_item(
            "feature_isolated", delete_spec=False, project_root=project_with_work_items
        )

        assert result is True
        assert spec_file.exists()  # Spec should still exist

        # Verify work item removed from JSON
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" not in updated_data["work_items"]

        # Verify metadata updated
        assert updated_data["metadata"]["total_items"] == 3

    def test_delete_work_item_with_spec(self, project_with_work_items):
        """Test deleting work item and spec file."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"

        # Verify initial state
        assert spec_file.exists()

        # Delete work item and spec
        result = delete_work_item(
            "feature_isolated", delete_spec=True, project_root=project_with_work_items
        )

        assert result is True
        assert not spec_file.exists()  # Spec should be deleted

        # Verify work item removed
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" not in updated_data["work_items"]

    def test_delete_work_item_with_dependents_warning(self, project_with_work_items, capsys):
        """Test that deleting work item with dependents shows warning."""
        # Delete feature_auth which has bug_login_issue depending on it
        result = delete_work_item(
            "feature_auth", delete_spec=False, project_root=project_with_work_items
        )

        assert result is True

        captured = capsys.readouterr()
        assert "bug_login_issue" in captured.out
        assert "depend on this item" in captured.out

    def test_delete_work_item_metadata_update(self, project_with_work_items):
        """Test that metadata is correctly updated after deletion."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Initial metadata
        initial_data = json.loads(work_items_file.read_text())
        assert initial_data["metadata"]["total_items"] == 4
        assert initial_data["metadata"]["completed"] == 1
        assert initial_data["metadata"]["in_progress"] == 1

        # Delete completed item
        delete_work_item(
            "feature_foundation", delete_spec=False, project_root=project_with_work_items
        )

        # Check updated metadata
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["metadata"]["total_items"] == 3
        assert updated_data["metadata"]["completed"] == 0  # One less completed
        assert updated_data["metadata"]["in_progress"] == 1

    def test_delete_work_item_no_work_items_file(self, tmp_path):
        """Test deleting when work_items.json doesn't exist."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        with pytest.raises(SolokitFileNotFoundError) as exc_info:
            delete_work_item("any_item", delete_spec=False, project_root=project_root)

        assert "work_items.json" in exc_info.value.context["file_path"]
        assert exc_info.value.context["file_type"] == "work items"

    def test_delete_work_item_spec_not_found(self, project_with_work_items, capsys):
        """Test deleting when spec file doesn't exist."""
        # Remove spec file first
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"
        spec_file.unlink()

        # Try to delete with delete_spec=True
        result = delete_work_item(
            "feature_isolated", delete_spec=True, project_root=project_with_work_items
        )

        # Should still succeed but show warning
        assert result is True
        captured = capsys.readouterr()
        assert "not found" in captured.out

    # Interactive mode tests removed for Claude Code integration
    # Interactive deletion is now handled by /work-delete slash command using AskUserQuestion
    # Removed tests:
    # - test_delete_work_item_interactive_cancel
    # - test_delete_work_item_interactive_keep_spec
    # - test_delete_work_item_interactive_delete_spec
    # - test_delete_work_item_interactive_eof
    # - test_delete_work_item_non_interactive_no_flags

    def test_delete_work_item_dependents_not_modified(self, project_with_work_items):
        """Test that dependent work items are not modified during deletion."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Get initial state of bug_login_issue (depends on feature_auth)
        initial_data = json.loads(work_items_file.read_text())
        initial_dependencies = initial_data["work_items"]["bug_login_issue"]["dependencies"]

        # Delete feature_auth
        delete_work_item("feature_auth", delete_spec=False, project_root=project_with_work_items)

        # Verify bug_login_issue still has feature_auth in dependencies (not auto-updated)
        updated_data = json.loads(work_items_file.read_text())
        updated_dependencies = updated_data["work_items"]["bug_login_issue"]["dependencies"]

        # Dependencies should remain unchanged (user warned to update manually)
        assert updated_dependencies == initial_dependencies
        assert "feature_auth" in updated_dependencies

    def test_delete_work_item_all_statuses(self, project_with_work_items):
        """Test deleting work items with different statuses."""
        # Delete completed item
        result1 = delete_work_item(
            "feature_foundation", delete_spec=False, project_root=project_with_work_items
        )
        assert result1 is True

        # Delete in_progress item
        result2 = delete_work_item(
            "feature_auth", delete_spec=False, project_root=project_with_work_items
        )
        assert result2 is True

        # Delete not_started item
        result3 = delete_work_item(
            "bug_login_issue", delete_spec=False, project_root=project_with_work_items
        )
        assert result3 is True

        # Verify all deleted
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"
        data = json.loads(work_items_file.read_text())
        assert len(data["work_items"]) == 1  # Only feature_isolated remains

    def test_delete_work_item_interactive_keep_spec(self, project_with_work_items, monkeypatch):
        """Test interactive deletion choosing to keep spec."""
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"

        # Mock user input to choose option 1 (keep spec)
        monkeypatch.setattr("builtins.input", lambda _: "1")

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is True
        assert spec_file.exists()  # Spec should be kept

    def test_delete_work_item_interactive_delete_spec(self, project_with_work_items, monkeypatch):
        """Test interactive deletion choosing to delete spec."""
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"

        # Mock user input to choose option 2 (delete spec)
        monkeypatch.setattr("builtins.input", lambda _: "2")

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is True
        assert not spec_file.exists()  # Spec should be deleted

    def test_delete_work_item_interactive_cancel(self, project_with_work_items, monkeypatch):
        """Test interactive deletion choosing to cancel."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Mock user input to choose option 3 (cancel)
        monkeypatch.setattr("builtins.input", lambda _: "3")

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is False
        # Work item should still exist
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" in updated_data["work_items"]

    def test_delete_work_item_interactive_invalid_choice(
        self, project_with_work_items, monkeypatch
    ):
        """Test interactive deletion with invalid choice."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Mock user input with invalid choice
        monkeypatch.setattr("builtins.input", lambda _: "99")

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is False
        # Work item should still exist
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" in updated_data["work_items"]

    def test_delete_work_item_interactive_keyboard_interrupt(
        self, project_with_work_items, monkeypatch
    ):
        """Test interactive deletion with KeyboardInterrupt."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Mock user input to raise KeyboardInterrupt
        def mock_input(_):
            raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", mock_input)

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is False
        # Work item should still exist
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" in updated_data["work_items"]

    def test_delete_work_item_interactive_eof_error(self, project_with_work_items, monkeypatch):
        """Test interactive deletion with EOFError."""
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"

        # Mock user input to raise EOFError
        def mock_input(_):
            raise EOFError

        monkeypatch.setattr("builtins.input", mock_input)

        result = delete_work_item(
            "feature_isolated", delete_spec=None, project_root=project_with_work_items
        )

        assert result is False
        # Work item should still exist
        updated_data = json.loads(work_items_file.read_text())
        assert "feature_isolated" in updated_data["work_items"]


class TestMainFunction:
    """Tests for the main CLI function."""

    def test_main_successful_deletion(self, project_with_work_items, monkeypatch, capsys):
        """Test main function with successful deletion."""
        import sys

        monkeypatch.chdir(project_with_work_items)
        monkeypatch.setattr(sys, "argv", ["work-delete", "feature_isolated", "--keep-spec"])

        from solokit.work_items.delete import main

        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Deleted work item" in captured.out

    def test_main_with_delete_spec_flag(self, project_with_work_items, monkeypatch, capsys):
        """Test main function with --delete-spec flag."""
        import sys

        monkeypatch.chdir(project_with_work_items)
        monkeypatch.setattr(sys, "argv", ["work-delete", "feature_isolated", "--delete-spec"])

        from solokit.work_items.delete import main

        result = main()

        assert result == 0
        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"
        assert not spec_file.exists()

    def test_main_work_item_not_found(self, project_with_work_items, monkeypatch, capsys):
        """Test main function when work item doesn't exist."""
        import sys

        monkeypatch.chdir(project_with_work_items)
        monkeypatch.setattr(sys, "argv", ["work-delete", "nonexistent", "--keep-spec"])

        from solokit.work_items.delete import main

        result = main()

        assert result != 0
        captured = capsys.readouterr()
        assert "Error" in captured.out
        # Should show available work items
        assert "Available work items" in captured.out

    def test_main_conflicting_flags(self, project_with_work_items, monkeypatch):
        """Test main function with both --keep-spec and --delete-spec."""
        import sys

        from solokit.core.exceptions import ValidationError

        monkeypatch.chdir(project_with_work_items)
        monkeypatch.setattr(
            sys, "argv", ["work-delete", "feature_isolated", "--keep-spec", "--delete-spec"]
        )

        from solokit.work_items.delete import main

        with pytest.raises(ValidationError) as exc_info:
            main()

        assert "both --keep-spec and --delete-spec" in exc_info.value.message

    def test_main_no_work_items_file(self, tmp_path, monkeypatch, capsys):
        """Test main function when work_items.json doesn't exist."""
        import sys

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["work-delete", "any_item", "--keep-spec"])

        from solokit.work_items.delete import main

        result = main()

        assert result != 0
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_main_shows_limited_work_items_list(
        self, project_with_work_items, sample_work_items_data, monkeypatch, capsys
    ):
        """Test that main shows only first 5 work items when listing available items."""
        import sys

        # Add more work items to exceed the limit
        work_items_file = project_with_work_items / ".session" / "tracking" / "work_items.json"
        data = json.loads(work_items_file.read_text())
        for i in range(10):
            data["work_items"][f"extra_item_{i}"] = {
                "id": f"extra_item_{i}",
                "title": f"Extra {i}",
                "type": "feature",
                "status": "not_started",
                "priority": "low",
                "dependencies": [],
            }
        work_items_file.write_text(json.dumps(data))

        monkeypatch.chdir(project_with_work_items)
        monkeypatch.setattr(sys, "argv", ["work-delete", "nonexistent", "--keep-spec"])

        from solokit.work_items.delete import main

        result = main()

        assert result != 0
        captured = capsys.readouterr()
        assert "and" in captured.out and "more" in captured.out  # Shows "... and X more"


class TestDeleteWorkItemEdgeCases:
    """Test edge cases for work item deletion."""

    def test_delete_work_item_load_json_error(self, tmp_path, monkeypatch):
        """Test deleting when work_items.json is corrupted."""
        from solokit.core.exceptions import FileOperationError

        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir()

        # Create invalid JSON file
        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text("{invalid json")

        with pytest.raises(FileOperationError) as exc_info:
            delete_work_item("any_item", delete_spec=False, project_root=project_root)

        # Invalid JSON raises a parse operation error
        assert exc_info.value.context["operation"] == "parse"

    def test_delete_work_item_save_json_error(self, project_with_work_items, monkeypatch):
        """Test deleting when saving work_items.json fails."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        # Mock save_json to raise an error
        with patch("solokit.work_items.delete.save_json", side_effect=OSError("Write failed")):
            with pytest.raises(FileOperationError) as exc_info:
                delete_work_item(
                    "feature_isolated", delete_spec=False, project_root=project_with_work_items
                )

        assert exc_info.value.context["operation"] == "write"

    def test_delete_work_item_spec_delete_permission_error(
        self, project_with_work_items, capsys, monkeypatch
    ):
        """Test deleting when spec file deletion fails due to permission error."""
        from unittest.mock import patch

        spec_file = project_with_work_items / ".session" / "specs" / "feature_isolated.md"
        assert spec_file.exists()

        # Mock unlink to raise PermissionError
        def mock_unlink(*args, **kwargs):
            raise PermissionError("Permission denied")

        with patch.object(type(spec_file), "unlink", mock_unlink):
            result = delete_work_item(
                "feature_isolated", delete_spec=True, project_root=project_with_work_items
            )

        # Should still succeed but show warning
        assert result is True
        captured = capsys.readouterr()
        assert "Could not delete spec file" in captured.out

    def test_delete_work_item_without_metadata(self, tmp_path):
        """Test deleting work item when metadata section doesn't exist."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir()
        specs_dir = session_dir / "specs"
        specs_dir.mkdir()

        # Create work_items.json without metadata
        work_items_data = {
            "work_items": {
                "test_item": {
                    "id": "test_item",
                    "title": "Test Item",
                    "type": "feature",
                    "status": "not_started",
                    "priority": "low",
                    "dependencies": [],
                    "spec_file": ".session/specs/test_item.md",
                }
            }
            # No metadata key
        }
        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data))

        # Create spec file
        spec_file = specs_dir / "test_item.md"
        spec_file.write_text("# Test spec")

        # Delete should succeed and create metadata
        result = delete_work_item("test_item", delete_spec=False, project_root=project_root)

        assert result is True
        updated_data = json.loads(work_items_file.read_text())
        assert "metadata" in updated_data
        assert updated_data["metadata"]["total_items"] == 0
