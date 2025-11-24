"""
Tests for env_generator module.

Validates .env.example and .editorconfig generation.

Run tests:
    pytest tests/unit/init/test_env_generator.py -v

Target: 90%+ coverage
"""

from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.init.env_generator import (
    generate_editorconfig,
    generate_env_example_nextjs,
    generate_env_example_python,
    generate_env_files,
)


class TestGenerateEditorconfig:
    """Tests for generate_editorconfig()."""

    def test_generate_editorconfig(self, tmp_path):
        """Test generating .editorconfig."""
        path = generate_editorconfig(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "indent_style = space" in content
        assert "indent_size = 2" in content

    def test_python_specific_config(self, tmp_path):
        """Test that Python files have indent_size = 4."""
        path = generate_editorconfig(tmp_path)

        content = path.read_text()
        assert "[*.py]" in content
        assert "indent_size = 4" in content.split("[*.py]")[1].split("[")[0]

    def test_generate_editorconfig_uses_cwd_when_no_path(self):
        """Test that it uses current directory when project_root is None."""
        with patch("solokit.init.env_generator.Path.cwd") as mock_cwd:
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                from pathlib import Path

                tmp = Path(tmpdir)
                mock_cwd.return_value = tmp

                path = generate_editorconfig(project_root=None)

                assert path.exists()
                assert path.parent == tmp

    def test_generate_editorconfig_write_fails(self, tmp_path):
        """Test handling when writing .editorconfig fails."""
        # Create a mock Path that will fail on write_text
        from pathlib import Path

        with patch.object(Path, "write_text", side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileOperationError) as exc:
                generate_editorconfig(tmp_path)

            assert exc.value.operation == "write"


class TestGenerateEnvExampleNextjs:
    """Tests for generate_env_example_nextjs()."""

    def test_generate_nextjs_env(self, tmp_path):
        """Test generating .env.example for Next.js."""
        path = generate_env_example_nextjs(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "DATABASE_URL" in content
        assert "NEXTAUTH_SECRET" in content


class TestGenerateEnvExamplePython:
    """Tests for generate_env_example_python()."""

    def test_generate_python_env(self, tmp_path):
        """Test generating .env.example for Python."""
        path = generate_env_example_python(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "DATABASE_URL" in content
        assert "API_HOST" in content
        assert "SECRET_KEY" in content


class TestGenerateEnvFiles:
    """Tests for generate_env_files()."""

    def test_generate_for_nodejs_template(self, tmp_path):
        """Test generating env files for Node.js template."""
        files = generate_env_files("saas_t3", tmp_path)

        assert len(files) == 2
        assert (tmp_path / ".editorconfig").exists()
        assert (tmp_path / ".env.example").exists()

    def test_generate_for_python_template(self, tmp_path):
        """Test generating env files for Python template."""
        files = generate_env_files("ml_ai_fastapi", tmp_path)

        assert len(files) == 2
        assert (tmp_path / ".editorconfig").exists()
        assert (tmp_path / ".env.example").exists()

    def test_generate_env_files_uses_cwd_when_no_path(self):
        """Test that it uses current directory when project_root is None."""
        with patch("solokit.init.env_generator.Path.cwd") as mock_cwd:
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                from pathlib import Path

                tmp = Path(tmpdir)
                mock_cwd.return_value = tmp

                files = generate_env_files("saas_t3", project_root=None)

                assert len(files) == 2
                assert (tmp / ".editorconfig").exists()
                assert (tmp / ".env.example").exists()

    def test_generate_env_files_fails(self, tmp_path):
        """Test handling when generating env files fails."""
        # Mock generate_editorconfig to raise an exception
        with patch("solokit.init.env_generator.generate_editorconfig") as mock_gen:
            mock_gen.side_effect = Exception("Disk full")

            with pytest.raises(FileOperationError) as exc:
                generate_env_files("saas_t3", tmp_path)

            assert exc.value.operation == "create"
