"""
Tests for backup module.

Validates backup system functionality for safe adoption.

Run tests:
    pytest tests/unit/adopt/test_backup.py -v

Target: 95%+ coverage
"""

import shutil
import sys
from datetime import datetime
from unittest.mock import patch
import pytest

from solokit.adopt.backup import (
    BACKUP_DIR,
    backup_file,
    backup_file_with_structure,
    cleanup_old_backups,
    create_backup_directory,
    get_backup_gitignore_entry,
    get_latest_backup,
    list_backups,
)


class TestCreateBackupDirectory:
    """Tests for create_backup_directory() function."""

    def test_creates_timestamped_directory(self, temp_project):
        """Test that backup directory is created with timestamp."""
        backup_dir = create_backup_directory(temp_project)

        assert backup_dir.exists()
        assert backup_dir.is_dir()
        assert backup_dir.parent.name == BACKUP_DIR

    def test_timestamp_format_is_valid(self, temp_project):
        """Test that timestamp format is YYYYMMDD_HHMMSS."""
        backup_dir = create_backup_directory(temp_project)

        timestamp = backup_dir.name
        # Should parse as YYYYMMDD_HHMMSS
        datetime.strptime(timestamp, "%Y%m%d_%H%M%S")

    def test_creates_parent_directory_structure(self, temp_project):
        """Test that parent .solokit-backup directory is created."""
        backup_dir = create_backup_directory(temp_project)

        parent = backup_dir.parent
        assert parent.exists()
        assert parent.name == BACKUP_DIR
        assert parent.parent == temp_project

    def test_multiple_calls_create_unique_directories(self, temp_project):
        """Test that multiple calls create different timestamped directories."""
        backup_dir1 = create_backup_directory(temp_project)

        # Sleep to ensure different timestamp
        import time

        time.sleep(1)
        backup_dir2 = create_backup_directory(temp_project)

        assert backup_dir1 != backup_dir2
        assert backup_dir1.exists()
        assert backup_dir2.exists()

    def test_existing_backup_dir_structure_is_preserved(self, temp_project):
        """Test that existing backup directory structure is not destroyed."""
        # Create first backup with a file
        backup_dir1 = create_backup_directory(temp_project)
        (backup_dir1 / "test.txt").write_text("content")

        # Create second backup
        backup_dir2 = create_backup_directory(temp_project)

        # First backup should still exist with its file
        assert backup_dir1.exists()
        assert (backup_dir1 / "test.txt").exists()
        assert backup_dir2.exists()

    def test_creates_directory_with_exist_ok(self, temp_project):
        """Test that existing directory doesn't cause errors."""
        backup_dir = create_backup_directory(temp_project)

        # Manually create the same directory path (shouldn't happen in practice)
        # This tests the exist_ok=True parameter
        backup_dir.mkdir(parents=True, exist_ok=True)

        assert backup_dir.exists()


