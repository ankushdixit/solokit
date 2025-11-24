"""Unit tests for work_item_query module.

This module tests the WorkItemQuery class which handles listing, filtering,
sorting, and displaying work items.
"""

import json

import pytest

from solokit.work_items.query import WorkItemQuery
from solokit.work_items.repository import WorkItemRepository


@pytest.fixture
def repository_with_data(tmp_path):
    """Provide a WorkItemRepository instance with existing data."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()

    # Create work_items.json with sample data
    work_items_file = tracking_dir / "work_items.json"
    sample_data = {
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
                "sessions": [{"session_number": 1, "date": "2025-01-03", "duration": "1h"}],
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
        },
        "metadata": {
            "total_items": 3,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
            "last_updated": "2025-01-03T00:00:00",
        },
        "milestones": {},
    }
    work_items_file.write_text(json.dumps(sample_data, indent=2))

    return WorkItemRepository(session_dir)


@pytest.fixture
def query(repository_with_data):
    """Provide a WorkItemQuery instance."""
    return WorkItemQuery(repository_with_data)


class TestIsBlocked:
    """Tests for dependency blocking logic."""

    def test_is_blocked_completed_item_not_blocked(self, query):
        """Test that completed items are never blocked."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["feature_foundation"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_no_dependencies(self, query):
        """Test that items without dependencies are not blocked."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["feature_foundation"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_incomplete_dependency(self, query):
        """Test that item is blocked when dependency is incomplete."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["bug_login_issue"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is True

    def test_is_blocked_all_dependencies_complete(self, query):
        """Test that item is not blocked when all dependencies are complete."""
        # Arrange
        # Add new item that depends on completed item
        data = json.loads(query.repository.work_items_file.read_text())
        data["work_items"]["feature_new"] = {
            "id": "feature_new",
            "status": "not_started",
            "dependencies": ["feature_foundation"],
        }
        query.repository.work_items_file.write_text(json.dumps(data))

        all_items = query.repository.get_all_work_items()
        item = all_items["feature_new"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_missing_dependency(self, query):
        """Test that missing dependency is ignored."""
        # Arrange
        item = {"id": "test", "status": "not_started", "dependencies": ["nonexistent"]}
        all_items = {}

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_in_progress_item(self, query):
        """Test that in_progress items are never blocked."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        # feature_auth is in_progress with dependencies
        item = all_items["feature_auth"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False  # in_progress items should never be blocked


class TestSortItems:
    """Tests for work item sorting."""

    def test_sort_items_by_priority(self, query):
        """Test that items are sorted by priority."""
        # Arrange
        items = {
            "low": {
                "priority": "low",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "critical": {
                "priority": "critical",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "medium": {
                "priority": "medium",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        priorities = [item["priority"] for item in result]
        assert priorities == ["critical", "medium", "low"]

    def test_sort_items_ready_before_blocked(self, query):
        """Test that ready items come before blocked items."""
        # Arrange
        items = {
            "blocked": {
                "priority": "high",
                "status": "not_started",
                "_blocked": True,
                "created_at": "2025-01-01",
            },
            "ready": {
                "priority": "high",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-02",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        assert result[0]["_blocked"] is False
        assert result[1]["_blocked"] is True

    def test_sort_items_in_progress_first(self, query):
        """Test that in_progress items come first."""
        # Arrange
        items = {
            "not_started": {
                "priority": "high",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "in_progress": {
                "priority": "high",
                "status": "in_progress",
                "_blocked": False,
                "created_at": "2025-01-02",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        assert result[0]["status"] == "in_progress"


class TestGetStatusIcon:
    """Tests for status icon helper."""

    def test_get_status_icon_completed(self, query):
        """Test status icon for completed item."""
        # Act
        icon = query._get_status_icon({"status": "completed"})

        # Assert
        assert icon == "[✓]"

    def test_get_status_icon_in_progress(self, query):
        """Test status icon for in_progress item."""
        # Act
        icon = query._get_status_icon({"status": "in_progress"})

        # Assert
        assert icon == "[>>]"

    def test_get_status_icon_not_started(self, query):
        """Test status icon for not_started item."""
        # Act
        icon = query._get_status_icon({"status": "not_started"})

        # Assert
        assert icon == "[  ]"


class TestShowItem:
    """Tests for showing detailed work item information."""

    def test_show_item_empty_repository(self, tmp_path):
        """Test showing item when repository is empty raises FileOperationError."""
        from solokit.core.exceptions import FileOperationError

        # Arrange
        project_root = tmp_path / "empty_project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir()

        repository = WorkItemRepository(session_dir)
        query = WorkItemQuery(repository)

        # Act & Assert
        with pytest.raises(FileOperationError):
            query.show_item("any_id")

    def test_show_item_not_found(self, repository_with_data, query):
        """Test showing non-existent item raises WorkItemNotFoundError."""
        from solokit.core.exceptions import WorkItemNotFoundError

        # Act & Assert
        with pytest.raises(WorkItemNotFoundError):
            query.show_item("nonexistent_work_item")

    def test_show_item_with_spec_file(self, repository_with_data, query, tmp_path):
        """Test showing item with spec file present."""

        # Create spec file
        specs_dir = tmp_path / "project" / ".session" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        spec_file = specs_dir / "feature_foundation.md"
        spec_content = "# Feature: Foundation\n\n## Overview\nFoundation module overview\n" * 30
        spec_file.write_text(spec_content)

        # Act
        item = query.show_item("feature_foundation")

        # Assert
        assert item is not None
        assert item["id"] == "feature_foundation"

    def test_show_item_with_long_spec_file(self, repository_with_data, query, tmp_path):
        """Test showing item with spec file >50 lines shows truncation message."""
        # Create spec file with >50 lines
        specs_dir = tmp_path / "project" / ".session" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        spec_file = specs_dir / "feature_foundation.md"
        # Create 100 lines of content
        spec_content = "\n".join([f"Line {i}" for i in range(100)])
        spec_file.write_text(spec_content)

        # Act
        item = query.show_item("feature_foundation")

        # Assert
        assert item is not None
        assert item["id"] == "feature_foundation"

    def test_show_item_with_dependencies(self, repository_with_data, query):
        """Test showing item with dependencies displays dependency info."""
        # Act
        item = query.show_item("bug_login_issue")

        # Assert
        assert item is not None
        assert "feature_auth" in item["dependencies"]

    def test_show_item_with_git_info(self, repository_with_data, query):
        """Test showing item with git information."""
        import json

        # Add git info to an item
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["feature_auth"]["git"] = {
            "branch": "feature/auth",
            "commits": ["abc123", "def456"],
        }
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        item = query.show_item("feature_auth")

        # Assert
        assert item is not None
        assert item["git"]["branch"] == "feature/auth"

    def test_show_item_not_started_with_no_blockers(self, repository_with_data, query):
        """Test showing not_started item with no blocking dependencies."""
        import json

        # Create item with no dependencies
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["feature_new"] = {
            "id": "feature_new",
            "title": "New Feature",
            "type": "feature",
            "status": "not_started",
            "priority": "high",
            "dependencies": [],
            "milestone": "v1.0",
            "spec_file": ".session/specs/feature_new.md",
            "created_at": "2025-01-04T00:00:00",
            "sessions": [],
        }
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        item = query.show_item("feature_new")

        # Assert
        assert item is not None
        assert item["status"] == "not_started"

    def test_show_item_not_started_with_blockers(self, repository_with_data, query):
        """Test showing not_started item with blocking dependencies."""
        # Act - bug_login_issue depends on feature_auth which is in_progress
        item = query.show_item("bug_login_issue")

        # Assert
        assert item is not None
        assert item["status"] == "not_started"
        assert len(item["dependencies"]) > 0

    def test_show_item_in_progress(self, repository_with_data, query):
        """Test showing in_progress item."""
        # Act
        item = query.show_item("feature_auth")

        # Assert
        assert item is not None
        assert item["status"] == "in_progress"

    def test_show_item_completed(self, repository_with_data, query):
        """Test showing completed item."""
        # Act
        item = query.show_item("feature_foundation")

        # Assert
        assert item is not None
        assert item["status"] == "completed"

    def test_show_item_with_milestone(self, repository_with_data, query):
        """Test showing item with milestone displays milestone info."""
        # Act
        item = query.show_item("feature_auth")

        # Assert
        assert item is not None
        assert item["milestone"] == "v1.0"

    def test_show_item_nonexistent_dependency(self, repository_with_data, query):
        """Test showing item with dependency that doesn't exist."""
        import json

        # Add item with nonexistent dependency
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["feature_broken"] = {
            "id": "feature_broken",
            "title": "Broken Feature",
            "type": "feature",
            "status": "not_started",
            "priority": "high",
            "dependencies": ["nonexistent_dep"],
            "milestone": "",
            "spec_file": ".session/specs/feature_broken.md",
            "created_at": "2025-01-04T00:00:00",
            "sessions": [],
        }
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        item = query.show_item("feature_broken")

        # Assert
        assert item is not None
        assert "nonexistent_dep" in item["dependencies"]


class TestListItems:
    """Tests for listing and filtering work items."""

    def test_list_items_empty_repository(self, tmp_path):
        """Test listing items when repository is empty."""
        # Arrange
        project_root = tmp_path / "empty_project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir()

        repository = WorkItemRepository(session_dir)
        query = WorkItemQuery(repository)

        # Act
        result = query.list_items()

        # Assert
        assert result["count"] == 0
        assert len(result["items"]) == 0

    def test_list_items_with_filters(self, repository_with_data, query):
        """Test listing items with status filter."""
        # Act
        result = query.list_items(status_filter="completed")

        # Assert
        assert result["count"] == 1
        assert result["items"][0]["id"] == "feature_foundation"

    def test_list_items_with_type_filter(self, repository_with_data, query):
        """Test listing items with type filter."""
        # Act
        result = query.list_items(type_filter="bug")

        # Assert
        assert result["count"] == 1
        assert result["items"][0]["id"] == "bug_login_issue"

    def test_list_items_with_milestone_filter(self, repository_with_data, query):
        """Test listing items with milestone filter."""
        # Act
        result = query.list_items(milestone_filter="v1.0")

        # Assert
        assert result["count"] == 2

    def test_display_items_empty_list(self, query):
        """Test displaying empty list of items."""
        # Act - should not raise exception
        query._display_items([])

    def test_display_items_with_urgent_flag(self, repository_with_data, query):
        """Test displaying items with urgent flag."""
        import json

        # Add urgent flag to an item
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["bug_login_issue"]["urgent"] = True
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Get all items and add blocking info
        all_items = repository_with_data.get_all_work_items()
        items_with_meta = []
        for work_id, item in all_items.items():
            item["_blocked"] = query._is_blocked(item, all_items)
            item["_ready"] = not item["_blocked"] and item["status"] == "not_started"
            items_with_meta.append(item)

        # Act - should display urgent indicator
        query._display_items(items_with_meta)

    def test_display_items_with_blocked_status(self, repository_with_data, query):
        """Test displaying items with blocked status."""
        # Get all items and compute blocking
        all_items = repository_with_data.get_all_work_items()
        items_with_meta = []
        for work_id, item in all_items.items():
            item["_blocked"] = query._is_blocked(item, all_items)
            item["_ready"] = not item["_blocked"] and item["status"] == "not_started"
            items_with_meta.append(item)

        # Act - should display blocking info
        query._display_items(items_with_meta)

    def test_display_items_with_ready_status(self, repository_with_data, query):
        """Test displaying items with ready status."""
        import json

        # Create item that's ready to start
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["feature_ready"] = {
            "id": "feature_ready",
            "title": "Ready Feature",
            "type": "feature",
            "status": "not_started",
            "priority": "high",
            "dependencies": ["feature_foundation"],  # completed
            "milestone": "",
            "spec_file": ".session/specs/feature_ready.md",
            "created_at": "2025-01-04T00:00:00",
            "sessions": [],
        }
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Get all items and compute blocking
        all_items = repository_with_data.get_all_work_items()
        items_with_meta = []
        for work_id, item in all_items.items():
            item["_blocked"] = query._is_blocked(item, all_items)
            item["_ready"] = not item["_blocked"] and item["status"] == "not_started"
            items_with_meta.append(item)

        # Act
        query._display_items(items_with_meta)

    def test_display_items_with_completed_single_session(self, repository_with_data, query):
        """Test displaying completed item with single session (singular 'session')."""
        import json

        # Create completed item with exactly 1 session
        data = json.loads(repository_with_data.work_items_file.read_text())
        data["work_items"]["feature_single"] = {
            "id": "feature_single",
            "title": "Single Session Feature",
            "type": "feature",
            "status": "completed",
            "priority": "high",
            "dependencies": [],
            "milestone": "",
            "spec_file": ".session/specs/feature_single.md",
            "created_at": "2025-01-04T00:00:00",
            "sessions": [{"session_number": 1, "date": "2025-01-05", "duration": "1h"}],
        }
        repository_with_data.work_items_file.write_text(json.dumps(data))

        # Get all items and compute blocking
        all_items = repository_with_data.get_all_work_items()
        items_with_meta = []
        for work_id, item in all_items.items():
            item["_blocked"] = query._is_blocked(item, all_items)
            item["_ready"] = not item["_blocked"] and item["status"] == "not_started"
            items_with_meta.append(item)

        # Act
        query._display_items(items_with_meta)

    def test_display_items_with_no_status_str(self, repository_with_data, query):
        """Test displaying not_started item that's not ready (no special status string)."""

        # Create not_started item that's not blocked but also not ready (shouldn't happen, but testing the else branch)
        all_items = repository_with_data.get_all_work_items()

        # Manually construct items with metadata that hits the else branch
        items_with_meta = []
        for work_id, item in all_items.items():
            item["_blocked"] = False
            item["_ready"] = False  # Not ready and not blocked
            if item["status"] == "not_started":
                items_with_meta.append(item)
                break

        # Act
        if items_with_meta:
            query._display_items(items_with_meta)

    def test_is_blocked_with_no_dependencies(self, query):
        """Test that item with empty dependencies list is not blocked."""
        # Arrange
        item = {"id": "test", "status": "not_started", "dependencies": []}
        all_items = {}

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False
