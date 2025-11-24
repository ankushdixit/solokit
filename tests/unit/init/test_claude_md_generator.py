"""
Tests for claude_md_generator module.

Validates CLAUDE.md generation with stack-specific guidance and project configuration.

Run tests:
    pytest tests/unit/init/test_claude_md_generator.py -v

Run with coverage:
    pytest tests/unit/init/test_claude_md_generator.py --cov=solokit.init.claude_md_generator --cov-report=term-missing

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.init.claude_md_generator import (
    _format_additional_options,
    _get_solokit_version,
    _get_tier_specific_requirements,
    generate_claude_md,
)


@pytest.fixture
def mock_template_structure(tmp_path):
    """Create mock template structure for testing."""
    # Create module directory (so Path(__file__).parent.parent works)
    module_dir = tmp_path / "init"
    module_dir.mkdir()

    # Create templates directory
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Return a helper function to create template files
    def create_template(template_id, content):
        template_path = templates_dir / template_id / "base"
        template_path.mkdir(parents=True)
        (template_path / "CLAUDE.md.template").write_text(content)
        return module_dir / "claude_md_generator.py"

    return create_template


class TestGenerateClaudeMd:
    """Tests for generate_claude_md()."""

    def test_generate_claude_md_for_saas_t3(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test generating CLAUDE.md for SaaS T3 template."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "saas_t3",
                    "# CLAUDE.md - {project_name}\n"
                    "Stack: {template_name}\n"
                    "Coverage: {coverage_target}%\n",
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md(
                        "saas_t3", "tier-2-standard", 80, ["ci_cd"], project
                    )

                    assert claude_path.exists()
                    content = claude_path.read_text()
                    assert "SaaS T3" in content
                    assert "80%" in content

    def test_generate_claude_md_for_ml_ai_fastapi(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test generating CLAUDE.md for ML/AI FastAPI template."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["ml_ai_fastapi"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "ml_ai_fastapi",
                    "# CLAUDE.md - {project_name}\n"
                    "Stack: {template_name}\n"
                    "Package Manager: {package_manager}\n",
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md(
                        "ml_ai_fastapi", "tier-1-essential", 60, [], project
                    )

                    content = claude_path.read_text()
                    assert "ML/AI FastAPI" in content
                    assert "pip" in content

    def test_claude_md_includes_project_name(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes project name from directory."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Project: {project_name}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "my-awesome-project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    content = claude_path.read_text()
                    assert "my-awesome-project" in content

    def test_claude_md_includes_template_info(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes template name and ID."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "saas_t3", "Template: {template_name}\nID: {template_id}\n"
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    content = claude_path.read_text()
                    assert "SaaS T3" in content
                    assert "saas_t3" in content

    def test_claude_md_includes_tier_info(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes tier ID and name."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Tier: {tier} ({tier_name})\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-2-standard", 80, [], project)

                    content = claude_path.read_text()
                    assert "tier-2-standard" in content
                    assert "Tier 2: Standard" in content

    def test_claude_md_includes_coverage_target(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes coverage target."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Coverage: {coverage_target}%\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-2-standard", 85, [], project)

                    content = claude_path.read_text()
                    assert "85%" in content

    def test_claude_md_includes_package_manager(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes correct package manager for stack."""
        # Test npm stack
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "saas_t3", "Package Manager: {package_manager}\n"
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    content = claude_path.read_text()
                    assert "npm" in content

        # Test pip stack
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["ml_ai_fastapi"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "ml_ai_fastapi", "Package Manager: {package_manager}\n"
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project2 = tmp_path / "project2"
                    project2.mkdir()
                    claude_path = generate_claude_md(
                        "ml_ai_fastapi", "tier-1-essential", 60, [], project2
                    )

                    content = claude_path.read_text()
                    assert "pip" in content

    def test_claude_md_formats_additional_options(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md formats additional options correctly."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            # Add additional_options to registry
            registry = mock_template_registry.copy()
            registry["additional_options"] = {
                "ci_cd": {"name": "GitHub Actions CI/CD"},
                "docker": {"name": "Docker Support"},
            }

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Options: {additional_options}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md(
                        "saas_t3", "tier-1-essential", 60, ["ci_cd", "docker"], project
                    )

                    content = claude_path.read_text()
                    assert "GitHub Actions CI/CD" in content
                    assert "Docker Support" in content

    def test_claude_md_with_no_options(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md shows 'None' when no additional options."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Options: {additional_options}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    content = claude_path.read_text()
                    assert "None" in content

    def test_claude_md_includes_solokit_version(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes Solokit version."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "Version: {solokit_version}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    with patch(
                        "solokit.init.claude_md_generator._get_solokit_version",
                        return_value="1.2.3",
                    ):
                        project = tmp_path / "project"
                        project.mkdir()
                        claude_path = generate_claude_md(
                            "saas_t3", "tier-1-essential", 60, [], project
                        )

                        content = claude_path.read_text()
                        assert "1.2.3" in content

    def test_claude_md_includes_tier_requirements(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md includes tier-specific requirements."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "saas_t3", "Requirements:\n{tier_specific_requirements}\n"
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    # Test tier 2
                    claude_path = generate_claude_md("saas_t3", "tier-2-standard", 70, [], project)

                    content = claude_path.read_text()
                    assert "Tier 2+" in content
                    assert "Pre-commit hooks pass" in content

    def test_claude_md_uses_correct_commands_for_python(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md for Python stack includes pytest commands."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["ml_ai_fastapi"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "ml_ai_fastapi",
                    "# {project_name}\nStack uses {package_manager}\nRun tests with pytest\n",
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md(
                        "ml_ai_fastapi", "tier-1-essential", 60, [], project
                    )

                    content = claude_path.read_text()
                    assert "pip" in content
                    assert "pytest" in content

    def test_claude_md_uses_correct_commands_for_npm(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test that CLAUDE.md for npm stack includes npm commands."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure(
                    "saas_t3",
                    "# {project_name}\nStack uses {package_manager}\nRun tests with npm test\n",
                )

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    claude_path = generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    content = claude_path.read_text()
                    assert "npm" in content

    def test_claude_md_with_default_project_root(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test generating CLAUDE.md with default project_root (None)."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "# {project_name}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    # Change to tmp_path directory and use None for project_root
                    import os

                    original_cwd = os.getcwd()
                    try:
                        project = tmp_path / "test_project"
                        project.mkdir()
                        os.chdir(project)

                        # Call with project_root=None
                        claude_path = generate_claude_md(
                            "saas_t3", "tier-1-essential", 60, [], None
                        )

                        assert claude_path.exists()
                        assert claude_path.parent == project
                    finally:
                        os.chdir(original_cwd)

    def test_error_handling_template_not_found(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test error handling when CLAUDE.md.template not found."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                # Don't create template file, just use the directory structure
                # from mock_template_structure (but don't call it)
                module_dir = tmp_path / "init"
                module_dir.mkdir(exist_ok=True)
                mock_file = module_dir / "claude_md_generator.py"

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    with pytest.raises(FileOperationError) as exc:
                        generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                    assert exc.value.operation == "read"
                    assert "CLAUDE.md.template" in exc.value.file_path
                    assert "not found" in exc.value.details

    def test_error_handling_on_read_failure(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test error handling when template read fails."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "# {project_name}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    # Mock read_text to raise an exception
                    with patch.object(
                        Path, "read_text", side_effect=PermissionError("Read denied")
                    ):
                        with pytest.raises(FileOperationError) as exc:
                            generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                        assert exc.value.operation == "read"
                        assert "CLAUDE.md.template" in exc.value.file_path

    def test_error_handling_on_write_failure(
        self, tmp_path, mock_template_registry, mock_template_structure
    ):
        """Test error handling when CLAUDE.md write fails."""
        with patch("solokit.init.claude_md_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.claude_md_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                mock_file = mock_template_structure("saas_t3", "# {project_name}\n")

                import solokit.init.claude_md_generator as module

                with patch.object(module, "__file__", str(mock_file)):
                    project = tmp_path / "project"
                    project.mkdir()
                    with patch.object(
                        Path, "write_text", side_effect=PermissionError("Access denied")
                    ):
                        with pytest.raises(FileOperationError) as exc:
                            generate_claude_md("saas_t3", "tier-1-essential", 60, [], project)

                        assert exc.value.operation == "write"
                        assert "CLAUDE.md" in exc.value.file_path


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_solokit_version(self):
        """Test getting Solokit version."""
        version = _get_solokit_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_solokit_version_fallback(self):
        """Test version fallback when import fails."""
        # Patch the version function inside importlib.metadata
        with patch(
            "importlib.metadata.version",
            side_effect=Exception("Import error"),
        ):
            version = _get_solokit_version()
            assert version == "unknown"

    def test_format_additional_options_empty(self):
        """Test formatting empty additional options."""
        result = _format_additional_options([], {})
        assert result == "None"

    def test_format_additional_options_with_names(self):
        """Test formatting additional options with names from registry."""
        registry = {
            "additional_options": {
                "ci_cd": {"name": "GitHub Actions CI/CD"},
                "docker": {"name": "Docker Support"},
            }
        }

        result = _format_additional_options(["ci_cd", "docker"], registry)
        assert "GitHub Actions CI/CD" in result
        assert "Docker Support" in result
        assert ", " in result

    def test_format_additional_options_without_names(self):
        """Test formatting additional options without names in registry."""
        registry = {"additional_options": {}}

        result = _format_additional_options(["ci_cd", "custom_option"], registry)
        assert "Ci Cd" in result  # Title case from ID
        assert "Custom Option" in result  # Title case from ID

    def test_get_tier_specific_requirements_tier1(self):
        """Test tier-specific requirements for tier 1."""
        registry = {}
        result = _get_tier_specific_requirements("tier-1-essential", registry)
        assert result == ""  # Tier 1 has no additional requirements

    def test_get_tier_specific_requirements_tier2(self):
        """Test tier-specific requirements for tier 2."""
        registry = {}
        result = _get_tier_specific_requirements("tier-2-standard", registry)
        assert "Tier 2+" in result
        assert "Pre-commit hooks pass" in result
        assert "No secrets in code" in result

    def test_get_tier_specific_requirements_tier3(self):
        """Test tier-specific requirements for tier 3."""
        registry = {}
        result = _get_tier_specific_requirements("tier-3-comprehensive", registry)
        assert "Tier 2+" in result
        assert "Tier 3+" in result
        assert "E2E tests pass" in result
        assert "Mutation testing score" in result

    def test_get_tier_specific_requirements_tier4(self):
        """Test tier-specific requirements for tier 4."""
        registry = {}
        result = _get_tier_specific_requirements("tier-4-production", registry)
        assert "Tier 2+" in result
        assert "Tier 3+" in result
        assert "Tier 4" in result
        assert "Lighthouse CI passes" in result
        assert "Security audit passes" in result
