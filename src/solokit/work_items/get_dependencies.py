"""Fast dependency information retrieval for Claude Code integration.

This module provides optimized dependency lookups without reading full spec files.
Used by /work-new and /work-delete commands to fetch available dependencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def get_available_dependencies(
    exclude_statuses: list[str] | None = None,
    title_filter: str | None = None,
    max_results: int = 3,
) -> list[dict[str, Any]]:
    """Get available work items that can be used as dependencies.

    Args:
        exclude_statuses: List of statuses to exclude (default: ["completed"])
        title_filter: Optional title to use for smart filtering/relevance
        max_results: Maximum number of results to return (default: 3)

    Returns:
        List of dependency info dicts with keys: id, type, title, status

    Raises:
        FileNotFoundError: If work_items.json doesn't exist
        json.JSONDecodeError: If work_items.json is invalid
    """
    if exclude_statuses is None:
        exclude_statuses = ["completed"]

    # Find .session directory
    session_dir = _find_session_dir()
    if not session_dir:
        print("Error: Not in an Solokit project (no .session directory found)", file=sys.stderr)
        return []

    # Load work items
    work_items_file = session_dir / "tracking" / "work_items.json"
    if not work_items_file.exists():
        print(f"Error: Work items file not found: {work_items_file}", file=sys.stderr)
        return []

    try:
        with open(work_items_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {work_items_file}: {e}", file=sys.stderr)
        return []

    # Extract work_items from the data structure
    work_items = data.get("work_items", {})
    if not work_items:
        print("No work items found", file=sys.stderr)
        return []

    # Filter available dependencies
    available = []
    for work_id, item in work_items.items():
        status = item.get("status", "unknown")
        if status not in exclude_statuses:
            available.append(
                {
                    "id": work_id,
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", "Untitled"),
                    "status": status,
                }
            )

    # Apply smart filtering if title provided
    if title_filter and available:
        available = _filter_by_relevance(available, title_filter)

    # Limit results
    return available[:max_results]


def _find_session_dir() -> Path | None:
    """Find the .session directory by walking up from current directory."""
    current = Path.cwd()
    while current != current.parent:
        session_dir = current / ".session"
        if session_dir.is_dir():
            return session_dir
        current = current.parent
    return None


def _filter_by_relevance(items: list[dict], title: str) -> list[dict]:
    """Filter and sort items by relevance to the given title.

    Simple keyword-based relevance scoring:
    - Exact word matches in title get highest score
    - Partial matches get medium score
    - Items with same type get bonus points

    Args:
        items: List of work item dicts
        title: Title to compare against

    Returns:
        Sorted list (most relevant first)
    """
    title_lower = title.lower()
    title_words = set(title_lower.split())

    def relevance_score(item: dict) -> float:
        item_title_lower = item["title"].lower()
        item_words = set(item_title_lower.split())

        # Exact word matches (high weight)
        word_matches = len(title_words & item_words)

        # Partial matches (medium weight)
        partial_matches = sum(1 for tw in title_words for iw in item_words if tw in iw or iw in tw)

        # Calculate score
        score = (word_matches * 3.0) + (partial_matches * 1.5)

        return score

    # Score and sort
    scored = [(item, relevance_score(item)) for item in items]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return only items with non-zero scores, or all if none match
    relevant = [item for item, score in scored if score > 0]
    return relevant if relevant else items


def main() -> None:
    """CLI entry point for get_dependencies script."""
    import argparse

    from solokit.core.argparse_helpers import HelpfulArgumentParser
    from solokit.core.system_utils import get_python_binary

    binary = get_python_binary()

    parser = HelpfulArgumentParser(
        description="Get available dependencies for work items",
        epilog=f"""
Examples:
  {binary} -m solokit.work_items.get_dependencies
  {binary} -m solokit.work_items.get_dependencies --title "My new feature"
  {binary} -m solokit.work_items.get_dependencies --title "Bug fix" --max 5
  {binary} -m solokit.work_items.get_dependencies --exclude-status not_started,in_progress

Returns work items that can be used as dependencies (excluding completed by default).
Uses smart filtering when --title is provided to show most relevant dependencies.

💡 View all work items: /work-list
💡 Create work item with dependencies: /work-new (or CLI: sk work-new -t feature -T "..." -p high -d feat_001,bug_002)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--title", help="Optional title for smart filtering by relevance")
    parser.add_argument("--max", type=int, default=3, help="Maximum number of results")
    parser.add_argument("--exclude-status", help="Comma-separated list of statuses to exclude")

    args = parser.parse_args()

    # Parse exclude statuses
    exclude = None
    if args.exclude_status:
        exclude = [s.strip() for s in args.exclude_status.split(",")]

    # Get dependencies
    dependencies = get_available_dependencies(
        exclude_statuses=exclude,
        title_filter=args.title,
        max_results=args.max,
    )

    # Output results
    if not dependencies:
        print("⚠️ No available dependencies found\n", file=sys.stderr)
        print("All work items may be completed or excluded by your filters.", file=sys.stderr)
        print("\nTo see all work items:", file=sys.stderr)
        print("  sk work-list\n", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(dependencies)} available dependencies:")
    print()
    for dep in dependencies:
        print(f"ID: {dep['id']}")
        print(f"Type: {dep['type']}")
        print(f"Title: {dep['title']}")
        print(f"Status: {dep['status']}")
        print()


if __name__ == "__main__":
    main()
