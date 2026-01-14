"""
Tests for minimal init mode.

Validates the --minimal initialization flow that creates session tracking
without templates or quality tiers.

Run tests:
    pytest tests/unit/init/test_minimal_init.py -v

Target: 90%+ coverage
"""

import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.init.claude_md_generator import generate_minimal_claude_md
from solokit.init.gitignore_updater import update_minimal_gitignore
from solokit.init.initial_commit import create_minimal_initial_commit
from solokit.init.readme_generator import generate_minimal_readme
from solokit.init.session_structure import initialize_minimal_tracking_files


class TestInitializeMinimalTrackingFiles:
    """Tests for initialize_minimal_tracking_files()."""

    def test_creates_minimal_config(self, tmp_path, tracking_template_files):
        """Test that minimal config has quality gates disabled."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)
        (tmp_path / ".session" / "guides").mkdir(parents=True)

        import solokit.init.session_structure as session_structure_module

        fake_solokit_dir = tmp_path / "fake_solokit"
        fake_init_dir = fake_solokit_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_solokit_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_minimal_tracking_files(tmp_path)

            config = json.loads((tmp_path / ".session" / "config.json").read_text())

            # Verify quality gates are disabled
            assert config["quality_gates"]["tier"] == "minimal"
            assert config["quality_gates"]["coverage_threshold"] == 0
            assert config["quality_gates"]["test_execution"]["enabled"] is False
            assert config["quality_gates"]["test_execution"]["required"] is False
            assert config["quality_gates"]["linting"]["enabled"] is False
            assert config["quality_gates"]["security"]["enabled"] is False
            assert config["quality_gates"]["documentation"]["enabled"] is False

            # Spec completeness should be enabled but not required
            assert config["quality_gates"]["spec_completeness"]["enabled"] is True
            assert config["quality_gates"]["spec_completeness"]["required"] is False

    def test_creates_tracking_files(self, tmp_path, tracking_template_files):
        """Test that tracking files are created."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)
        (tmp_path / ".session" / "guides").mkdir(parents=True)

        import solokit.init.session_structure as session_structure_module

        fake_solokit_dir = tmp_path / "fake_solokit"
        fake_init_dir = fake_solokit_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_solokit_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_minimal_tracking_files(tmp_path)

            # Verify tracking files exist
            assert (tmp_path / ".session" / "config.json").exists()
            assert (tmp_path / ".session" / "tracking" / "stack_updates.json").exists()
            assert (tmp_path / ".session" / "tracking" / "tree_updates.json").exists()

    def test_copies_guides(self, tmp_path, tracking_template_files_with_guides):
        """Test that guide files are copied."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)
        (tmp_path / ".session" / "guides").mkdir(parents=True)

        import solokit.init.session_structure as session_structure_module

        fake_solokit_dir = tmp_path / "fake_solokit"
        fake_init_dir = fake_solokit_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_solokit_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files_with_guides.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)
            elif item.is_dir():
                shutil.copytree(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_minimal_tracking_files(tmp_path)

            # Verify guide files were copied
            assert (tmp_path / ".session" / "guides" / "STACK_GUIDE.md").exists()
            assert (tmp_path / ".session" / "guides" / "PRD_WRITING_GUIDE.md").exists()

    def test_git_workflow_config(self, tmp_path, tracking_template_files):
        """Test that git workflow config is properly set."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)
        (tmp_path / ".session" / "guides").mkdir(parents=True)

        import solokit.init.session_structure as session_structure_module

        fake_solokit_dir = tmp_path / "fake_solokit"
        fake_init_dir = fake_solokit_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_solokit_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_minimal_tracking_files(tmp_path)

            config = json.loads((tmp_path / ".session" / "config.json").read_text())

            assert config["git_workflow"]["mode"] == "pr"
            assert config["git_workflow"]["auto_push"] is True
            assert config["git_workflow"]["auto_create_pr"] is True


