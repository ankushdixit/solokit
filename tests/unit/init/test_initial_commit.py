"""
Tests for initial_commit module.

Validates initial git commit creation.

Run tests:
    pytest tests/unit/init/test_initial_commit.py -v

Target: 90%+ coverage
"""

from unittest.mock import Mock, patch

from solokit.init.initial_commit import create_commit_message, create_initial_commit


class TestCreateCommitMessage:
    """Tests for create_commit_message()."""

    def test_basic_commit_message(self):
        """Test creating basic commit message."""
        message = create_commit_message(
            "SaaS T3",
            "tier-2-standard",
            80,
            [],
            {"frontend": "Next.js", "backend": "tRPC"},
        )

        assert "SaaS T3" in message
        assert "Tier 2" in message
        assert "80%" in message
        assert "Next.js" in message
        assert "tRPC" in message

    def test_with_additional_options(self):
        """Test commit message with additional options."""
        message = create_commit_message(
            "SaaS T3",
            "tier-1-essential",
            60,
            ["ci_cd", "docker"],
            {"frontend": "Next.js"},
        )

        assert "Ci Cd" in message or "CI CD" in message.upper()
        assert "Docker" in message

    def test_no_additional_options(self):
        """Test commit message with no additional options."""
        message = create_commit_message(
            "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}
        )

        assert "None" in message


class TestCreateInitialCommit:
    """Tests for create_initial_commit()."""

    def test_create_commit_success(self, tmp_path):
        """Test successful initial commit creation."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = [
                Mock(success=False),  # rev-list fails (no commits yet)
                Mock(success=True),  # git add succeeds
                Mock(success=True),  # git commit succeeds
            ]

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is True
            assert mock_runner.run.call_count == 3

    def test_skip_if_commits_exist(self, tmp_path):
        """Test skipping commit if repository already has commits."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True, stdout="5")  # 5 commits exist

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is True
            # Should only call rev-list, not add or commit
            assert mock_runner.run.call_count == 1

    def test_git_add_fails(self, tmp_path):
        """Test handling when git add fails."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = [
                Mock(success=False),  # rev-list fails
                Mock(success=False, stderr="Add failed"),  # git add fails
            ]

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is False

    def test_git_commit_fails(self, tmp_path):
        """Test handling when git commit fails."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = [
                Mock(success=False),  # rev-list fails
                Mock(success=True),  # git add succeeds
                Mock(success=False, stderr="Commit failed"),  # git commit fails
            ]

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is False

    def test_commit_message_format(self, tmp_path):
        """Test that commit message is properly formatted."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = [
                Mock(success=False),
                Mock(success=True),
                Mock(success=True),
            ]

            create_initial_commit(
                "SaaS T3",
                "tier-2-standard",
                80,
                ["ci_cd"],
                {"frontend": "Next.js"},
                tmp_path,
            )

            # Get the commit call
            commit_call = mock_runner.run.call_args_list[2]
            commit_args = commit_call[0][0]

            assert commit_args[0] == "git"
            assert commit_args[1] == "commit"
            assert commit_args[2] == "-m"
            assert "SaaS T3" in commit_args[3]

    def test_uses_current_directory_when_no_path_provided(self):
        """Test that it uses current directory when project_root is None."""
        with patch("solokit.init.initial_commit.Path.cwd") as mock_cwd:
            mock_cwd.return_value = "/fake/path"
            with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="5")

                create_initial_commit(
                    "SaaS T3",
                    "tier-1-essential",
                    60,
                    [],
                    {"frontend": "Next.js"},
                    project_root=None,
                )

                # Verify CommandRunner was called with the cwd path
                mock_runner_class.assert_called_once()

    def test_exception_during_rev_list_check(self, tmp_path):
        """Test handling when exception occurs during rev-list check."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            # First call raises exception, then add succeeds, commit succeeds
            mock_runner.run.side_effect = [
                Exception("Git error"),  # rev-list throws exception
                Mock(success=True),  # git add succeeds
                Mock(success=True),  # git commit succeeds
            ]

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is True
            # Should continue and create commit despite exception
            assert mock_runner.run.call_count == 3

    def test_exception_during_commit_creation(self, tmp_path):
        """Test handling when exception occurs during commit creation."""
        with patch("solokit.init.initial_commit.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            # rev-list succeeds, then exception during add
            mock_runner.run.side_effect = [
                Mock(success=False),  # rev-list fails (no commits)
                Exception("Fatal error during git add"),  # Exception
            ]

            result = create_initial_commit(
                "SaaS T3", "tier-1-essential", 60, [], {"frontend": "Next.js"}, tmp_path
            )

            assert result is False