class TestBackupFile:
    """Tests for backup_file() function."""

    def test_backs_up_existing_file(self, temp_project):
        """Test successful backup of existing file."""
        source = temp_project / "config.json"
        source.write_text('{"key": "value"}')

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == '{"key": "value"}'
        assert backup_path.name == "config.json"

    def test_returns_none_for_missing_file(self, temp_project):
        """Test that missing files return None."""
        source = temp_project / "nonexistent.txt"
        backup_dir = create_backup_directory(temp_project)

        backup_path = backup_file(source, backup_dir)

        assert backup_path is None

    def test_preserves_file_metadata(self, temp_project):
        """Test that file metadata (timestamps) are preserved."""
        source = temp_project / "file.txt"
        source.write_text("content")

        # Get original modification time
        original_mtime = source.stat().st_mtime

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        # Backup should preserve modification time (shutil.copy2)
        assert backup_path is not None
        backup_mtime = backup_path.stat().st_mtime
        assert abs(backup_mtime - original_mtime) < 1  # Within 1 second

    def test_uses_filename_only_not_full_path(self, temp_project):
        """Test that backup uses only filename, not full path."""
        subdir = temp_project / "subdir"
        subdir.mkdir()
        source = subdir / "config.json"
        source.write_text("{}")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        assert backup_path is not None
        assert backup_path.parent == backup_dir
        assert backup_path.name == "config.json"

    def test_handles_name_conflicts_with_parent_prefix(self, temp_project):
        """Test that conflicting filenames get parent directory prefix."""
        # Create two files with same name in different directories
        dir1 = temp_project / "dir1"
        dir2 = temp_project / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "config.json"
        file2 = dir2 / "config.json"
        file1.write_text('{"source": "dir1"}')
        file2.write_text('{"source": "dir2"}')

        backup_dir = create_backup_directory(temp_project)

        # Backup first file
        backup1 = backup_file(file1, backup_dir)
        assert backup1 is not None
        assert backup1.name == "config.json"

        # Backup second file - should get parent prefix
        backup2 = backup_file(file2, backup_dir)
        assert backup2 is not None
        assert backup2.name == "dir2_config.json"

    def test_handles_oserror_gracefully(self, temp_project):
        """Test that OSError during backup is handled gracefully."""
        source = temp_project / "file.txt"
        source.write_text("content")

        backup_dir = create_backup_directory(temp_project)

        with patch("shutil.copy2", side_effect=OSError("Permission denied")):
            backup_path = backup_file(source, backup_dir)

            assert backup_path is None

    def test_backs_up_binary_file(self, temp_project):
        """Test backing up binary file."""
        source = temp_project / "image.png"
        binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        source.write_bytes(binary_data)

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        assert backup_path is not None
        assert backup_path.read_bytes() == binary_data

    def test_backs_up_empty_file(self, temp_project):
        """Test backing up empty file."""
        source = temp_project / "empty.txt"
        source.write_text("")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        assert backup_path is not None
        assert backup_path.read_text() == ""

    def test_nested_file_path(self, temp_project):
        """Test backing up file from deeply nested path."""
        nested = temp_project / "a" / "b" / "c"
        nested.mkdir(parents=True)
        source = nested / "deep.txt"
        source.write_text("deep content")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file(source, backup_dir)

        assert backup_path is not None
        assert backup_path.name == "deep.txt"
        assert backup_path.parent == backup_dir


class TestBackupFileWithStructure:
    """Tests for backup_file_with_structure() function."""

    def test_preserves_directory_structure(self, temp_project):
        """Test that relative directory structure is preserved."""
        subdir = temp_project / "src" / "config"
        subdir.mkdir(parents=True)
        source = subdir / "app.json"
        source.write_text('{"app": "config"}')

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        assert backup_path is not None
        assert backup_path == backup_dir / "src" / "config" / "app.json"
        assert backup_path.exists()
        assert backup_path.read_text() == '{"app": "config"}'

    def test_returns_none_for_missing_file(self, temp_project):
        """Test that missing files return None."""
        source = temp_project / "nonexistent.txt"
        backup_dir = create_backup_directory(temp_project)

        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        assert backup_path is None

    def test_creates_intermediate_directories(self, temp_project):
        """Test that intermediate directories are created."""
        nested = temp_project / "a" / "b" / "c" / "d"
        nested.mkdir(parents=True)
        source = nested / "file.txt"
        source.write_text("content")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        assert backup_path is not None
        assert backup_path.parent.exists()
        assert backup_path == backup_dir / "a" / "b" / "c" / "d" / "file.txt"

    def test_handles_file_outside_project_root(self, temp_project, tmp_path):
        """Test handling file outside project root uses filename only."""
        outside = tmp_path / "outside"
        outside.mkdir()
        source = outside / "external.txt"
        source.write_text("external content")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        # Should fall back to just the filename
        assert backup_path is not None
        assert backup_path == backup_dir / "external.txt"
        assert backup_path.read_text() == "external content"

    def test_preserves_file_metadata(self, temp_project):
        """Test that file metadata is preserved."""
        source = temp_project / "file.txt"
        source.write_text("content")
        original_mtime = source.stat().st_mtime

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        assert backup_path is not None
        backup_mtime = backup_path.stat().st_mtime
        assert abs(backup_mtime - original_mtime) < 1

    def test_handles_oserror_gracefully(self, temp_project):
        """Test that OSError during backup is handled gracefully."""
        source = temp_project / "file.txt"
        source.write_text("content")

        backup_dir = create_backup_directory(temp_project)

        with patch("shutil.copy2", side_effect=OSError("Permission denied")):
            backup_path = backup_file_with_structure(source, backup_dir, temp_project)

            assert backup_path is None

    def test_backs_up_root_level_file(self, temp_project):
        """Test backing up file at project root level."""
        source = temp_project / "README.md"
        source.write_text("# Project")

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(source, backup_dir, temp_project)

        assert backup_path is not None
        assert backup_path == backup_dir / "README.md"

    def test_handles_symlinks(self, temp_project):
        """Test handling symbolic links."""
        target = temp_project / "target.txt"
        target.write_text("target content")

        link = temp_project / "link.txt"
        try:
            link.symlink_to(target)
        except OSError as e:
            if getattr(e, "winerror", 0) == 1314:
                pytest.skip("Symlink creation requires Administrator privileges on Windows")
            raise

        backup_dir = create_backup_directory(temp_project)
        backup_path = backup_file_with_structure(link, backup_dir, temp_project)

        # Should backup the linked file content
        assert backup_path is not None
        assert backup_path.read_text() == "target content"