class TestGenerateMinimalClaudeMd:
    """Tests for generate_minimal_claude_md()."""

    def test_generates_claude_md(self, tmp_path):
        """Test that CLAUDE.md is generated."""
        path = generate_minimal_claude_md(tmp_path)

        assert path.exists()
        assert path.name == "CLAUDE.md"

    def test_contains_solokit_usage_guide(self, tmp_path):
        """Test that CLAUDE.md contains Solokit usage guide."""
        generate_minimal_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()

        assert "## Solokit Usage Guide" in content
        assert "/start" in content
        assert "/end" in content
        assert "/work-new" in content
        assert "/work-list" in content

    def test_contains_project_name(self, tmp_path):
        """Test that CLAUDE.md contains project name."""
        generate_minimal_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()

        assert f"# {tmp_path.name}" in content

    def test_contains_minimal_mode_indicator(self, tmp_path):
        """Test that CLAUDE.md indicates minimal mode."""
        generate_minimal_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()

        assert "minimal mode" in content

    def test_no_stack_specific_content(self, tmp_path):
        """Test that CLAUDE.md does not contain stack-specific content."""
        generate_minimal_claude_md(tmp_path)

        content = (tmp_path / "CLAUDE.md").read_text()

        # Should not have stack-specific sections
        assert "npm install" not in content.lower()
        assert "pip install" not in content.lower()
        assert "quality tier" not in content.lower()

    def test_error_handling(self, tmp_path):
        """Test error handling when write fails."""
        with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
            with pytest.raises(FileOperationError):
                generate_minimal_claude_md(tmp_path)


class TestGenerateMinimalReadme:
    """Tests for generate_minimal_readme()."""

    def test_generates_readme(self, tmp_path):
        """Test that README.md is generated."""
        path = generate_minimal_readme(tmp_path)

        assert path.exists()
        assert path.name == "README.md"

    def test_contains_project_name(self, tmp_path):
        """Test that README.md contains project name."""
        generate_minimal_readme(tmp_path)

        content = (tmp_path / "README.md").read_text()

        assert f"# {tmp_path.name}" in content

    def test_contains_session_commands(self, tmp_path):
        """Test that README.md contains session commands."""
        generate_minimal_readme(tmp_path)

        content = (tmp_path / "README.md").read_text()

        assert "/work-new" in content
        assert "/start" in content
        assert "/end" in content

    def test_no_stack_specific_content(self, tmp_path):
        """Test that README.md does not contain stack-specific content."""
        generate_minimal_readme(tmp_path)

        content = (tmp_path / "README.md").read_text()

        # Should not have stack-specific sections
        assert "npm run" not in content
        assert "pytest" not in content
        assert "coverage target" not in content.lower()

    def test_error_handling(self, tmp_path):
        """Test error handling when write fails."""
        with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
            with pytest.raises(FileOperationError):
                generate_minimal_readme(tmp_path)


class TestUpdateMinimalGitignore:
    """Tests for update_minimal_gitignore()."""

    def test_creates_gitignore_if_not_exists(self, tmp_path):
        """Test that .gitignore is created if it doesn't exist."""
        update_minimal_gitignore(tmp_path)

        assert (tmp_path / ".gitignore").exists()

    def test_adds_solokit_entries(self, tmp_path):
        """Test that Solokit entries are added."""
        update_minimal_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()

        assert ".session/briefings/" in content
        assert ".session/history/" in content

    def test_adds_os_specific_entries(self, tmp_path):
        """Test that OS-specific entries are added."""
        update_minimal_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()

        assert ".DS_Store" in content
        assert "Thumbs.db" in content

    def test_does_not_add_stack_specific_entries(self, tmp_path):
        """Test that stack-specific entries are NOT added."""
        update_minimal_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()

        # Should not have stack-specific patterns
        assert "node_modules/" not in content
        assert "__pycache__/" not in content
        assert ".next/" not in content
        assert "venv/" not in content

    def test_appends_to_existing_gitignore(self, tmp_path):
        """Test that entries are appended to existing .gitignore."""
        existing_content = "# Existing content\n*.log\n"
        (tmp_path / ".gitignore").write_text(existing_content)

        update_minimal_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()

        assert "*.log" in content
        assert ".session/briefings/" in content

    def test_does_not_duplicate_entries(self, tmp_path):
        """Test that existing entries are not duplicated."""
        existing_content = ".session/briefings/\n.DS_Store\n"
        (tmp_path / ".gitignore").write_text(existing_content)

        update_minimal_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()

        # Count occurrences - should only appear once
        assert content.count(".session/briefings/") == 1


