"""
Tests for git_setup module.

Validates git repository initialization and project blank checks.

Run tests:
    pytest tests/unit/init/test_git_setup.py -v

Run with coverage:
    pytest tests/unit/init/test_git_setup.py --cov=solokit.init.git_setup --cov-report=term-missing

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import ErrorCode, GitError, ValidationError
from solokit.init.git_setup import (
    check_blank_project_or_exit,
    check_or_init_git,
    is_blank_project,
)


class TestIsBlankProject:
    """Tests for is_blank_project()."""

    def test_blank_project_empty_dir(self, temp_project):
        """Test blank project with only .git and README."""
        (temp_project / ".git").mkdir()
        (temp_project / "README.md").write_text("# Test")

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is True
        assert blocking == []

    def test_blank_project_with_docs_dir(self, temp_project):
        """Test blank project with docs/ directory."""
        (temp_project / "docs").mkdir()
        (temp_project / "docs" / ".gitkeep").write_text("")

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is True
        assert blocking == []

    def test_non_blank_with_package_json(self, temp_project):
        """Test non-blank project with package.json."""
        (temp_project / "package.json").write_text('{"name": "test"}')

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert "package.json (Node.js project detected)" in blocking

    def test_non_blank_with_pyproject_toml(self, temp_project):
        """Test non-blank project with pyproject.toml."""
        (temp_project / "pyproject.toml").write_text("[project]")

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert "pyproject.toml (Python project detected)" in blocking

    def test_non_blank_with_session_dir(self, temp_project):
        """Test non-blank project with .session/ (already initialized)."""
        (temp_project / ".session").mkdir()

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert ".session/ (Solokit already initialized)" in blocking

    def test_non_blank_with_src_directory_content(self, project_with_src):
        """Test non-blank project with src/ containing files."""
        is_blank, blocking = is_blank_project(project_with_src)

        assert is_blank is False
        assert "src/ directory" in blocking

    def test_blank_with_src_only_gitkeep(self, temp_project):
        """Test blank project when src/ only has .gitkeep."""
        src = temp_project / "src"
        src.mkdir()
        (src / ".gitkeep").write_text("")

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is True
        assert blocking == []

    def test_non_blank_with_node_modules(self, temp_project):
        """Test non-blank project with node_modules/."""
        node_modules = temp_project / "node_modules"
        node_modules.mkdir()
        (node_modules / "package").mkdir()

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert "node_modules/ directory" in blocking

    def test_non_blank_with_venv(self, temp_project):
        """Test non-blank project with venv/."""
        venv = temp_project / "venv"
        venv.mkdir()
        (venv / "lib").mkdir()

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert "venv/ directory" in blocking

    def test_non_blank_multiple_blocking_files(self, temp_project):
        """Test non-blank project with multiple blocking files."""
        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "tsconfig.json").write_text("{}")
        src = temp_project / "src"
        src.mkdir()
        (src / "index.ts").write_text("export {};")

        is_blank, blocking = is_blank_project(temp_project)

        assert is_blank is False
        assert len(blocking) >= 2
        assert any("package.json" in b for b in blocking)
        assert any("src/" in b for b in blocking)

    def test_defaults_to_cwd_when_none(self):
        """Test that function defaults to current directory when project_root is None."""
        with patch("solokit.init.git_setup.Path.cwd") as mock_cwd:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_cwd.return_value = mock_path

            # Create mock for __truediv__ operator to return paths that don't exist
            # Note: __truediv__ is called as self / other, so it receives self (unused) and other (the path part)
            def mock_div(self, other):
                mock_file = Mock()
                mock_file.exists.return_value = False
                mock_file.is_dir.return_value = False
                return mock_file

            mock_path.__class__.__truediv__ = mock_div

            is_blank, blocking = is_blank_project(None)

            assert is_blank is True
            mock_cwd.assert_called_once()

    def test_permission_error_on_directory(self, temp_project):
        """Test handling of permission errors when reading directories."""
        src = temp_project / "src"
        src.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(Path, "iterdir", side_effect=PermissionError("Access denied")):
            is_blank, blocking = is_blank_project(temp_project)

            assert is_blank is False
            assert any("permission denied" in b for b in blocking)


class TestCheckBlankProjectOrExit:
    """Tests for check_blank_project_or_exit()."""

    def test_blank_project_no_exception(self, blank_project):
        """Test that blank project doesn't raise exception."""
        # Remove package.json if exists
        package_json = blank_project / "package.json"
        if package_json.exists():
            package_json.unlink()

        # Should not raise
        check_blank_project_or_exit(blank_project)

    def test_non_blank_raises_validation_error(self, non_blank_project):
        """Test that non-blank project raises ValidationError."""
        with pytest.raises(ValidationError) as exc:
            check_blank_project_or_exit(non_blank_project)

        assert exc.value.code == ErrorCode.PROJECT_NOT_BLANK
        assert "Cannot initialize" in exc.value.message
        assert "package.json" in exc.value.message

    def test_error_message_contains_blocking_files(self, temp_project):
        """Test that error message lists all blocking files."""
        (temp_project / "package.json").write_text('{"name": "test"}')
        (temp_project / "tsconfig.json").write_text("{}")

        with pytest.raises(ValidationError) as exc:
            check_blank_project_or_exit(temp_project)

        assert "package.json" in exc.value.message
        assert "tsconfig.json" in exc.value.message

    def test_error_includes_remediation(self, non_blank_project):
        """Test that error includes remediation steps."""
        with pytest.raises(ValidationError) as exc:
            check_blank_project_or_exit(non_blank_project)

        assert "Solutions:" in exc.value.message
        assert "sk adopt" in exc.value.message
        assert "mkdir my-project" in exc.value.message
        assert "sk adopt" in exc.value.remediation

    def test_context_includes_existing_files(self, non_blank_project):
        """Test that exception context includes existing files list."""
        with pytest.raises(ValidationError) as exc:
            check_blank_project_or_exit(non_blank_project)

        assert "existing_files" in exc.value.context
        assert isinstance(exc.value.context["existing_files"], list)


