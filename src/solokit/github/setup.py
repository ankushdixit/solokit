"""
GitHub Repository Setup Module.

Provides functionality for creating and connecting GitHub repositories
after project initialization.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from solokit.core.cli_prompts import confirm_action, select_from_list, text_input
from solokit.core.command_runner import CommandRunner
from solokit.core.output import get_output

logger = logging.getLogger(__name__)


@dataclass
class GitHubSetupResult:
    """Result of GitHub repository setup."""

    success: bool
    repo_url: str | None = None
    error_message: str | None = None
    skipped: bool = False


class GitHubSetup:
    """Handles GitHub repository setup after project initialization."""

    def __init__(self, project_path: Path | None = None):
        """Initialize GitHub setup.

        Args:
            project_path: Path to project directory. Defaults to current directory.
        """
        self.project_path = project_path or Path.cwd()
        self.runner = CommandRunner(default_timeout=60, working_dir=self.project_path)
        self.output = get_output()

    def check_prerequisites(self) -> tuple[bool, str | None, bool]:
        """Check if gh CLI is installed and authenticated.

        Returns:
            Tuple of (can_proceed: bool, error_message: str | None, authenticated: bool)
        """
        gh_path = shutil.which("gh")
        if not gh_path:
            return False, self._get_install_instructions(), False

        # Check authentication
        result = self.runner.run([gh_path, "auth", "status"], check=False)
        if result.returncode != 0:
            return (
                False,
                "GitHub CLI is not authenticated.\nPlease run: gh auth login",
                False,
            )

        return True, None, True

    def _get_install_instructions(self) -> str:
        """Get platform-specific installation instructions for gh CLI."""
        return (
            "GitHub CLI (gh) is not installed.\n"
            "Please install it:\n"
            "  macOS:   brew install gh\n"
            "  Ubuntu:  sudo apt install gh\n"
            "  Windows: winget install --id GitHub.cli\n"
            "  Other:   https://cli.github.com/\n\n"
            "After installation, run: gh auth login"
        )

    def prompt_setup(self) -> bool:
        """Prompt user if they want to set up GitHub.

        Returns:
            True if user wants to proceed with GitHub setup
        """
        return confirm_action(
            "Would you like to set up a GitHub repository?",
            default=False,
        )

    def prompt_setup_mode(self) -> Literal["create", "connect", "skip"]:
        """Prompt user for setup mode.

        Returns:
            'create' for new repo, 'connect' for existing, 'skip' to skip
        """
        choice = select_from_list(
            "How would you like to set up GitHub?",
            choices=[
                "Create a new repository on GitHub",
                "Connect to an existing GitHub repository",
                "Skip GitHub setup for now",
            ],
        )

        if "Create" in choice:
            return "create"
        elif "Connect" in choice:
            return "connect"
        return "skip"

    def prompt_repo_details(self) -> tuple[str, str, str]:
        """Prompt user for new repository details.

        Returns:
            Tuple of (repo_name, visibility, description)
        """
        # Default repo name from directory name
        default_name = self.project_path.name

        repo_name = text_input(
            f"Repository name [{default_name}]: ",
            default=default_name,
        )
        if not repo_name:
            repo_name = default_name

        visibility = select_from_list(
            "Repository visibility:",
            choices=["private", "public"],
            default="private",
        )

        description = text_input(
            "Description (optional): ",
            default="",
        )

        return repo_name, visibility, description

    def prompt_existing_repo_url(self) -> str:
        """Prompt user for existing repository URL.

        Returns:
            Repository URL
        """
        return text_input(
            "Enter repository URL (e.g., https://github.com/user/repo): ",
            validate_fn=lambda x: x.startswith("https://") or x.startswith("git@"),
        )

    def create_repository(
        self,
        name: str,
        visibility: str = "private",
        description: str = "",
    ) -> GitHubSetupResult:
        """Create a new GitHub repository.

        Args:
            name: Repository name
            visibility: 'public' or 'private'
            description: Repository description

        Returns:
            GitHubSetupResult with outcome
        """
        self.output.progress("Creating GitHub repository...")

        # Build command
        cmd = ["gh", "repo", "create", name, f"--{visibility}", "--source=."]
        if description:
            cmd.extend(["--description", description])

        # Add remote and push
        cmd.append("--push")

        result = self.runner.run(cmd, timeout=120, check=False)

        if result.success:
            # Extract repo URL from output or construct it
            repo_url = self._extract_repo_url(result.stdout, name)
            self.output.success(f"Repository created: {repo_url}")
            return GitHubSetupResult(success=True, repo_url=repo_url)

        # Handle common errors
        error_msg = result.stderr or result.stdout
        if "already exists" in error_msg.lower():
            return GitHubSetupResult(
                success=False,
                error_message=f"Repository '{name}' already exists on GitHub.\n"
                "Please choose a different name or connect to the existing repository.",
            )

        return GitHubSetupResult(
            success=False,
            error_message=f"Failed to create repository: {error_msg}",
        )

    def connect_existing(self, repo_url: str) -> GitHubSetupResult:
        """Connect to an existing GitHub repository.

        Args:
            repo_url: URL of the existing repository

        Returns:
            GitHubSetupResult with outcome
        """
        self.output.progress("Connecting to existing repository...")

        # Check if origin already exists
        check_result = self.runner.run(["git", "remote", "get-url", "origin"], check=False)
        if check_result.success:
            existing_url = check_result.stdout.strip()
            if existing_url == repo_url:
                self.output.success("Remote 'origin' already configured correctly")
                return GitHubSetupResult(success=True, repo_url=repo_url)
            else:
                # Remove existing origin
                self.runner.run(["git", "remote", "remove", "origin"], check=False)

        # Add remote
        add_result = self.runner.run(["git", "remote", "add", "origin", repo_url], check=False)
        if not add_result.success:
            return GitHubSetupResult(
                success=False,
                error_message=f"Failed to add remote: {add_result.stderr}",
            )

        self.output.success(f"Remote 'origin' added: {repo_url}")

        # Try to push
        push_result = self.runner.run(
            ["git", "push", "-u", "origin", "main"],
            timeout=120,
            check=False,
        )

        if push_result.success:
            self.output.success("Initial commit pushed to GitHub")
        else:
            # Push might fail for various reasons (empty repo, branch name mismatch, etc.)
            # This is not a fatal error
            self.output.warning(
                "Could not push to remote. You may need to push manually:\n"
                "  git push -u origin main"
            )

        return GitHubSetupResult(success=True, repo_url=repo_url)

    def _extract_repo_url(self, output: str, repo_name: str) -> str:
        """Extract repository URL from gh output or construct it.

        Args:
            output: Output from gh repo create command
            repo_name: Repository name

        Returns:
            Repository URL
        """
        # Try to find URL in output
        for line in output.split("\n"):
            if "github.com" in line:
                # Extract URL-like string
                parts = line.split()
                for part in parts:
                    if "github.com" in part:
                        return part.strip()

        # Try to get from git remote
        result = self.runner.run(["git", "remote", "get-url", "origin"], check=False)
        if result.success:
            return result.stdout.strip()

        # Fallback: get username and construct URL
        user_result = self.runner.run(["gh", "api", "user", "-q", ".login"], check=False)
        if user_result.success:
            username = user_result.stdout.strip()
            return f"https://github.com/{username}/{repo_name}"

        return f"https://github.com/<your-username>/{repo_name}"

    def run_interactive(self) -> GitHubSetupResult:
        """Run interactive GitHub setup flow.

        Returns:
            GitHubSetupResult with outcome
        """
        # Check prerequisites
        can_proceed, error_msg, _ = self.check_prerequisites()
        if not can_proceed:
            self.output.warning(error_msg or "Cannot proceed with GitHub setup")
            return GitHubSetupResult(success=False, error_message=error_msg, skipped=True)

        # Ask if user wants to set up GitHub
        if not self.prompt_setup():
            self.output.info("Skipping GitHub setup")
            return GitHubSetupResult(success=True, skipped=True)

        # Get setup mode
        mode = self.prompt_setup_mode()

        if mode == "skip":
            self.output.info("Skipping GitHub setup")
            return GitHubSetupResult(success=True, skipped=True)

        if mode == "create":
            # Get repository details
            repo_name, visibility, description = self.prompt_repo_details()
            return self.create_repository(repo_name, visibility, description)

        # mode == "connect"
        repo_url = self.prompt_existing_repo_url()
        if not repo_url:
            self.output.info("No URL provided, skipping GitHub setup")
            return GitHubSetupResult(success=True, skipped=True)
        return self.connect_existing(repo_url)

    def run_non_interactive(
        self,
        repo_name: str | None = None,
        visibility: str = "private",
        description: str = "",
        existing_url: str | None = None,
    ) -> GitHubSetupResult:
        """Run non-interactive GitHub setup.

        Args:
            repo_name: Name for new repository (creates new if provided)
            visibility: 'public' or 'private' for new repos
            description: Description for new repos
            existing_url: URL to connect to existing repo

        Returns:
            GitHubSetupResult with outcome
        """
        # Check prerequisites
        can_proceed, error_msg, _ = self.check_prerequisites()
        if not can_proceed:
            return GitHubSetupResult(success=False, error_message=error_msg)

        if existing_url:
            return self.connect_existing(existing_url)

        if repo_name:
            return self.create_repository(repo_name, visibility, description)

        return GitHubSetupResult(
            success=False,
            error_message="Either repo_name or existing_url must be provided",
        )


def run_github_setup(project_path: Path | None = None) -> GitHubSetupResult:
    """Convenience function to run interactive GitHub setup.

    Args:
        project_path: Path to project directory

    Returns:
        GitHubSetupResult with outcome
    """
    setup = GitHubSetup(project_path)
    return setup.run_interactive()
