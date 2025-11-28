#!/usr/bin/env python3
"""Display current session status."""

import json
from datetime import datetime
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import SESSION_STATUS_TIMEOUT
from solokit.core.exceptions import (
    FileNotFoundError,
    FileOperationError,
    SessionNotFoundError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import Priority, WorkItemStatus

logger = get_logger(__name__)
output = get_output()


def get_session_status() -> int:
    """
    Get current session status.

    Loads and displays the current session status including:
    - Work item information
    - Time elapsed
    - Git changes
    - Milestone progress
    - Next items

    Returns:
        int: Exit code (0 for success, error code for failure)

    Raises:
        SessionNotFoundError: If no active session exists
        FileNotFoundError: If required session files are missing
        FileOperationError: If file read operations fail
        ValidationError: If session data is invalid
        WorkItemNotFoundError: If work item doesn't exist
    """
    logger.debug("Fetching session status")
    session_dir = Path(".session")
    status_file = session_dir / "tracking" / "status_update.json"

    if not status_file.exists():
        logger.info("No active session file found")
        raise SessionNotFoundError()

    # Load status
    logger.debug("Loading session status from: %s", status_file)
    try:
        status = json.loads(status_file.read_text())
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(status_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        )
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(status_file),
            details=str(e),
            cause=e,
        )

    # Load work items first (for context-aware messaging)
    work_items_file = session_dir / "tracking" / "work_items.json"
    logger.debug("Loading work items from: %s", work_items_file)

    if not work_items_file.exists():
        raise FileNotFoundError(
            file_path=str(work_items_file),
            file_type="work items",
        )

    try:
        data = json.loads(work_items_file.read_text())
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(work_items_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        )

    work_item_id = status.get("current_work_item")

    if not work_item_id:
        logger.warning("No active work item in session")

        # Provide context-aware message
        work_items = data.get("work_items", {})
        total_items = len(work_items)

        if total_items == 0:
            raise ValidationError(
                message="No active work item in this session",
                context={"status_file": str(status_file)},
                remediation=(
                    "No work items found. Create one first:\n"
                    "  1. Use /work-new for interactive creation\n"
                    "  2. Or CLI: sk work-new --type feature --title '...' --priority high\n\n"
                    "💡 Use '/work-list' to see all work items"
                ),
            )
        else:
            raise ValidationError(
                message="No active work item in this session",
                context={"status_file": str(status_file)},
                remediation=(
                    f"You have {total_items} work items available.\n\n"
                    "To get started:\n"
                    "  1. View work items: /work-list\n"
                    "  2. Start a work item: /start <work_item_id>\n"
                    "  3. Or use /start to choose interactively\n\n"
                    "💡 Use '/work-next' to see recommended work items"
                ),
            )

    logger.debug("Current work item: %s", work_item_id)

    # Work items already loaded above (data variable)
    item = data["work_items"].get(work_item_id)

    if not item:
        logger.error("Work item not found: %s", work_item_id)
        raise WorkItemNotFoundError(work_item_id)

    logger.info("Displaying session status for work item: %s", work_item_id)

    output.section("Current Session Status")

    # Work item info
    output.info(f"Work Item: {work_item_id}")
    output.info(f"Type: {item['type']}")
    output.info(f"Priority: {item['priority']}")

    sessions = len(item.get("sessions", []))
    estimated = item.get("estimated_effort", "Unknown")
    output.info(f"Session: {sessions} (of estimated {estimated})")
    output.info("")

    # Time elapsed (if session start time recorded)
    session_start = status.get("session_start")
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        output.info(f"Time Elapsed: {hours}h {minutes}m")
        output.info("")
        logger.debug("Session elapsed time: %dh %dm", hours, minutes)

    # Git changes
    try:
        logger.debug("Fetching git changes")
        runner = CommandRunner(default_timeout=SESSION_STATUS_TIMEOUT)
        result = runner.run(["git", "diff", "--name-status", "HEAD"])

        if result.success and result.stdout:
            lines = result.stdout.strip().split("\n")
            output.info(f"Files Changed ({len(lines)}):")
            for line in lines[:10]:  # Show first 10
                output.info(f"  {line}")
            if len(lines) > 10:
                output.info(f"  ... and {len(lines) - 10} more")
            output.info("")
            logger.debug("Found %d changed files", len(lines))
    except Exception as e:
        # Git operations are optional for status display
        # Log but don't fail if git command fails
        logger.debug("Failed to get git changes: %s", e)

    # Git branch
    git_info = item.get("git", {})
    if git_info:
        branch = git_info.get("branch", "N/A")
        commits = len(git_info.get("commits", []))
        output.info(f"Git Branch: {branch}")
        output.info(f"Commits: {commits}")
        output.info("")
        logger.debug("Git info - branch: %s, commits: %d", branch, commits)

    # Milestone
    milestone_name = item.get("milestone")
    if milestone_name:
        logger.debug("Processing milestone: %s", milestone_name)
        milestones = data.get("milestones", {})
        milestone = milestones.get(milestone_name)
        if milestone:
            # Calculate progress (simplified)
            milestone_items = [
                i for i in data["work_items"].values() if i.get("milestone") == milestone_name
            ]
            total = len(milestone_items)
            completed = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.COMPLETED.value
            )
            percent = int((completed / total) * 100) if total > 0 else 0

            in_prog = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.IN_PROGRESS.value
            )
            not_started = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.NOT_STARTED.value
            )

            output.info(f"Milestone: {milestone_name} ({percent}% complete)")
            output.info(f"  Related items: {in_prog} in progress, {not_started} not started")
            output.info("")
            logger.info(
                "Milestone %s: %d%% complete (%d/%d items)",
                milestone_name,
                percent,
                completed,
                total,
            )

    # Next items
    output.info("Next up:")
    items = data["work_items"]
    next_items = [
        (wid, i) for wid, i in items.items() if i["status"] == WorkItemStatus.NOT_STARTED.value
    ][:3]

    priority_emoji = {
        Priority.CRITICAL.value: "🔴",
        Priority.HIGH.value: "🟠",
        Priority.MEDIUM.value: "🟡",
        Priority.LOW.value: "🟢",
    }

    logger.debug("Found %d next items to display", len(next_items))
    for wid, i in next_items:
        emoji = priority_emoji.get(i["priority"], "")
        # Check if blocked
        blocked = any(
            items.get(dep_id, {}).get("status") != WorkItemStatus.COMPLETED.value
            for dep_id in i.get("dependencies", [])
        )
        status_str = "(blocked)" if blocked else "(ready)"
        output.info(f"  {emoji} {wid} {status_str}")
    output.info("")

    # Quick actions
    output.info("Quick actions:")
    output.info("  - Validate session: /validate")
    output.info("  - Complete session: /end")
    output.info(f"  - View work item: /work-show {work_item_id}")
    output.info("")

    logger.info("Session status displayed successfully")
    return 0


if __name__ == "__main__":
    exit(get_session_status())
