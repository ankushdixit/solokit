#!/usr/bin/env python3
"""
Generate session briefing for next work item.
Enhanced with full project context loading.

This module has been refactored into a package structure.
All functionality is now in solokit.session.briefing.* modules.
This file maintains the CLI entry point and backward compatibility.
"""

import json
from datetime import datetime
from pathlib import Path

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    GitError,
    SessionAlreadyActiveError,
    SessionNotFoundError,
    UnmetDependencyError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import WorkItemStatus

# Import from refactored briefing package
from solokit.session.briefing import (
    calculate_days_ago,  # noqa: F401
    check_command_exists,  # noqa: F401
    check_git_status,  # noqa: F401
    determine_git_branch_final_status,  # noqa: F401
    extract_keywords,  # noqa: F401
    extract_section,  # noqa: F401
    finalize_previous_work_item_git_status,
    generate_briefing,
    generate_deployment_briefing,  # noqa: F401
    generate_integration_test_briefing,  # noqa: F401
    generate_previous_work_section,  # noqa: F401
    get_next_work_item,  # noqa: F401
    get_relevant_learnings,  # noqa: F401
    load_current_stack,  # noqa: F401
    load_current_tree,  # noqa: F401
    load_learnings,  # noqa: F401
    load_milestone_context,  # noqa: F401
    load_project_docs,  # noqa: F401
    load_work_item_spec,  # noqa: F401
    load_work_items,  # noqa: F401
    shift_heading_levels,  # noqa: F401
    validate_environment,  # noqa: F401
)

logger = get_logger(__name__)
output = get_output()


