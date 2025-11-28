#!/usr/bin/env python3
"""
Work Item Deletion - Safe deletion of work items.

Handles deletion of work items with dependency checking and interactive confirmation.
"""

from pathlib import Path

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.exceptions import (
    FileOperationError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.file_ops import load_json, save_json
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import WorkItemStatus

logger = get_logger(__name__)
output = get_output()


def find_dependents(work_items: dict, work_item_id: str) -> list[str]:
    """
    Find work items that depend on the given work item.

    Args:
        work_items: Dictionary of all work items
        work_item_id: ID to find dependents for

    Returns:
        List of work item IDs that depend on this item
    """
    dependents = []
    for wid, item in work_items.items():
        deps = item.get("dependencies", [])
        if work_item_id in deps:
            dependents.append(wid)
    return dependents


@log_errors()
def delete_work_item(
    work_item_id: str, delete_spec: bool | None = None, project_root: Path | None = None
) -> bool:
    """
    Delete a work item from the system.

    Args:
        work_item_id: ID of work item to delete
        delete_spec: Whether to also delete the spec file (None for interactive prompt)
        project_root: Project root path (defaults to current directory)

    Returns:
        True if deletion successful, False if user cancels

    Raises:
        SolokitFileNotFoundError: If work_items.json doesn't exist
        WorkItemNotFoundError: If work item ID doesn't exist
        FileOperationError: If unable to load or save work items file
        ValidationError: If running in non-interactive mode without flags
    """
    # Setup paths
    if project_root is None:
        project_root = Path.cwd()

    session_dir = project_root / ".session"
    work_items_file = session_dir / "tracking" / "work_items.json"

    # Check if work items file exists
    if not work_items_file.exists():
        logger.error("Work items file not found")
        raise SolokitFileNotFoundError(file_path=str(work_items_file), file_type="work items")

    # Load work items
    try:
        work_items_data = load_json(work_items_file)
    except (OSError, ValueError) as e:
        logger.error("Failed to load work items: %s", e)
        raise FileOperationError(
            operation="read", file_path=str(work_items_file), details=str(e), cause=e
        ) from e

    work_items = work_items_data.get("work_items", {})

    # Validate work item exists
    if work_item_id not in work_items:
        # Don't log error here - user-facing error message is clear
        raise WorkItemNotFoundError(work_item_id)

    item = work_items[work_item_id]

    # Find dependents
    dependents = find_dependents(work_items, work_item_id)

    # Show work item details
    output.warning(f"\nThis will permanently delete work item '{work_item_id}'")
    output.info("\nWork item details:")
    output.info(f"  Title: {item.get('title', 'N/A')}")
    output.info(f"  Type: {item.get('type', 'N/A')}")
    output.info(f"  Status: {item.get('status', 'N/A')}")

    dependencies = item.get("dependencies", [])
    if dependencies:
        output.info(f"  Dependencies: {', '.join(dependencies)}")
    else:
        output.info("  Dependencies: none")

    if dependents:
        output.info(
            f"  Dependents: {', '.join(dependents)} ({len(dependents)} item(s) depend on this)"
        )
    else:
        output.info("  Dependents: none")

    # Interactive prompt if no flag provided
    if delete_spec is None:
        output.info("\nWhat would you like to delete?")
        output.info("  1. Delete work item only (keep spec file)")
        output.info("  2. Delete work item and spec file")
        output.info("  3. Cancel")
        output.info("")

        try:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1":
                delete_spec = False
            elif choice == "2":
                delete_spec = True
            elif choice == "3":
                output.info("Deletion cancelled.")
                return False
            else:
                output.warning("Invalid choice. Deletion cancelled.")
                return False
        except (EOFError, KeyboardInterrupt):
            output.info("\nDeletion cancelled.")
            return False

    # Show what will be done
    if delete_spec:
        output.info("\n→ Will delete work item and spec file")
    else:
        output.info("\n→ Will delete work item only (keeping spec file)")

    # Perform deletion
    logger.info("Deleting work item '%s'", work_item_id)
    del work_items[work_item_id]

    # Update metadata
    work_items_data["work_items"] = work_items
    if "metadata" not in work_items_data:
        work_items_data["metadata"] = {}

    work_items_data["metadata"]["total_items"] = len(work_items)
    work_items_data["metadata"]["completed"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
    )
    work_items_data["metadata"]["in_progress"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
    )
    work_items_data["metadata"]["blocked"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
    )

    # Save work items
    try:
        save_json(work_items_file, work_items_data)
        logger.info("Successfully updated work_items.json")
        output.info(f"✓ Deleted work item '{work_item_id}'")
    except OSError as e:
        logger.error("Failed to save work items: %s", e)
        raise FileOperationError(
            operation="write", file_path=str(work_items_file), details=str(e), cause=e
        ) from e

    # Delete spec file if requested
    if delete_spec:
        spec_file_path = item.get("spec_file", f".session/specs/{work_item_id}.md")
        spec_path = project_root / spec_file_path

        if spec_path.exists():
            try:
                spec_path.unlink()
                logger.info("Deleted spec file: %s", spec_file_path)
                output.info(f"✓ Deleted spec file '{spec_file_path}'")
            except (OSError, PermissionError) as e:
                logger.warning("Failed to delete spec file: %s", e)
                output.warning(f"Could not delete spec file: {e}")
        else:
            logger.debug("Spec file not found: %s", spec_file_path)
            output.info(f"Note: Spec file '{spec_file_path}' not found")

    # Warn about dependents
    if dependents:
        output.warning("\nThe following work items depend on this item:")
        for dep in dependents:
            output.info(f"    - {dep}")
        output.info("  Update their dependencies manually if needed.")

    output.info("\nDeletion successful.")
    logger.info("Work item deletion completed successfully")
    return True


def main() -> int:
    """CLI entry point for work item deletion."""
    import argparse

    from solokit.core.argparse_helpers import HelpfulArgumentParser

    parser = HelpfulArgumentParser(
        description="Delete a work item",
        epilog="""
Examples:
  sk work-delete feat_001
  sk work-delete feat_001 --keep-spec
  sk work-delete feat_001 --delete-spec

By default, prompts to confirm spec file deletion.
Use --keep-spec to preserve the spec file.
Use --delete-spec to skip confirmation and delete both.

💡 View all work items: /work-list
💡 Restore accidentally deleted items from git: git checkout HEAD -- .session/
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("work_item_id", help="ID of work item to delete")
    parser.add_argument(
        "--keep-spec",
        action="store_true",
        help="Keep the spec file (delete work item only)",
    )
    parser.add_argument(
        "--delete-spec",
        action="store_true",
        help="Delete both work item and spec file",
    )

    args = parser.parse_args()

    # Determine delete_spec value
    delete_spec_value = None
    if args.keep_spec and args.delete_spec:
        raise ValidationError(
            message="Cannot specify both --keep-spec and --delete-spec",
            remediation="Choose only one option: --keep-spec OR --delete-spec",
        )
    elif args.keep_spec:
        delete_spec_value = False
    elif args.delete_spec:
        delete_spec_value = True

    # Perform deletion
    try:
        success = delete_work_item(args.work_item_id, delete_spec=delete_spec_value)
        return 0 if success else 1
    except WorkItemNotFoundError as e:
        output.info(f"❌ Error: {e.message}")
        if e.remediation:
            output.info(f"\n{e.remediation}")
        # Show available work items
        try:
            from pathlib import Path

            work_items_file = Path.cwd() / ".session" / "tracking" / "work_items.json"
            if work_items_file.exists():
                work_items_data = load_json(work_items_file)
                work_items = work_items_data.get("work_items", {})
                if work_items:
                    output.info("\nAvailable work items:")
                    for wid in list(work_items.keys())[:5]:
                        output.info(f"  - {wid}")
                    if len(work_items) > 5:
                        output.info(f"  ... and {len(work_items) - 5} more")
        except Exception:  # noqa: BLE001 - This is optional enhancement, don't fail on it
            pass
        return e.exit_code
    except (SolokitFileNotFoundError, FileOperationError, ValidationError) as e:
        output.info(f"❌ Error: {e.message}")
        if e.remediation:
            output.info(f"\n{e.remediation}")
        return e.exit_code


if __name__ == "__main__":
    exit(main())
