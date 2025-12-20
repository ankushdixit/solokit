"""Unit tests for generate_tree module.

This module tests the tree generation functionality which creates
a visual representation of the project directory structure.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.project.tree import TreeGenerator


@pytest.fixture(autouse=True)
def mock_shutil_which():
    """Mock shutil.which to return None by default to prevent path resolution."""
    with patch("shutil.which", return_value=None):
        yield

@pytest.fixture
def temp_project(tmp_path):
    """Provide a temporary project directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    return project_root


@pytest.fixture
def tree_generator(temp_project):
    """Provide a TreeGenerator instance with temp directory."""
    return TreeGenerator(project_root=temp_project)


class TestTreeGeneratorInit:
    """Tests for TreeGenerator initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default path uses cwd."""
        # Act
        generator = TreeGenerator()

        # Assert
        assert generator.project_root == Path.cwd()
        assert generator.tree_file.name == "tree.txt"
        assert generator.updates_file.name == "tree_updates.json"

    def test_init_with_custom_path(self, temp_project):
        """Test initialization with custom path."""
        # Act
        generator = TreeGenerator(project_root=temp_project)

        # Assert
        assert generator.project_root == temp_project
        assert str(temp_project) in str(generator.tree_file)

    def test_init_has_ignore_patterns(self, tree_generator):
        """Test initialization includes ignore patterns."""
        # Assert
        assert len(tree_generator.ignore_patterns) > 0
        assert ".git" in tree_generator.ignore_patterns
        assert "__pycache__" in tree_generator.ignore_patterns
        assert "node_modules" in tree_generator.ignore_patterns
        assert ".session" in tree_generator.ignore_patterns