@log_errors()
def main():
    """Main entry point for session briefing generation.

    Raises:
        SessionNotFoundError: If .session directory doesn't exist
        WorkItemNotFoundError: If specified work item doesn't exist
        SessionAlreadyActiveError: If another work item is in-progress (without --force)
        UnmetDependencyError: If work item has unmet dependencies
        ValidationError: If no available work items found
        GitError: If git workflow fails
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start session for work item")
    parser.add_argument(
        "work_item_id",
        nargs="?",
        help="Specific work item ID to start (optional)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force start even if another item is in-progress",
    )
    args = parser.parse_args()

    logger.info("Starting session briefing generation")

    # Ensure .session directory exists
    session_dir = Path(".session")
    if not session_dir.exists():
        logger.error(".session directory not found")
        raise SessionNotFoundError()

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Determine which work item to start
    if args.work_item_id:
        # User specified a work item explicitly
        item_id = args.work_item_id
        item = work_items_data.get("work_items", {}).get(item_id)

        if not item:
            logger.error("Work item not found: %s", item_id)
            raise WorkItemNotFoundError(item_id)

        # Check if a DIFFERENT work item is in-progress (excluding the requested one)
        in_progress = [
            (id, wi)
            for id, wi in work_items_data.get("work_items", {}).items()
            if wi["status"] == WorkItemStatus.IN_PROGRESS.value and id != item_id
        ]

        # If another item is in-progress, warn and exit (unless --force)
        if in_progress and not args.force:
            in_progress_id = in_progress[0][0]
            logger.warning(
                "Blocked start of %s due to in-progress item: %s (use --force to override)",
                item_id,
                in_progress_id,
            )
            raise SessionAlreadyActiveError(in_progress_id)

        # Check dependencies are satisfied
        deps_satisfied = all(
            work_items_data.get("work_items", {}).get(dep_id, {}).get("status")
            == WorkItemStatus.COMPLETED.value
            for dep_id in item.get("dependencies", [])
        )

        if not deps_satisfied:
            unmet_deps = [
                dep_id
                for dep_id in item.get("dependencies", [])
                if work_items_data.get("work_items", {}).get(dep_id, {}).get("status")
                != "completed"
            ]
            logger.error("Work item %s has unmet dependencies: %s", item_id, unmet_deps)
            # Raise exception for the first unmet dependency
            # (The exception message will indicate there are dependencies to complete)
            raise UnmetDependencyError(item_id, unmet_deps[0])

        # Note: If requested item is already in-progress, no conflict - just resume it
        logger.info("User explicitly requested work item: %s", item_id)
    else:
        # Use automatic selection
        item_id, item = get_next_work_item(work_items_data)

        if not item_id:
            logger.warning("No available work items found")
            from solokit.core.exceptions import ErrorCode, ValidationError

            # Check if any work items exist at all
            work_items = work_items_data.get("work_items", {})
            total_items = len(work_items)

            if total_items == 0:
                # No work items exist
                raise ValidationError(
                    message="No work items found in this project",
                    code=ErrorCode.INVALID_STATUS,
                    remediation=(
                        "Create a work item first:\n"
                        "  1. sk work-new --type feature --title '...' --priority high\n"
                        "  2. Or use /work-new in Claude Code for interactive creation\n\n"
                        "💡 Work items help track your development tasks and sessions"
                    ),
                )
            else:
                # Work items exist but none are available
                raise ValidationError(
                    message=f"No available work items ({total_items} total exist)",
                    code=ErrorCode.INVALID_STATUS,
                    remediation=(
                        "All work items may be blocked by dependencies or already completed.\n\n"
                        "To proceed:\n"
                        "  1. Check work item status: /work-list\n"
                        "  2. View dependencies: /work-graph\n"
                        "  3. Find next available: /work-next\n\n"
                        "💡 Use '/work-list --status not_started' to see pending items"
                    ),
                )

    # Finalize previous work item's git status if starting a new work item
    finalize_previous_work_item_git_status(work_items_data, item_id)

    logger.info("Generating briefing for work item: %s", item_id)
    # Generate briefing
    briefing = generate_briefing(item_id, item, learnings_data)

    # Save briefing
    briefings_dir = session_dir / "briefings"
    briefings_dir.mkdir(exist_ok=True)

    # Determine session number
    # If work item is already in progress, reuse existing session number
    if item.get("status") == WorkItemStatus.IN_PROGRESS.value and item.get("sessions"):
        session_num = item["sessions"][-1]["session_num"]
        logger.info("Resuming existing session %d for work item %s", session_num, item_id)
    else:
        # Create new session number for new work or restarted work
        session_num = (
            max(
                [int(f.stem.split("_")[1]) for f in briefings_dir.glob("session_*.md")],
                default=0,
            )
            + 1
        )
        logger.info("Starting new session %d for work item %s", session_num, item_id)

    # Start git workflow for work item
    try:
        # Import git workflow from new location
        from solokit.git.integration import GitWorkflow

        workflow = GitWorkflow()
        git_result = workflow.start_work_item(item_id, session_num)

        if git_result["success"]:
            if git_result["action"] == "created":
                output.success(f"Created git branch: {git_result['branch']}\n")
            else:
                output.success(f"Resumed git branch: {git_result['branch']}\n")
        else:
            output.warning(f"Git workflow warning: {git_result['message']}\n")
    except GitError:
        # Re-raise GitError only if it's critical (not a git repo, command not found)
        # Other git errors are logged as warnings but don't block the briefing
        raise
    except Exception as e:
        # Log unexpected errors but don't block briefing generation
        # Git workflow issues are non-fatal
        logger.warning("Could not start git workflow: %s", e)
        output.warning(f"Could not start git workflow: {e}\n")

    # Update work item status and session tracking
    work_items_file = session_dir / "tracking" / "work_items.json"
    if work_items_file.exists():
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        # Update work item status
        if item_id in work_items_data["work_items"]:
            work_item = work_items_data["work_items"][item_id]
            work_item["status"] = WorkItemStatus.IN_PROGRESS.value
            work_item["updated_at"] = datetime.now().isoformat()

            # Add session tracking
            if "sessions" not in work_item:
                work_item["sessions"] = []
            work_item["sessions"].append(
                {"session_num": session_num, "started_at": datetime.now().isoformat()}
            )

            # Update metadata counters
            work_items = work_items_data.get("work_items", {})
            work_items_data["metadata"]["total_items"] = len(work_items)
            work_items_data["metadata"]["completed"] = sum(
                1
                for item in work_items.values()
                if item["status"] == WorkItemStatus.COMPLETED.value
            )
            work_items_data["metadata"]["in_progress"] = sum(
                1
                for item in work_items.values()
                if item["status"] == WorkItemStatus.IN_PROGRESS.value
            )
            work_items_data["metadata"]["blocked"] = sum(
                1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
            )
            work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

            # Save updated work items
            with open(work_items_file, "w") as f:
                json.dump(work_items_data, f, indent=2)

            # Notify that status has been updated
            output.success(f"Work item status updated: {item_id} → in_progress\n")

    briefing_file = briefings_dir / f"session_{session_num:03d}_briefing.md"

    # Always write briefing file to include fresh context (Enhancement #11 Phase 2)
    # This is critical for in-progress items to show previous work context
    with open(briefing_file, "w") as f:
        f.write(briefing)

    if item.get("status") == WorkItemStatus.IN_PROGRESS.value:
        logger.info("Updated briefing with previous work context: %s", briefing_file)
    else:
        logger.info("Created briefing file: %s", briefing_file)

    # Print briefing (always show it, whether new or existing)
    output.info(briefing)

    # Update status file
    status_file = session_dir / "tracking" / "status_update.json"
    status = {
        "current_session": session_num,
        "current_work_item": item_id,
        "started_at": datetime.now().isoformat(),
        "status": WorkItemStatus.IN_PROGRESS.value,
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    return 0


def _cli_main():
    """CLI wrapper for main() that handles exceptions and exit codes."""
    try:
        return main()
    except SessionNotFoundError as e:
        output.info(f"Error: {e.message}")
        output.info(f"\n{e.remediation}")
        return e.exit_code
    except WorkItemNotFoundError as e:
        output.info(f"Error: {e.message}")
        output.info(f"\n{e.remediation}")
        # Also show available work items
        try:
            work_items_data = load_work_items()
            output.info("\nAvailable work items:")
            for wid, wi in work_items_data.get("work_items", {}).items():
                status_emoji = {
                    WorkItemStatus.NOT_STARTED.value: "○",
                    WorkItemStatus.IN_PROGRESS.value: "◐",
                    WorkItemStatus.COMPLETED.value: "✓",
                    WorkItemStatus.BLOCKED.value: "✗",
                }.get(wi["status"], "○")
                output.info(f"  {status_emoji} {wid} - {wi['title']} ({wi['status']})")
        except Exception:
            pass  # If we can't load work items, just skip the list
        return e.exit_code
    except SessionAlreadyActiveError as e:
        output.info(f"\nWarning: {e.message}")
        output.info("\nOptions:")
        output.info("1. Complete current work item first: /end")
        output.info("2. Force start new work item: sk start <work_item_id> --force")
        output.info("3. Cancel: Ctrl+C\n")
        return e.exit_code
    except UnmetDependencyError as e:
        output.info(f"Error: {e.message}")
        output.info(f"\n{e.remediation}")
        # Show unmet dependency details
        try:
            work_items_data = load_work_items()
            dep_id = e.context.get("dependency_id")
            if dep_id:
                dep = work_items_data.get("work_items", {}).get(dep_id, {})
                output.info("\nDependency details:")
                output.info(
                    f"  - {dep_id}: {dep.get('title', 'Unknown')} (status: {dep.get('status', 'unknown')})"
                )
        except Exception:
            pass  # If we can't load work items, just skip the details
        return e.exit_code
    except ValidationError as e:
        output.info(f"Error: {e.message}")
        if e.remediation:
            output.info(f"\n{e.remediation}")
        return e.exit_code
    except GitError as e:
        output.info(f"Warning: {e.message}")
        if e.remediation:
            output.info(f"\n{e.remediation}")
        # Git errors are warnings, not fatal - return success
        # This maintains backwards compatibility
        return 0
    except Exception as e:
        logger.exception("Unexpected error in briefing generation")
        output.info(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(_cli_main())
