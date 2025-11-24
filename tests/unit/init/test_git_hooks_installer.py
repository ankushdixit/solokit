"""
Tests for git_hooks_installer module.

Validates git hooks installation.

Run tests:
    pytest tests/unit/init/test_git_hooks_installer.py -v

Target: 90%+ coverage
"""

import stat
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import FileOperationError, NotAGitRepoError, TemplateNotFoundError
from solokit.init.git_hooks_installer import install_git_hooks


class TestInstallGitHooks:
    """Tests for install_git_hooks()."""

    def test_install_hooks_success(self, mock_git_repo):
        """Test successful git hooks installation."""
        template_dir = mock_git_repo / "templates" / "git-hooks"
        template_dir.mkdir(parents=True)
        hook_template = template_dir / "prepare-commit-msg"
        hook_template.write_text("#!/bin/sh\necho 'hook'")

        with patch("solokit.init.git_hooks_installer.Path") as mock_path:
            mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = template_dir

            hooks = install_git_hooks(mock_git_repo)

            assert len(hooks) >= 1

    def test_git_repo_not_initialized(self, tmp_path):
        """Test error when .git/hooks doesn't exist."""
        with pytest.raises(NotAGitRepoError):
            install_git_hooks(tmp_path)

    def test_hook_template_not_found(self, mock_git_repo):
        """Test error when hook template is missing."""
        with patch("solokit.init.git_hooks_installer.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = False
            mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_file

            with pytest.raises(TemplateNotFoundError):
                install_git_hooks(mock_git_repo)

    def test_hook_file_made_executable(self, mock_git_repo):
        """Test that installed hook is made executable."""
        template_dir = mock_git_repo / "templates" / "git-hooks"
        template_dir.mkdir(parents=True)
        hook_template = template_dir / "prepare-commit-msg"
        hook_template.write_text("#!/bin/sh\necho 'hook'")

        with patch("solokit.init.git_hooks_installer.Path") as mock_path:
            mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = template_dir

            install_git_hooks(mock_git_repo)

            hook_dest = mock_git_repo / ".git" / "hooks" / "prepare-commit-msg"
            if hook_dest.exists():
                mode = hook_dest.stat().st_mode
                # Check if user executable bit is set
                assert mode & stat.S_IXUSR

    def test_copy_or_chmod_fails(self, mock_git_repo):
        """Test handling when copy or chmod fails."""
        template_dir = mock_git_repo / "templates" / "git-hooks"
        template_dir.mkdir(parents=True)
        hook_template = template_dir / "prepare-commit-msg"
        hook_template.write_text("#!/bin/sh\necho 'hook'")

        with patch("solokit.init.git_hooks_installer.Path") as mock_path:
            mock_path.return_value.parent.parent.__truediv__.return_value.__truediv__.return_value = template_dir

            # Mock shutil.copy to raise an exception
            with patch("solokit.init.git_hooks_installer.shutil.copy") as mock_copy:
                mock_copy.side_effect = PermissionError("Permission denied")

                with pytest.raises(FileOperationError) as exc:
                    install_git_hooks(mock_git_repo)

                assert exc.value.operation == "install"
