"""
Tests for template_installer module.

Validates template loading, file copying, and placeholder replacement.

Run tests:
    pytest tests/unit/init/test_template_installer.py -v

Run with coverage:
    pytest tests/unit/init/test_template_installer.py --cov=solokit.init.template_installer --cov-report=term-missing

Target: 90%+ coverage
"""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from solokit.core.exceptions import FileOperationError, TemplateNotFoundError
from solokit.init.template_installer import (
    copy_directory_tree,
    get_template_directory,
    get_template_info,
    install_additional_option,
    install_base_template,
    install_template,
    install_tier_files,
    load_template_registry,
    replace_placeholders,
)


class TestLoadTemplateRegistry:
    """Tests for load_template_registry()."""

    def test_load_registry_success(self, mock_template_registry):
        """Test successful registry loading."""
        registry_json = json.dumps(mock_template_registry)

        with patch("solokit.init.template_installer.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file

            with patch("builtins.open", mock_open(read_data=registry_json)):
                result = load_template_registry()

                assert result["version"] == "1.0.0"
                assert "saas_t3" in result["templates"]

    def test_registry_not_found(self):
        """Test error when registry file doesn't exist."""
        import solokit.init.template_installer as installer_module

        # Mock __file__ to point to a location where template-registry.json doesn't exist
        with patch.object(installer_module, "__file__", "/fake/solokit/init/template_installer.py"):
            with pytest.raises(TemplateNotFoundError) as exc:
                load_template_registry()

            assert exc.value.template_name == "template-registry.json"

    def test_registry_invalid_json(self):
        """Test error when registry has invalid JSON."""
        with patch("solokit.init.template_installer.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = mock_file

            with patch("builtins.open", mock_open(read_data="invalid json{")):
                with pytest.raises(FileOperationError) as exc:
                    load_template_registry()

                assert exc.value.operation == "parse"
                assert "Invalid JSON" in exc.value.details


class TestGetTemplateInfo:
    """Tests for get_template_info()."""

    def test_get_valid_template(self, mock_template_registry):
        """Test getting info for valid template."""
        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            info = get_template_info("saas_t3")

            assert info["id"] == "saas_t3"
            assert info["display_name"] == "SaaS T3"

    def test_get_invalid_template(self, mock_template_registry):
        """Test error for invalid template ID."""
        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            with pytest.raises(TemplateNotFoundError) as exc:
                get_template_info("invalid_template")

            assert exc.value.template_name == "invalid_template"
            assert "Available templates" in exc.value.template_path


class TestGetTemplateDirectory:
    """Tests for get_template_directory()."""

    def test_template_directory_exists(self, tmp_path):
        """Test getting existing template directory."""
        # Create mock template directory
        templates_root = tmp_path / "templates"
        templates_root.mkdir()
        saas_dir = templates_root / "saas_t3"
        saas_dir.mkdir()

        with patch("solokit.init.template_installer.Path") as mock_path:
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                templates_root
            )
            mock_path.return_value = saas_dir.parent.parent / "init" / "template_installer.py"

            # Override exists check
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "__truediv__", return_value=saas_dir):
                    get_template_directory("saas_t3")
                    # Just verify it doesn't raise

    def test_template_directory_not_found(self):
        """Test error when template directory doesn't exist."""
        import solokit.init.template_installer as installer_module

        # Mock __file__ to point to a location where the template doesn't exist
        with patch.object(installer_module, "__file__", "/fake/solokit/init/template_installer.py"):
            with pytest.raises(TemplateNotFoundError):
                get_template_directory("nonexistent")


class TestCopyDirectoryTree:
    """Tests for copy_directory_tree()."""

    def test_copy_simple_files(self, tmp_path):
        """Test copying simple file structure."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "file1.txt").write_text("content1")
        (src / "file2.txt").write_text("content2")

        dst = tmp_path / "dst"

        count = copy_directory_tree(src, dst)

        assert count == 2
        assert (dst / "file1.txt").read_text() == "content1"
        assert (dst / "file2.txt").read_text() == "content2"

    def test_copy_nested_directories(self, tmp_path):
        """Test copying nested directory structure."""
        src = tmp_path / "src"
        src.mkdir()
        subdir = src / "subdir"
        subdir.mkdir()
        (src / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")

        dst = tmp_path / "dst"

        count = copy_directory_tree(src, dst)

        assert count == 2
        assert (dst / "file1.txt").exists()
        assert (dst / "subdir" / "file2.txt").exists()

    def test_copy_with_skip_patterns(self, tmp_path):
        """Test copying with skip patterns."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("keep")
        (src / "file.template").write_text("skip")
        (src / "__pycache__").mkdir()

        dst = tmp_path / "dst"

        count = copy_directory_tree(src, dst, skip_patterns=[".template", "__pycache__"])

        assert count == 1
        assert (dst / "file.txt").exists()
        assert not (dst / "file.template").exists()
        assert not (dst / "__pycache__").exists()

    def test_copy_creates_destination(self, tmp_path):
        """Test that destination directory is created if it doesn't exist."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("content")

        dst = tmp_path / "deep" / "nested" / "dst"

        copy_directory_tree(src, dst)

        assert dst.exists()
        assert (dst / "file.txt").exists()

    def test_copy_error_handling(self, tmp_path):
        """Test error handling during copy."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.txt").write_text("content")

        dst = tmp_path / "dst"

        with patch("shutil.copy2", side_effect=PermissionError("Access denied")):
            with pytest.raises(FileOperationError) as exc:
                copy_directory_tree(src, dst)

            assert exc.value.operation == "copy"


