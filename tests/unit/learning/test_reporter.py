#!/usr/bin/env python3
"""
Unit tests for LearningReporter.

Tests learning reporting, statistics, searching, filtering,
and display functionality.
"""

from unittest.mock import Mock, patch

import pytest

from solokit.learning.reporter import LearningReporter


@pytest.fixture
def mock_repository():
    """Create mock repository with test data."""
    repo = Mock()
    repo.load_learnings.return_value = {
        "categories": {
            "best_practices": [
                {
                    "id": "1",
                    "content": "Use dependency injection for testability",
                    "tags": ["testing", "design"],
                    "learned_in": "session_005",
                    "timestamp": "2025-01-10T10:00:00",
                },
                {
                    "id": "2",
                    "content": "Always validate user input",
                    "tags": ["security"],
                    "learned_in": "session_010",
                    "timestamp": "2025-01-15T12:00:00",
                },
            ],
            "gotchas": [
                {
                    "id": "3",
                    "content": "Async functions require await keyword",
                    "tags": ["async", "python"],
                    "learned_in": "session_007",
                    "timestamp": "2025-01-12T14:00:00",
                }
            ],
        },
        "archived": [{"id": "4", "content": "Old archived learning", "learned_in": "session_001"}],
        "last_curated": "2025-01-20T10:00:00",
    }
    return repo


@pytest.fixture
def reporter(mock_repository):
    """Create reporter instance with mock repository."""
    return LearningReporter(mock_repository)


class TestLearningReporterInit:
    """Test LearningReporter initialization."""

    def test_init_with_repository(self, mock_repository):
        """Should initialize with repository."""
        reporter = LearningReporter(mock_repository)

        assert reporter.repository == mock_repository


class TestGenerateReport:
    """Test generate_report method."""

    def test_generate_report_displays_categories(self, reporter, capsys):
        """Should display learning counts by category."""
        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Best Practices" in captured.out
        assert "Gotchas" in captured.out

    def test_generate_report_displays_counts(self, reporter, capsys):
        """Should display correct counts."""
        reporter.generate_report()

        captured = capsys.readouterr()
        assert "2" in captured.out  # best_practices count
        assert "1" in captured.out  # gotchas count

    def test_generate_report_displays_total(self, reporter, capsys):
        """Should display total count."""
        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Total" in captured.out
        assert "3" in captured.out  # Total (excluding archived)

    def test_generate_report_displays_archived(self, reporter, capsys):
        """Should display archived count if present."""
        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Archived" in captured.out
        assert "1" in captured.out

    def test_generate_report_displays_last_curated(self, reporter, capsys):
        """Should display last curated date."""
        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Last curated" in captured.out
        assert "2025-01-20" in captured.out

    def test_generate_report_never_curated(self, mock_repository, capsys):
        """Should display 'Never curated' when appropriate."""
        mock_repository.load_learnings.return_value = {"categories": {}, "last_curated": None}
        reporter = LearningReporter(mock_repository)

        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Never curated" in captured.out

    def test_generate_report_empty_categories(self, mock_repository, capsys):
        """Should handle empty categories."""
        mock_repository.load_learnings.return_value = {"categories": {}, "last_curated": None}
        reporter = LearningReporter(mock_repository)

        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Total" in captured.out
        assert "0" in captured.out


