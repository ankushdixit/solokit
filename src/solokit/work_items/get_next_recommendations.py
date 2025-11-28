#!/usr/bin/env python3
"""
Get next recommended work items for interactive selection.

This script returns the top 4 ready-to-start work items based on:
- Dependencies are satisfied (not blocked)
- Priority (critical > high > medium > low)
- Status is not_started

Output format (one per line):
work_item_id | type | title | priority

Usage:
    python -m solokit.work_items.get_next_recommendations [--limit N]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def get_ready_work_items(limit: int = 4) -> list[dict[str, Any]]:
    """Get list of ready-to-start work items sorted by priority.

    Args:
        limit: Maximum number of items to return (default 4)

    Returns:
        list: Ready work items with id, type, title, priority
    """
    # Find work_items.json
    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
        print("Error: .session/tracking/work_items.json not found", file=sys.stderr)
        return []

    # Load work items
    try:
        with open(work_items_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {work_items_file}: {e}", file=sys.stderr)
        return []

    # Extract work_items from data structure
    work_items = data.get("work_items", {})
    if not work_items:
        print("⚠️ No work items found in this project\n", file=sys.stderr)
        print("To get started:", file=sys.stderr)
        print(
            "  1. Create a work item: sk work-new --type feature --title '...' --priority high",
            file=sys.stderr,
        )
        print("  2. Or use /work-new in Claude Code for interactive creation\n", file=sys.stderr)
        print("💡 Work items help track your development tasks and sessions", file=sys.stderr)
        return []

    # Check for urgent items first (highest priority, ignores dependencies)
    urgent_items = [
        {
            "id": wid,
            "type": item.get("type", "unknown"),
            "title": item.get("title", "Untitled"),
            "priority": item.get("priority", "medium"),
            "urgent": True,
        }
        for wid, item in work_items.items()
        if item.get("urgent", False) and item.get("status") == "not_started"
    ]

    # If urgent items exist, return them first
    if urgent_items:
        return urgent_items[:limit]

    # Filter to not_started items
    not_started = {
        wid: item for wid, item in work_items.items() if item.get("status") == "not_started"
    }

    if not not_started:
        print("No work items available to start", file=sys.stderr)
        return []

    # Check dependencies and filter to ready items
    ready_items = []

    for work_id, item in not_started.items():
        dependencies = item.get("dependencies", [])

        # Check if all dependencies are completed
        is_ready = True
        if dependencies:
            for dep_id in dependencies:
                dep_item = work_items.get(dep_id)
                if not dep_item or dep_item.get("status") != "completed":
                    is_ready = False
                    break

        if is_ready:
            ready_items.append(
                {
                    "id": work_id,
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", "Untitled"),
                    "priority": item.get("priority", "medium"),
                }
            )

    if not ready_items:
        print("⚠️ No work items ready to start\n", file=sys.stderr)
        print(
            "All work items may be blocked by dependencies or already completed.", file=sys.stderr
        )
        print("\nTo investigate:", file=sys.stderr)
        print("  1. Check all work items: sk work-list", file=sys.stderr)
        print("  2. View dependencies: sk work-graph", file=sys.stderr)
        print(
            "  3. Create a new work item: sk work-new --type feature --title '...' --priority high\n",
            file=sys.stderr,
        )
        return []

    # Sort by priority (critical > high > medium > low)
    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    ready_items.sort(key=lambda x: priority_order.get(x["priority"], 99))

    # Return top N items
    return ready_items[:limit]


def main() -> int:
    """Main entry point for script."""
    import argparse

    from solokit.core.argparse_helpers import HelpfulArgumentParser
    from solokit.core.system_utils import get_python_binary

    binary = get_python_binary()

    parser = HelpfulArgumentParser(
        description="Get next recommended work items for interactive selection",
        epilog=f"""
Examples:
  {binary} -m solokit.work_items.get_next_recommendations
  {binary} -m solokit.work_items.get_next_recommendations --limit 10

Returns work items that are ready to start (all dependencies satisfied),
sorted by priority (critical > high > medium > low).

Output format: work_item_id | type | title | priority

💡 View all work items: /work-list
💡 Start a work item: /start <work_item_id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Maximum number of recommendations to return",
    )
    args = parser.parse_args()

    ready_items = get_ready_work_items(limit=args.limit)

    if not ready_items:
        sys.exit(1)

    # Print table header
    print("\n📋 Ready Work Items (sorted by priority):\n")

    # Calculate column widths
    max_id_len = max((len(item["id"]) for item in ready_items), default=15)
    max_type_len = max((len(item["type"]) for item in ready_items), default=8)
    max_title_len = max((len(item["title"]) for item in ready_items), default=30)

    # Priority emoji mapping
    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }

    # Print header
    header = f"  {'ID':<{max_id_len}} | {'Type':<{max_type_len}} | {'Priority':<12} | {'Title':<{max_title_len}}"
    separator = "  " + "-" * len(header.replace("  ", ""))
    print(header)
    print(separator)

    # Print rows
    for idx, item in enumerate(ready_items):
        emoji = priority_emoji.get(item["priority"], "")
        marker = "→" if idx == 0 else " "  # Arrow for top recommendation
        priority_display = f"{emoji} {item['priority']}"
        print(
            f"{marker} {item['id']:<{max_id_len}} | {item['type']:<{max_type_len}} | {priority_display:<12} | {item['title']:<{max_title_len}}"
        )

    print(f"\n💡 Top recommendation: {ready_items[0]['id']}")
    print(f"   To start: /start {ready_items[0]['id']}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