class TestGenerateTree:
    """Tests for tree generation with tree command."""

    def test_generate_tree_success(self, tree_generator):
        """Test successful tree generation with tree command."""
        # Arrange
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "project/\n├── file1.py\n└── file2.py"

        # Act
        with patch("sys.platform", "linux"):
            with patch("subprocess.run", return_value=mock_result):
                tree = tree_generator.generate_tree()

        # Assert
        assert "project/" in tree
        assert "file1.py" in tree
        assert "file2.py" in tree

    def test_generate_tree_failure_uses_fallback(self, tree_generator):
        """Test tree generation uses fallback when command fails."""
        # Arrange
        mock_result = Mock()
        mock_result.returncode = 1

        # Act
        with patch("subprocess.run", return_value=mock_result):
            with patch.object(tree_generator, "_generate_tree_fallback", return_value="fallback"):
                tree = tree_generator.generate_tree()

        # Assert
        assert tree == "fallback"

    def test_generate_tree_timeout_uses_fallback(self, tree_generator):
        """Test tree generation uses fallback on timeout."""
        # Act
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tree", 30)):
            with patch.object(tree_generator, "_generate_tree_fallback", return_value="fallback"):
                tree = tree_generator.generate_tree()

        # Assert
        assert tree == "fallback"

    def test_generate_tree_not_found_uses_fallback(self, tree_generator):
        """Test tree generation uses fallback when tree command not found."""
        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with patch.object(tree_generator, "_generate_tree_fallback", return_value="fallback"):
                tree = tree_generator.generate_tree()

        # Assert
        assert tree == "fallback"

    def test_generate_tree_oserror_uses_fallback(self, tree_generator):
        """Test tree generation uses fallback when OSError occurs."""
        # Act
        with patch("subprocess.run", side_effect=OSError("Command failed")):
            with patch.object(tree_generator, "_generate_tree_fallback", return_value="fallback"):
                tree = tree_generator.generate_tree()

        # Assert
        assert tree == "fallback"

    def test_generate_tree_builds_ignore_args(self, tree_generator):
        """Test tree generation builds correct ignore arguments."""
        # Arrange
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "tree output"

        # Act
        with patch("sys.platform", "linux"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                tree_generator.generate_tree()

        # Assert
        call_args = mock_run.call_args[0][0]
        assert "tree" in call_args
        assert "-a" in call_args
        assert "--dirsfirst" in call_args
        assert "-I" in call_args


class TestGenerateTreeFallback:
    """Tests for fallback tree generation."""

    def test_generate_tree_fallback_basic(self, tree_generator, temp_project):
        """Test fallback tree generation with basic structure."""
        # Arrange
        (temp_project / "file1.py").touch()
        (temp_project / "file2.py").touch()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        assert temp_project.name in tree
        assert "file1.py" in tree
        assert "file2.py" in tree

    def test_generate_tree_fallback_directories_first(self, tree_generator, temp_project):
        """Test fallback tree shows directories before files."""
        # Arrange
        (temp_project / "afile.py").touch()
        (temp_project / "zdir").mkdir()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        lines = tree.split("\n")
        # Find indices
        zdir_idx = next(i for i, line in enumerate(lines) if "zdir" in line)
        afile_idx = next(i for i, line in enumerate(lines) if "afile.py" in line)
        # Directory should come before file
        assert zdir_idx < afile_idx

    def test_generate_tree_fallback_ignores_patterns(self, tree_generator, temp_project):
        """Test fallback tree ignores specified patterns."""
        # Arrange
        (temp_project / "file.py").touch()
        (temp_project / "file.pyc").touch()
        (temp_project / "__pycache__").mkdir()
        (temp_project / ".git").mkdir()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        assert "file.py" in tree
        assert ".pyc" not in tree
        assert "__pycache__" not in tree
        assert ".git" not in tree

    def test_generate_tree_fallback_nested_structure(self, tree_generator, temp_project):
        """Test fallback tree handles nested directories."""
        # Arrange
        subdir = temp_project / "src" / "utils"
        subdir.mkdir(parents=True)
        (subdir / "helper.py").touch()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        assert "src" in tree
        assert "utils" in tree
        assert "helper.py" in tree

    def test_generate_tree_fallback_formatting(self, tree_generator, temp_project):
        """Test fallback tree uses correct formatting characters."""
        # Arrange
        (temp_project / "file1.py").touch()
        (temp_project / "file2.py").touch()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        # Should use tree formatting characters
        assert "├──" in tree or "└──" in tree

    def test_generate_tree_fallback_empty_directory(self, tree_generator, temp_project):
        """Test fallback tree handles empty directory."""
        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        assert temp_project.name in tree
        # Should have just the root directory
        lines = [line for line in tree.split("\n") if line.strip()]
        assert len(lines) == 1

    def test_generate_tree_fallback_oserror(self, tree_generator):
        """Test fallback tree raises FileOperationError on OSError."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        # Act & Assert
        with patch.object(Path, "iterdir", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                tree_generator._generate_tree_fallback()
            assert "Failed to generate project tree" in str(exc_info.value)

    def test_generate_tree_fallback_ignores_nested_patterns(self, tree_generator, temp_project):
        """Test fallback tree ignores patterns in nested paths."""
        # Arrange
        src_dir = temp_project / "src"
        src_dir.mkdir()
        cache_dir = src_dir / "__pycache__"
        cache_dir.mkdir()
        (src_dir / "file.py").touch()

        # Act
        tree = tree_generator._generate_tree_fallback()

        # Assert
        assert "src" in tree
        assert "file.py" in tree
        assert "__pycache__" not in tree


class TestDetectChanges:
    """Tests for change detection."""

    def test_detect_changes_file_added(self, tree_generator):
        """Test detecting file additions."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n├── file1.py\n└── file2.py"

        # Act
        changes = tree_generator.detect_changes(old_tree, new_tree)

        # Assert
        file_adds = [c for c in changes if c["type"] == "file_added"]
        assert len(file_adds) == 1
        assert "file2.py" in file_adds[0]["path"]

    def test_detect_changes_file_removed(self, tree_generator):
        """Test detecting file removals."""
        # Arrange
        old_tree = "project/\n├── file1.py\n└── file2.py"
        new_tree = "project/\n├── file1.py"

        # Act
        changes = tree_generator.detect_changes(old_tree, new_tree)

        # Assert
        file_removes = [c for c in changes if c["type"] == "file_removed"]
        assert len(file_removes) == 1
        assert "file2.py" in file_removes[0]["path"]

    def test_detect_changes_directory_added(self, tree_generator):
        """Test detecting directory additions."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n├── src/\n└── file1.py"

        # Act
        changes = tree_generator.detect_changes(old_tree, new_tree)

        # Assert
        dir_adds = [c for c in changes if c["type"] == "directory_added"]
        assert len(dir_adds) == 1
        assert "src" in dir_adds[0]["path"]

    def test_detect_changes_directory_removed(self, tree_generator):
        """Test detecting directory removals."""
        # Arrange
        old_tree = "project/\n├── src/\n└── file1.py"
        new_tree = "project/\n├── file1.py"

        # Act
        changes = tree_generator.detect_changes(old_tree, new_tree)

        # Assert
        dir_removes = [c for c in changes if c["type"] == "directory_removed"]
        assert len(dir_removes) == 1
        assert "src" in dir_removes[0]["path"]

    def test_detect_changes_mixed(self, tree_generator):
        """Test detecting mixed changes."""
        # Arrange
        old_tree = "project/\n├── old_dir/\n└── old_file.py"
        new_tree = "project/\n├── new_dir/\n└── new_file.py"

        # Act
        changes = tree_generator.detect_changes(old_tree, new_tree)

        # Assert
        assert len(changes) >= 4  # 2 additions, 2 removals
        types = [c["type"] for c in changes]
        assert "directory_added" in types
        assert "directory_removed" in types
        assert "file_added" in types
        assert "file_removed" in types

    def test_detect_changes_none(self, tree_generator):
        """Test no changes when trees are identical."""
        # Arrange
        tree = "project/\n├── file1.py"

        # Act
        changes = tree_generator.detect_changes(tree, tree)

        # Assert
        assert len(changes) == 0


class TestUpdateTree:
    """Tests for tree update functionality."""

    def test_update_tree_no_changes(self, tree_generator, temp_project):
        """Test updating tree when no changes detected."""
        # Arrange
        tree_content = "project/\n├── file1.py"
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(tree_content)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=tree_content):
            changes = tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert
        assert len(changes) == 0

    def test_update_tree_with_significant_changes_non_interactive(
        self, tree_generator, temp_project, capsys
    ):
        """Test updating tree with significant changes in non-interactive mode."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n├── src/\n└── file1.py"
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(old_tree)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            with patch.object(tree_generator, "_record_tree_update"):
                changes = tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert
        assert len(changes) > 0
        captured = capsys.readouterr()
        assert "Structural Changes Detected" in captured.out
        assert "Non-interactive mode" in captured.out

    def test_update_tree_with_significant_changes_interactive(self, tree_generator, temp_project):
        """Test updating tree with significant changes in interactive mode."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n├── src/\n└── file1.py"
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(old_tree)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            with patch("builtins.input", return_value="Added src directory"):
                with patch.object(tree_generator, "_record_tree_update") as mock_record:
                    changes = tree_generator.update_tree(session_num=1, non_interactive=False)

        # Assert
        assert len(changes) > 0
        mock_record.assert_called_once()

    def test_update_tree_first_time(self, tree_generator, temp_project):
        """Test updating tree for the first time (no existing file)."""
        # Arrange
        new_tree = "project/\n├── file1.py"

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            _changes = tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert
        assert tree_generator.tree_file.exists()
        assert tree_generator.tree_file.read_text() == new_tree

    def test_update_tree_creates_directory(self, tree_generator, temp_project):
        """Test updating tree creates parent directory if needed."""
        # Arrange
        new_tree = "project/\n├── file1.py"

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert
        assert tree_generator.tree_file.parent.exists()

    def test_update_tree_filters_minor_changes(self, tree_generator, temp_project):
        """Test updating tree filters out minor changes."""
        # Arrange
        old_tree = "project/\n" + "\n".join([f"├── file{i}.py" for i in range(30)])
        # Add many file changes (>20) - should be filtered
        new_tree = "project/\n" + "\n".join([f"├── newfile{i}.py" for i in range(30)])
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(old_tree)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            with patch.object(tree_generator, "_record_tree_update") as mock_record:
                changes = tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert - should have changes but not record them (filtered as minor)
        assert len(changes) > 0
        # Since all are file changes and > 20, they're filtered
        # Only directory changes would be significant
        # So _record_tree_update should not be called
        mock_record.assert_not_called()

    def test_update_tree_no_session_num(self, tree_generator, temp_project):
        """Test updating tree without session number."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n├── src/\n└── file1.py"
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(old_tree)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            with patch.object(tree_generator, "_record_tree_update") as mock_record:
                changes = tree_generator.update_tree(session_num=None, non_interactive=True)

        # Assert
        assert len(changes) > 0
        mock_record.assert_not_called()

    def test_update_tree_shows_limited_changes(self, tree_generator, temp_project, capsys):
        """Test updating tree shows only first 10 significant changes."""
        # Arrange
        old_tree = "project/\n├── file1.py"
        new_tree = "project/\n" + "\n".join([f"├── dir{i}/" for i in range(15)])
        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.write_text(old_tree)

        # Act
        with patch.object(tree_generator, "generate_tree", return_value=new_tree):
            with patch.object(tree_generator, "_record_tree_update"):
                tree_generator.update_tree(session_num=1, non_interactive=True)

        # Assert
        captured = capsys.readouterr()
        assert "and 5 more changes" in captured.out or "more changes" in captured.out

    def test_update_tree_read_error(self, tree_generator, temp_project):
        """Test update_tree handles read error for existing tree file."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        tree_generator.tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.tree_file.touch()

        # Act & Assert
        with patch.object(tree_generator, "generate_tree", return_value="new tree"):
            with patch.object(Path, "read_text", side_effect=OSError("Read failed")):
                with pytest.raises(FileOperationError) as exc_info:
                    tree_generator.update_tree(session_num=1, non_interactive=True)
                assert "Failed to read existing tree file" in str(exc_info.value)

    def test_update_tree_write_error(self, tree_generator, temp_project):
        """Test update_tree handles write error when saving tree."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        # Act & Assert
        with patch.object(tree_generator, "generate_tree", return_value="new tree"):
            with patch.object(Path, "write_text", side_effect=OSError("Write failed")):
                with pytest.raises(FileOperationError) as exc_info:
                    tree_generator.update_tree(session_num=1, non_interactive=True)
                assert "Failed to write tree file" in str(exc_info.value)


class TestRecordTreeUpdate:
    """Tests for recording tree updates."""

    def test_record_tree_update_new_file(self, tree_generator, temp_project):
        """Test recording tree update to new file."""
        # Arrange
        tree_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        session_num = 1
        changes = [{"type": "directory_added", "path": "src/"}]
        reasoning = "Added source directory"

        # Act
        with patch("solokit.project.tree.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            tree_generator._record_tree_update(session_num, changes, reasoning)

        # Assert
        assert tree_generator.updates_file.exists()
        data = json.loads(tree_generator.updates_file.read_text())
        assert "updates" in data
        assert len(data["updates"]) == 1
        assert data["updates"][0]["session"] == 1
        assert data["updates"][0]["reasoning"] == reasoning
        assert "architecture_impact" in data["updates"][0]

    def test_record_tree_update_append_to_existing(self, tree_generator, temp_project):
        """Test appending tree update to existing file."""
        # Arrange
        tree_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        existing_data = {
            "updates": [
                {
                    "timestamp": "2024-01-01T09:00:00",
                    "session": 0,
                    "changes": [],
                    "reasoning": "Initial",
                    "architecture_impact": "",
                }
            ]
        }
        tree_generator.updates_file.write_text(json.dumps(existing_data))
        session_num = 1
        changes = [{"type": "directory_added", "path": "src/"}]
        reasoning = "Added source directory"

        # Act
        with patch("solokit.project.tree.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            tree_generator._record_tree_update(session_num, changes, reasoning)

        # Assert
        data = json.loads(tree_generator.updates_file.read_text())
        assert len(data["updates"]) == 2
        assert data["updates"][1]["session"] == 1

    def test_record_tree_update_invalid_existing(self, tree_generator, temp_project):
        """Test recording update when existing file is invalid JSON."""
        # Arrange
        tree_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        tree_generator.updates_file.write_text("invalid json {")
        session_num = 1
        changes = [{"type": "directory_added", "path": "src/"}]
        reasoning = "Added source directory"

        # Act
        with patch("solokit.project.tree.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            tree_generator._record_tree_update(session_num, changes, reasoning)

        # Assert
        data = json.loads(tree_generator.updates_file.read_text())
        assert len(data["updates"]) == 1

    def test_record_tree_update_write_error(self, tree_generator, temp_project):
        """Test _record_tree_update handles write error."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        tree_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        session_num = 1
        changes = [{"type": "directory_added", "path": "src/"}]
        reasoning = "Added source directory"

        # Act & Assert
        with patch.object(Path, "write_text", side_effect=OSError("Write failed")):
            with pytest.raises(FileOperationError) as exc_info:
                tree_generator._record_tree_update(session_num, changes, reasoning)
            assert "Failed to write tree updates" in str(exc_info.value)


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_with_session(self, temp_project, capsys):
        """Test main function with session number."""
        # Arrange
        test_args = ["--session", "1", "--non-interactive"]

        # Act
        with patch("sys.argv", ["generate_tree.py"] + test_args):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.update_tree.return_value = [
                    {"type": "directory_added", "path": "src/"}
                ]
                mock_instance.tree_file = temp_project / "tree.txt"
                mock_generator_class.return_value = mock_instance

                from solokit.project.tree import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Tree updated with 1 changes" in captured.out
        assert "Saved to:" in captured.out

    def test_main_show_changes(self, temp_project, capsys):
        """Test main function with --show-changes flag."""
        # Arrange
        test_args = ["--show-changes"]
        updates_data = {
            "updates": [
                {
                    "timestamp": "2024-01-01T10:00:00",
                    "session": 1,
                    "changes": [{"type": "directory_added", "path": "src/"}],
                    "reasoning": "Added source directory",
                }
            ]
        }

        # Act
        with patch("sys.argv", ["generate_tree.py"] + test_args):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.updates_file.exists.return_value = True
                mock_instance.updates_file.read_text.return_value = json.dumps(updates_data)
                mock_generator_class.return_value = mock_instance

                from solokit.project.tree import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Recent structural changes:" in captured.out
        assert "Session 1" in captured.out
        assert "Added source directory" in captured.out

    def test_main_show_changes_no_file(self, temp_project, capsys):
        """Test main function with --show-changes when no updates file exists."""
        # Arrange
        test_args = ["--show-changes"]

        # Act
        with patch("sys.argv", ["generate_tree.py"] + test_args):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.updates_file.exists.return_value = False
                mock_generator_class.return_value = mock_instance

                from solokit.project.tree import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "No tree updates recorded yet" in captured.out

    def test_main_no_changes(self, temp_project, capsys):
        """Test main function when no changes detected."""
        # Act
        with patch("sys.argv", ["generate_tree.py"]):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.update_tree.return_value = []
                mock_instance.tree_file = temp_project / "tree.txt"
                mock_generator_class.return_value = mock_instance

                from solokit.project.tree import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Tree generated (no changes)" in captured.out
        assert "Saved to:" in captured.out

    def test_main_show_changes_parse_error(self, temp_project, capsys):
        """Test main function with --show-changes when file has parse error."""
        # Arrange
        test_args = ["--show-changes"]

        # Act & Assert
        with patch("sys.argv", ["generate_tree.py"] + test_args):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.updates_file.exists.return_value = True
                mock_instance.updates_file.read_text.return_value = "invalid json {"
                mock_generator_class.return_value = mock_instance

                from solokit.project.tree import main

                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 5  # FileOperationError exit code
                captured = capsys.readouterr()
                assert "Failed to parse tree updates file" in captured.err

    def test_main_solokit_error(self, temp_project, capsys):
        """Test main function handles SolokitError."""
        # Arrange
        from solokit.core.exceptions import FileOperationError

        # Act
        with patch("sys.argv", ["generate_tree.py"]):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_generator_class.side_effect = FileOperationError(
                    operation="read",
                    file_path="test.txt",
                    details="File not found",
                )

                from solokit.project.tree import main

                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Assert
        assert exc_info.value.code == 5  # FileOperationError exit code
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_keyboard_interrupt(self, temp_project, capsys):
        """Test main function handles KeyboardInterrupt."""
        # Act
        with patch("sys.argv", ["generate_tree.py"]):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_generator_class.side_effect = KeyboardInterrupt()

                from solokit.project.tree import main

                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Assert
        assert exc_info.value.code == 130
        captured = capsys.readouterr()
        assert "cancelled by user" in captured.err

    def test_main_unexpected_error(self, temp_project, capsys):
        """Test main function handles unexpected errors."""
        # Act
        with patch("sys.argv", ["generate_tree.py"]):
            with patch("solokit.project.tree.TreeGenerator") as mock_generator_class:
                mock_generator_class.side_effect = RuntimeError("Unexpected error")

                from solokit.project.tree import main

                with pytest.raises(SystemExit) as exc_info:
                    main()

        # Assert
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.err
