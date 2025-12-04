"""
Tests for readme_generator module.

Validates README.md generation with stack-specific information.

Run tests:
    pytest tests/unit/init/test_readme_generator.py -v

Run with coverage:
    pytest tests/unit/init/test_readme_generator.py --cov=solokit.init.readme_generator --cov-report=term-missing

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.init.readme_generator import generate_readme


class TestGenerateReadme:
    """Tests for generate_readme()."""

    def test_generate_readme_for_saas_t3(self, tmp_path, mock_template_registry):
        """Test generating README for SaaS T3 template."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-2-standard", 80, ["ci_cd"], tmp_path)

                assert readme_path.exists()
                content = readme_path.read_text()
                assert "SaaS T3" in content
                assert "80%" in content
                assert "Next.js" in content

    def test_readme_includes_tech_stack(self, tmp_path, mock_template_registry):
        """Test that README includes complete tech stack."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "Next.js 16.0.7" in content
                assert "tRPC 11.0.0" in content
                assert "PostgreSQL 16.2" in content

    def test_readme_includes_npm_commands(self, tmp_path, mock_template_registry):
        """Test that README includes npm commands for Node.js stacks."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "npm install" in content
                assert "npm run dev" in content
                assert "npm test" in content

    def test_readme_includes_python_commands(self, tmp_path, mock_template_registry):
        """Test that README includes Python commands for Python stacks."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["ml_ai_fastapi"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("ml_ai_fastapi", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "source venv/bin/activate" in content
                assert "pytest" in content
                assert "uvicorn" in content

    def test_readme_includes_additional_options(self, tmp_path, mock_template_registry):
        """Test that README includes additional options."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme(
                    "saas_t3", "tier-1-essential", 60, ["ci_cd", "docker"], tmp_path
                )

                content = readme_path.read_text()
                assert "Additional Features" in content
                assert "Ci Cd" in content or "CI/CD" in content.upper()
                assert "Docker" in content

    def test_readme_uses_project_name(self, tmp_path, mock_template_registry):
        """Test that README uses project directory name."""
        project = tmp_path / "my-awesome-project"
        project.mkdir()

        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], project)

                content = readme_path.read_text()
                assert "my-awesome-project" in content

    def test_readme_includes_solokit_commands(self, tmp_path, mock_template_registry):
        """Test that README includes Solokit workflow commands."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "/sk:work-new" in content
                assert "/sk:start" in content
                assert "/sk:end" in content

    def test_error_handling_on_write_failure(self, tmp_path, mock_template_registry):
        """Test error handling when README write fails."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                with patch.object(Path, "write_text", side_effect=PermissionError("Access denied")):
                    with pytest.raises(FileOperationError) as exc:
                        generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                    assert exc.value.operation == "write"
                    assert "README.md" in exc.value.file_path

    def test_readme_uses_cwd_when_project_root_none(self, mock_template_registry):
        """Test that README uses cwd when project_root is None."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                with patch("solokit.init.readme_generator.Path.cwd") as mock_cwd:
                    mock_project = Path("/test/project")
                    mock_cwd.return_value = mock_project

                    with patch.object(Path, "write_text"):
                        readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], None)

                        mock_cwd.assert_called_once()
                        assert readme_path == mock_project / "README.md"

    def test_readme_handles_invalid_tier(self, tmp_path, mock_template_registry):
        """Test that README handles invalid tier gracefully."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                # Use an invalid tier
                readme_path = generate_readme("saas_t3", "tier-99-invalid", 60, [], tmp_path)

                assert readme_path.exists()
                content = readme_path.read_text()
                # Should still generate content even with invalid tier
                assert "SaaS T3" in content

    def test_readme_includes_js_specific_quality_gates(self, tmp_path):
        """Test that README includes JS-specific quality gates."""
        mock_registry = {
            "quality_tiers": {
                "tier-2-standard": {
                    "name": "Tier 2: Standard",
                    "includes": ["Base features"],
                    "adds": ["Standard features"],
                    "adds_js": ["ESLint", "Prettier"],
                    "adds_python": ["Ruff", "Black"],
                }
            }
        }
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"frontend": "Next.js"},
            "package_manager": "npm",
        }

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme("test", "tier-2-standard", 60, [], tmp_path)

                content = readme_path.read_text()
                # Should include JS-specific quality gates
                assert "ESLint" in content
                assert "Prettier" in content
                # Should NOT include Python-specific quality gates
                assert "Ruff" not in content

    def test_readme_includes_python_specific_quality_gates(self, tmp_path):
        """Test that README includes Python-specific quality gates."""
        mock_registry = {
            "quality_tiers": {
                "tier-2-standard": {
                    "name": "Tier 2: Standard",
                    "includes": ["Base features"],
                    "adds": ["Standard features"],
                    "adds_js": ["ESLint", "Prettier"],
                    "adds_python": ["Ruff", "Black"],
                }
            }
        }
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"backend": "FastAPI"},
            "package_manager": "pip",
        }

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme("test", "tier-2-standard", 60, [], tmp_path)

                content = readme_path.read_text()
                # Should include Python-specific quality gates
                assert "Ruff" in content
                assert "Black" in content
                # Should NOT include JS-specific quality gates
                assert "ESLint" not in content

    def test_readme_includes_prisma_database_setup(self, tmp_path):
        """Test that README includes Prisma database setup."""
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"database": "PostgreSQL + Prisma"},
            "package_manager": "npm",
        }
        mock_registry = {"quality_tiers": {}}

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme("test", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "prisma generate" in content
                assert "prisma migrate" in content
                assert "prisma studio" in content

    def test_readme_includes_alembic_database_setup(self, tmp_path):
        """Test that README includes Alembic database setup."""
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"database": "PostgreSQL + Alembic"},
            "package_manager": "pip",
        }
        mock_registry = {"quality_tiers": {}}

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme("test", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "alembic upgrade head" in content
                assert "alembic revision" in content

    def test_readme_includes_e2e_testing_for_tier3(self, tmp_path, mock_template_registry):
        """Test that README includes E2E testing section for tier-3+."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-3-comprehensive", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "E2E Testing" in content
                assert "test:e2e" in content
                assert "playwright install" in content

    def test_readme_includes_accessibility_testing_for_tier4(
        self, tmp_path, mock_template_registry
    ):
        """Test that README includes accessibility testing for tier-4."""
        with patch("solokit.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "solokit.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-4-production", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "Accessibility Testing" in content
                assert "test:a11y" in content
                assert "Lighthouse CI" in content
                assert "npm run lighthouse" in content

    def test_readme_includes_additional_options_with_description(self, tmp_path):
        """Test that README includes additional options with descriptions."""
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"frontend": "Next.js"},
            "package_manager": "npm",
        }
        mock_registry = {
            "quality_tiers": {},
            "additional_options": {
                "ci_cd": {
                    "name": "CI/CD Pipeline",
                    "description": "GitHub Actions workflow for automated testing",
                },
                "docker": {"name": "Docker", "description": "Containerization support"},
            },
        }

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme(
                    "test", "tier-1-essential", 60, ["ci_cd", "docker"], tmp_path
                )

                content = readme_path.read_text()
                assert "CI/CD Pipeline" in content
                assert "automated testing" in content
                assert "Docker" in content
                assert "Containerization support" in content

    def test_readme_includes_known_issues(self, tmp_path):
        """Test that README includes known issues section."""
        mock_template = {
            "display_name": "Test Stack",
            "stack": {"frontend": "Next.js"},
            "package_manager": "npm",
            "known_issues": [
                {
                    "package": "test-package",
                    "severity": "CRITICAL",
                    "description": "This is a critical issue",
                },
                {
                    "package": "another-package",
                    "severity": "HIGH",
                    "description": "This is a high severity issue",
                },
                {
                    "package": "low-package",
                    "severity": "LOW",
                    "description": "This should not appear",
                },
            ],
        }
        mock_registry = {"quality_tiers": {}}

        with patch("solokit.init.readme_generator.get_template_info", return_value=mock_template):
            with patch(
                "solokit.init.readme_generator.load_template_registry", return_value=mock_registry
            ):
                readme_path = generate_readme("test", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "Known Issues" in content
                assert "test-package" in content
                assert "CRITICAL" in content
                assert "critical issue" in content
                assert "another-package" in content
                assert "HIGH" in content
                # LOW severity should not be included
                assert "low-package" not in content