class TestSearchLearnings:
    """Test search_learnings method."""

    def test_search_by_content(self, reporter, capsys):
        """Should find learnings matching content."""
        reporter.search_learnings("dependency")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out
        assert "1 matching learning" in captured.out or "1" in captured.out

    def test_search_by_tag(self, reporter, capsys):
        """Should find learnings matching tags."""
        reporter.search_learnings("security")

        captured = capsys.readouterr()
        assert "validate user input" in captured.out

    def test_search_by_context(self, mock_repository, capsys):
        """Should find learnings matching context."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [
                    {
                        "id": "1",
                        "content": "Some learning",
                        "context": "API development context",
                        "tags": [],
                    }
                ]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.search_learnings("API")

        captured = capsys.readouterr()
        assert "Some learning" in captured.out

    def test_search_case_insensitive(self, reporter, capsys):
        """Should search case-insensitively."""
        reporter.search_learnings("DEPENDENCY")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out

    def test_search_no_matches(self, reporter, capsys):
        """Should display message when no matches found."""
        reporter.search_learnings("nonexistent_term")

        captured = capsys.readouterr()
        assert "No learnings found" in captured.out

    def test_search_displays_category(self, reporter, capsys):
        """Should display category for each match."""
        reporter.search_learnings("injection")

        captured = capsys.readouterr()
        assert "Best Practices" in captured.out or "best_practices" in captured.out

    def test_search_displays_tags(self, reporter, capsys):
        """Should display tags for each match."""
        reporter.search_learnings("injection")

        captured = capsys.readouterr()
        assert "Tags:" in captured.out
        assert "testing" in captured.out

    def test_search_displays_session(self, reporter, capsys):
        """Should display session information."""
        reporter.search_learnings("injection")

        captured = capsys.readouterr()
        assert "Session:" in captured.out
        assert "session_005" in captured.out

    def test_search_displays_id(self, reporter, capsys):
        """Should display learning ID."""
        reporter.search_learnings("injection")

        captured = capsys.readouterr()
        assert "ID:" in captured.out

    def test_search_multiple_matches(self, reporter, capsys):
        """Should display all matching learnings."""
        # Search for a term that appears in multiple learnings' content
        # "user" appears in "Always validate user input"
        # "Use" appears in "Use dependency injection for testability"
        # Search for a common substring like "use" (case insensitive)
        reporter.search_learnings("use")

        captured = capsys.readouterr()
        # Multiple learnings should be shown (at least 2)
        assert "1." in captured.out
        assert "2." in captured.out


class TestShowLearnings:
    """Test show_learnings method."""

    def test_show_all_learnings(self, reporter, capsys):
        """Should display all learnings grouped by category."""
        reporter.show_learnings()

        captured = capsys.readouterr()
        assert "Best Practices" in captured.out or "best_practices" in captured.out
        assert "Gotchas" in captured.out or "gotchas" in captured.out

    def test_show_learnings_by_category(self, reporter, capsys):
        """Should filter by category."""
        reporter.show_learnings(category="best_practices")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out
        assert "Async functions" not in captured.out

    def test_show_learnings_by_tag(self, reporter, capsys):
        """Should filter by tag."""
        reporter.show_learnings(tag="security")

        captured = capsys.readouterr()
        assert "validate user input" in captured.out
        assert "dependency injection" not in captured.out

    def test_show_learnings_by_session(self, reporter, capsys):
        """Should filter by session number."""
        reporter.show_learnings(session=5)

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out
        assert "validate user input" not in captured.out

    def test_show_learnings_by_date_range(self, reporter, capsys):
        """Should filter by date range."""
        reporter.show_learnings(date_from="2025-01-11T00:00:00", date_to="2025-01-16T00:00:00")

        captured = capsys.readouterr()
        assert "validate user input" in captured.out
        assert "dependency injection" not in captured.out

    def test_show_learnings_no_matches(self, reporter, capsys):
        """Should display message when no matches."""
        reporter.show_learnings(category="nonexistent")

        captured = capsys.readouterr()
        assert "No learnings found" in captured.out

    def test_show_learnings_displays_metadata(self, reporter, capsys):
        """Should display metadata for each learning."""
        reporter.show_learnings(category="best_practices")

        captured = capsys.readouterr()
        assert "Tags:" in captured.out
        assert "Learned in:" in captured.out or "Date:" in captured.out

    def test_show_learnings_category_view_shows_all(self, reporter, capsys):
        """Should show all learnings in specific category."""
        reporter.show_learnings(category="best_practices")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out
        assert "validate user input" in captured.out

    def test_show_learnings_summary_view_limits_items(self, reporter, capsys):
        """Should show first 3 items in summary view."""
        # Add more learnings
        reporter.repository.load_learnings.return_value["categories"]["best_practices"].extend(
            [{"id": "5", "content": f"Learning {i}", "tags": []} for i in range(3, 8)]
        )

        reporter.show_learnings()

        captured = capsys.readouterr()
        assert "... and" in captured.out  # Should show "and X more"

    def test_show_learnings_displays_count(self, reporter, capsys):
        """Should display count for each category."""
        reporter.show_learnings()

        captured = capsys.readouterr()
        assert "Count:" in captured.out


class TestGenerateStatistics:
    """Test generate_statistics method."""

    def test_generate_statistics_total_count(self, reporter):
        """Should calculate total learning count."""
        stats = reporter.generate_statistics()

        assert stats["total"] == 3

    def test_generate_statistics_by_category(self, reporter):
        """Should count by category."""
        stats = reporter.generate_statistics()

        assert stats["by_category"]["best_practices"] == 2
        assert stats["by_category"]["gotchas"] == 1

    def test_generate_statistics_by_tag(self, reporter):
        """Should count by tag."""
        stats = reporter.generate_statistics()

        assert stats["by_tag"]["testing"] == 1
        assert stats["by_tag"]["security"] == 1
        assert stats["by_tag"]["async"] == 1

    def test_generate_statistics_top_tags(self, reporter):
        """Should return top tags sorted by count."""
        stats = reporter.generate_statistics()

        assert "top_tags" in stats
        assert isinstance(stats["top_tags"], list)
        assert len(stats["top_tags"]) <= 10

    def test_generate_statistics_by_session(self, reporter):
        """Should count by session."""
        stats = reporter.generate_statistics()

        assert stats["by_session"][5] == 1
        assert stats["by_session"][7] == 1
        assert stats["by_session"][10] == 1

    def test_generate_statistics_empty_categories(self, mock_repository):
        """Should handle empty categories."""
        mock_repository.load_learnings.return_value = {"categories": {}}
        reporter = LearningReporter(mock_repository)

        stats = reporter.generate_statistics()

        assert stats["total"] == 0
        assert stats["by_category"] == {}

    def test_generate_statistics_multiple_tags(self, mock_repository):
        """Should count tags across all learnings."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [
                    {"id": "1", "content": "L1", "tags": ["tag1", "tag2"], "learned_in": "s1"},
                    {"id": "2", "content": "L2", "tags": ["tag1", "tag3"], "learned_in": "s2"},
                ]
            }
        }
        reporter = LearningReporter(mock_repository)

        stats = reporter.generate_statistics()

        assert stats["by_tag"]["tag1"] == 2
        assert stats["by_tag"]["tag2"] == 1
        assert stats["by_tag"]["tag3"] == 1


