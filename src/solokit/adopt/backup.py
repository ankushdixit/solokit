"""
Backup System for Safe Adoption.

Creates timestamped backups of files before modification during sk adopt.
Follows the "do no harm" philosophy for existing projects.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_DIR = ".solokit-backup"


def create_backup_directory(project_root: Path) -> Path:
    """
    Create a timestamped backup directory.

    Args:
        project_root: Project root directory

    Returns:
        Path to the created backup directory

    Example:
        >>> backup_dir = create_backup_directory(Path("/my/project"))
        >>> backup_dir
        PosixPath('/my/project/.solokit-backup/20250125_143022')
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / BACKUP_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created backup directory: {backup_dir}")
    return backup_dir


def backup_file(file_path: Path, backup_dir: Path) -> Path | None:
    """
    Create a backup of a single file.

    Preserves the relative directory structure for nested files
    (e.g., prisma/schema.prisma maintains its path in backup).

    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store the backup

    Returns:
        Path to the backup file, or None if source file doesn't exist
    """
    if not file_path.exists():
        logger.debug(f"File does not exist, skipping backup: {file_path}")
        return None

    # Use just the filename for the backup path
    # Nested paths like prisma/schema.prisma become schema.prisma in backup
    # This is simpler and avoids complex path reconstruction
    backup_path = backup_dir / file_path.name

    # Handle potential conflicts by including parent dir in name
    if backup_path.exists():
        # If there's a conflict (e.g., two schema.prisma files),
        # include parent directory in the name
        parent_prefix = file_path.parent.name
        backup_path = backup_dir / f"{parent_prefix}_{file_path.name}"

    try:
        # Create parent directories if needed (for edge cases)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backed up: {file_path} -> {backup_path}")
        return backup_path
    except OSError as e:
        logger.warning(f"Failed to backup {file_path}: {e}")
        return None


def backup_file_with_structure(
    file_path: Path,
    backup_dir: Path,
    project_root: Path,
) -> Path | None:
    """
    Create a backup preserving the full relative directory structure.

    This is useful when you need to restore files to their exact locations.

    Args:
        file_path: Absolute path to the file to backup
        backup_dir: Directory to store the backup
        project_root: Project root for calculating relative paths

    Returns:
        Path to the backup file, or None if source file doesn't exist
    """
    if not file_path.exists():
        logger.debug(f"File does not exist, skipping backup: {file_path}")
        return None

    try:
        relative_path = file_path.relative_to(project_root)
    except ValueError:
        # File is not under project_root, use filename only
        relative_path = Path(file_path.name)

    backup_path = backup_dir / relative_path

    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Backed up with structure: {file_path} -> {backup_path}")
        return backup_path
    except OSError as e:
        logger.warning(f"Failed to backup {file_path}: {e}")
        return None


def get_backup_gitignore_entry() -> str:
    """
    Return the gitignore entry for backup directory.

    Returns:
        Gitignore pattern string with comment
    """
    return f"\n# Solokit adoption backups\n{BACKUP_DIR}/\n"


def list_backups(project_root: Path) -> list[Path]:
    """
    List all backup directories in chronological order.

    Args:
        project_root: Project root directory

    Returns:
        List of backup directory paths, oldest first
    """
    backup_root = project_root / BACKUP_DIR
    if not backup_root.exists():
        return []

    backups = [d for d in backup_root.iterdir() if d.is_dir()]
    # Sort by directory name (which is timestamp-based)
    return sorted(backups)


def get_latest_backup(project_root: Path) -> Path | None:
    """
    Get the most recent backup directory.

    Args:
        project_root: Project root directory

    Returns:
        Path to latest backup directory, or None if no backups exist
    """
    backups = list_backups(project_root)
    return backups[-1] if backups else None


def cleanup_old_backups(project_root: Path, keep: int = 5) -> int:
    """
    Remove old backup directories, keeping only the most recent ones.

    Args:
        project_root: Project root directory
        keep: Number of recent backups to keep (default: 5)

    Returns:
        Number of backup directories removed
    """
    backups = list_backups(project_root)

    if len(backups) <= keep:
        return 0

    to_remove = backups[:-keep]
    removed = 0

    for backup_dir in to_remove:
        try:
            shutil.rmtree(backup_dir)
            logger.info(f"Removed old backup: {backup_dir}")
            removed += 1
        except OSError as e:
            logger.warning(f"Failed to remove backup {backup_dir}: {e}")

    return removed