class TestReplacePlaceholders:
    """Tests for replace_placeholders()."""

    def test_replace_single_placeholder(self):
        """Test replacing single placeholder."""
        content = "Project: {project_name}"
        replacements = {"project_name": "my-app"}

        result = replace_placeholders(content, replacements)

        assert result == "Project: my-app"

    def test_replace_multiple_placeholders(self):
        """Test replacing multiple placeholders."""
        content = "# {project_name}\n\n{project_description}"
        replacements = {"project_name": "my-app", "project_description": "A cool app"}

        result = replace_placeholders(content, replacements)

        assert result == "# my-app\n\nA cool app"

    def test_replace_no_placeholders(self):
        """Test content with no placeholders."""
        content = "No placeholders here"
        replacements = {"project_name": "my-app"}

        result = replace_placeholders(content, replacements)

        assert result == "No placeholders here"

    def test_replace_unused_replacements(self):
        """Test with replacements that aren't in content."""
        content = "{project_name}"
        replacements = {"project_name": "my-app", "unused": "value"}

        result = replace_placeholders(content, replacements)

        assert result == "my-app"


class TestInstallBaseTemplate:
    """Tests for install_base_template()."""

    def test_install_base_files(self, tmp_path, template_base_dir):
        """Test installing base template files."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory",
            return_value=template_base_dir.parent,
        ):
            count = install_base_template(
                "saas_t3", project_root, {"project_name": "my-app", "project_description": "Test"}
            )

            assert count >= 1
            assert (project_root / "README.md").exists()

    def test_base_template_not_found(self, tmp_path):
        """Test error when base template directory doesn't exist."""
        with patch("solokit.init.template_installer.get_template_directory", return_value=tmp_path):
            with pytest.raises(TemplateNotFoundError):
                install_base_template("saas_t3", tmp_path, {})

    def test_process_template_files(self, tmp_path):
        """Test processing .template files."""
        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        (base / "config.json.template").write_text('{"name": "{project_name}"}')

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            install_base_template("saas_t3", project_root, {"project_name": "my-app"})

            assert (project_root / "config.json").exists()
            content = (project_root / "config.json").read_text()
            assert '"name": "my-app"' in content

    def test_template_file_processing_error(self, tmp_path):
        """Test error handling when processing template file fails."""
        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        (base / "config.json.template").write_text('{"name": "{project_name}"}')

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            # Mock write_text to raise an exception
            with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
                with pytest.raises(FileOperationError) as exc:
                    install_base_template("saas_t3", project_root, {"project_name": "my-app"})

                assert exc.value.operation == "process"


class TestInstallTierFiles:
    """Tests for install_tier_files()."""

    def test_install_tier_files(self, tmp_path, template_tier_dir):
        """Test installing tier-specific files."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory",
            return_value=template_tier_dir.parent,
        ):
            count = install_tier_files(
                "saas_t3", "tier-1-essential", project_root, {"project_name": "my-app"}
            )

            assert count >= 1

    def test_tier_directory_not_found(self, tmp_path):
        """Test when tier directory doesn't exist (should not raise)."""
        with patch("solokit.init.template_installer.get_template_directory", return_value=tmp_path):
            count = install_tier_files("saas_t3", "tier-99", tmp_path, {})

            assert count == 0

    def test_tier_template_file_processing_error(self, tmp_path):
        """Test error handling when processing tier template file fails."""
        template_dir = tmp_path / "templates" / "saas_t3"
        tier_dir = template_dir / "tier-1-essential"
        tier_dir.mkdir(parents=True)
        (tier_dir / "config.json.template").write_text('{"tier": "{project_name}"}')

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            # Mock write_text to raise an exception
            with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
                with pytest.raises(FileOperationError) as exc:
                    install_tier_files(
                        "saas_t3", "tier-1-essential", project_root, {"project_name": "my-app"}
                    )

                assert exc.value.operation == "process"


