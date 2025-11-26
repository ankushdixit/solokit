"""
Tests for GitHub setup module.

Validates GitHub repository creation and connection functionality.

Run tests:
    pytest tests/unit/github/test_setup.py -v

Run with coverage:
    pytest tests/unit/github/test_setup.py --cov=solokit.github.setup --cov-report=term-missing
"""

from unittest.mock import Mock, patch

from solokit.github.setup import GitHubSetup, GitHubSetupResult, run_github_setup


class TestGitHubSetupResult:
    """Tests for GitHubSetupResult dataclass."""

    def test_success_result(self):
        """Test successful result with repo URL."""
        result = GitHubSetupResult(success=True, repo_url="https://github.com/user/repo")

        assert result.success is True
        assert result.repo_url == "https://github.com/user/repo"
        assert result.error_message is None
        assert result.skipped is False

    def test_failed_result(self):
        """Test failed result with error message."""
        result = GitHubSetupResult(success=False, error_message="Repository already exists")

        assert result.success is False
        assert result.repo_url is None
        assert result.error_message == "Repository already exists"
        assert result.skipped is False

    def test_skipped_result(self):
        """Test skipped result."""
        result = GitHubSetupResult(success=True, skipped=True)

        assert result.success is True
        assert result.skipped is True
        assert result.repo_url is None


class TestGitHubSetupPrerequisites:
    """Tests for GitHubSetup.check_prerequisites()."""

    def test_gh_not_installed(self, tmp_path):
        """Test when gh CLI is not installed."""
        setup = GitHubSetup(tmp_path)

        with patch("solokit.github.setup.shutil.which", return_value=None):
            can_proceed, error_msg, authenticated = setup.check_prerequisites()

            assert can_proceed is False
            assert "GitHub CLI (gh) is not installed" in error_msg
            assert authenticated is False

    def test_gh_installed_but_not_authenticated(self, tmp_path):
        """Test when gh CLI is installed but not authenticated."""
        setup = GitHubSetup(tmp_path)

        with patch("solokit.github.setup.shutil.which", return_value="/usr/bin/gh"):
            with patch.object(setup.runner, "run") as mock_run:
                mock_run.return_value = Mock(returncode=1, success=False)

                can_proceed, error_msg, authenticated = setup.check_prerequisites()

                assert can_proceed is False
                assert "not authenticated" in error_msg
                assert authenticated is False

    def test_gh_installed_and_authenticated(self, tmp_path):
        """Test when gh CLI is installed and authenticated."""
        setup = GitHubSetup(tmp_path)

        with patch("solokit.github.setup.shutil.which", return_value="/usr/bin/gh"):
            with patch.object(setup.runner, "run") as mock_run:
                mock_run.return_value = Mock(returncode=0, success=True)

                can_proceed, error_msg, authenticated = setup.check_prerequisites()

                assert can_proceed is True
                assert error_msg is None
                assert authenticated is True


class TestGitHubSetupPrompts:
    """Tests for GitHubSetup prompt methods."""

    def test_prompt_setup_yes(self, tmp_path):
        """Test prompt_setup returns True when user confirms."""
        setup = GitHubSetup(tmp_path)

        with patch("solokit.github.setup.confirm_action", return_value=True):
            result = setup.prompt_setup()

            assert result is True

    def test_prompt_setup_no(self, tmp_path):
        """Test prompt_setup returns False when user declines."""
        setup = GitHubSetup(tmp_path)

        with patch("solokit.github.setup.confirm_action", return_value=False):
            result = setup.prompt_setup()

            assert result is False

    def test_prompt_setup_mode_create(self, tmp_path):
        """Test prompt_setup_mode returns 'create' for new repo."""
        setup = GitHubSetup(tmp_path)

        with patch(
            "solokit.github.setup.select_from_list",
            return_value="Create a new repository on GitHub",
        ):
            result = setup.prompt_setup_mode()

            assert result == "create"

    def test_prompt_setup_mode_connect(self, tmp_path):
        """Test prompt_setup_mode returns 'connect' for existing repo."""
        setup = GitHubSetup(tmp_path)

        with patch(
            "solokit.github.setup.select_from_list",
            return_value="Connect to an existing GitHub repository",
        ):
            result = setup.prompt_setup_mode()

            assert result == "connect"

    def test_prompt_setup_mode_skip(self, tmp_path):
        """Test prompt_setup_mode returns 'skip'."""
        setup = GitHubSetup(tmp_path)

        with patch(
            "solokit.github.setup.select_from_list", return_value="Skip GitHub setup for now"
        ):
            result = setup.prompt_setup_mode()

            assert result == "skip"

    def test_prompt_repo_details(self, tmp_path):
        """Test prompt_repo_details returns user input."""
        project_path = tmp_path / "my-project"
        project_path.mkdir()
        setup = GitHubSetup(project_path)

        with patch("solokit.github.setup.text_input", side_effect=["custom-name", "A description"]):
            with patch("solokit.github.setup.select_from_list", return_value="public"):
                name, visibility, description = setup.prompt_repo_details()

                assert name == "custom-name"
                assert visibility == "public"
                assert description == "A description"

    def test_prompt_repo_details_uses_default_name(self, tmp_path):
        """Test prompt_repo_details uses directory name as default."""
        project_path = tmp_path / "my-project"
        project_path.mkdir()
        setup = GitHubSetup(project_path)

        with patch("solokit.github.setup.text_input", side_effect=["", ""]):
            with patch("solokit.github.setup.select_from_list", return_value="private"):
                name, visibility, description = setup.prompt_repo_details()

                assert name == "my-project"  # Uses directory name


