"""
Shared fixtures for init module tests.

This module provides common fixtures for testing the Solokit initialization system.
All tests in tests/unit/init/ can use these fixtures.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "test-project"
    project.mkdir()
    return project


@pytest.fixture
def blank_project(tmp_path):
    """Create a blank project directory (only .git and README)."""
    project = tmp_path / "blank-project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "README.md").write_text("# Test Project")
    return project


@pytest.fixture
def non_blank_project(tmp_path):
    """Create a non-blank project directory (has package.json)."""
    project = tmp_path / "non-blank-project"
    project.mkdir()
    (project / "package.json").write_text('{"name": "test"}')
    return project


@pytest.fixture
def project_with_src(tmp_path):
    """Create a project with src/ directory containing files."""
    project = tmp_path / "project-with-src"
    project.mkdir()
    src = project / "src"
    src.mkdir()
    (src / "index.ts").write_text("export {};")
    return project


@pytest.fixture
def mock_template_registry():
    """Mock template registry data."""
    return {
        "version": "1.0.0",
        "templates": {
            "saas_t3": {
                "id": "saas_t3",
                "display_name": "SaaS T3",
                "description": "Production SaaS with T3 Stack",
                "stack": {
                    "frontend": "Next.js 16.0.1",
                    "backend": "tRPC 11.0.0",
                    "database": "PostgreSQL 16.2",
                },
                "package_manager": "npm",
                "tiers": [
                    "tier-1-essential",
                    "tier-2-standard",
                    "tier-3-comprehensive",
                    "tier-4-production",
                ],
                "known_issues": [],
            },
            "ml_ai_fastapi": {
                "id": "ml_ai_fastapi",
                "display_name": "ML/AI FastAPI",
                "description": "ML/AI Backend with FastAPI",
                "stack": {
                    "backend": "FastAPI 0.115.6",
                    "database": "PostgreSQL 16.2",
                },
                "package_manager": "pip",
                "tiers": [
                    "tier-1-essential",
                    "tier-2-standard",
                    "tier-3-comprehensive",
                    "tier-4-production",
                ],
                "known_issues": [],
            },
        },
        "quality_tiers": {
            "tier-1-essential": {
                "name": "Tier 1: Essential",
                "includes": ["Basic testing", "Linting"],
            },
            "tier-2-standard": {
                "name": "Tier 2: Standard",
                "includes": ["Everything in Tier 1"],
                "adds": ["Type checking", "Git hooks (Husky)"],
            },
        },
    }


@pytest.fixture
def mock_stack_versions():
    """Mock stack-versions.yaml data."""
    return {
        "version": "1.0.0",
        "stacks": {
            "saas_t3": {
                "installation": {
                    "commands": {
                        "base": "npm install next@16.0.1 react@19.0.0",
                        "tier1": "npm install -D vitest@3.0.5",
                        "tier2": "npm install -D typescript@5.7.2",
                        "tier3": "npm install -D @playwright/test@1.49.1",
                        "tier4_dev": "npm install -D @sentry/nextjs@8.46.0",
                        "tier4_prod": "npm install patch-package@8.0.0",
                    }
                }
            },
            "ml_ai_fastapi": {
                "installation": {
                    "commands": {
                        "base": "pip install fastapi==0.115.6 uvicorn==0.34.0",
                        "tier1": "pip install pytest==8.3.4 pytest-cov==6.0.0",
                        "tier2": "pip install detect-secrets==1.5.0 pip-audit==2.7.3",
                        "tier3": "pip install radon==6.0.1 vulture==2.14",
                        "tier4_dev": "pip install prometheus-client==0.23.1 statsd==4.0.1",
                        "tier4_prod": "pip install fastapi-health==0.4.0 pydantic-settings==2.11.0",
                    }
                }
            },
        },
    }


@pytest.fixture
def mock_command_runner():
    """Mock CommandRunner for subprocess calls."""
    mock = Mock()
    mock.run.return_value = Mock(success=True, stdout="", stderr="", returncode=0)
    return mock


@pytest.fixture
def mock_successful_command():
    """Mock a successful command execution."""
    return Mock(success=True, stdout="Success", stderr="", returncode=0)


@pytest.fixture
def mock_failed_command():
    """Mock a failed command execution."""
    return Mock(success=False, stdout="", stderr="Error occurred", returncode=1)


@pytest.fixture
def template_base_dir(tmp_path):
    """Create a mock template base directory with files."""
    base = tmp_path / "base"
    base.mkdir()

    # Create some files
    (base / "README.md").write_text("# {project_name}")
    (base / "package.json.template").write_text('{"name": "{project_name}"}')

    # Create subdirectory
    src = base / "src"
    src.mkdir()
    (src / "index.ts").write_text("// Starter code")

    return base


@pytest.fixture
def template_tier_dir(tmp_path):
    """Create a mock template tier directory with files."""
    tier = tmp_path / "tier-1-essential"
    tier.mkdir()

    (tier / "vitest.config.ts").write_text("export default {};")
    (tier / ".eslintrc.json.template").write_text('{"extends": []}')

    return tier


@pytest.fixture
def session_dir(tmp_path):
    """.session directory structure."""
    session = tmp_path / ".session"
    session.mkdir()
    (session / "tracking").mkdir()
    (session / "briefings").mkdir()
    (session / "history").mkdir()
    (session / "specs").mkdir()
    return session


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository."""
    project = tmp_path / "git-project"
    project.mkdir()
    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    return project


@pytest.fixture
def tracking_template_files(tmp_path):
    """Create mock tracking template files."""
    templates = tmp_path / "templates"
    templates.mkdir()

    (templates / "work_items.json").write_text('{"work_items": []}')
    (templates / "learnings.json").write_text('{"learnings": []}')
    (templates / "status_update.json").write_text('{"status": "idle"}')
    (templates / "config.schema.json").write_text('{"type": "object"}')

    return templates


@pytest.fixture
def tracking_template_files_with_guides(tmp_path):
    """Create mock tracking template files including guides."""
    templates = tmp_path / "templates"
    templates.mkdir()

    (templates / "work_items.json").write_text('{"work_items": []}')
    (templates / "learnings.json").write_text('{"learnings": []}')
    (templates / "status_update.json").write_text('{"status": "idle"}')
    (templates / "config.schema.json").write_text('{"type": "object"}')

    # Create guides directory with guide files
    guides = templates / "guides"
    guides.mkdir()
    (guides / "STACK_GUIDE.md").write_text("# Stack Guide\n\nTest content.")
    (guides / "PRD_WRITING_GUIDE.md").write_text("# PRD Guide\n\nTest content.")

    return templates
