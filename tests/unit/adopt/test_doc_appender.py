"""
Tests for doc_appender module.

Validates documentation appending for README.md and CLAUDE.md during adoption.

Run tests:
    pytest tests/unit/adopt/test_doc_appender.py -v

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.adopt.doc_appender import (
    SOLOKIT_CLAUDE_MD_MARKER,
    SOLOKIT_README_MARKER,
    append_documentation,
    append_to_claude_md,
    append_to_readme,
)
from solokit.core.exceptions import FileOperationError


class TestAppendToReadme:
    """Tests for append_to_readme() function."""

    def test_append_to_existing_readme(self, project_with_readme):
        """Test appending Solokit section to existing README."""
        result = append_to_readme(project_with_readme)

        assert result is True

        readme = (project_with_readme / "README.md").read_text()
        assert "# Test Project" in readme  # Original content preserved
        assert "Existing content" in readme
        assert SOLOKIT_README_MARKER in readme
        assert "Session-Driven Development" in readme
        assert "sk start" in readme

    def test_append_adds_blank_line_before_section(self, project_with_readme):
        """Test that blank line is added before new section."""
        # Start with content ending without newline
        readme_path = project_with_readme / "README.md"
        readme_path.write_text("# Test Project\nNo trailing newline")

        append_to_readme(project_with_readme)

        content = readme_path.read_text()
        # Should have proper spacing before marker
        assert "\n\n" + SOLOKIT_README_MARKER in content or "\n" + SOLOKIT_README_MARKER in content

    def test_create_readme_if_missing(self, temp_project):
        """Test creating README.md if it doesn't exist."""
        result = append_to_readme(temp_project)

        assert result is True

        readme = (temp_project / "README.md").read_text()
        assert f"# {temp_project.name}" in readme
        assert SOLOKIT_README_MARKER in readme
        assert "Session-Driven Development" in readme

    def test_idempotency_with_marker(self, temp_project):
        """Test idempotency - don't double-append if marker exists."""
        readme_path = temp_project / "README.md"
        readme_path.write_text(f"# Project\n\n{SOLOKIT_README_MARKER}\nAlready added\n")

        result = append_to_readme(temp_project)

        assert result is False

        # Should not have duplicate content
        content = readme_path.read_text()
        assert content.count(SOLOKIT_README_MARKER) == 1

    def test_case_insensitive_readme_detection(self, tmp_path):
        """Test finding README with different casing."""
        project = tmp_path / "project"
        project.mkdir()

        # Create lowercase readme
        (project / "readme.md").write_text("# Project")

        result = append_to_readme(project)

        assert result is True

        # Should append to existing lowercase file
        content = (project / "readme.md").read_text()
        assert SOLOKIT_README_MARKER in content

    def test_uppercase_extension_detection(self, tmp_path):
        """Test finding README.MD (uppercase extension)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "README.MD").write_text("# Project")

        result = append_to_readme(project)

        assert result is True

        content = (project / "README.MD").read_text()
        assert SOLOKIT_README_MARKER in content

    def test_default_project_root(self):
        """Test using default project root (Path.cwd())."""
        with patch("solokit.adopt.doc_appender.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")

            with patch.object(Path, "exists", return_value=False):
                with patch.object(Path, "write_text"):
                    result = append_to_readme()

                    assert result is True
                    mock_cwd.assert_called_once()

    def test_readme_content_includes_commands(self, temp_project):
        """Test that README content includes key Solokit commands."""
        append_to_readme(temp_project)

        content = (temp_project / "README.md").read_text()

        # Check for essential commands
        assert "sk start" in content
        assert "sk end" in content
        assert "sk work-new" in content
        assert "sk work-list" in content
        assert "sk status" in content

    def test_readme_content_includes_session_files(self, temp_project):
        """Test that README content describes session files."""
        append_to_readme(temp_project)

        content = (temp_project / "README.md").read_text()

        assert ".session/" in content
        assert "specs/" in content
        assert "briefings/" in content
        assert "history/" in content
        assert "tracking/" in content

    def test_readme_includes_version(self, temp_project):
        """Test that README includes Solokit version."""
        append_to_readme(temp_project)

        content = (temp_project / "README.md").read_text()

        assert "Adopted with Solokit" in content

    def test_file_operation_error_on_write_failure(self, temp_project):
        """Test FileOperationError raised on write failure."""
        with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc:
                append_to_readme(temp_project)

            assert "Failed to update README.md" in exc.value.details

    def test_file_operation_error_on_read_failure(self, project_with_readme):
        """Test FileOperationError raised on read failure."""
        with patch.object(Path, "read_text", side_effect=OSError("Cannot read")):
            with pytest.raises(FileOperationError) as exc:
                append_to_readme(project_with_readme)

            assert "Failed to update README.md" in exc.value.details

    def test_appends_with_proper_spacing(self, project_with_readme):
        """Test that content is appended with proper spacing."""
        readme_path = project_with_readme / "README.md"
        original = "# Test Project\n\nContent\n"
        readme_path.write_text(original)

        append_to_readme(project_with_readme)

        content = readme_path.read_text()

        # Should have original content plus new section with proper spacing
        assert "# Test Project" in content
        assert "Content" in content
        # Should have at least one blank line before marker
        lines = content.split("\n")
        marker_index = next(i for i, line in enumerate(lines) if SOLOKIT_README_MARKER in line)
        assert lines[marker_index - 1] == ""  # Blank line before marker


class TestAppendToClaudeMd:
    """Tests for append_to_claude_md() function."""

    def test_append_to_existing_claude_md(self, project_with_claude_md):
        """Test appending Solokit section to existing CLAUDE.md."""
        result = append_to_claude_md("tier-2-standard", 80, project_with_claude_md)

        assert result is True

        claude_md = (project_with_claude_md / "CLAUDE.md").read_text()
        assert "# Claude Guidelines" in claude_md  # Original content preserved
        assert "Existing guidance" in claude_md
        assert SOLOKIT_CLAUDE_MD_MARKER in claude_md
        assert "Solokit Session Management" in claude_md
        assert "**Quality Tier**: Tier 2 Standard" in claude_md
        assert "**Test Coverage Target**: 80%" in claude_md

    def test_create_claude_md_if_missing(self, temp_project):
        """Test creating CLAUDE.md if it doesn't exist."""
        result = append_to_claude_md("tier-3-comprehensive", 90, temp_project)

        assert result is True

        claude_md = (temp_project / "CLAUDE.md").read_text()
        assert f"AI Assistant Guidelines for {temp_project.name}" in claude_md
        assert SOLOKIT_CLAUDE_MD_MARKER in claude_md
        assert "Solokit Session Management" in claude_md
        assert "**Quality Tier**: Tier 3 Comprehensive" in claude_md
        assert "**Test Coverage Target**: 90%" in claude_md

    def test_idempotency_with_marker(self, temp_project):
        """Test idempotency - don't double-append if marker exists."""
        claude_path = temp_project / "CLAUDE.md"
        claude_path.write_text(f"# Guidelines\n\n{SOLOKIT_CLAUDE_MD_MARKER}\nAlready added\n")

        result = append_to_claude_md("tier-2-standard", 80, temp_project)

        assert result is False

        # Should not have duplicate content
        content = claude_path.read_text()
        assert content.count(SOLOKIT_CLAUDE_MD_MARKER) == 1

    def test_tier_formatting_in_content(self, temp_project):
        """Test that tier is properly formatted in content."""
        append_to_claude_md("tier-1-essential", 60, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "**Quality Tier**: Tier 1 Essential" in content

    def test_tier_4_formatting(self, temp_project):
        """Test tier-4-production formatting."""
        append_to_claude_md("tier-4-production", 90, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "**Quality Tier**: Tier 4 Production" in content

    def test_coverage_target_in_content(self, temp_project):
        """Test that coverage target is included in content."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "**Test Coverage Target**: 80%" in content

    def test_default_project_root(self):
        """Test using default project root (Path.cwd())."""
        with patch("solokit.adopt.doc_appender.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")

            with patch.object(Path, "exists", return_value=False):
                with patch.object(Path, "write_text"):
                    result = append_to_claude_md("tier-2-standard", 80)

                    assert result is True
                    mock_cwd.assert_called_once()

    def test_claude_md_includes_work_item_guidance(self, temp_project):
        """Test that CLAUDE.md includes work item management guidance."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "Work Item Management" in content
        assert "sk work-new" in content
        assert "sk work-list" in content
        assert "NEVER edit" in content
        assert "work_items.json" in content

    def test_claude_md_includes_session_workflow(self, temp_project):
        """Test that CLAUDE.md includes session workflow guidance."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "Session Workflow" in content
        assert "/start" in content
        assert "/end" in content
        assert "/validate" in content

    def test_claude_md_includes_learning_guidance(self, temp_project):
        """Test that CLAUDE.md includes learning capture guidance."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "Learning Capture" in content
        assert "/learn" in content
        assert "/learn-search" in content

    def test_claude_md_includes_behavior_guidelines(self, temp_project):
        """Test that CLAUDE.md includes Claude behavior guidelines."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "Claude Behavior Guidelines" in content
        assert "Be Thorough" in content
        assert "What NOT to Do" in content

    def test_claude_md_includes_quick_reference(self, temp_project):
        """Test that CLAUDE.md includes quick reference table."""
        append_to_claude_md("tier-2-standard", 80, temp_project)

        content = (temp_project / "CLAUDE.md").read_text()

        assert "Quick Reference" in content
        assert "Solokit Commands" in content

    def test_file_operation_error_on_write_failure(self, temp_project):
        """Test FileOperationError raised on write failure."""
        with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc:
                append_to_claude_md("tier-2-standard", 80, temp_project)

            assert "Failed to update CLAUDE.md" in exc.value.details

    def test_appends_with_proper_spacing(self, project_with_claude_md):
        """Test that content is appended with proper spacing."""
        claude_path = project_with_claude_md / "CLAUDE.md"
        original = "# Guidelines\n\nContent\n"
        claude_path.write_text(original)

        append_to_claude_md("tier-2-standard", 80, project_with_claude_md)

        content = claude_path.read_text()

        # Should have original content plus new section with proper spacing
        assert "# Guidelines" in content
        assert "Content" in content


class TestAppendDocumentation:
    """Tests for append_documentation() convenience function."""

    def test_append_both_readme_and_claude_md(self, temp_project):
        """Test appending to both README.md and CLAUDE.md."""
        result = append_documentation("tier-2-standard", 80, temp_project)

        assert result["readme"] is True
        assert result["claude_md"] is True

        # Both files should exist
        assert (temp_project / "README.md").exists()
        assert (temp_project / "CLAUDE.md").exists()

    def test_returns_false_for_existing_markers(self, tmp_path):
        """Test returns False for files that already have markers."""
        project = tmp_path / "project"
        project.mkdir()

        # Create files with markers
        (project / "README.md").write_text(f"# Project\n\n{SOLOKIT_README_MARKER}\n")
        (project / "CLAUDE.md").write_text(f"# Claude\n\n{SOLOKIT_CLAUDE_MD_MARKER}\n")

        result = append_documentation("tier-2-standard", 80, project)

        assert result["readme"] is False
        assert result["claude_md"] is False

    def test_mixed_existing_and_new(self, project_with_readme):
        """Test mixed scenario - README exists, CLAUDE.md is new."""
        result = append_documentation("tier-2-standard", 80, project_with_readme)

        # README should be appended
        assert result["readme"] is True
        # CLAUDE.md should be created
        assert result["claude_md"] is True

    def test_default_project_root(self):
        """Test using default project root (Path.cwd())."""
        with patch("solokit.adopt.doc_appender.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")

            with patch("solokit.adopt.doc_appender.append_to_readme") as mock_readme:
                with patch("solokit.adopt.doc_appender.append_to_claude_md") as mock_claude:
                    mock_readme.return_value = True
                    mock_claude.return_value = True

                    result = append_documentation("tier-2-standard", 80)

                    assert result["readme"] is True
                    assert result["claude_md"] is True

    def test_passes_tier_and_coverage_correctly(self, temp_project):
        """Test that tier and coverage are passed correctly to both functions."""
        append_documentation("tier-3-comprehensive", 90, temp_project)

        claude_md = (temp_project / "CLAUDE.md").read_text()

        # CLAUDE.md should have tier and coverage
        assert "**Quality Tier**: Tier 3 Comprehensive" in claude_md
        assert "**Test Coverage Target**: 90%" in claude_md

    def test_propagates_file_operation_error(self, temp_project):
        """Test that FileOperationError is propagated from underlying functions."""
        with patch(
            "solokit.adopt.doc_appender.append_to_readme",
            side_effect=FileOperationError(
                operation="write", file_path="README.md", details="Test error"
            ),
        ):
            with pytest.raises(FileOperationError):
                append_documentation("tier-2-standard", 80, temp_project)


class TestMarkerDetection:
    """Tests for marker detection helper function."""

    def test_check_section_exists_true(self, tmp_path):
        """Test _check_section_exists returns True when marker present."""
        from solokit.adopt.doc_appender import _check_section_exists

        file_path = tmp_path / "test.md"
        file_path.write_text(f"# Content\n\n{SOLOKIT_README_MARKER}\n")

        result = _check_section_exists(file_path, SOLOKIT_README_MARKER)

        assert result is True

    def test_check_section_exists_false(self, tmp_path):
        """Test _check_section_exists returns False when marker absent."""
        from solokit.adopt.doc_appender import _check_section_exists

        file_path = tmp_path / "test.md"
        file_path.write_text("# Content\n\nNo marker here\n")

        result = _check_section_exists(file_path, SOLOKIT_README_MARKER)

        assert result is False

    def test_check_section_file_not_exists(self, tmp_path):
        """Test _check_section_exists returns False when file doesn't exist."""
        from solokit.adopt.doc_appender import _check_section_exists

        file_path = tmp_path / "nonexistent.md"

        result = _check_section_exists(file_path, SOLOKIT_README_MARKER)

        assert result is False

    def test_check_section_handles_read_error(self, tmp_path):
        """Test _check_section_exists handles read errors gracefully."""
        from solokit.adopt.doc_appender import _check_section_exists

        file_path = tmp_path / "test.md"
        file_path.write_text("content")

        with patch.object(Path, "read_text", side_effect=OSError("Cannot read")):
            result = _check_section_exists(file_path, SOLOKIT_README_MARKER)

            assert result is False


class TestVersionRetrieval:
    """Tests for version retrieval helper function."""

    def test_get_solokit_version_success(self):
        """Test _get_solokit_version retrieves version successfully."""
        from solokit.adopt.doc_appender import _get_solokit_version

        version = _get_solokit_version()

        # Should return a version string (or "unknown" if not installed)
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_solokit_version_fallback(self):
        """Test _get_solokit_version returns 'unknown' on failure."""
        from importlib.metadata import PackageNotFoundError

        from solokit.adopt.doc_appender import _get_solokit_version

        # Patch at the module level where it's imported
        with patch("importlib.metadata.version", side_effect=PackageNotFoundError("Not found")):
            version = _get_solokit_version()

            assert version == "unknown"


class TestReadmeContentGeneration:
    """Tests for README content generation."""

    def test_readme_section_structure(self):
        """Test README section has proper structure."""
        from solokit.adopt.doc_appender import _get_readme_solokit_section

        content = _get_readme_solokit_section()

        # Should have marker
        assert SOLOKIT_README_MARKER in content

        # Should have main heading
        assert "## Session-Driven Development" in content

        # Should have sections
        assert "### Quick Start" in content
        assert "### Session Commands" in content
        assert "### Work Item Commands" in content
        assert "### Learning Commands" in content
        assert "### Session Files" in content


class TestClaudeMdContentGeneration:
    """Tests for CLAUDE.md content generation."""

    def test_claude_md_section_structure(self):
        """Test CLAUDE.md section has proper structure."""
        from solokit.adopt.doc_appender import _get_claude_md_solokit_section

        content = _get_claude_md_solokit_section("tier-2-standard", 80)

        # Should have marker
        assert SOLOKIT_CLAUDE_MD_MARKER in content

        # Should have main sections
        assert "## Solokit Session Management" in content
        assert "### Understanding Solokit Commands" in content
        assert "### Work Item Management" in content
        assert "### Session Workflow" in content
        assert "### Learning Capture" in content
        assert "## Claude Behavior Guidelines" in content
        assert "## What NOT to Do" in content
        assert "## Quick Reference" in content

    def test_claude_md_tier_formatting(self):
        """Test tier formatting in CLAUDE.md content."""
        from solokit.adopt.doc_appender import _get_claude_md_solokit_section

        content = _get_claude_md_solokit_section("tier-3-comprehensive", 90)

        assert "**Quality Tier**: Tier 3 Comprehensive" in content
        assert "**Test Coverage Target**: 90%" in content


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_readme_with_no_trailing_newline(self, tmp_path):
        """Test appending to README with no trailing newline."""
        project = tmp_path / "project"
        project.mkdir()
        readme = project / "README.md"
        readme.write_text("# Project")  # No trailing newline

        result = append_to_readme(project)

        assert result is True

        content = readme.read_text()
        # Should have proper spacing
        assert SOLOKIT_README_MARKER in content

    def test_readme_with_single_trailing_newline(self, tmp_path):
        """Test appending to README with single trailing newline."""
        project = tmp_path / "project"
        project.mkdir()
        readme = project / "README.md"
        readme.write_text("# Project\n")

        result = append_to_readme(project)

        assert result is True

        content = readme.read_text()
        assert SOLOKIT_README_MARKER in content

    def test_empty_readme_file(self, tmp_path):
        """Test appending to empty README file."""
        project = tmp_path / "project"
        project.mkdir()
        readme = project / "README.md"
        readme.write_text("")

        result = append_to_readme(project)

        assert result is True

        content = readme.read_text()
        assert SOLOKIT_README_MARKER in content

    def test_claude_md_with_no_trailing_newline(self, tmp_path):
        """Test appending to CLAUDE.md with no trailing newline."""
        project = tmp_path / "project"
        project.mkdir()
        claude_md = project / "CLAUDE.md"
        claude_md.write_text("# Guidelines")  # No trailing newline

        result = append_to_claude_md("tier-2-standard", 80, project)

        assert result is True

        content = claude_md.read_text()
        assert SOLOKIT_CLAUDE_MD_MARKER in content
