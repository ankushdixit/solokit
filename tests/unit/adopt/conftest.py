"""
Shared fixtures for adopt module tests.

This module provides common fixtures for testing the Solokit adoption system.
All tests in tests/unit/adopt/ can use these fixtures.
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
def python_project(tmp_path):
    """Create a Python project with pyproject.toml."""
    project = tmp_path / "python-project"
    project.mkdir()
    (project / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
    """)
    return project


@pytest.fixture
def nodejs_project(tmp_path):
    """Create a Node.js project with package.json."""
    project = tmp_path / "nodejs-project"
    project.mkdir()
    (project / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0"
}
    """)
    return project


@pytest.fixture
def typescript_project(tmp_path):
    """Create a TypeScript project."""
    project = tmp_path / "typescript-project"
    project.mkdir()
    (project / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0",
    "devDependencies": {
        "typescript": "^5.0.0"
    }
}
    """)
    (project / "tsconfig.json").write_text("""
{
    "compilerOptions": {
        "target": "ES2020"
    }
}
    """)
    return project


@pytest.fixture
def fullstack_project(tmp_path):
    """Create a fullstack project with both Python and Node.js."""
    project = tmp_path / "fullstack-project"
    project.mkdir()
    (project / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0"
}
    """)
    (project / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
    """)
    return project


@pytest.fixture
def nextjs_project(tmp_path):
    """Create a Next.js project."""
    project = tmp_path / "nextjs-project"
    project.mkdir()
    (project / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "next": "^14.0.0",
        "react": "^18.0.0"
    }
}
    """)
    (project / "next.config.js").write_text("module.exports = {};")
    return project


@pytest.fixture
def django_project(tmp_path):
    """Create a Django project."""
    project = tmp_path / "django-project"
    project.mkdir()
    (project / "manage.py").write_text("""
#!/usr/bin/env python
import sys
from django.core.management import execute_from_command_line
    """)
    (project / "requirements.txt").write_text("django==4.2.0")
    return project


@pytest.fixture
def fastapi_project(tmp_path):
    """Create a FastAPI project."""
    project = tmp_path / "fastapi-project"
    project.mkdir()
    (project / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["fastapi", "uvicorn"]
    """)
    return project


@pytest.fixture
def project_with_readme(tmp_path):
    """Create a project with existing README.md."""
    project = tmp_path / "project-with-readme"
    project.mkdir()
    (project / "README.md").write_text("# Test Project\n\nExisting content\n")
    return project


@pytest.fixture
def project_with_claude_md(tmp_path):
    """Create a project with existing CLAUDE.md."""
    project = tmp_path / "project-with-claude"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Claude Guidelines\n\nExisting guidance\n")
    return project


@pytest.fixture
def project_with_gitignore(tmp_path):
    """Create a project with existing .gitignore."""
    project = tmp_path / "project-with-gitignore"
    project.mkdir()
    (project / ".gitignore").write_text("node_modules/\n*.log\n")
    return project


@pytest.fixture
def project_with_tools(tmp_path):
    """Create a project with various development tools configured."""
    project = tmp_path / "project-with-tools"
    project.mkdir()

    # Package files
    (project / "package.json").write_text("""
{
    "name": "test-project",
    "version": "1.0.0",
    "devDependencies": {
        "typescript": "^5.0.0",
        "eslint": "^8.0.0",
        "prettier": "^3.0.0",
        "jest": "^29.0.0"
    }
}
    """)

    # Config files
    (project / "tsconfig.json").write_text("{}")
    (project / ".eslintrc.json").write_text('{"extends": ["eslint:recommended"]}')
    (project / ".prettierrc").write_text('{"semi": true}')
    (project / "jest.config.js").write_text("module.exports = {};")

    # Test directory
    (project / "tests").mkdir()
    (project / "tests" / "example.test.ts").write_text("test('example', () => {});")

    # Git hooks
    (project / ".pre-commit-config.yaml").write_text("repos: []")

    # CI/CD
    github = project / ".github" / "workflows"
    github.mkdir(parents=True)
    (github / "ci.yml").write_text("name: CI")

    return project


@pytest.fixture
def git_project(tmp_path):
    """Create a project with git initialized."""
    project = tmp_path / "git-project"
    project.mkdir()
    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    (git_dir / "config").write_text("[core]\nrepositoryformatversion = 0")
    return project


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
def empty_project(tmp_path):
    """Create an empty project directory."""
    project = tmp_path / "empty-project"
    project.mkdir()
    return project


@pytest.fixture
def project_with_lock_files(tmp_path):
    """Create a project with various lock files."""
    project = tmp_path / "project-with-locks"
    project.mkdir()

    # Node.js
    (project / "package.json").write_text('{"name": "test"}')
    (project / "yarn.lock").write_text("# Yarn lock file")

    # Python
    (project / "pyproject.toml").write_text("[project]\nname = 'test'")
    (project / "poetry.lock").write_text("# Poetry lock file")

    return project


@pytest.fixture
def project_with_extensions(tmp_path):
    """Create a project with various file extensions for fallback detection."""
    project = tmp_path / "project-with-extensions"
    project.mkdir()

    # Create Python files
    src = project / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("# utils")
    (src / "models.py").write_text("# models")

    # Create JS files
    lib = project / "lib"
    lib.mkdir()
    (lib / "index.js").write_text("console.log('hello');")
    (lib / "utils.js").write_text("// utils")

    return project