class TestInstallAdditionalOption:
    """Tests for install_additional_option()."""

    def test_install_option_files(self, tmp_path):
        """Test installing additional option files."""
        template_dir = tmp_path / "templates" / "saas_t3"
        option_dir = template_dir / "ci-cd"
        option_dir.mkdir(parents=True)
        (option_dir / "github-actions.yml").write_text("workflow")

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            count = install_additional_option("saas_t3", "ci-cd", project_root, {})

            assert count >= 1

    def test_option_not_found(self, tmp_path):
        """Test when option directory doesn't exist (should not raise)."""
        with patch("solokit.init.template_installer.get_template_directory", return_value=tmp_path):
            count = install_additional_option("saas_t3", "nonexistent", tmp_path, {})

            assert count == 0

    def test_option_with_template_files(self, tmp_path):
        """Test installing option with .template files that need processing."""
        template_dir = tmp_path / "templates" / "saas_t3"
        option_dir = template_dir / "ci-cd"
        option_dir.mkdir(parents=True)
        (option_dir / "workflow.yml.template").write_text("name: {project_name}")

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            count = install_additional_option(
                "saas_t3", "ci-cd", project_root, {"project_name": "my-app"}
            )

            assert count >= 1
            assert (project_root / "workflow.yml").exists()
            content = (project_root / "workflow.yml").read_text()
            assert "my-app" in content

    def test_option_template_file_processing_error(self, tmp_path):
        """Test error handling when processing option template file fails."""
        template_dir = tmp_path / "templates" / "saas_t3"
        option_dir = template_dir / "ci-cd"
        option_dir.mkdir(parents=True)
        (option_dir / "workflow.yml.template").write_text("name: {project_name}")

        project_root = tmp_path / "project"
        project_root.mkdir()

        with patch(
            "solokit.init.template_installer.get_template_directory", return_value=template_dir
        ):
            # Mock write_text to raise an exception
            with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
                with pytest.raises(FileOperationError) as exc:
                    install_additional_option(
                        "saas_t3", "ci-cd", project_root, {"project_name": "my-app"}
                    )

                assert exc.value.operation == "process"


class TestInstallTemplate:
    """Tests for install_template()."""

    def test_install_complete_template(self, tmp_path, mock_template_registry):
        """Test complete template installation."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create mock template structure
        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        (base / "README.md").write_text("# {project_name}")

        tier1 = template_dir / "tier-1-essential"
        tier1.mkdir()
        (tier1 / "test.ts").write_text("test")

        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            with patch(
                "solokit.init.template_installer.get_template_directory", return_value=template_dir
            ):
                result = install_template("saas_t3", "tier-1-essential", [], project_root)

                assert result["template_id"] == "saas_t3"
                assert result["tier"] == "tier-1-essential"
                assert result["files_installed"] >= 1

    def test_cumulative_tier_installation(self, tmp_path, mock_template_registry):
        """Test that tiers are cumulative (installs all up to selected)."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        (base / "README.md").write_text("base")

        tier1 = template_dir / "tier-1-essential"
        tier1.mkdir()
        (tier1 / "tier1.txt").write_text("tier1")

        tier2 = template_dir / "tier-2-standard"
        tier2.mkdir()
        (tier2 / "tier2.txt").write_text("tier2")

        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            with patch(
                "solokit.init.template_installer.get_template_directory", return_value=template_dir
            ):
                install_template("saas_t3", "tier-2-standard", [], project_root)

                # Should have files from base, tier-1, and tier-2
                assert (project_root / "README.md").exists()
                assert (project_root / "tier1.txt").exists()
                assert (project_root / "tier2.txt").exists()

    def test_install_with_additional_options(self, tmp_path, mock_template_registry):
        """Test installation with additional options."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        (base / "README.md").write_text("base")

        ci_cd = template_dir / "ci-cd"
        ci_cd.mkdir()
        (ci_cd / "workflow.yml").write_text("ci")

        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            with patch(
                "solokit.init.template_installer.get_template_directory", return_value=template_dir
            ):
                result = install_template("saas_t3", "tier-1-essential", ["ci_cd"], project_root)

                assert "ci_cd" in result["additional_options"]
                assert (project_root / "workflow.yml").exists()

    def test_placeholder_replacement_in_template(self, tmp_path, mock_template_registry):
        """Test that placeholders are replaced correctly."""
        project_root = tmp_path / "my-awesome-app"
        project_root.mkdir()

        template_dir = tmp_path / "templates" / "saas_t3"
        base = template_dir / "base"
        base.mkdir(parents=True)
        # Create a .template file so it gets processed with placeholder replacement
        (base / "README.md.template").write_text("# {project_name}")

        with patch(
            "solokit.init.template_installer.load_template_registry",
            return_value=mock_template_registry,
        ):
            with patch(
                "solokit.init.template_installer.get_template_directory", return_value=template_dir
            ):
                install_template("saas_t3", "tier-1-essential", [], project_root)

                readme = (project_root / "README.md").read_text()
                assert "my-awesome-app" in readme

    def test_install_template_uses_cwd_when_no_path(self, mock_template_registry):
        """Test that it uses current directory when project_root is None."""
        with patch("solokit.init.template_installer.Path.cwd") as mock_cwd:
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                from pathlib import Path

                tmp = Path(tmpdir)
                mock_cwd.return_value = tmp

                template_dir = tmp / "templates" / "saas_t3"
                base = template_dir / "base"
                base.mkdir(parents=True)
                (base / "README.md").write_text("base")

                with patch(
                    "solokit.init.template_installer.load_template_registry",
                    return_value=mock_template_registry,
                ):
                    with patch(
                        "solokit.init.template_installer.get_template_directory",
                        return_value=template_dir,
                    ):
                        result = install_template(
                            "saas_t3", "tier-1-essential", [], project_root=None
                        )

                        assert result["project_root"] == str(tmp)
                        assert (tmp / "README.md").exists()
