#!/usr/bin/env python3
"""Unit tests for documentation_loader.py module.

Tests cover:
- Loading project documentation files
- Error handling for file read failures
- Error handling for unicode decode errors
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.session.briefing.documentation_loader import DocumentationLoader


class TestDocumentationLoader:
    """Tests for DocumentationLoader class."""

    def test_init_default_project_root(self):
        """Test initialization with default project root."""
        loader = DocumentationLoader()
        assert loader.project_root == Path.cwd()

    def test_init_custom_project_root(self, tmp_path):
        """Test initialization with custom project root."""
        loader = DocumentationLoader(project_root=tmp_path)
        assert loader.project_root == tmp_path

    def test_load_project_docs_success(self, tmp_path):
        """Test successful loading of all documentation files."""
        # Arrange
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        vision_file = docs_dir / "vision.md"
        vision_file.write_text("# Vision\nOur vision is...")

        prd_file = docs_dir / "prd.md"
        prd_file.write_text("# PRD\nProduct requirements...")

        arch_file = docs_dir / "architecture.md"
        arch_file.write_text("# Architecture\nSystem architecture...")

        readme_file = tmp_path / "README.md"
        readme_file.write_text("# README\nProject readme...")

        loader = DocumentationLoader(project_root=tmp_path)

        # Act
        docs = loader.load_project_docs()

        # Assert
        assert len(docs) == 4
        assert "vision.md" in docs
        assert "prd.md" in docs
        assert "architecture.md" in docs
        assert "README.md" in docs
        assert "Our vision is..." in docs["vision.md"]

    def test_load_project_docs_partial_files(self, tmp_path):
        """Test loading when only some documentation files exist."""
        # Arrange
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        vision_file = docs_dir / "vision.md"
        vision_file.write_text("# Vision\nOur vision is...")

        loader = DocumentationLoader(project_root=tmp_path)

        # Act
        docs = loader.load_project_docs()

        # Assert
        assert len(docs) == 1
        assert "vision.md" in docs

    def test_load_project_docs_no_files(self, tmp_path):
        """Test loading when no documentation files exist."""
        # Arrange
        loader = DocumentationLoader(project_root=tmp_path)

        # Act
        docs = loader.load_project_docs()

        # Assert
        assert len(docs) == 0
        assert docs == {}

    def test_load_project_docs_oserror(self, tmp_path):
        """Test error handling when file read fails with OSError."""
        # Arrange
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        vision_file = docs_dir / "vision.md"
        vision_file.write_text("# Vision")

        loader = DocumentationLoader(project_root=tmp_path)

        # Mock Path.read_text to raise OSError
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            # Act & Assert
            with pytest.raises(FileOperationError) as exc_info:
                loader.load_project_docs()

            assert exc_info.value.operation == "read"
            assert "Permission denied" in exc_info.value.details

    def test_load_project_docs_unicode_decode_error(self, tmp_path):
        """Test error handling when file contains invalid unicode."""
        # Arrange
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        vision_file = docs_dir / "vision.md"
        vision_file.write_text("# Vision")

        loader = DocumentationLoader(project_root=tmp_path)

        # Mock Path.read_text to raise UnicodeDecodeError
        unicode_error = UnicodeDecodeError("utf-8", b"\x80\x81", 0, 1, "invalid start byte")
        with patch.object(Path, "read_text", side_effect=unicode_error):
            # Act & Assert
            with pytest.raises(FileOperationError) as exc_info:
                loader.load_project_docs()

            assert exc_info.value.operation == "read"
            assert "invalid start byte" in exc_info.value.details

    def test_load_project_docs_empty_files(self, tmp_path):
        """Test loading empty documentation files."""
        # Arrange
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        vision_file = docs_dir / "vision.md"
        vision_file.write_text("")

        loader = DocumentationLoader(project_root=tmp_path)

        # Act
        docs = loader.load_project_docs()

        # Assert
        assert len(docs) == 1
        assert "vision.md" in docs
        assert docs["vision.md"] == ""
