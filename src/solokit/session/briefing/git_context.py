#!/usr/bin/env python3
"""
Git context and status checking.
Part of the briefing module decomposition.
"""

import json
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import GIT_QUICK_TIMEOUT
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import ErrorCode, GitError, SystemError
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import GitStatus, WorkItemStatus

logger = get_logger(__name__)
output = get_output()


class GitContext:
    """Handle git status and branch information."""

    def __init__(self) -> None:
        """Initialize git context handler."""
        self.runner = CommandRunner(default_timeout=GIT_QUICK_TIMEOUT)

    @log_errors()
    def check_git_status(self) -> dict[str, Any]:
        """Check git status for session start.

        Returns:
            Dict with keys: clean (bool), status (str), branch (str or None)

        Raises:
            GitError: If git command fails
            NotAGitRepoError: If not in a git repository
            SystemError: If git workflow import or execution fails
        """
        try:
            # Import git workflow from new location
            from solokit.core.exceptions import WorkingDirNotCleanError
            from solokit.git.integration import GitWorkflow

            workflow = GitWorkflow()
            current_branch = workflow.get_current_branch()

            # Try to check git status - if uncommitted changes, handle gracefully
            try:
                workflow.check_git_status()
                return {
                    "clean": True,
                    "status": "Working directory clean",
                    "branch": current_branch,
                }
            except WorkingDirNotCleanError as e:
                # This is not an error - just return the status
                changes = e.context.get("uncommitted_changes", [])
                logger.info(f"Working directory has uncommitted changes: {len(changes)} files")
                return {
                    "clean": False,
                    "status": "Working directory not clean (uncommitted changes)",
                    "branch": current_branch,
                }
        except ImportError as e:
            raise SystemError(
                message="Failed to import GitWorkflow",
                code=ErrorCode.IMPORT_FAILED,
                context={"module": "solokit.git.integration", "error": str(e)},
                remediation="Ensure git integration module is properly installed",
                cause=e,
            ) from e
        except GitError:
            # Re-raise GitError as-is (already standardized)
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise GitError(
                message=f"Failed to check git status: {e}",
                code=ErrorCode.GIT_COMMAND_FAILED,
                context={"error": str(e)},
                remediation="Check git installation and repository state",
                cause=e,
            ) from e

    @log_errors()
    def determine_git_branch_final_status(self, branch_name: str, git_info: dict) -> str:
        """Determine the final status of a git branch by inspecting actual git state.

        Args:
            branch_name: Name of the git branch
            git_info: Git info dict from work item

        Returns:
            One of: "merged", "pr_created", "pr_closed", "ready_for_pr", "deleted"

        Raises:
            GitError: If git commands fail critically
            SystemError: If JSON parsing or other operations fail
        """
        parent_branch = git_info.get("parent_branch", "main")

        try:
            # Check 1: Is branch merged?
            result = self.runner.run(["git", "branch", "--merged", parent_branch])
            if result.success and branch_name in result.stdout:
                logger.debug(f"Branch {branch_name} is merged to {parent_branch}")
                return GitStatus.MERGED.value

            # Check 2: Does PR exist? (requires gh CLI)
            result = self.runner.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch_name,
                    "--state",
                    "all",
                    "--json",
                    "number,state",
                ]
            )
            if result.success and result.stdout.strip():
                try:
                    prs = json.loads(result.stdout)
                    if prs:
                        pr = prs[0]  # Get first/most recent PR
                        pr_state = pr.get("state", "").upper()

                        if pr_state == "MERGED":
                            logger.debug(f"Branch {branch_name} has merged PR")
                            return GitStatus.MERGED.value
                        elif pr_state == "CLOSED":
                            logger.debug(f"Branch {branch_name} has closed (unmerged) PR")
                            return GitStatus.PR_CLOSED.value
                        elif pr_state == "OPEN":
                            logger.debug(f"Branch {branch_name} has open PR")
                            return GitStatus.PR_CREATED.value
                except json.JSONDecodeError as e:
                    # Log but don't fail - gh CLI output may be malformed
                    logger.debug(f"Error parsing PR JSON: {e}")
                    # Continue to check branch existence
            else:
                logger.debug("gh CLI not available or no PRs found")

            # Check 3: Does branch still exist locally?
            result = self.runner.run(["git", "show-ref", "--verify", f"refs/heads/{branch_name}"])
            if result.success:
                logger.debug(f"Branch {branch_name} exists locally")
                # Branch exists locally, no PR found
                return GitStatus.READY_FOR_PR.value

            # Check 4: Does branch exist remotely?
            result = self.runner.run(["git", "ls-remote", "--heads", "origin", branch_name])
            if result.success and result.stdout.strip():
                logger.debug(f"Branch {branch_name} exists remotely")
                # Branch exists remotely, no PR found
                return GitStatus.READY_FOR_PR.value

            # Branch doesn't exist and no PR found
            logger.debug(f"Branch {branch_name} not found locally or remotely")
            return GitStatus.DELETED.value

        except GitError:
            # Re-raise GitError from CommandRunner
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise GitError(
                message=f"Failed to determine git branch status for '{branch_name}': {e}",
                code=ErrorCode.GIT_COMMAND_FAILED,
                context={
                    "branch_name": branch_name,
                    "parent_branch": parent_branch,
                    "error": str(e),
                },
                remediation="Check git installation and repository state",
                cause=e,
            ) from e

    @log_errors()
    def finalize_previous_work_item_git_status(
        self, work_items_data: dict, current_work_item_id: str
    ) -> str | None:
        """Finalize git status for previous completed work item when starting a new one.

        This handles the case where:
        - Previous work item was completed
        - User performed git operations externally (pushed, created PR, merged)
        - Starting a new work item (not resuming the previous one)

        Args:
            work_items_data: Loaded work items data
            current_work_item_id: ID of work item being started

        Returns:
            Previous work item ID if finalized, None otherwise

        Raises:
            GitError: If git operations fail
            SystemError: If file operations fail
        """
        work_items = work_items_data.get("work_items", {})

        # Find previously active work item
        previous_work_item = None
        previous_work_item_id = None

        for wid, wi in work_items.items():
            # Skip current work item
            if wid == current_work_item_id:
                continue

            # Find work item with git branch in "in_progress" status
            git_info = wi.get("git", {})
            if git_info.get("status") == GitStatus.IN_PROGRESS.value:
                # Only finalize if work item itself is completed
                if wi.get("status") == WorkItemStatus.COMPLETED.value:
                    previous_work_item = wi
                    previous_work_item_id = wid
                    break

        if not previous_work_item:
            # No previous work item to finalize
            logger.debug("No previous work item with stale git status found")
            return None

        git_info = previous_work_item.get("git", {})
        branch_name = git_info.get("branch")

        if not branch_name:
            logger.debug(f"Previous work item {previous_work_item_id} has no git branch")
            return None

        logger.info(f"Finalizing git status for completed work item: {previous_work_item_id}")

        try:
            # Inspect actual git state
            final_status = self.determine_git_branch_final_status(branch_name, git_info)

            # Update git status
            work_items[previous_work_item_id]["git"]["status"] = final_status

            # Save updated work items
            work_items_file = Path(".session/tracking/work_items.json")
            try:
                with open(work_items_file, "w") as f:
                    json.dump(work_items_data, f, indent=2)
            except OSError as e:
                raise SystemError(
                    message=f"Failed to save work items file: {work_items_file}",
                    code=ErrorCode.FILE_OPERATION_FAILED,
                    context={
                        "file_path": str(work_items_file),
                        "work_item_id": previous_work_item_id,
                        "error": str(e),
                    },
                    remediation="Check file permissions and disk space",
                    cause=e,
                ) from e

            logger.info(
                "Updated git status for %s: in_progress → %s",
                previous_work_item_id,
                final_status,
            )
            output.success(
                f"Finalized git status for previous work item: "
                f"{previous_work_item_id} → {final_status}"
            )

            return previous_work_item_id

        except GitError:
            # Re-raise GitError from determine_git_branch_final_status
            raise
        except SystemError:
            # Re-raise SystemError from file operations
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise SystemError(
                message=f"Failed to finalize git status for work item '{previous_work_item_id}': {e}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={
                    "work_item_id": previous_work_item_id,
                    "current_work_item_id": current_work_item_id,
                    "branch_name": branch_name,
                    "error": str(e),
                },
                remediation="Check work items data integrity and git repository state",
                cause=e,
            ) from e