class TestCheckOrInitGit:
    """Tests for check_or_init_git()."""

    def test_git_already_exists(self, mock_git_repo):
        """Test when git repository already exists."""
        result = check_or_init_git(mock_git_repo)

        assert result is True

    def test_git_init_success(self, temp_project, mock_successful_command):
        """Test successful git initialization."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = mock_successful_command

            result = check_or_init_git(temp_project)

            assert result is True
            # Should be called twice: git init + git branch -m main
            assert mock_runner.run.call_count == 2
            # First call: git init
            assert mock_runner.run.call_args_list[0][0][0] == ["git", "init"]
            # Second call: git branch -m main
            assert mock_runner.run.call_args_list[1][0][0] == ["git", "branch", "-m", "main"]

    def test_git_init_fails(self, temp_project, mock_failed_command):
        """Test git init command failure."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = mock_failed_command

            with pytest.raises(GitError) as exc:
                check_or_init_git(temp_project)

            assert exc.value.code == ErrorCode.GIT_COMMAND_FAILED
            assert "Failed to initialize git repository" in exc.value.message

    def test_git_branch_rename_fails(self, temp_project):
        """Test git branch rename failure."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner

            # First call (git init) succeeds, second (git branch) fails
            mock_runner.run.side_effect = [
                Mock(success=True, stdout="", stderr="", returncode=0),
                Mock(success=False, stdout="", stderr="Branch error", returncode=1),
            ]

            with pytest.raises(GitError) as exc:
                check_or_init_git(temp_project)

            assert exc.value.code == ErrorCode.GIT_COMMAND_FAILED
            assert "Failed to set default branch" in exc.value.message

    def test_defaults_to_cwd(self):
        """Test that function defaults to current directory when project_root is None."""
        with patch("solokit.init.git_setup.Path.cwd") as mock_cwd:
            mock_path = Mock()
            mock_git = Mock()
            mock_git.exists.return_value = True
            # Use spec to allow __truediv__ method
            mock_path.__truediv__ = Mock(return_value=mock_git)
            mock_cwd.return_value = mock_path

            result = check_or_init_git(None)

            assert result is True
            mock_cwd.assert_called_once()

    def test_uses_correct_timeout(self, temp_project):
        """Test that CommandRunner uses GIT_QUICK_TIMEOUT."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True, stdout="", stderr="", returncode=0)

            check_or_init_git(temp_project)

            # Verify CommandRunner was initialized with GIT_QUICK_TIMEOUT
            from solokit.core.constants import GIT_QUICK_TIMEOUT

            mock_runner_class.assert_called_once_with(
                default_timeout=GIT_QUICK_TIMEOUT, working_dir=temp_project
            )

    def test_error_context_includes_stderr(self, temp_project):
        """Test that GitError context includes stderr output."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(
                success=False, stdout="", stderr="Permission denied", returncode=128
            )

            with pytest.raises(GitError) as exc:
                check_or_init_git(temp_project)

            assert "stderr" in exc.value.context
            assert exc.value.context["stderr"] == "Permission denied"

    def test_remediation_message_provided(self, temp_project, mock_failed_command):
        """Test that remediation message is provided on error."""
        with patch("solokit.init.git_setup.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = mock_failed_command

            with pytest.raises(GitError) as exc:
                check_or_init_git(temp_project)

            assert exc.value.remediation is not None
            assert "git is installed" in exc.value.remediation.lower()