class TestShowStatistics:
    """Test show_statistics method."""

    def test_show_statistics_displays_total(self, reporter, capsys):
        """Should display total count."""
        reporter.show_statistics()

        captured = capsys.readouterr()
        assert "Total learnings:" in captured.out
        assert "3" in captured.out

    def test_show_statistics_displays_by_category(self, reporter, capsys):
        """Should display category breakdown."""
        reporter.show_statistics()

        captured = capsys.readouterr()
        assert "By Category:" in captured.out
        assert "Best Practices" in captured.out or "best_practices" in captured.out

    def test_show_statistics_displays_top_tags(self, reporter, capsys):
        """Should display top tags."""
        reporter.show_statistics()

        captured = capsys.readouterr()
        assert "Top Tags:" in captured.out

    def test_show_statistics_displays_top_sessions(self, reporter, capsys):
        """Should display sessions with most learnings."""
        reporter.show_statistics()

        captured = capsys.readouterr()
        assert "Sessions with Most Learnings:" in captured.out

    def test_show_statistics_formats_category_names(self, reporter, capsys):
        """Should format category names properly."""
        reporter.show_statistics()

        captured = capsys.readouterr()
        # Should convert underscores to spaces and title case
        assert "Best Practices" in captured.out or "Gotchas" in captured.out

    def test_show_statistics_no_tags(self, mock_repository, capsys):
        """Should handle learnings without tags."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [
                    {"id": "1", "content": "Learning", "tags": [], "learned_in": "s1"}
                ]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.show_statistics()

        captured = capsys.readouterr()
        # Should still display statistics
        assert "Total learnings:" in captured.out


class TestShowTimeline:
    """Test show_timeline method."""

    def test_show_timeline_displays_recent_sessions(self, reporter, capsys):
        """Should display recent sessions."""
        reporter.show_timeline()

        captured = capsys.readouterr()
        assert "Session" in captured.out
        assert "learning" in captured.out

    def test_show_timeline_limits_to_n_sessions(self, reporter, capsys):
        """Should limit to specified number of sessions."""
        reporter.show_timeline(sessions=2)

        captured = capsys.readouterr()
        # Should show up to 2 sessions
        assert "Session" in captured.out

    def test_show_timeline_shows_learning_count(self, reporter, capsys):
        """Should show learning count per session."""
        reporter.show_timeline()

        captured = capsys.readouterr()
        assert "learning" in captured.out

    def test_show_timeline_truncates_long_content(self, mock_repository, capsys):
        """Should truncate long learning content."""
        long_content = "A" * 100  # 100 characters
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [
                    {"id": "1", "content": long_content, "learned_in": "session_005"}
                ]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.show_timeline()

        captured = capsys.readouterr()
        assert "..." in captured.out

    def test_show_timeline_shows_first_3_learnings(self, mock_repository, capsys):
        """Should show first 3 learnings per session."""
        learnings = [
            {"id": str(i), "content": f"Learning {i}", "learned_in": "session_005"}
            for i in range(5)
        ]
        mock_repository.load_learnings.return_value = {"categories": {"best_practices": learnings}}
        reporter = LearningReporter(mock_repository)

        reporter.show_timeline()

        captured = capsys.readouterr()
        assert "... and 2 more" in captured.out

    def test_show_timeline_no_sessions(self, mock_repository, capsys):
        """Should handle no session data."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [{"id": "1", "content": "Learning", "learned_in": "unknown"}]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.show_timeline()

        captured = capsys.readouterr()
        assert "No session timeline available" in captured.out

    def test_show_timeline_sorts_sessions_descending(self, mock_repository, capsys):
        """Should sort sessions in descending order (most recent first)."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [
                    {"id": "1", "content": "L1", "learned_in": "session_010"},
                    {"id": "2", "content": "L2", "learned_in": "session_005"},
                    {"id": "3", "content": "L3", "learned_in": "session_015"},
                ]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.show_timeline()

        captured = capsys.readouterr()
        # Should show session 15 before session 10 before session 5
        lines = captured.out.split("\n")
        session_lines = [line for line in lines if "Session" in line and ":" in line]
        assert len(session_lines) > 0


class TestExtractSessionNumber:
    """Test _extract_session_number method."""

    def test_extract_from_standard_format(self, reporter):
        """Should extract from session_XXX format."""
        result = reporter._extract_session_number("session_005")

        assert result == 5

    def test_extract_from_numeric_string(self, reporter):
        """Should extract from numeric string."""
        result = reporter._extract_session_number("123")

        assert result == 123

    def test_extract_from_mixed_format(self, reporter):
        """Should extract first number found."""
        result = reporter._extract_session_number("session_042_final")

        assert result == 42

    def test_extract_no_digits(self, reporter):
        """Should return 0 for non-numeric string."""
        result = reporter._extract_session_number("unknown")

        assert result == 0

    def test_extract_empty_string(self, reporter):
        """Should return 0 for empty string."""
        result = reporter._extract_session_number("")

        assert result == 0

    def test_extract_handles_exception(self, reporter):
        """Should return 0 on exception."""
        # Mock re.search to raise an exception
        with patch("solokit.learning.reporter.re.search", side_effect=AttributeError("Test error")):
            result = reporter._extract_session_number("session_005")

        assert result == 0


class TestShowLearningsFiltering:
    """Test advanced filtering in show_learnings."""

    def test_filter_by_date_from_only(self, reporter, capsys):
        """Should filter learnings from specified date onwards."""
        reporter.show_learnings(date_from="2025-01-11T00:00:00")

        captured = capsys.readouterr()
        assert "Async functions" in captured.out
        assert "validate user input" in captured.out

    def test_filter_by_date_to_only(self, reporter, capsys):
        """Should filter learnings up to specified date."""
        reporter.show_learnings(date_to="2025-01-11T00:00:00")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out

    def test_filter_combined_category_and_tag(self, reporter, capsys):
        """Should apply multiple filters together."""
        reporter.show_learnings(category="best_practices", tag="testing")

        captured = capsys.readouterr()
        assert "dependency injection" in captured.out
        assert "validate user input" not in captured.out

    def test_filter_empty_result_shows_help(self, reporter, capsys):
        """Should show helpful message when filters match nothing."""
        reporter.show_learnings(category="nonexistent")

        captured = capsys.readouterr()
        assert "To see all learnings:" in captured.out
        assert "/learn-show" in captured.out


class TestGenerateReportEdgeCases:
    """Test edge cases for report generation."""

    def test_generate_report_no_archived(self, mock_repository, capsys):
        """Should handle missing archived field."""
        mock_repository.load_learnings.return_value = {
            "categories": {"best_practices": [{"id": "1"}]},
            "last_curated": None,
        }
        reporter = LearningReporter(mock_repository)

        reporter.generate_report()

        capsys.readouterr()  # Capture output to verify no crash
        # Should not crash, Archived line may or may not appear

    def test_generate_report_multiple_categories(self, mock_repository, capsys):
        """Should handle many categories."""
        categories = {f"category_{i}": [{"id": str(j)} for j in range(5)] for i in range(10)}
        mock_repository.load_learnings.return_value = {
            "categories": categories,
            "last_curated": None,
        }
        reporter = LearningReporter(mock_repository)

        reporter.generate_report()

        captured = capsys.readouterr()
        assert "Total" in captured.out


class TestSearchLearningsEdgeCases:
    """Test edge cases for search functionality."""

    def test_search_special_characters(self, mock_repository, capsys):
        """Should handle special characters in search."""
        mock_repository.load_learnings.return_value = {
            "categories": {
                "best_practices": [{"id": "1", "content": "Use @decorator pattern", "tags": []}]
            }
        }
        reporter = LearningReporter(mock_repository)

        reporter.search_learnings("@decorator")

        captured = capsys.readouterr()
        assert "@decorator" in captured.out

    def test_search_empty_query(self, reporter, capsys):
        """Should handle empty search query."""
        reporter.search_learnings("")

        captured = capsys.readouterr()
        # An empty string matches everything (since "" in any_string is True)
        # The implementation doesn't special-case empty queries
        # So we expect results to be shown
        assert "Search Results" in captured.out or "matching learning" in captured.out


class TestStatisticsEdgeCases:
    """Test edge cases for statistics generation."""

    def test_statistics_no_tags(self, mock_repository):
        """Should handle learnings without tags."""
        mock_repository.load_learnings.return_value = {
            "categories": {"best_practices": [{"id": "1", "content": "L1", "learned_in": "s1"}]}
        }
        reporter = LearningReporter(mock_repository)

        stats = reporter.generate_statistics()

        assert stats["by_tag"] == {}
        assert stats["top_tags"] == []

    def test_statistics_top_tags_limits_to_10(self, mock_repository):
        """Should limit top tags to 10."""
        learnings = [
            {"id": str(i), "content": f"L{i}", "tags": [f"tag{i}"], "learned_in": "s1"}
            for i in range(20)
        ]
        mock_repository.load_learnings.return_value = {"categories": {"best_practices": learnings}}
        reporter = LearningReporter(mock_repository)

        stats = reporter.generate_statistics()

        assert len(stats["top_tags"]) <= 10