class TestCreateMinimalInitialCommit:
    """Tests for create_minimal_initial_commit()."""

    def test_creates_commit(self, tmp_path):
        """Test that initial commit is created."""
        # Initialize git repo
        from solokit.core.command_runner import CommandRunner

        runner = CommandRunner(working_dir=tmp_path)
        runner.run(["git", "init"])
        runner.run(["git", "config", "user.email", "test@test.com"])
        runner.run(["git", "config", "user.name", "Test User"])

        # Create some files
        (tmp_path / "README.md").write_text("# Test")

        result = create_minimal_initial_commit(tmp_path)

        assert result is True

    def test_commit_message_content(self, tmp_path):
        """Test that commit message has correct content."""
        from solokit.core.command_runner import CommandRunner

        runner = CommandRunner(working_dir=tmp_path)
        runner.run(["git", "init"])
        runner.run(["git", "config", "user.email", "test@test.com"])
        runner.run(["git", "config", "user.name", "Test User"])

        (tmp_path / "README.md").write_text("# Test")

        create_minimal_initial_commit(tmp_path)

        # Get commit message
        result = runner.run(["git", "log", "-1", "--format=%B"])
        message = result.stdout

        assert "Solokit (minimal mode)" in message
        assert "Quality gates: disabled" in message

    def test_skips_if_commits_exist(self, tmp_path):
        """Test that commit is skipped if repo already has commits."""
        from solokit.core.command_runner import CommandRunner

        runner = CommandRunner(working_dir=tmp_path)
        runner.run(["git", "init"])
        runner.run(["git", "config", "user.email", "test@test.com"])
        runner.run(["git", "config", "user.name", "Test User"])

        (tmp_path / "README.md").write_text("# Test")
        runner.run(["git", "add", "-A"])
        runner.run(["git", "commit", "-m", "Existing commit"])

        result = create_minimal_initial_commit(tmp_path)

        assert result is True

        # Verify only one commit exists
        result = runner.run(["git", "rev-list", "--count", "HEAD"])
        assert result.stdout.strip() == "1"


class TestMinimalInitArgParsing:
    """Tests for --minimal argument parsing in init.py."""

    def test_minimal_flag_recognized(self):
        """Test that --minimal flag is recognized."""

        from solokit.project.init import main

        # Patch argparse to capture args
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = Mock()
            mock_args.minimal = True
            mock_args.template = None
            mock_args.tier = None
            mock_args.coverage = None
            mock_parse.return_value = mock_args

            with patch("solokit.init.orchestrator.run_minimal_init", return_value=0) as mock_init:
                result = main()

                mock_init.assert_called_once()
                assert result == 0

    def test_minimal_with_template_fails(self):
        """Test that --minimal with --template fails."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = Mock()
            mock_args.minimal = True
            mock_args.template = "saas_t3"
            mock_args.tier = None
            mock_args.coverage = None
            mock_parse.return_value = mock_args

            from solokit.project.init import main

            result = main()

            assert result == 1

    def test_minimal_with_tier_fails(self):
        """Test that --minimal with --tier fails."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = Mock()
            mock_args.minimal = True
            mock_args.template = None
            mock_args.tier = "tier-2-standard"
            mock_args.coverage = None
            mock_parse.return_value = mock_args

            from solokit.project.init import main

            result = main()

            assert result == 1

    def test_minimal_with_coverage_fails(self):
        """Test that --minimal with --coverage fails."""
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = Mock()
            mock_args.minimal = True
            mock_args.template = None
            mock_args.tier = None
            mock_args.coverage = 80
            mock_parse.return_value = mock_args

            from solokit.project.init import main

            result = main()

            assert result == 1
