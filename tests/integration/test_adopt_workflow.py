"""Integration tests for sk adopt feature.

This module tests the complete adoption workflow in realistic environments
without mocking, using actual file system operations and subprocess calls.

Test scenarios:
- Complete adoption workflow for Python projects
- Node.js project adoption with correct language detection
- Fullstack project adoption (Python + Node.js)
- Idempotency (running adoption twice)
- Existing documentation preservation
- CLI argument validation

Run tests:
    pytest tests/integration/test_adopt_workflow.py -v
"""

import json
import subprocess
from pathlib import Path


def create_python_project(project_dir: Path) -> None:
    """Create a realistic Python project structure."""
    # Create pyproject.toml
    pyproject_toml = """[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-python-project"
version = "0.1.0"
description = "A test Python project"
dependencies = [
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "mypy>=1.8.0",
]
"""
    (project_dir / "pyproject.toml").write_text(pyproject_toml)

    # Create src/ directory structure
    src_dir = project_dir / "src" / "testproject"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text(
        """def main():
    print("Hello from Python!")

if __name__ == "__main__":
    main()
"""
    )

    # Create tests/ directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text(
        """from testproject.main import main

def test_main():
    assert main() is None
"""
    )

    # Create existing README.md with some content
    readme_content = """# Test Python Project

This is a test project for integration testing.

## Installation

```bash
pip install -e .
```

## Usage

```python
from testproject import main
main()
```
"""
    (project_dir / "README.md").write_text(readme_content)


def create_nodejs_project(project_dir: Path) -> None:
    """Create a realistic Node.js project structure."""
    # Create package.json
    package_json = {
        "name": "test-nodejs-project",
        "version": "1.0.0",
        "description": "A test Node.js project",
        "main": "src/index.js",
        "scripts": {"test": "jest", "start": "node src/index.js"},
        "dependencies": {"express": "^4.18.0"},
        "devDependencies": {
            "jest": "^29.0.0",
            "eslint": "^8.50.0",
            "prettier": "^3.0.0",
        },
    }
    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # Create src/ directory
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "index.js").write_text(
        """const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello from Node.js!');
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
"""
    )

    # Create tests/ directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "index.test.js").write_text(
        """describe('App', () => {
  test('should load', () => {
    expect(true).toBe(true);
  });
});
"""
    )

    # Create existing README.md
    (project_dir / "README.md").write_text(
        """# Test Node.js Project

A simple Express server.

## Getting Started

```bash
npm install
npm start
```
"""
    )


def create_fullstack_project(project_dir: Path) -> None:
    """Create a fullstack project with both Python and Node.js."""
    # Python backend
    pyproject_toml = """[project]
name = "fullstack-backend"
version = "0.1.0"
dependencies = ["fastapi>=0.104.0", "uvicorn>=0.24.0"]
"""
    (project_dir / "pyproject.toml").write_text(pyproject_toml)

    # Node.js frontend
    package_json = {
        "name": "fullstack-frontend",
        "version": "1.0.0",
        "dependencies": {"react": "^18.2.0", "next": "^14.0.0"},
        "devDependencies": {"typescript": "^5.2.0"},
    }
    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # TypeScript config
    tsconfig = {"compilerOptions": {"target": "ES2020", "module": "ESNext"}}
    (project_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    # Backend structure
    backend_dir = project_dir / "backend"
    backend_dir.mkdir()
    (backend_dir / "main.py").write_text(
        """from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}
"""
    )

    # Frontend structure
    frontend_dir = project_dir / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "App.tsx").write_text(
        """export default function App() {
  return <div>Hello from React!</div>
}
"""
    )


