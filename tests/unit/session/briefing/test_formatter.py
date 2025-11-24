"""Unit tests for BriefingFormatter module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.types import WorkItemType
from solokit.session.briefing.formatter import BriefingFormatter


@pytest.fixture
def formatter():
    """Provide a BriefingFormatter instance."""
    return BriefingFormatter()


class TestShiftHeadingLevels:
    """Tests for shift_heading_levels method."""

    def test_shift_heading_levels_zero_shift(self, formatter):
        """Test that zero shift returns unchanged content."""
        content = "# Title\n## Section"
        result = formatter.shift_heading_levels(content, 0)
        assert result == content

    def test_shift_heading_levels_negative_shift(self, formatter):
        """Test that negative shift returns unchanged content."""
        content = "# Title\n## Section"
        result = formatter.shift_heading_levels(content, -1)
        assert result == content

    def test_shift_heading_levels_empty_content(self, formatter):
        """Test that empty content returns empty string."""
        result = formatter.shift_heading_levels("", 2)
        assert result == ""


class TestStripTemplateComments:
    """Tests for strip_template_comments method."""

    def test_strip_template_comments_removes_comments(self, formatter):
        """Test that HTML comments are removed."""
        content = "# Title\n<!-- This is a comment -->\nContent"
        result = formatter.strip_template_comments(content)
        assert "<!-- This is a comment -->" not in result
        assert "# Title" in result
        assert "Content" in result


class TestGeneratePreviousWorkSection:
    """Tests for generate_previous_work_section method."""

    def test_generate_previous_work_section_no_sessions(self, formatter):
        """Test previous work section with no sessions."""
        item = {"sessions": []}
        result = formatter.generate_previous_work_section("test_item", item)
        assert result == ""

    def test_generate_previous_work_section_with_sessions(self, formatter, tmp_path):
        """Test previous work section with sessions and OSError handling."""
        # Create session directory
        session_dir = tmp_path / ".session" / "history"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create summary file
        summary_file = session_dir / "session_001_summary.md"
        summary_content = """# Session Summary

## Commits Made

- commit 1
- commit 2

## Quality Gates