class TestGitHubSetupCreateRepository:
    """Tests for GitHubSetup.create_repository()."""

    def test_create_repository_success(self, tmp_path):
        """Test successful repository creation."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            # gh repo create succeeds
            mock_run.return_value = Mock(
                success=True,
                stdout="https://github.com/user/my-repo\nPushed to origin",
            )

            result = setup.create_repository("my-repo", "private", "My description")

            assert result.success is True
            assert "github.com" in result.repo_url

    def test_create_repository_already_exists(self, tmp_path):
        """Test repository creation when repo already exists."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.return_value = Mock(
                success=False, stderr="repository my-repo already exists", stdout=""
            )

            result = setup.create_repository("my-repo", "private", "")

            assert result.success is False
            assert "already exists" in result.error_message

    def test_create_repository_failure(self, tmp_path):
        """Test repository creation failure."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.return_value = Mock(success=False, stderr="Network error", stdout="")

            result = setup.create_repository("my-repo", "private", "")

            assert result.success is False
            assert "Failed to create repository" in result.error_message


class TestGitHubSetupConnectExisting:
    """Tests for GitHubSetup.connect_existing()."""

    def test_connect_existing_no_remote(self, tmp_path):
        """Test connecting when no remote exists."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            # First call: check remote (fails - no remote)
            # Second call: add remote (succeeds)
            # Third call: push (succeeds)
            mock_run.side_effect = [
                Mock(success=False),  # git remote get-url origin
                Mock(success=True),  # git remote add origin
                Mock(success=True),  # git push -u origin main
            ]

            result = setup.connect_existing("https://github.com/user/repo")

            assert result.success is True
            assert result.repo_url == "https://github.com/user/repo"

    def test_connect_existing_same_remote_already_set(self, tmp_path):
        """Test connecting when same remote is already configured."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.return_value = Mock(success=True, stdout="https://github.com/user/repo\n")

            result = setup.connect_existing("https://github.com/user/repo")

            assert result.success is True
            # Should only check, not add/push since already configured
            mock_run.assert_called_once()

    def test_connect_existing_different_remote_replaces(self, tmp_path):
        """Test connecting replaces different existing remote."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.side_effect = [
                Mock(success=True, stdout="https://github.com/other/repo\n"),  # get-url
                Mock(success=True),  # remote remove
                Mock(success=True),  # remote add
                Mock(success=True),  # push
            ]

            result = setup.connect_existing("https://github.com/user/repo")

            assert result.success is True
            assert mock_run.call_count == 4

    def test_connect_existing_push_fails_warning(self, tmp_path):
        """Test connecting succeeds even if push fails (warning only)."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.side_effect = [
                Mock(success=False),  # get-url (no remote)
                Mock(success=True),  # remote add
                Mock(success=False, stderr="push failed"),  # push fails
            ]

            result = setup.connect_existing("https://github.com/user/repo")

            # Should still succeed - push failure is not fatal
            assert result.success is True


class TestGitHubSetupInteractive:
    """Tests for GitHubSetup.run_interactive()."""

    def test_run_interactive_gh_not_installed(self, tmp_path):
        """Test interactive flow when gh is not installed."""
        setup = GitHubSetup(tmp_path)

        with patch.object(
            setup, "check_prerequisites", return_value=(False, "gh not installed", False)
        ):
            result = setup.run_interactive()

            assert result.success is False
            assert result.skipped is True

    def test_run_interactive_user_declines(self, tmp_path):
        """Test interactive flow when user declines setup."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(setup, "prompt_setup", return_value=False):
                result = setup.run_interactive()

                assert result.success is True
                assert result.skipped is True

    def test_run_interactive_user_skips(self, tmp_path):
        """Test interactive flow when user chooses skip."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(setup, "prompt_setup", return_value=True):
                with patch.object(setup, "prompt_setup_mode", return_value="skip"):
                    result = setup.run_interactive()

                    assert result.success is True
                    assert result.skipped is True

    def test_run_interactive_create_success(self, tmp_path):
        """Test interactive flow for creating new repo."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(setup, "prompt_setup", return_value=True):
                with patch.object(setup, "prompt_setup_mode", return_value="create"):
                    with patch.object(
                        setup, "prompt_repo_details", return_value=("my-repo", "private", "desc")
                    ):
                        with patch.object(
                            setup,
                            "create_repository",
                            return_value=GitHubSetupResult(
                                success=True, repo_url="https://github.com/user/my-repo"
                            ),
                        ):
                            result = setup.run_interactive()

                            assert result.success is True
                            assert result.repo_url == "https://github.com/user/my-repo"

    def test_run_interactive_connect_success(self, tmp_path):
        """Test interactive flow for connecting existing repo."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(setup, "prompt_setup", return_value=True):
                with patch.object(setup, "prompt_setup_mode", return_value="connect"):
                    with patch.object(
                        setup,
                        "prompt_existing_repo_url",
                        return_value="https://github.com/user/repo",
                    ):
                        with patch.object(
                            setup,
                            "connect_existing",
                            return_value=GitHubSetupResult(
                                success=True, repo_url="https://github.com/user/repo"
                            ),
                        ):
                            result = setup.run_interactive()

                            assert result.success is True

    def test_run_interactive_connect_no_url(self, tmp_path):
        """Test interactive flow when user provides no URL."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(setup, "prompt_setup", return_value=True):
                with patch.object(setup, "prompt_setup_mode", return_value="connect"):
                    with patch.object(setup, "prompt_existing_repo_url", return_value=""):
                        result = setup.run_interactive()

                        assert result.success is True
                        assert result.skipped is True