class TestCompleteAdoptionWorkflow:
    """Test complete adoption workflow for different project types."""

    def test_python_project_adoption(self, tmp_path):
        """Test adopting a Python project with complete workflow."""
        # Arrange - Create Python project
        project_dir = tmp_path / "python_project"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Act - Run adoption
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        # Assert - .session/ directory structure created
        session_dir = project_dir / ".session"
        assert session_dir.exists(), ".session/ directory should be created"

        # Verify subdirectories
        assert (session_dir / "tracking").exists()
        assert (session_dir / "specs").exists()
        assert (session_dir / "briefings").exists()
        assert (session_dir / "history").exists()

        # Assert - Tracking files exist
        tracking_dir = session_dir / "tracking"
        assert (tracking_dir / "work_items.json").exists()
        assert (tracking_dir / "learnings.json").exists()

        # Config is in .session/ root, not tracking/
        config_path = session_dir / "config.json"
        assert config_path.exists()

        # Verify config.json content
        config = json.loads(config_path.read_text())
        assert config["quality_gates"]["tier"] == "tier-2-standard"
        assert config["quality_gates"]["coverage_threshold"] == 80

        # Verify work_items.json structure
        work_items = json.loads((tracking_dir / "work_items.json").read_text())
        assert "work_items" in work_items
        assert "milestones" in work_items
        assert "metadata" in work_items

        # Verify learnings.json structure
        learnings = json.loads((tracking_dir / "learnings.json").read_text())
        assert "learnings" in learnings

        # Assert - README.md has Solokit section appended
        readme_content = (project_dir / "README.md").read_text()
        assert "Test Python Project" in readme_content  # Original content preserved
        assert "Solokit" in readme_content or "Session Management" in readme_content

        # Assert - CLAUDE.md has Solokit section
        assert (project_dir / "CLAUDE.md").exists()
        claude_md_content = (project_dir / "CLAUDE.md").read_text()
        assert "Solokit" in claude_md_content or "Session-Driven Development" in claude_md_content

        # Assert - .gitignore has Solokit entries
        gitignore_content = (project_dir / ".gitignore").read_text()
        assert ".session/briefings/" in gitignore_content
        assert ".session/history/" in gitignore_content
        # Python-specific entries
        assert ".coverage" in gitignore_content
        assert "htmlcov/" in gitignore_content

        # Assert - Claude commands installed
        claude_commands_dir = project_dir / ".claude" / "commands"
        assert claude_commands_dir.exists()
        assert (claude_commands_dir / "start.md").exists()
        assert (claude_commands_dir / "end.md").exists()
        assert (claude_commands_dir / "status.md").exists()

        # Assert - Initial scans created (in tracking directory)
        assert (tracking_dir / "stack.txt").exists()
        assert (tracking_dir / "tree.txt").exists()

    def test_nodejs_project_adoption(self, tmp_path):
        """Test adopting a Node.js project with correct language detection."""
        # Arrange - Create Node.js project
        project_dir = tmp_path / "nodejs_project"
        project_dir.mkdir()
        create_nodejs_project(project_dir)

        # Act - Run adoption
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        # Assert - Correct language detected in output
        assert "nodejs" in result.stdout.lower() or "node" in result.stdout.lower()

        # Assert - Node.js-specific gitignore entries
        gitignore_content = (project_dir / ".gitignore").read_text()
        assert "coverage/" in gitignore_content  # Node.js coverage directory
        assert "coverage.json" in gitignore_content

        # Should NOT have Python-specific entries
        assert ".coverage" not in gitignore_content  # Python coverage file
        assert "htmlcov/" not in gitignore_content  # Python coverage HTML

        # Assert - Session structure exists
        assert (project_dir / ".session").exists()
        assert (project_dir / ".session" / "config.json").exists()

    def test_fullstack_project_adoption(self, tmp_path):
        """Test adopting a fullstack project (Python + Node.js)."""
        # Arrange - Create fullstack project
        project_dir = tmp_path / "fullstack_project"
        project_dir.mkdir()
        create_fullstack_project(project_dir)

        # Act - Run adoption
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-3-comprehensive",
                "--coverage=90",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        # Assert - FULLSTACK language detected
        assert "fullstack" in result.stdout.lower()

        # Assert - Both Python and Node.js gitignore entries
        gitignore_content = (project_dir / ".gitignore").read_text()
        # Python entries
        assert ".coverage" in gitignore_content
        assert "htmlcov/" in gitignore_content
        # Node.js entries
        assert "coverage/" in gitignore_content
        assert "coverage.json" in gitignore_content

        # Assert - Config has correct tier
        config_path = project_dir / ".session" / "config.json"
        config = json.loads(config_path.read_text())
        assert config["quality_gates"]["tier"] == "tier-3-comprehensive"
        assert config["quality_gates"]["coverage_threshold"] == 90

    def test_idempotency_no_duplicate_content(self, tmp_path):
        """Test that running adoption twice doesn't duplicate content."""
        # Arrange - Create Python project
        project_dir = tmp_path / "idempotent_project"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Act - Run adoption twice
        subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        result2 = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Second run succeeded
        assert result2.returncode == 0

        # Assert - No duplicate entries in README.md
        readme_content = (project_dir / "README.md").read_text()
        # Count occurrences of Solokit-related headers
        solokit_count = readme_content.lower().count("solokit")
        # Should appear only once (or a reasonable number of times, not doubled)
        assert solokit_count < 10, "README.md appears to have duplicate Solokit sections"

        # Assert - No duplicate entries in CLAUDE.md
        claude_md_content = (project_dir / "CLAUDE.md").read_text()
        # Check that major sections don't appear twice
        # Count occurrences of distinctive section markers
        session_driven_count = claude_md_content.count("Session-Driven Development")
        # Should appear a reasonable number of times, not doubled
        assert session_driven_count <= 4, (
            f"CLAUDE.md has duplicated sections ({session_driven_count} occurrences)"
        )

        # Assert - No duplicate entries in .gitignore
        gitignore_content = (project_dir / ".gitignore").read_text()
        assert gitignore_content.count(".session/briefings/") == 1
        assert gitignore_content.count(".session/history/") == 1
        assert gitignore_content.count(".coverage") <= 1

    def test_existing_documentation_preservation(self, tmp_path):
        """Test that existing README and CLAUDE.md content is preserved."""
        # Arrange - Create project with existing documentation
        project_dir = tmp_path / "existing_docs_project"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Add custom content to README
        original_readme = """# My Awesome Project

This is my unique project with special features.

## Features

- Feature A
- Feature B
- Feature C

## Installation

Custom installation instructions here.

## Contributing

Please follow our contribution guidelines.
"""
        (project_dir / "README.md").write_text(original_readme)

        # Add existing CLAUDE.md
        original_claude_md = """# Claude Instructions

This project uses custom Claude workflows.

## Development Patterns

- Pattern 1
- Pattern 2

## Important Notes

Keep these things in mind when working on this project.
"""
        (project_dir / "CLAUDE.md").write_text(original_claude_md)

        # Act - Run adoption
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0

        # Assert - Original README content preserved
        readme_content = (project_dir / "README.md").read_text()
        assert "My Awesome Project" in readme_content
        assert "Feature A" in readme_content
        assert "Feature B" in readme_content
        assert "Feature C" in readme_content
        assert "Custom installation instructions" in readme_content
        assert "contribution guidelines" in readme_content
        # Solokit content should be appended
        assert "Solokit" in readme_content or "Session" in readme_content

        # Assert - Original CLAUDE.md content preserved
        claude_md_content = (project_dir / "CLAUDE.md").read_text()
        assert "custom Claude workflows" in claude_md_content
        assert "Pattern 1" in claude_md_content
        assert "Pattern 2" in claude_md_content
        assert "Important Notes" in claude_md_content
        # Solokit content should be appended
        assert "Solokit" in claude_md_content or "Session-Driven" in claude_md_content


