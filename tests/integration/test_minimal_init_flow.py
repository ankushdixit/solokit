"""
Integration tests for minimal init flow.

Tests the complete end-to-end flow of `sk init --minimal`.

Run tests:
    pytest tests/integration/test_minimal_init_flow.py -v

Target: Full flow validation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMinimalInitFlow:
    """Integration tests for the complete minimal init flow."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_full_minimal_init_creates_expected_structure(self, temp_project_dir):
        """Test that minimal init creates all expected directories and files."""
        # Mock GitHub setup to skip interactive prompts
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            result = run_minimal_init(temp_project_dir)

            assert result == 0

            # Verify directory structure
            assert (temp_project_dir / ".session").exists()
            assert (temp_project_dir / ".session" / "tracking").exists()
            assert (temp_project_dir / ".session" / "briefings").exists()
            assert (temp_project_dir / ".session" / "history").exists()
            assert (temp_project_dir / ".session" / "specs").exists()
            assert (temp_project_dir / ".session" / "guides").exists()

            # Verify documentation files
            assert (temp_project_dir / "CLAUDE.md").exists()
            assert (temp_project_dir / "README.md").exists()
            assert (temp_project_dir / "CHANGELOG.md").exists()

            # Verify config.json
            assert (temp_project_dir / ".session" / "config.json").exists()

            # Verify .gitignore
            assert (temp_project_dir / ".gitignore").exists()

    def test_minimal_init_config_has_quality_gates_disabled(self, temp_project_dir):
        """Test that config.json has quality gates disabled."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            config = json.loads((temp_project_dir / ".session" / "config.json").read_text())

            assert config["quality_gates"]["tier"] == "minimal"
            assert config["quality_gates"]["test_execution"]["enabled"] is False
            assert config["quality_gates"]["linting"]["enabled"] is False
            assert config["quality_gates"]["security"]["enabled"] is False
            assert config["quality_gates"]["documentation"]["enabled"] is False

    def test_minimal_init_claude_commands_installed(self, temp_project_dir):
        """Test that Claude commands are installed."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            # Verify .claude/commands directory exists
            commands_dir = temp_project_dir / ".claude" / "commands"
            assert commands_dir.exists()

            # Verify at least some commands are installed
            command_files = list(commands_dir.glob("*.md"))
            assert len(command_files) > 0

    def test_minimal_init_guides_copied(self, temp_project_dir):
        """Test that guide files are copied."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            guides_dir = temp_project_dir / ".session" / "guides"

            # Verify guide files exist
            assert (guides_dir / "PRD_WRITING_GUIDE.md").exists()
            assert (guides_dir / "STACK_GUIDE.md").exists()

    def test_minimal_init_creates_git_repo(self, temp_project_dir):
        """Test that git repository is initialized."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            # Verify .git directory exists
            assert (temp_project_dir / ".git").exists()

    def test_minimal_init_fails_if_already_initialized(self, temp_project_dir):
        """Test that minimal init fails if project already initialized."""
        # Create .session directory to simulate existing init
        (temp_project_dir / ".session").mkdir()

        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            result = run_minimal_init(temp_project_dir)

            assert result == 1

    def test_minimal_init_gitignore_has_solokit_entries(self, temp_project_dir):
        """Test that .gitignore has Solokit-specific entries."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            gitignore_content = (temp_project_dir / ".gitignore").read_text()

            assert ".session/briefings/" in gitignore_content
            assert ".session/history/" in gitignore_content

    def test_minimal_init_claude_md_content(self, temp_project_dir):
        """Test that CLAUDE.md has expected content."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            claude_content = (temp_project_dir / "CLAUDE.md").read_text()

            # Verify essential sections
            assert "Solokit Usage Guide" in claude_content
            assert "/start" in claude_content
            assert "/end" in claude_content
            assert "minimal mode" in claude_content

    def test_minimal_init_readme_content(self, temp_project_dir):
        """Test that README.md has expected content."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            readme_content = (temp_project_dir / "README.md").read_text()

            # Verify essential sections
            assert "Session-Driven Development" in readme_content
            assert "/work-new" in readme_content

    def test_minimal_init_changelog_content(self, temp_project_dir):
        """Test that CHANGELOG.md has expected content."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            changelog_content = (temp_project_dir / "CHANGELOG.md").read_text()

            assert "# Changelog" in changelog_content
            assert "[Unreleased]" in changelog_content

    def test_minimal_init_tracking_files_initialized(self, temp_project_dir):
        """Test that tracking files are properly initialized."""
        with patch("solokit.github.setup.GitHubSetup.run_interactive") as mock_github:
            mock_result = type(
                "Result",
                (),
                {"success": True, "skipped": True, "repo_url": None, "error_message": None},
            )()
            mock_github.return_value = mock_result

            from solokit.init.orchestrator import run_minimal_init

            run_minimal_init(temp_project_dir)

            tracking_dir = temp_project_dir / ".session" / "tracking"

            # Verify tracking files exist and are valid JSON
            work_items = json.loads((tracking_dir / "work_items.json").read_text())
            assert "work_items" in work_items

            learnings = json.loads((tracking_dir / "learnings.json").read_text())
            assert "learnings" in learnings

            stack_updates = json.loads((tracking_dir / "stack_updates.json").read_text())
            assert "updates" in stack_updates