class TestGetBackupGitignoreEntry:
    """Tests for get_backup_gitignore_entry() function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        entry = get_backup_gitignore_entry()
        assert isinstance(entry, str)

    def test_includes_backup_directory_pattern(self):
        """Test that entry includes backup directory pattern."""
        entry = get_backup_gitignore_entry()
        assert BACKUP_DIR in entry

    def test_includes_comment(self):
        """Test that entry includes explanatory comment."""
        entry = get_backup_gitignore_entry()
        assert "#" in entry
        assert "Solokit" in entry

    def test_includes_trailing_slash(self):
        """Test that directory pattern includes trailing slash."""
        entry = get_backup_gitignore_entry()
        assert f"{BACKUP_DIR}/" in entry

    def test_includes_newlines(self):
        """Test that entry includes newlines for proper formatting."""
        entry = get_backup_gitignore_entry()
        assert entry.startswith("\n")
        assert entry.endswith("\n")


class TestListBackups:
    """Tests for list_backups() function."""

    def test_returns_empty_list_when_no_backups(self, temp_project):
        """Test that empty list is returned when no backups exist."""
        backups = list_backups(temp_project)
        assert backups == []

    def test_lists_single_backup(self, temp_project):
        """Test listing single backup directory."""
        backup_dir = create_backup_directory(temp_project)

        backups = list_backups(temp_project)

        assert len(backups) == 1
        assert backups[0] == backup_dir

    def test_lists_multiple_backups(self, temp_project):
        """Test listing multiple backup directories."""
        backup1 = create_backup_directory(temp_project)

        import time

        time.sleep(1)
        backup2 = create_backup_directory(temp_project)

        backups = list_backups(temp_project)

        assert len(backups) == 2
        assert backup1 in backups
        assert backup2 in backups

    def test_returns_backups_in_chronological_order(self, temp_project):
        """Test that backups are returned oldest first."""
        # Create backups with specific timestamps
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        old_backup = backup_root / "20240101_120000"
        mid_backup = backup_root / "20240615_143000"
        new_backup = backup_root / "20241231_235959"

        old_backup.mkdir()
        mid_backup.mkdir()
        new_backup.mkdir()

        backups = list_backups(temp_project)

        assert len(backups) == 3
        assert backups[0] == old_backup
        assert backups[1] == mid_backup
        assert backups[2] == new_backup

    def test_ignores_files_in_backup_directory(self, temp_project):
        """Test that files in backup directory are ignored."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        backup_dir = backup_root / "20240101_120000"
        backup_dir.mkdir()

        # Create a file (not directory) in backup root
        (backup_root / "notes.txt").write_text("backup notes")

        backups = list_backups(temp_project)

        assert len(backups) == 1
        assert backups[0] == backup_dir

    def test_handles_non_existent_backup_root(self, temp_project):
        """Test graceful handling when backup root doesn't exist."""
        backups = list_backups(temp_project)
        assert backups == []