class TestCLIArgumentValidation:
    """Test CLI argument validation and error handling."""

    def test_adopt_help_command(self, tmp_path):
        """Test that sk adopt --help works."""
        # Arrange - Create a minimal project
        project_dir = tmp_path / "help_test"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            """[project]
name = "test"
version = "0.1.0"
"""
        )

        # Act
        result = subprocess.run(
            ["sk", "adopt", "--help"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "adopt" in result.stdout.lower() or "Adopt" in result.stdout
        assert "--tier" in result.stdout
        assert "--coverage" in result.stdout

    def test_partial_args_error(self, tmp_path):
        """Test that providing only --tier without --coverage produces an error."""
        # Arrange
        project_dir = tmp_path / "partial_args"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            """[project]
name = "test"
version = "0.1.0"
"""
        )

        # Act - Only provide --tier
        result = subprocess.run(
            ["sk", "adopt", "--tier=tier-2-standard"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Should fail with error message
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        assert "--tier and --coverage are both required" in error_output

    def test_coverage_without_tier_error(self, tmp_path):
        """Test that providing only --coverage without --tier produces an error."""
        # Arrange
        project_dir = tmp_path / "coverage_only"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            """[project]
name = "test"
version = "0.1.0"
"""
        )

        # Act - Only provide --coverage
        result = subprocess.run(
            ["sk", "adopt", "--coverage=80"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Should fail with error message
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        assert "--tier and --coverage are both required" in error_output


class TestAdoptionWithOptions:
    """Test adoption with additional options."""

    def test_adopt_with_additional_options(self, tmp_path):
        """Test adoption with additional options like ci_cd and docker."""
        # Arrange
        project_dir = tmp_path / "options_project"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Act - Run with additional options
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-4-production",
                "--coverage=90",
                "--options=ci_cd,docker",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"

        # Assert - Config has correct tier
        config_path = project_dir / ".session" / "config.json"
        config = json.loads(config_path.read_text())
        assert config["quality_gates"]["tier"] == "tier-4-production"
        assert config["quality_gates"]["coverage_threshold"] == 90

    def test_adopt_empty_project_directory(self, tmp_path):
        """Test adopting into a nearly empty directory (minimal manifest)."""
        # Arrange - Create minimal project
        project_dir = tmp_path / "minimal_project"
        project_dir.mkdir()
        # Just a minimal pyproject.toml
        (project_dir / "pyproject.toml").write_text(
            """[project]
name = "minimal"
version = "0.1.0"
"""
        )

        # Act
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-1-essential",
                "--coverage=60",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Should succeed even with minimal project
        assert result.returncode == 0

        # Assert - Session structure created
        assert (project_dir / ".session").exists()
        assert (project_dir / ".session" / "config.json").exists()

        # Assert - README.md created if it didn't exist
        assert (project_dir / "README.md").exists()

        # Assert - CLAUDE.md created
        assert (project_dir / "CLAUDE.md").exists()


class TestSkipCommitFlag:
    """Test --skip-commit flag behavior."""

    def test_skip_commit_flag_prevents_git_commit(self, tmp_path):
        """Test that --skip-commit prevents creating a git commit."""
        # Arrange - Create git repository
        project_dir = tmp_path / "skip_commit_project"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_dir,
            capture_output=True,
        )

        # Act - Run with --skip-commit
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - Command succeeded
        assert result.returncode == 0

        # Assert - No new commit created (log should show only 1 commit)
        log_result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        commits = log_result.stdout.strip().split("\n")
        assert len(commits) == 1  # Only initial commit
        assert "Initial commit" in commits[0]

        # Assert - Changes are unstaged
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        assert len(status_result.stdout.strip()) > 0  # Has uncommitted changes


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_adopt_project_with_existing_gitignore(self, tmp_path):
        """Test adopting a project that already has a .gitignore."""
        # Arrange
        project_dir = tmp_path / "existing_gitignore"
        project_dir.mkdir()
        create_python_project(project_dir)

        # Create existing .gitignore
        existing_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""
        (project_dir / ".gitignore").write_text(existing_gitignore)

        # Act
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0

        # Assert - Original gitignore content preserved
        gitignore_content = (project_dir / ".gitignore").read_text()
        assert "__pycache__/" in gitignore_content
        assert "venv/" in gitignore_content
        assert ".vscode/" in gitignore_content
        assert ".DS_Store" in gitignore_content

        # Assert - Solokit entries added
        assert ".session/briefings/" in gitignore_content
        assert ".session/history/" in gitignore_content

    def test_adopt_typescript_project(self, tmp_path):
        """Test adopting a TypeScript project."""
        # Arrange - Create TypeScript project
        project_dir = tmp_path / "typescript_project"
        project_dir.mkdir()

        # package.json with TypeScript
        package_json = {
            "name": "typescript-project",
            "version": "1.0.0",
            "dependencies": {},
            "devDependencies": {
                "typescript": "^5.2.0",
                "@types/node": "^20.0.0",
            },
        }
        (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))

        # tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "strict": True,
            }
        }
        (project_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

        # Source files
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "index.ts").write_text(
            """export function greet(name: string): string {
  return `Hello, ${name}!`;
}
"""
        )

        # Act
        result = subprocess.run(
            [
                "sk",
                "adopt",
                "--tier=tier-2-standard",
                "--coverage=80",
                "--yes",
                "--skip-commit",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0

        # Assert - TypeScript detected in output
        assert "typescript" in result.stdout.lower() or "ts" in result.stdout.lower()

        # Assert - Session created
        assert (project_dir / ".session").exists()
