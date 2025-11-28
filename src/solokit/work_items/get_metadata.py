#!/usr/bin/env python3
"""
Get work item metadata without loading full spec.

Lightweight utility to fetch just the metadata fields for a work item,
avoiding the overhead of loading and displaying full specifications.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def get_work_item_metadata(
    work_item_id: str, include_dependency_details: bool = False
) -> dict | None:
    """Get work item metadata without loading spec file.

    Args:
        work_item_id: ID of the work item
        include_dependency_details: If True, include full details (type, title) for each dependency

    Returns:
        dict: Work item metadata (id, type, title, status, priority, dependencies, milestone)
              If include_dependency_details=True, also includes 'dependency_details' list
        None: If work item doesn't exist
    """
    # Find work_items.json
    session_dir = Path.cwd() / ".session"
    work_items_file = session_dir / "tracking" / "work_items.json"

    if not work_items_file.exists():
        return None

    # Load work items
    with open(work_items_file) as f:
        data = json.load(f)

    work_items = data.get("work_items", {})

    if work_item_id not in work_items:
        return None

    item = work_items[work_item_id]

    # Build metadata
    metadata = {
        "id": item["id"],
        "type": item["type"],
        "title": item["title"],
        "status": item["status"],
        "priority": item["priority"],
        "dependencies": item.get("dependencies", []),
        "milestone": item.get("milestone", ""),
    }

    # Optionally include dependency details (fetch all in one pass)
    if include_dependency_details and metadata["dependencies"]:
        dep_details = []
        for dep_id in metadata["dependencies"]:
            if dep_id in work_items:
                dep_item = work_items[dep_id]
                dep_details.append(
                    {
                        "id": dep_id,
                        "type": dep_item["type"],
                        "title": dep_item["title"],
                        "status": dep_item.get("status", "unknown"),
                    }
                )
        metadata["dependency_details"] = dep_details

    return metadata


def main() -> int:
    """CLI entry point."""
    from solokit.core.system_utils import get_python_binary

    if len(sys.argv) < 2:
        binary = get_python_binary()
        print("❌ Error: Missing required argument <work_item_id>\n", file=sys.stderr)
        print(
            f"Usage: {binary} -m solokit.work_items.get_metadata <work_item_id> [--with-deps]\n",
            file=sys.stderr,
        )
        print("Examples:", file=sys.stderr)
        print(f"  {binary} -m solokit.work_items.get_metadata feat_001", file=sys.stderr)
        print(
            f"  {binary} -m solokit.work_items.get_metadata feat_001 --with-deps\n", file=sys.stderr
        )
        print("💡 List all work items: /work-list", file=sys.stderr)
        print("💡 Use '/work-show <work_id>' for full details including spec\n", file=sys.stderr)
        sys.exit(1)

    work_item_id = sys.argv[1]
    include_deps = "--with-deps" in sys.argv

    metadata = get_work_item_metadata(work_item_id, include_dependency_details=include_deps)

    if metadata is None:
        print(f"Error: Work item '{work_item_id}' not found", file=sys.stderr)
        sys.exit(1)

    # Print in a clean, parseable format
    print(f"ID: {metadata['id']}")
    print(f"Type: {metadata['type']}")
    print(f"Title: {metadata['title']}")
    print(f"Status: {metadata['status']}")
    print(f"Priority: {metadata['priority']}")
    print(f"Milestone: {metadata['milestone'] or '(none)'}")

    if metadata["dependencies"]:
        if "dependency_details" in metadata:
            # Print with full details
            deps_str = []
            for dep in metadata["dependency_details"]:
                deps_str.append(f"{dep['id']} ([{dep['type']}] {dep['title']} - {dep['status']})")
            print("Dependencies:\n  " + "\n  ".join(deps_str))
        else:
            # Print just IDs
            print(f"Dependencies: {', '.join(metadata['dependencies'])}")
    else:
        print("Dependencies: (none)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
