#!/usr/bin/env python3
"""
Git workflow integration for Session-Driven Development.

Handles:
- Branch creation for work items
- Branch continuation for multi-session work
- Commit generation
- Push to remote
- Branch merging (local or PR-based)
- PR creation and management
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.config import get_config_manager
from solokit.core.constants import (
    GIT_LONG_TIMEOUT,
    GIT_QUICK_TIMEOUT,
    GIT_STANDARD_TIMEOUT,
    get_config_file,
    get_work_items_file,
)
from solokit.core.error_handlers import convert_subprocess_errors
from solokit.core.exceptions import (
    CommandExecutionError,
    ErrorCode,
    FileOperationError,
    GitError,
    NotAGitRepoError,
    WorkingDirNotCleanError,
)
from solokit.core.types import GitStatus, WorkItemStatus, WorkItemType

logger = logging.getLogger(__name__)


class GitWorkflow:
    """Manage git workflow for sessions."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize GitWorkflow with project root path."""
        self.project_root = project_root or Path.cwd()
        self.work_items_file = get_work_items_file(self.project_root)
        self.config_file = get_config_file(self.project_root)

        # Use ConfigManager for centralized config management
        config_manager = get_config_manager()
        config_manager.load_config(self.config_file)
        self.config = config_manager.git_workflow

        # Initialize command runner
        self.runner = CommandRunner(default_timeout=GIT_LONG_TIMEOUT, working_dir=self.project_root)

    @convert_subprocess_errors
    def check_git_status(self) -> None:
        """Check if working directory is clean.

        Raises:
            NotAGitRepoError: If not in a git repository
            WorkingDirNotCleanError: If working directory has uncommitted changes
            CommandExecutionError: If git command times out or fails
        """
        result = self.runner.run(["git", "status", "--porcelain"], timeout=GIT_QUICK_TIMEOUT)

        if not result.success:
            if result.timed_out:
                raise CommandExecutionError("git status", -1, "Command timed out")
            raise NotAGitRepoError("Not a git repository")

        if result.stdout.strip():
            changes = result.stdout.strip().split("\n")
            raise WorkingDirNotCleanError(changes=changes)

    def get_current_branch(self) -> str | None:
        """Get current git branch name."""
        result = self.runner.run(["git", "branch", "--show-current"], timeout=GIT_QUICK_TIMEOUT)
        return result.stdout.strip() if result.success else None

    @convert_subprocess_errors
    def create_branch(self, work_item_id: str, session_num: int) -> tuple[str, str | None]:
        """Create a new branch for work item.

        Args:
            work_item_id: ID of the work item
            session_num: Session number

        Returns:
            Tuple of (branch_name, parent_branch)

        Raises:
            GitError: If branch creation fails
            CommandExecutionError: If git command fails
        """
        # Capture parent branch BEFORE creating new branch
        parent_branch = self.get_current_branch()
        branch_name = work_item_id

        # Create and checkout branch
        result = self.runner.run(["git", "checkout", "-b", branch_name], timeout=GIT_QUICK_TIMEOUT)

        if not result.success:
            raise GitError(
                f"Failed to create branch: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED
            )

        return branch_name, parent_branch

    @convert_subprocess_errors
    def checkout_branch(self, branch_name: str) -> None:
        """Checkout existing branch.

        Args:
            branch_name: Name of the branch to checkout

        Raises:
            GitError: If checkout fails
            CommandExecutionError: If git command fails
        """
        result = self.runner.run(["git", "checkout", branch_name], timeout=GIT_QUICK_TIMEOUT)

        if not result.success:
            raise GitError(
                f"Failed to checkout branch: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED
            )

    @convert_subprocess_errors
    def commit_changes(self, message: str) -> str:
        """Stage all changes and commit.

        Args:
            message: Commit message

        Returns:
            Short commit SHA (7 characters)

        Raises:
            GitError: If staging or commit fails
            CommandExecutionError: If git command fails
        """
        # Stage all changes
        stage_result = self.runner.run(["git", "add", "."], timeout=GIT_STANDARD_TIMEOUT)
        if not stage_result.success:
            raise GitError(f"Staging failed: {stage_result.stderr}", ErrorCode.GIT_COMMAND_FAILED)

        # Commit
        result = self.runner.run(["git", "commit", "-m", message], timeout=GIT_STANDARD_TIMEOUT)

        if not result.success:
            raise GitError(f"Commit failed: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED)

        # Get commit SHA
        sha_result = self.runner.run(["git", "rev-parse", "HEAD"], timeout=GIT_QUICK_TIMEOUT)
        commit_sha = sha_result.stdout.strip()[:7] if sha_result.success else "unknown"
        return commit_sha

    @convert_subprocess_errors
    def push_branch(self, branch_name: str) -> None:
        """Push branch to remote.

        Args:
            branch_name: Name of the branch to push

        Raises:
            GitError: If push fails (ignores no remote/upstream errors)
            CommandExecutionError: If git command fails
        """
        result = self.runner.run(
            ["git", "push", "-u", "origin", branch_name], timeout=GIT_LONG_TIMEOUT
        )

        if not result.success:
            # Check if it's just "no upstream" error - not a real error
            if "no upstream" in result.stderr.lower() or "no remote" in result.stderr.lower():
                logger.info("No remote configured (local only)")
                return
            raise GitError(f"Push failed: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED)

    @convert_subprocess_errors
    def delete_remote_branch(self, branch_name: str) -> None:
        """Delete branch from remote.

        Args:
            branch_name: Name of the remote branch to delete

        Raises:
            GitError: If deletion fails (ignores already deleted branches)
            CommandExecutionError: If git command fails
        """
        result = self.runner.run(
            ["git", "push", "origin", "--delete", branch_name], timeout=GIT_STANDARD_TIMEOUT
        )

        if not result.success:
            # Not an error if branch doesn't exist on remote
            if "remote ref does not exist" in result.stderr.lower():
                logger.info(f"Remote branch {branch_name} doesn't exist (already deleted)")
                return
            raise GitError(
                f"Failed to delete remote branch: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED
            )

    @convert_subprocess_errors
    def push_main_to_remote(self, branch_name: str = "main") -> None:
        """Push main (or other parent branch) to remote after local merge.

        Args:
            branch_name: Name of the branch to push (default: main)

        Raises:
            GitError: If push fails
            CommandExecutionError: If git command fails
        """
        result = self.runner.run(["git", "push", "origin", branch_name], timeout=GIT_LONG_TIMEOUT)

        if not result.success:
            raise GitError(
                f"Failed to push {branch_name}: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED
            )

    @convert_subprocess_errors
    def create_pull_request(
        self, work_item_id: str, branch_name: str, work_item: dict, session_num: int
    ) -> str:
        """Create a pull request using gh CLI.

        Args:
            work_item_id: ID of the work item
            branch_name: Name of the branch
            work_item: Work item data
            session_num: Session number

        Returns:
            PR URL

        Raises:
            GitError: If PR creation fails or gh CLI not installed
            CommandExecutionError: If gh command fails
        """
        # Check if gh CLI is available
        check_gh = self.runner.run(["gh", "--version"], timeout=GIT_QUICK_TIMEOUT)

        if not check_gh.success:
            raise GitError(
                "gh CLI not installed. Install from: https://cli.github.com/",
                ErrorCode.GIT_COMMAND_FAILED,
            )

        # Generate PR title and body from templates
        title = self._format_pr_title(work_item, session_num)
        body = self._format_pr_body(work_item, work_item_id, session_num)

        # Create PR using gh CLI
        result = self.runner.run(
            ["gh", "pr", "create", "--title", title, "--body", body], timeout=GIT_LONG_TIMEOUT
        )

        if not result.success:
            raise GitError(f"Failed to create PR: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED)

        return result.stdout.strip()

    def _format_pr_title(self, work_item: dict, session_num: int) -> str:
        """Format PR title from template."""
        template = self.config.pr_title_template
        return template.format(
            type=work_item.get("type", WorkItemType.FEATURE.value).title(),
            title=work_item.get("title", "Work Item"),
            work_item_id=work_item.get("id", "unknown"),
            session_num=session_num,
        )

    def _format_pr_body(self, work_item: dict, work_item_id: str, session_num: int) -> str:
        """Format PR body from template."""
        template = self.config.pr_body_template

        # Get recent commits for this work item
        commit_messages = ""
        if "git" in work_item and "commits" in work_item["git"]:
            commits = work_item["git"]["commits"]
            if commits:
                commit_messages = "\n".join([f"- {c}" for c in commits])

        return template.format(
            work_item_id=work_item_id,
            type=work_item.get("type", WorkItemType.FEATURE.value),
            title=work_item.get("title", ""),
            description=work_item.get("description", ""),
            session_num=session_num,
            commit_messages=commit_messages if commit_messages else "See commits for details",
        )

    @convert_subprocess_errors
    def merge_to_parent(self, branch_name: str, parent_branch: str = "main") -> None:
        """Merge branch to parent branch and delete branch.

        Args:
            branch_name: Name of the branch to merge
            parent_branch: Name of the parent branch to merge into (default: main)

        Raises:
            GitError: If checkout, merge, or delete fails
            CommandExecutionError: If git command fails
        """
        # Checkout parent branch (not hardcoded main)
        checkout_result = self.runner.run(
            ["git", "checkout", parent_branch], timeout=GIT_QUICK_TIMEOUT
        )
        if not checkout_result.success:
            raise GitError(
                f"Failed to checkout {parent_branch}: {checkout_result.stderr}",
                ErrorCode.GIT_COMMAND_FAILED,
            )

        # Merge
        result = self.runner.run(
            ["git", "merge", "--no-ff", branch_name], timeout=GIT_STANDARD_TIMEOUT
        )

        if not result.success:
            raise GitError(f"Merge failed: {result.stderr}", ErrorCode.GIT_COMMAND_FAILED)

        # Delete branch
        self.runner.run(["git", "branch", "-d", branch_name], timeout=GIT_QUICK_TIMEOUT)

    def start_work_item(self, work_item_id: str, session_num: int) -> dict:
        """Start working on a work item (create or resume branch).

        Args:
            work_item_id: ID of the work item
            session_num: Session number

        Returns:
            Dictionary with action, branch, success, and message

        Raises:
            FileOperationError: If work items file cannot be read/written
            GitError: If branch operations fail
        """
        # Load work items
        try:
            with open(self.work_items_file) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.work_items_file),
                details=f"Failed to load work items: {e}",
                cause=e,
            ) from e

        work_item = data["work_items"][work_item_id]

        # Check if work item already has a branch
        if "git" in work_item and work_item["git"].get("status") == GitStatus.IN_PROGRESS.value:
            # Resume existing branch
            branch_name = work_item["git"]["branch"]
            try:
                self.checkout_branch(branch_name)
                return {
                    "action": "resumed",
                    "branch": branch_name,
                    "success": True,
                    "message": f"Switched to branch {branch_name}",
                }
            except GitError as e:
                return {
                    "action": "resumed",
                    "branch": branch_name,
                    "success": False,
                    "message": str(e),
                }
        else:
            # Create new branch
            try:
                branch_name, parent_branch = self.create_branch(work_item_id, session_num)

                # Update work item with git info (including parent branch)
                work_item["git"] = {
                    "branch": branch_name,
                    "parent_branch": parent_branch,  # Store parent for merging
                    "created_at": datetime.now().isoformat(),
                    "status": GitStatus.IN_PROGRESS.value,
                    "commits": [],
                }

                # Save updated work items
                try:
                    with open(self.work_items_file, "w") as f:
                        json.dump(data, f, indent=2)
                except OSError as e:
                    raise FileOperationError(
                        operation="write",
                        file_path=str(self.work_items_file),
                        details=f"Failed to save work items: {e}",
                        cause=e,
                    ) from e

                return {
                    "action": "created",
                    "branch": branch_name,
                    "success": True,
                    "message": branch_name,
                }
            except GitError as e:
                return {
                    "action": "created",
                    "branch": "",
                    "success": False,
                    "message": str(e),
                }

    def complete_work_item(
        self, work_item_id: str, commit_message: str = "", merge: bool = False, session_num: int = 1
    ) -> dict:
        """Complete work on a work item (verify commits, push, optionally merge or create PR).

        Note: This function no longer creates commits. Claude should commit all changes
        before calling this function. This function verifies commits exist and proceeds
        with push/PR creation.

        Behavior depends on git_workflow.mode config:
        - "pr": Push, create pull request (no local merge)
        - "local": Push, merge locally, push main, delete remote branch

        Args:
            work_item_id: ID of the work item
            commit_message: Deprecated - no longer used (kept for backward compatibility)
            merge: Whether to merge/create PR
            session_num: Session number

        Returns:
            Dictionary with success, commit (count), pushed, and message

        Raises:
            FileOperationError: If work items file cannot be read/written
        """
        # Load work items
        try:
            with open(self.work_items_file) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.work_items_file),
                details=f"Failed to load work items: {e}",
                cause=e,
            ) from e

        work_item = data["work_items"][work_item_id]

        if "git" not in work_item:
            return {
                "success": False,
                "message": "Work item has no git tracking (may be single-session item)",
            }

        branch_name = work_item["git"]["branch"]
        workflow_mode = self.config.mode
        parent_branch = work_item["git"].get("parent_branch", "main")

        # Step 1: Extract existing commits from the branch
        # Note: We no longer attempt to create commits - Claude should have already committed
        # This function just verifies commits exist and proceeds with push/PR
        result = self.runner.run(
            [
                "git",
                "log",
                "--format=%h",
                f"{parent_branch}..{branch_name}",
            ],
            timeout=GIT_STANDARD_TIMEOUT,
        )

        if result.success and result.stdout.strip():
            existing_commits = result.stdout.strip().split("\n")
            # Update commits array with any new commits not already tracked
            for commit in reversed(existing_commits):  # Oldest to newest
                if commit not in work_item["git"]["commits"]:
                    work_item["git"]["commits"].append(commit)

            commit_sha = f"{len(existing_commits)} commit(s)"
            logger.info(f"Found {len(existing_commits)} commits on branch {branch_name}")
        else:
            # No commits found - this is an error state
            return {
                "success": False,
                "message": f"No commits found on branch '{branch_name}'. Please commit your changes before ending the session.",
            }

        # Step 2: Push to remote (if enabled)
        push_success = True
        try:
            self.push_branch(branch_name)
        except GitError as e:
            push_success = False
            logger.warning(f"Push failed: {e}")

        # Step 3: Handle completion based on workflow mode
        if merge and work_item["status"] == WorkItemStatus.COMPLETED.value:
            if workflow_mode == "pr":
                # PR Mode: Create pull request (no local merge)
                pr_success = False
                pr_msg = "PR creation skipped (auto_create_pr disabled)"

                if self.config.auto_create_pr:
                    try:
                        pr_url = self.create_pull_request(
                            work_item_id, branch_name, work_item, session_num
                        )
                        pr_success = True
                        pr_msg = f"PR created: {pr_url}"
                    except GitError as e:
                        pr_msg = str(e)

                if pr_success:
                    work_item["git"]["status"] = GitStatus.PR_CREATED.value
                    work_item["git"]["pr_url"] = pr_msg.split(": ")[-1] if ": " in pr_msg else ""
                else:
                    work_item["git"]["status"] = GitStatus.READY_FOR_PR.value

                message = f"Committed {commit_sha}, Pushed to remote. {pr_msg}"

            else:
                # Local Mode: Merge locally, push main, delete remote branch
                # Merge locally
                try:
                    self.merge_to_parent(branch_name, parent_branch)
                    merge_success = True
                    merge_msg = f"Merged to {parent_branch} and branch deleted"
                except GitError as e:
                    merge_success = False
                    merge_msg = str(e)

                if merge_success:
                    # Push merged main to remote
                    try:
                        self.push_main_to_remote(parent_branch)
                        push_main_msg = f"Pushed {parent_branch} to remote"
                    except GitError as e:
                        push_main_msg = f"Failed to push {parent_branch}: {e}"

                    # Delete remote branch if configured
                    if self.config.delete_branch_after_merge:
                        try:
                            self.delete_remote_branch(branch_name)
                            delete_msg = f"Deleted remote branch {branch_name}"
                        except GitError as e:
                            delete_msg = f"Failed to delete remote branch: {e}"
                    else:
                        delete_msg = "Remote branch kept (delete_branch_after_merge disabled)"

                    work_item["git"]["status"] = GitStatus.MERGED.value
                    message = f"Committed {commit_sha}, {merge_msg}, {push_main_msg}, {delete_msg}"
                else:
                    work_item["git"]["status"] = GitStatus.READY_TO_MERGE.value
                    message = f"Committed {commit_sha}, {merge_msg} - Manual merge required"
        else:
            # Work not complete or merge not requested
            work_item["git"]["status"] = (
                GitStatus.READY_TO_MERGE.value
                if work_item["status"] == WorkItemStatus.COMPLETED.value
                else GitStatus.IN_PROGRESS.value
            )
            push_msg = "Pushed to remote" if push_success else "Push failed"
            message = f"Committed {commit_sha}, {push_msg}"

        # Save updated work items
        try:
            with open(self.work_items_file, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise FileOperationError(
                operation="write",
                file_path=str(self.work_items_file),
                details=f"Failed to save work items: {e}",
                cause=e,
            ) from e

        return {
            "success": True,
            "commit": commit_sha,
            "pushed": push_success,
            "message": message,
        }


def main() -> None:
    """CLI entry point for testing."""
    workflow = GitWorkflow()

    # Check status
    try:
        workflow.check_git_status()
        logger.info("Git status: Clean")
    except (NotAGitRepoError, WorkingDirNotCleanError, CommandExecutionError) as e:
        logger.error(f"Git status: {e}")

    current_branch = workflow.get_current_branch()
    logger.info(f"Current branch: {current_branch}")


if __name__ == "__main__":
    main()
