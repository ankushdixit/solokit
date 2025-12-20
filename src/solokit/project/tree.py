#!/usr/bin/env python3
"""
Generate and update project tree documentation.

Tracks structural changes to the project with reasoning.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import TREE_GENERATION_TIMEOUT
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    FileOperationError,
)
from solokit.core.output import get_output

output = get_output()


class TreeGenerator:
    """Generate project tree documentation."""

    def __init__(self, project_root: Path | None = None):
        """Initialize TreeGenerator with project root path."""
        self.project_root = project_root or Path.cwd()
        self.tree_file = self.project_root / ".session" / "tracking" / "tree.txt"
        self.updates_file = self.project_root / ".session" / "tracking" / "tree_updates.json"
        self.runner = CommandRunner(
            default_timeout=TREE_GENERATION_TIMEOUT, working_dir=self.project_root
        )

        # Items to ignore
        self.ignore_patterns = [
            # Version control
            ".git",
            # Python
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".venv",
            "venv",
            "*.egg-info",
            ".mypy_cache",
            ".ruff_cache",
            # JavaScript/TypeScript
            "node_modules",
            ".next",
            ".turbo",
            "out",
            "build",
            "dist",
            ".vercel",
            "*.tsbuildinfo",
            # Test coverage
            "coverage",
            ".nyc_output",
            # Caches
            ".cache",
            # OS
            ".DS_Store",
            # Temp/logs
            "*.log",
            "*.tmp",
            "*.backup",
            # Solokit
            ".session",
        ]

    @log_errors()
    def generate_tree(self) -> str:
        """Generate tree using tree command, falls back to Python implementation.

        Returns:
            str: Project tree representation

        Raises:
            FileOperationError: If tree generation fails completely
        """
        try:
            # On Windows, 'tree' command is incompatible (tree.com) or may not exist.
            # Use Python fallback for consistent behavior.
            if sys.platform == "win32":
                return self._generate_tree_fallback()

            # Build ignore arguments
            ignore_args = []
            for pattern in self.ignore_patterns:
                ignore_args.extend(["-I", pattern])

            result = self.runner.run(["tree", "-a", "--dirsfirst"] + ignore_args)

            if result.success:
                return result.stdout
            else:
                # tree command failed, use fallback
                return self._generate_tree_fallback()

        except (OSError, FileNotFoundError):
            # tree command not available, use fallback
            return self._generate_tree_fallback()

    def _generate_tree_fallback(self) -> str:
        """Fallback tree generation without tree command.

        Returns:
            str: Project tree representation

        Raises:
            FileOperationError: If filesystem operations fail
        """
        lines = [str(self.project_root.name) + "/"]

        def should_ignore(path: Path) -> bool:
            for pattern in self.ignore_patterns:
                if pattern.startswith("*"):
                    if path.name.endswith(pattern[1:]):
                        return True
                elif pattern in path.parts:
                    return True
            return False

        def add_tree(path: Path, prefix: str = "", is_last: bool = True) -> None:
            if should_ignore(path):
                return

            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + path.name)

            if path.is_dir():
                children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                children = [c for c in children if not should_ignore(c)]

                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    extension = "    " if is_last else "│   "
                    add_tree(child, prefix + extension, is_last_child)

        # Generate tree
        try:
            children = sorted(self.project_root.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            children = [c for c in children if not should_ignore(c)]

            for i, child in enumerate(children):
                add_tree(child, "", i == len(children) - 1)

            return "\n".join(lines)
        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.project_root),
                details="Failed to generate project tree",
                cause=e,
            ) from e

    def detect_changes(self, old_tree: str, new_tree: str) -> list[dict]:
        """Detect structural changes between trees."""
        old_lines = set(old_tree.split("\n"))
        new_lines = set(new_tree.split("\n"))

        added = new_lines - old_lines
        removed = old_lines - new_lines

        changes = []

        # Categorize changes
        for line in added:
            if "/" in line or line.strip().endswith("/"):
                changes.append({"type": "directory_added", "path": line.strip()})
            elif line.strip():
                changes.append({"type": "file_added", "path": line.strip()})

        for line in removed:
            if "/" in line or line.strip().endswith("/"):
                changes.append({"type": "directory_removed", "path": line.strip()})
            elif line.strip():
                changes.append({"type": "file_removed", "path": line.strip()})

        return changes

    @log_errors()
    def update_tree(
        self, session_num: int | None = None, non_interactive: bool = False
    ) -> list[dict[str, str]]:
        """Generate/update tree.txt and detect changes.

        Args:
            session_num: Current session number
            non_interactive: If True, skip interactive reasoning prompts

        Raises:
            FileOperationError: If reading/writing tree files fails
        """
        # Generate new tree
        new_tree = self.generate_tree()

        # Load old tree if exists
        old_tree = ""
        if self.tree_file.exists():
            try:
                old_tree = self.tree_file.read_text()
            except OSError as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(self.tree_file),
                    details="Failed to read existing tree file",
                    cause=e,
                ) from e

        # Detect changes
        changes = self.detect_changes(old_tree, new_tree)

        # Filter out minor changes (just ordering, etc.)
        significant_changes = [
            c
            for c in changes
            if c["type"] in ["directory_added", "directory_removed"]
            or len(changes) < 20  # If few changes, they're probably significant
        ]

        # Save new tree
        try:
            self.tree_file.parent.mkdir(parents=True, exist_ok=True)
            self.tree_file.write_text(new_tree)
        except OSError as e:
            raise FileOperationError(
                operation="write",
                file_path=str(self.tree_file),
                details="Failed to write tree file",
                cause=e,
            ) from e

        # If significant changes detected, prompt for reasoning (unless non-interactive)
        if significant_changes and session_num:
            output.info(f"\n{'=' * 50}")
            output.info("Structural Changes Detected")
            output.info("=" * 50)

            for change in significant_changes[:10]:  # Show first 10
                output.info(f"  {change['type'].upper()}: {change['path']}")

            if len(significant_changes) > 10:
                output.info(f"  ... and {len(significant_changes) - 10} more changes")

            if non_interactive:
                reasoning = "Automated update during session completion"
                output.info("\n(Non-interactive mode: recording changes without manual reasoning)")
            else:
                output.info("\nPlease provide reasoning for these structural changes:")
                reasoning = input("> ")

            # Update tree_updates.json
            self._record_tree_update(session_num, significant_changes, reasoning)

        return changes

    @log_errors()
    def _record_tree_update(
        self, session_num: int, changes: list[dict[str, Any]], reasoning: str
    ) -> None:
        """Record tree update in tree_updates.json.

        Args:
            session_num: Current session number
            changes: List of detected changes
            reasoning: User-provided reasoning for changes

        Raises:
            FileOperationError: If writing tree updates fails
        """
        updates: dict[str, Any] = {"updates": []}

        if self.updates_file.exists():
            try:
                updates = json.loads(self.updates_file.read_text())
            except (json.JSONDecodeError, OSError):
                # If tree_updates.json is corrupted or unreadable, start fresh
                # Log warning but don't fail - we can rebuild the history
                updates = {"updates": []}

        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_num,
            "changes": changes,
            "reasoning": reasoning,
            "architecture_impact": "",  # Could prompt for this too
        }

        updates["updates"].append(update_entry)

        try:
            self.updates_file.write_text(json.dumps(updates, indent=2))
        except OSError as e:
            raise FileOperationError(
                operation="write",
                file_path=str(self.updates_file),
                details="Failed to write tree updates",
                cause=e,
            ) from e


def main() -> None:
    """CLI entry point.

    Handles exceptions and provides user-friendly error messages.
    """
    import argparse

    from solokit.core.exceptions import SolokitError
    from solokit.core.output import get_output

    output = get_output()

    parser = argparse.ArgumentParser(description="Generate project tree documentation")
    parser.add_argument("--session", type=int, help="Current session number")
    parser.add_argument("--show-changes", action="store_true", help="Show changes from last run")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive prompts (use automated reasoning)",
    )
    args = parser.parse_args()

    try:
        generator = TreeGenerator()

        if args.show_changes:
            if generator.updates_file.exists():
                try:
                    updates = json.loads(generator.updates_file.read_text())
                    output.info("Recent structural changes:")
                    for update in updates["updates"][-5:]:
                        output.info(f"\nSession {update['session']} ({update['timestamp']})")
                        output.info(f"Reasoning: {update['reasoning']}")
                        output.info(f"Changes: {len(update['changes'])}")
                except (json.JSONDecodeError, KeyError) as e:
                    raise FileOperationError(
                        operation="read",
                        file_path=str(generator.updates_file),
                        details="Failed to parse tree updates file",
                        cause=e,
                    ) from e
            else:
                output.info("No tree updates recorded yet")
        else:
            changes = generator.update_tree(
                session_num=args.session, non_interactive=args.non_interactive
            )

            if changes:
                output.info(f"\n✓ Tree updated with {len(changes)} changes")
            else:
                output.info("\n✓ Tree generated (no changes)")

            output.info(f"✓ Saved to: {generator.tree_file}")

    except SolokitError as e:
        # Handle structured Solokit errors with user-friendly output
        output.error(f"\nError: {e.message}")
        if e.remediation:
            output.error(f"Suggestion: {e.remediation}")
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        output.error("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        # Unexpected errors
        output.error(f"\nUnexpected error: {e}")
        output.error("Please report this issue.")
        sys.exit(1)


if __name__ == "__main__":
    main()
