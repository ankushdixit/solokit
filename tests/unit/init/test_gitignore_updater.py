"""
Tests for gitignore_updater module.

Validates .gitignore updating with stack-specific patterns.

Run tests:
    pytest tests/unit/init/test_gitignore_updater.py -v

Target: 90%+ coverage
"""

from solokit.init.gitignore_updater import (
    get_os_specific_gitignore_entries,
    get_stack_specific_gitignore_entries,
    update_gitignore,
)


class TestGetStackSpecificGitignoreEntries:
    """Tests for get_stack_specific_gitignore_entries()."""

    def test_saas_t3_entries(self):
        """Test entries for SaaS T3 stack."""
        entries = get_stack_specific_gitignore_entries("saas_t3")

        assert "node_modules/" in entries
        assert ".next/" in entries
        assert ".env" in entries

    def test_ml_ai_fastapi_entries(self):
        """Test entries for ML/AI FastAPI stack."""
        entries = get_stack_specific_gitignore_entries("ml_ai_fastapi")

        assert "venv/" in entries
        assert "*.pyc" in entries
        assert "__pycache__/" in entries

    def test_common_entries_in_all(self):
        """Test that common entries appear in all stacks."""
        for template_id in ["saas_t3", "ml_ai_fastapi"]:
            entries = get_stack_specific_gitignore_entries(template_id)

            assert ".session/briefings/" in entries
            assert "coverage/" in entries

    def test_unknown_template(self):
        """Test that unknown template returns common entries only."""
        entries = get_stack_specific_gitignore_entries("unknown")

        assert ".session/briefings/" in entries
        assert len(entries) >= 1


class TestGetOsSpecificGitignoreEntries:
    """Tests for get_os_specific_gitignore_entries()."""

    def test_contains_macos_entries(self):
        """Test that macOS entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert ".DS_Store" in entries_str
        assert "._*" in entries_str

    def test_contains_windows_entries(self):
        """Test that Windows entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert "Thumbs.db" in entries_str
        assert "Desktop.ini" in entries_str

    def test_contains_linux_entries(self):
        """Test that Linux entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert "*~" in entries_str


class TestUpdateGitignore:
    """Tests for update_gitignore()."""

    def test_create_new_gitignore(self, tmp_path):
        """Test creating new .gitignore file."""
        gitignore = update_gitignore("saas_t3", tmp_path)

        assert gitignore.exists()
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".session/briefings/" in content

    def test_append_to_existing_gitignore(self, tmp_path):
        """Test appending to existing .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# Existing content\n*.log\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert "*.log" in content
        assert "node_modules/" in content

    def test_skip_duplicate_entries(self, tmp_path):
        """Test that duplicate entries are not added."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n.next/\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        # Count occurrences - should be 1 each
        assert content.count("node_modules/") == 1
        assert content.count(".next/") == 1

    def test_add_os_specific_entries(self, tmp_path):
        """Test adding OS-specific entries."""
        gitignore = update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert ".DS_Store" in content
        assert "Thumbs.db" in content

    def test_skip_os_entries_if_exist(self, tmp_path):
        """Test skipping OS entries if they already exist."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".DS_Store\nThumbs.db\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert content.count(".DS_Store") == 1
        assert content.count("Thumbs.db") == 1

    def test_update_gitignore_no_project_root_uses_cwd(self, tmp_path, monkeypatch):
        """Test that update_gitignore uses cwd when project_root is None."""
        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        # Call without project_root (should use cwd)
        gitignore = update_gitignore("saas_t3", project_root=None)

        assert gitignore.exists()
        assert gitignore.parent == tmp_path
        content = gitignore.read_text()
        assert "node_modules/" in content

    def test_read_error_raises_file_operation_error(self, tmp_path):
        """Test that read errors raise FileOperationError."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("existing content")

        # Mock read_text to raise an exception
        with patch("pathlib.Path.read_text", side_effect=PermissionError("Access denied")):
            try:
                update_gitignore("saas_t3", tmp_path)
                assert False, "Should have raised FileOperationError"
            except FileOperationError as e:
                assert e.operation == "read"
                assert ".gitignore" in e.file_path
                assert "Failed to read" in e.details

    def test_write_error_raises_file_operation_error(self, tmp_path):
        """Test that write errors raise FileOperationError."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        # Mock open to raise an exception during write
        with patch("builtins.open", side_effect=PermissionError("Write denied")):
            try:
                update_gitignore("saas_t3", tmp_path)
                assert False, "Should have raised FileOperationError"
            except FileOperationError as e:
                assert e.operation == "write"
                assert ".gitignore" in e.file_path
                assert "Failed to update" in e.details

    def test_append_to_file_without_trailing_newline(self, tmp_path):
        """Test appending to file that doesn't end with newline."""
        gitignore = tmp_path / ".gitignore"
        # Write content without trailing newline
        gitignore.write_text("# Existing content\n*.log")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert "*.log" in content
        assert "node_modules/" in content
        # Check that content is properly formatted (no missing newlines between sections)
        lines = content.split("\n")
        assert len([line for line in lines if line.strip()]) > 3

    def test_other_template_ids(self, tmp_path):
        """Test other known template IDs."""
        # Test dashboard_refine
        gitignore = update_gitignore("dashboard_refine", tmp_path)
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".next/" in content

        # Test fullstack_nextjs
        gitignore.unlink()
        gitignore = update_gitignore("fullstack_nextjs", tmp_path)
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".next/" in content
