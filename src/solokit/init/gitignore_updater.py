"""
Gitignore Updater Module

Updates .gitignore with Solokit and stack-specific entries.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError

logger = logging.getLogger(__name__)


def get_stack_specific_gitignore_entries(template_id: str) -> list[str]:
    """
    Get stack-specific .gitignore entries.

    Args:
        template_id: Template identifier

    Returns:
        List of gitignore patterns
    """
    # Common entries for all stacks
    common_entries = [
        ".session/briefings/",
        ".session/history/",
        "coverage/",
        "coverage.json",
    ]

    # Node.js/Next.js stacks
    if template_id in ["saas_t3", "dashboard_refine", "fullstack_nextjs"]:
        return common_entries + [
            "node_modules/",
            ".next/",
            "out/",
            "build/",
            "dist/",
            "*.tsbuildinfo",
            ".env",
            ".env.local",
            ".env.*.local",
        ]

    # Python stacks
    elif template_id == "ml_ai_fastapi":
        return common_entries + [
            "venv/",
            ".venv/",
            "*.pyc",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".env",
            ".env.local",
        ]

    else:
        return common_entries


def get_os_specific_gitignore_entries() -> list[str]:
    """
    Get OS-specific .gitignore entries.

    Returns:
        List of gitignore patterns with comments
    """
    return [
        "# OS-specific files",
        ".DS_Store           # macOS",
        ".DS_Store?          # macOS",
        "._*                 # macOS resource forks",
        ".Spotlight-V100     # macOS",
        ".Trashes            # macOS",
        "Thumbs.db           # Windows",
        "ehthumbs.db         # Windows",
        "Desktop.ini         # Windows",
        "$RECYCLE.BIN/       # Windows",
        "*~                  # Linux backup files",
    ]


def update_gitignore(template_id: str, project_root: Path | None = None) -> Path:
    """
    Add Solokit and stack-specific patterns to .gitignore.

    Args:
        template_id: Template identifier
        project_root: Project root directory

    Returns:
        Path to .gitignore file

    Raises:
        FileOperationError: If .gitignore read/write operations fail.
    """
    if project_root is None:
        project_root = Path.cwd()

    gitignore = project_root / ".gitignore"

    # Get entries to add
    stack_entries = get_stack_specific_gitignore_entries(template_id)
    os_entries = get_os_specific_gitignore_entries()

    try:
        existing_content = gitignore.read_text() if gitignore.exists() else ""
    except Exception as e:
        raise FileOperationError(
            operation="read",
            file_path=str(gitignore),
            details=f"Failed to read .gitignore: {str(e)}",
            cause=e,
        )

    # Determine which entries need to be added
    entries_to_add = []
    for entry in stack_entries:
        if entry not in existing_content:
            entries_to_add.append(entry)

    # Check which OS patterns need to be added
    # First, extract existing patterns (lines without comments)
    existing_lines = [line.strip() for line in existing_content.split("\n")]
    existing_patterns = set()
    for line in existing_lines:
        # Extract pattern (part before comment if any)
        pattern = line.split("#")[0].strip()
        if pattern:
            # Normalize pattern - remove trailing ? for comparison
            normalized = pattern.rstrip("?")
            existing_patterns.add(normalized)

    os_patterns_needed = []
    for entry in os_entries:
        if entry.startswith("#"):
            continue  # Skip header in first pass
        # Skip comment-only lines in first pass
        pattern = entry.split("#")[0].strip()
        if pattern:
            # Normalize pattern for comparison
            normalized = pattern.rstrip("?")
            if normalized not in existing_patterns:
                os_patterns_needed.append(entry)

    # If we need to add any OS patterns, include the header
    os_entries_to_add = []
    if os_patterns_needed:
        # Add the section header first
        if "# OS-specific files" not in existing_content:
            os_entries_to_add.append("# OS-specific files")
        # Then add all the patterns
        os_entries_to_add.extend(os_patterns_needed)

    # Write updates
    if entries_to_add or os_entries_to_add:
        logger.info("Updating .gitignore...")
        try:
            with open(gitignore, "a") as f:
                if existing_content and not existing_content.endswith("\n"):
                    f.write("\n")

                if entries_to_add:
                    f.write("\n# Solokit-related patterns\n")
                    for entry in entries_to_add:
                        f.write(f"{entry}\n")

                if os_entries_to_add:
                    f.write("\n")
                    for entry in os_entries_to_add:
                        f.write(f"{entry}\n")

            total_added = len(entries_to_add) + len(
                [e for e in os_entries_to_add if not e.startswith("#")]
            )
            logger.info(f"Added {total_added} entries to .gitignore")
        except Exception as e:
            raise FileOperationError(
                operation="write",
                file_path=str(gitignore),
                details=f"Failed to update .gitignore: {str(e)}",
                cause=e,
            )
    else:
        logger.info(".gitignore already up to date")

    return gitignore


def update_minimal_gitignore(project_root: Path | None = None) -> Path:
    """
    Add minimal Solokit patterns to .gitignore without stack-specific entries.

    This is used for minimal init mode - projects that don't have a specific
    tech stack but still need Solokit-related gitignore patterns.

    Args:
        project_root: Project root directory

    Returns:
        Path to .gitignore file

    Raises:
        FileOperationError: If .gitignore read/write operations fail.
    """
    if project_root is None:
        project_root = Path.cwd()

    gitignore = project_root / ".gitignore"

    # Minimal Solokit entries (no stack-specific patterns)
    minimal_entries = [
        ".session/briefings/",
        ".session/history/",
    ]

    os_entries = get_os_specific_gitignore_entries()

    try:
        existing_content = gitignore.read_text() if gitignore.exists() else ""
    except Exception as e:
        raise FileOperationError(
            operation="read",
            file_path=str(gitignore),
            details=f"Failed to read .gitignore: {str(e)}",
            cause=e,
        )

    # Determine which entries need to be added
    entries_to_add = []
    for entry in minimal_entries:
        if entry not in existing_content:
            entries_to_add.append(entry)

    # Check which OS patterns need to be added
    existing_lines = [line.strip() for line in existing_content.split("\n")]
    existing_patterns = set()
    for line in existing_lines:
        pattern = line.split("#")[0].strip()
        if pattern:
            normalized = pattern.rstrip("?")
            existing_patterns.add(normalized)

    os_patterns_needed = []
    for entry in os_entries:
        if entry.startswith("#"):
            continue
        pattern = entry.split("#")[0].strip()
        if pattern:
            normalized = pattern.rstrip("?")
            if normalized not in existing_patterns:
                os_patterns_needed.append(entry)

    os_entries_to_add = []
    if os_patterns_needed:
        if "# OS-specific files" not in existing_content:
            os_entries_to_add.append("# OS-specific files")
        os_entries_to_add.extend(os_patterns_needed)

    # Write updates
    if entries_to_add or os_entries_to_add:
        logger.info("Updating .gitignore...")
        try:
            with open(gitignore, "a") as f:
                if existing_content and not existing_content.endswith("\n"):
                    f.write("\n")

                if entries_to_add:
                    f.write("\n# Solokit-related patterns\n")
                    for entry in entries_to_add:
                        f.write(f"{entry}\n")

                if os_entries_to_add:
                    f.write("\n")
                    for entry in os_entries_to_add:
                        f.write(f"{entry}\n")

            total_added = len(entries_to_add) + len(
                [e for e in os_entries_to_add if not e.startswith("#")]
            )
            logger.info(f"Added {total_added} entries to .gitignore")
        except Exception as e:
            raise FileOperationError(
                operation="write",
                file_path=str(gitignore),
                details=f"Failed to update .gitignore: {str(e)}",
                cause=e,
            )
    else:
        logger.info(".gitignore already up to date")

    return gitignore