class TestGitHubSetupNonInteractive:
    """Tests for GitHubSetup.run_non_interactive()."""

    def test_non_interactive_gh_not_available(self, tmp_path):
        """Test non-interactive fails when gh not available."""
        setup = GitHubSetup(tmp_path)

        with patch.object(
            setup, "check_prerequisites", return_value=(False, "gh not installed", False)
        ):
            result = setup.run_non_interactive(repo_name="my-repo")

            assert result.success is False
            assert "gh not installed" in result.error_message

    def test_non_interactive_create_repo(self, tmp_path):
        """Test non-interactive repo creation."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(
                setup,
                "create_repository",
                return_value=GitHubSetupResult(
                    success=True, repo_url="https://github.com/user/my-repo"
                ),
            ):
                result = setup.run_non_interactive(
                    repo_name="my-repo", visibility="public", description="Test"
                )

                assert result.success is True
                setup.create_repository.assert_called_once_with("my-repo", "public", "Test")

    def test_non_interactive_connect_existing(self, tmp_path):
        """Test non-interactive connecting to existing repo."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            with patch.object(
                setup,
                "connect_existing",
                return_value=GitHubSetupResult(
                    success=True, repo_url="https://github.com/user/repo"
                ),
            ):
                result = setup.run_non_interactive(existing_url="https://github.com/user/repo")

                assert result.success is True
                setup.connect_existing.assert_called_once_with("https://github.com/user/repo")

    def test_non_interactive_no_args(self, tmp_path):
        """Test non-interactive fails when no args provided."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup, "check_prerequisites", return_value=(True, None, True)):
            result = setup.run_non_interactive()

            assert result.success is False
            assert "must be provided" in result.error_message


class TestRunGithubSetup:
    """Tests for run_github_setup convenience function."""

    def test_run_github_setup_calls_interactive(self, tmp_path):
        """Test convenience function calls run_interactive."""
        with patch("solokit.github.setup.GitHubSetup") as mock_class:
            mock_instance = Mock()
            mock_instance.run_interactive.return_value = GitHubSetupResult(
                success=True, skipped=True
            )
            mock_class.return_value = mock_instance

            result = run_github_setup(tmp_path)

            mock_class.assert_called_once_with(tmp_path)
            mock_instance.run_interactive.assert_called_once()
            assert result.success is True


class TestExtractRepoUrl:
    """Tests for GitHubSetup._extract_repo_url()."""

    def test_extract_from_output(self, tmp_path):
        """Test extracting URL from gh output."""
        setup = GitHubSetup(tmp_path)

        output = "Created repository user/my-repo on GitHub\nhttps://github.com/user/my-repo"
        url = setup._extract_repo_url(output, "my-repo")

        assert url == "https://github.com/user/my-repo"

    def test_extract_from_git_remote(self, tmp_path):
        """Test extracting URL from git remote when not in output."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.return_value = Mock(success=True, stdout="https://github.com/user/my-repo\n")

            url = setup._extract_repo_url("No URL here", "my-repo")

            assert url == "https://github.com/user/my-repo"

    def test_extract_fallback_to_api(self, tmp_path):
        """Test extracting URL by getting username from API."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.side_effect = [
                Mock(success=False),  # git remote fails
                Mock(success=True, stdout="testuser\n"),  # gh api user
            ]

            url = setup._extract_repo_url("No URL here", "my-repo")

            assert url == "https://github.com/testuser/my-repo"

    def test_extract_ultimate_fallback(self, tmp_path):
        """Test fallback URL when all else fails."""
        setup = GitHubSetup(tmp_path)

        with patch.object(setup.runner, "run") as mock_run:
            mock_run.return_value = Mock(success=False)

            url = setup._extract_repo_url("No URL here", "my-repo")

            assert "<your-username>" in url
            assert "my-repo" in url