- Test passed
- Lint passed
"""
        summary_file.write_text(summary_content)

        # Change to temp directory
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            item = {
                "sessions": [
                    {
                        "session_num": 1,
                        "started_at": "2025-01-01T00:00:00",
                        "ended_at": "2025-01-01T01:00:00",
                    }
                ]
            }
            result = formatter.generate_previous_work_section("test_item", item)
            assert "Previous Work" in result or result == ""
        finally:
            os.chdir(original_cwd)

    def test_generate_previous_work_section_with_read_error(self, formatter, tmp_path):
        """Test previous work section when summary file cannot be read (line 156-157)."""
        import os

        original_cwd = os.getcwd()

        # Create session directory
        session_dir = tmp_path / ".session" / "history"
        session_dir.mkdir(parents=True, exist_ok=True)
        summary_file = session_dir / "session_001_summary.md"
        summary_file.write_text("test")

        os.chdir(tmp_path)

        try:
            item = {
                "sessions": [
                    {
                        "session_num": 1,
                        "started_at": "2025-01-01T00:00:00",
                        "ended_at": "2025-01-01T01:00:00",
                    }
                ]
            }

            # Mock Path.read_text to raise OSError (lines 156-157)
            with patch.object(Path, "read_text", side_effect=OSError("Test error")):
                with pytest.raises(Exception):  # Should raise FileOperationError
                    formatter.generate_previous_work_section("test_item", item)
        finally:
            os.chdir(original_cwd)


class TestGenerateIntegrationTestBriefing:
    """Tests for generate_integration_test_briefing method."""

    def test_generate_integration_test_briefing_with_scenarios(self, formatter):
        """Test integration test briefing with test scenarios (line 250)."""
        work_item = {
            "type": WorkItemType.INTEGRATION_TEST.value,
            "test_scenarios": [
                {"name": "Scenario 1"},
                {"description": "Scenario 2"},
                {"name": "Scenario 3"},
                {"name": "Scenario 4"},
                {"name": "Scenario 5"},
                {"name": "Scenario 6"},  # Should be truncated (line 250)
            ],
        }
        result = formatter.generate_integration_test_briefing(work_item)
        assert "Test Scenarios (6 total)" in result
        assert "... and 1 more scenarios" in result

    def test_generate_integration_test_briefing_with_performance_benchmarks(self, formatter):
        """Test integration test briefing with performance benchmarks (lines 256-266)."""
        work_item = {
            "type": WorkItemType.INTEGRATION_TEST.value,
            "performance_benchmarks": {
                "response_time": {"p95": 100},
                "throughput": {"minimum": 1000},
            },
        }
        result = formatter.generate_integration_test_briefing(work_item)
        assert "Performance Requirements" in result
        assert "Response time: p95 < 100ms" in result
        assert "Throughput: > 1000 req/s" in result

    def test_generate_integration_test_briefing_with_api_contracts(self, formatter):
        """Test integration test briefing with API contracts (lines 271-276)."""
        work_item = {
            "type": WorkItemType.INTEGRATION_TEST.value,
            "api_contracts": [
                {"contract_file": "api.yaml", "version": "1.0"},
                {"contract_file": "other.yaml", "version": "2.0"},
            ],
        }
        result = formatter.generate_integration_test_briefing(work_item)
        assert "API Contracts (2 contracts)" in result
        assert "api.yaml (version: 1.0)" in result


class TestGenerateBriefing:
    """Tests for generate_briefing method."""

    def test_generate_briefing_with_vision(self, formatter):
        """Test briefing generation with vision document (line 433-434)."""
        result = formatter.generate_briefing(
            item_id="test_item",
            item={
                "title": "Test Item",
                "type": "feature",
                "priority": "high",
                "status": "not_started",
                "dependencies": [],
            },
            project_docs={"vision.md": "# Vision\nProject vision"},
            current_stack="Stack info",
            current_tree="Tree structure",
            work_item_spec="# Spec\nSpecification",
            env_checks=[],
            git_status={"status": "clean", "branch": "main"},
            spec_validation_warning=None,
            milestone_context=None,
            relevant_learnings=[],
        )
        assert "Vision" in result
        assert "Project vision" in result

    def test_generate_briefing_with_in_progress_status(self, formatter, tmp_path):
        """Test briefing generation for in-progress item (lines 459-461)."""
        # Create session directory
        session_dir = tmp_path / ".session" / "history"
        session_dir.mkdir(parents=True, exist_ok=True)

        # Change to temp directory
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = formatter.generate_briefing(
                item_id="test_item",
                item={
                    "title": "Test Item",
                    "type": "feature",
                    "priority": "high",
                    "status": "in_progress",
                    "dependencies": [],
                    "sessions": [
                        {
                            "session_num": 1,
                            "started_at": "2025-01-01T00:00:00",
                            "ended_at": "2025-01-01T01:00:00",
                        }
                    ],
                },
                project_docs={},
                current_stack="Stack info",
                current_tree="Tree structure",
                work_item_spec="# Spec\nSpecification",
                env_checks=[],
                git_status={"status": "clean", "branch": "main"},
                spec_validation_warning=None,
                milestone_context=None,
                relevant_learnings=[],
            )
            assert "Specification" in result
        finally:
            os.chdir(original_cwd)

    def test_generate_briefing_with_dependencies(self, formatter):
        """Test briefing generation with dependencies (lines 475-476)."""
        result = formatter.generate_briefing(
            item_id="test_item",
            item={
                "title": "Test Item",
                "type": "feature",
                "priority": "high",
                "status": "not_started",
                "dependencies": ["dep1", "dep2"],
            },
            project_docs={},
            current_stack="Stack info",
            current_tree="Tree structure",
            work_item_spec="# Spec\nSpecification",
            env_checks=[],
            git_status={"status": "clean", "branch": "main"},
            spec_validation_warning=None,
            milestone_context=None,
            relevant_learnings=[],
        )
        assert "dep1 ✓ completed" in result
        assert "dep2 ✓ completed" in result

    def test_generate_briefing_with_milestone_context(self, formatter):
        """Test briefing generation with milestone context (lines 482-502)."""
        milestone_context = {
            "title": "Milestone 1",
            "description": "Description",
            "progress": 50,
            "completed_items": 5,
            "total_items": 10,
            "target_date": "2025-12-31",
            "milestone_items": [
                {"id": "test_item", "title": "Test Item", "status": "in_progress"},
                {"id": "other_item", "title": "Other Item", "status": "completed"},
            ],
        }
        result = formatter.generate_briefing(
            item_id="test_item",
            item={
                "title": "Test Item",
                "type": "feature",
                "priority": "high",
                "status": "in_progress",
                "dependencies": [],
            },
            project_docs={},
            current_stack="Stack info",
            current_tree="Tree structure",
            work_item_spec="# Spec\nSpecification",
            env_checks=[],
            git_status={"status": "clean", "branch": "main"},
            spec_validation_warning=None,
            milestone_context=milestone_context,
            relevant_learnings=[],
        )
        assert "Milestone Context" in result
        assert "Milestone 1" in result
        assert "Progress: 50%" in result
        assert "Target Date: 2025-12-31" in result
        assert "other_item" in result