class TestGetLatestBackup:
    """Tests for get_latest_backup() function."""

    def test_returns_none_when_no_backups(self, temp_project):
        """Test that None is returned when no backups exist."""
        latest = get_latest_backup(temp_project)
        assert latest is None

    def test_returns_only_backup(self, temp_project):
        """Test returning the only backup when one exists."""
        backup_dir = create_backup_directory(temp_project)

        latest = get_latest_backup(temp_project)

        assert latest == backup_dir

    def test_returns_most_recent_backup(self, temp_project):
        """Test that most recent backup is returned."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        old_backup = backup_root / "20240101_120000"
        mid_backup = backup_root / "20240615_143000"
        new_backup = backup_root / "20241231_235959"

        old_backup.mkdir()
        mid_backup.mkdir()
        new_backup.mkdir()

        latest = get_latest_backup(temp_project)

        assert latest == new_backup

    def test_uses_list_backups_internally(self, temp_project):
        """Test that function uses list_backups() for consistency."""
        _backup1 = create_backup_directory(temp_project)  # noqa: F841

        import time

        time.sleep(1)
        backup2 = create_backup_directory(temp_project)

        latest = get_latest_backup(temp_project)

        # Should be the second backup (most recent)
        assert latest == backup2


class TestCleanupOldBackups:
    """Tests for cleanup_old_backups() function."""

    def test_returns_zero_when_no_backups_to_remove(self, temp_project):
        """Test that 0 is returned when no backups need removal."""
        # Create fewer backups than keep limit
        create_backup_directory(temp_project)

        import time

        time.sleep(1)
        create_backup_directory(temp_project)

        removed = cleanup_old_backups(temp_project, keep=5)

        assert removed == 0

    def test_keeps_specified_number_of_recent_backups(self, temp_project):
        """Test that specified number of recent backups are kept."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create 7 backups
        backups = []
        for i in range(7):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()
            backups.append(backup)

        removed = cleanup_old_backups(temp_project, keep=3)

        assert removed == 4  # Removed 4 old backups

        remaining = list_backups(temp_project)
        assert len(remaining) == 3

        # Should keep the 3 most recent
        assert remaining[0] == backups[4]
        assert remaining[1] == backups[5]
        assert remaining[2] == backups[6]

    def test_removes_oldest_backups_first(self, temp_project):
        """Test that oldest backups are removed first."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        old_backup = backup_root / "20240101_120000"
        mid_backup = backup_root / "20240615_143000"
        new_backup = backup_root / "20241231_235959"

        old_backup.mkdir()
        mid_backup.mkdir()
        new_backup.mkdir()

        removed = cleanup_old_backups(temp_project, keep=1)

        assert removed == 2
        assert not old_backup.exists()
        assert not mid_backup.exists()
        assert new_backup.exists()

    def test_default_keep_value_is_5(self, temp_project):
        """Test that default keep value is 5."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create 8 backups
        for i in range(8):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()

        removed = cleanup_old_backups(temp_project)  # Use default keep=5

        assert removed == 3
        remaining = list_backups(temp_project)
        assert len(remaining) == 5

    def test_handles_removal_errors_gracefully(self, temp_project):
        """Test that removal errors are handled gracefully."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create backups
        for i in range(7):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()

        # Mock shutil.rmtree to fail on first removal
        original_rmtree = shutil.rmtree
        call_count = [0]

        def mock_rmtree(path, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("Permission denied")
            original_rmtree(path, *args, **kwargs)

        with patch("shutil.rmtree", side_effect=mock_rmtree):
            removed = cleanup_old_backups(temp_project, keep=3)

            # Should remove 3 out of 4 (one failed)
            assert removed == 3

    def test_returns_zero_when_backups_equal_keep_limit(self, temp_project):
        """Test that nothing is removed when backups equal keep limit."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create exactly 5 backups
        for i in range(5):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()

        removed = cleanup_old_backups(temp_project, keep=5)

        assert removed == 0
        assert len(list_backups(temp_project)) == 5

    def test_returns_zero_when_no_backups_exist(self, temp_project):
        """Test that 0 is returned when no backups exist."""
        removed = cleanup_old_backups(temp_project, keep=5)
        assert removed == 0

    def test_removes_directory_contents(self, temp_project):
        """Test that backup directory contents are removed."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create backups with files
        for i in range(7):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()
            (backup / "config.json").write_text("{}")
            (backup / "data.txt").write_text("data")

        removed = cleanup_old_backups(temp_project, keep=3)

        assert removed == 4

        # Check that removed backups are gone with their contents
        remaining = list_backups(temp_project)
        assert len(remaining) == 3

        # Verify kept backups still have their contents
        for backup in remaining:
            assert (backup / "config.json").exists()
            assert (backup / "data.txt").exists()

    def test_keep_one_removes_all_but_latest(self, temp_project):
        """Test that keep=1 removes all but the most recent backup."""
        backup_root = temp_project / BACKUP_DIR
        backup_root.mkdir()

        # Create backups
        backups_created = []
        for i in range(5):
            backup = backup_root / f"2024{i:02d}01_120000"
            backup.mkdir()
            backups_created.append(backup)

        removed = cleanup_old_backups(temp_project, keep=1)

        assert removed == 4
        remaining = list_backups(temp_project)
        assert len(remaining) == 1
        assert remaining[0] == backups_created[-1]  # Only latest remains
