"""
Tests for project_detector module.

Validates project type detection, framework identification, and tooling discovery.

Run tests:
    pytest tests/unit/adopt/test_project_detector.py -v

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

from solokit.adopt.project_detector import (
    ExistingTooling,
    PackageManager,
    ProjectFramework,
    ProjectInfo,
    ProjectLanguage,
    detect_project_type,
    get_project_summary,
)


class TestDetectProjectType:
    """Tests for detect_project_type() main function."""

    def test_empty_directory_unknown(self, empty_project):
        """Test empty directory returns UNKNOWN language."""
        info = detect_project_type(empty_project)

        assert info.language == ProjectLanguage.UNKNOWN
        assert info.framework == ProjectFramework.NONE
        assert info.package_manager == PackageManager.UNKNOWN

    def test_nodejs_project_detection(self, nodejs_project):
        """Test Node.js project detection from package.json."""
        info = detect_project_type(nodejs_project)

        assert info.language == ProjectLanguage.NODEJS
        assert "Found package.json" in info.detection_notes

    def test_python_project_from_pyproject(self, python_project):
        """Test Python project detection from pyproject.toml."""
        info = detect_project_type(python_project)

        assert info.language == ProjectLanguage.PYTHON
        assert any("pyproject.toml" in note for note in info.detection_notes)

    def test_python_project_from_requirements(self, tmp_path):
        """Test Python project detection from requirements.txt."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements.txt").write_text("flask==2.0.0\n")

        info = detect_project_type(project)

        assert info.language == ProjectLanguage.PYTHON
        assert any("requirements.txt" in note for note in info.detection_notes)

    def test_typescript_project_detection(self, typescript_project):
        """Test TypeScript project detection."""
        info = detect_project_type(typescript_project)

        assert info.language == ProjectLanguage.TYPESCRIPT
        assert info.has_typescript is True
        assert any("TypeScript detected" in note for note in info.detection_notes)

    def test_typescript_from_tsconfig_only(self, tmp_path):
        """Test TypeScript detection from tsconfig.json without package.json deps."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "tsconfig.json").write_text('{"compilerOptions": {}}')

        info = detect_project_type(project)

        assert info.has_typescript is True
        assert any("tsconfig.json" in note for note in info.detection_notes)

    def test_fullstack_project_detection(self, fullstack_project):
        """Test fullstack project with both Python and Node.js."""
        info = detect_project_type(fullstack_project)

        assert info.language == ProjectLanguage.FULLSTACK
        assert "Found package.json" in info.detection_notes
        assert any("pyproject.toml" in note for note in info.detection_notes)

    def test_nextjs_framework_from_config(self, nextjs_project):
        """Test Next.js framework detection from next.config.js."""
        info = detect_project_type(nextjs_project)

        assert info.framework == ProjectFramework.NEXTJS
        assert any("Next.js detected" in note for note in info.detection_notes)

    def test_nextjs_from_dependency(self, tmp_path):
        """Test Next.js detection from package.json dependency."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "next": "^14.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NEXTJS

    def test_django_from_manage_py(self, django_project):
        """Test Django detection from manage.py."""
        info = detect_project_type(django_project)

        assert info.framework == ProjectFramework.DJANGO
        assert any("Django detected" in note for note in info.detection_notes)

    def test_fastapi_from_pyproject(self, fastapi_project):
        """Test FastAPI detection from pyproject.toml."""
        info = detect_project_type(fastapi_project)

        assert info.framework == ProjectFramework.FASTAPI
        assert any("FastAPI detected" in note for note in info.detection_notes)

    def test_default_project_root(self):
        """Test using default project root (Path.cwd())."""
        with patch("solokit.adopt.project_detector.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/fake/path")

            # This will try to detect in a non-existent path
            # Should return UNKNOWN without errors
            with patch.object(Path, "exists", return_value=False):
                info = detect_project_type()

                assert info.language == ProjectLanguage.UNKNOWN

    def test_confidence_calculation(self, project_with_tools):
        """Test confidence score calculation."""
        info = detect_project_type(project_with_tools)

        # Should have high confidence with multiple detection signals
        assert info.confidence > 0.5
        # Has language, framework/tools, package manager
        assert len(info.detection_notes) >= 5


class TestPackageManagerDetection:
    """Tests for package manager detection."""

    def test_npm_from_package_lock(self, tmp_path):
        """Test npm detection from package-lock.json."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "package-lock.json").write_text("{}")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.NPM

    def test_yarn_from_lock(self, tmp_path):
        """Test yarn detection from yarn.lock."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "yarn.lock").write_text("")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.YARN

    def test_pnpm_from_lock(self, tmp_path):
        """Test pnpm detection from pnpm-lock.yaml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "pnpm-lock.yaml").write_text("")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.PNPM

    def test_npm_default_with_package_json(self, nodejs_project):
        """Test npm assumed when package.json exists without lock file."""
        info = detect_project_type(nodejs_project)

        assert info.package_manager == PackageManager.NPM
        assert any("npm assumed" in note for note in info.detection_notes)

    def test_poetry_from_lock(self, tmp_path):
        """Test poetry detection from poetry.lock."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[tool.poetry]")
        (project / "poetry.lock").write_text("")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.POETRY

    def test_uv_from_lock(self, tmp_path):
        """Test uv detection from uv.lock."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / "uv.lock").write_text("")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.UV

    def test_pipenv_from_lock(self, tmp_path):
        """Test pipenv detection from Pipfile.lock."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "Pipfile").write_text("")
        (project / "Pipfile.lock").write_text("")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.PIPENV

    def test_pip_from_requirements(self, tmp_path):
        """Test pip detection from requirements.txt."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements.txt").write_text("flask==2.0.0")

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.PIP

    def test_poetry_from_pyproject_content(self, tmp_path):
        """Test poetry detection from pyproject.toml [tool.poetry] section."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[tool.poetry]
name = "test"
version = "0.1.0"
        """)

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.POETRY

    def test_uv_from_pyproject_content(self, tmp_path):
        """Test uv detection from pyproject.toml [tool.uv] section."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"

[tool.uv]
dev-dependencies = []
        """)

        info = detect_project_type(project)

        assert info.package_manager == PackageManager.UV

    def test_fullstack_package_managers(self, project_with_lock_files):
        """Test package manager detection for fullstack projects."""
        info = detect_project_type(project_with_lock_files)

        assert info.language == ProjectLanguage.FULLSTACK
        assert info.package_manager_node == PackageManager.YARN
        assert info.package_manager_python == PackageManager.POETRY


class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_nextjs_config_mjs(self, tmp_path):
        """Test Next.js detection from next.config.mjs."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "next.config.mjs").write_text("export default {};")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NEXTJS

    def test_nextjs_config_ts(self, tmp_path):
        """Test Next.js detection from next.config.ts."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "next.config.ts").write_text("export default {};")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NEXTJS

    def test_nuxt_detection(self, tmp_path):
        """Test Nuxt.js detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "nuxt.config.js").write_text("export default {};")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NUXT

    def test_vue_detection(self, tmp_path):
        """Test Vue.js detection from dependencies."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "vue": "^3.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.VUE

    def test_react_standalone_detection(self, tmp_path):
        """Test React detection (not Next.js)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "react": "^18.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.REACT

    def test_express_detection(self, tmp_path):
        """Test Express.js detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "express": "^4.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.EXPRESS

    def test_fastify_detection(self, tmp_path):
        """Test Fastify detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "fastify": "^4.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.FASTIFY

    def test_nestjs_detection(self, tmp_path):
        """Test NestJS detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("""
{
    "name": "test",
    "dependencies": {
        "@nestjs/core": "^10.0.0"
    }
}
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NESTJS

    def test_flask_from_requirements(self, tmp_path):
        """Test Flask detection from requirements.txt."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements.txt").write_text("flask==2.0.0\n")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.FLASK

    def test_django_from_requirements(self, tmp_path):
        """Test Django detection from requirements.txt."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements.txt").write_text("django==4.0.0\n")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.DJANGO

    def test_starlette_detection(self, tmp_path):
        """Test Starlette detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"
dependencies = ["starlette"]
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.STARLETTE

    def test_flask_from_pyproject(self, tmp_path):
        """Test Flask detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"
dependencies = ["flask>=2.0.0"]
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.FLASK
        assert any("Flask detected" in note for note in info.detection_notes)

    def test_django_from_pyproject(self, tmp_path):
        """Test Django detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"
dependencies = ["django>=4.0.0"]
        """)

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.DJANGO
        assert any("Django detected" in note for note in info.detection_notes)

    def test_fastapi_from_requirements(self, tmp_path):
        """Test FastAPI detection from requirements.txt."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "requirements.txt").write_text("fastapi>=0.100.0\nuvicorn\n")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.FASTAPI
        assert any("FastAPI detected" in note for note in info.detection_notes)

    def test_pyproject_read_error_handled(self, tmp_path):
        """Test that OSError when reading pyproject.toml is handled gracefully."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname = 'test'")

        with patch.object(Path, "read_text", side_effect=OSError("Cannot read")):
            # Should not raise exception
            info = detect_project_type(project)
            assert info is not None

    def test_requirements_read_error_handled(self, tmp_path):
        """Test that OSError when reading requirements.txt is handled gracefully."""
        project = tmp_path / "project"
        project.mkdir()
        pyproject = project / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'")
        requirements = project / "requirements.txt"
        requirements.write_text("flask")

        # Mock only the requirements.txt read to fail
        original_read = Path.read_text

        def mock_read(self):
            if "requirements.txt" in str(self):
                raise OSError("Cannot read")
            return original_read(self)

        with patch.object(Path, "read_text", mock_read):
            # Should not raise exception
            info = detect_project_type(project)
            assert info is not None

    def test_nuxt_config_ts(self, tmp_path):
        """Test Nuxt.js detection from nuxt.config.ts."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "nuxt.config.ts").write_text("export default {};")

        info = detect_project_type(project)

        assert info.framework == ProjectFramework.NUXT

    def test_malformed_package_json_no_crash(self, tmp_path):
        """Test that malformed package.json doesn't crash detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text("{ invalid json")

        # Should not raise exception
        info = detect_project_type(project)

        assert info.language == ProjectLanguage.NODEJS


class TestExistingToolingDetection:
    """Tests for existing tooling detection."""

    def test_eslint_detection(self, tmp_path):
        """Test ESLint detection from config files."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / ".eslintrc.json").write_text("{}")

        info = detect_project_type(project)

        assert info.tooling.linter == "eslint"

    def test_eslint_various_configs(self, tmp_path):
        """Test ESLint detection from various config file formats."""
        configs = [
            ".eslintrc.js",
            ".eslintrc.cjs",
            ".eslintrc.yml",
            "eslint.config.js",
            "eslint.config.mjs",
        ]

        for config_file in configs:
            project = tmp_path / f"project-{config_file}"
            project.mkdir()
            (project / "package.json").write_text('{"name": "test"}')
            (project / config_file).write_text("")

            info = detect_project_type(project)

            assert info.tooling.linter == "eslint", f"Failed for {config_file}"

    def test_ruff_detection_from_pyproject(self, tmp_path):
        """Test Ruff detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"

[tool.ruff]
line-length = 88
        """)

        info = detect_project_type(project)

        assert info.tooling.linter == "ruff"

    def test_ruff_detection_from_ruff_toml(self, tmp_path):
        """Test Ruff detection from ruff.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / "ruff.toml").write_text("line-length = 88")

        info = detect_project_type(project)

        assert info.tooling.linter == "ruff"

    def test_prettier_detection(self, tmp_path):
        """Test Prettier detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / ".prettierrc").write_text('{"semi": true}')

        info = detect_project_type(project)

        assert info.tooling.formatter == "prettier"

    def test_black_detection(self, tmp_path):
        """Test Black formatter detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"

[tool.black]
line-length = 88
        """)

        info = detect_project_type(project)

        assert info.tooling.formatter == "black"

    def test_typescript_type_checker(self, typescript_project):
        """Test TypeScript type checker detection."""
        info = detect_project_type(typescript_project)

        assert info.tooling.type_checker == "typescript"

    def test_mypy_detection_from_pyproject(self, tmp_path):
        """Test Mypy detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"

[tool.mypy]
python_version = "3.11"
        """)

        info = detect_project_type(project)

        assert info.tooling.type_checker == "mypy"

    def test_mypy_detection_from_mypy_ini(self, tmp_path):
        """Test Mypy detection from mypy.ini."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / "mypy.ini").write_text("[mypy]\npython_version = 3.11")

        info = detect_project_type(project)

        assert info.tooling.type_checker == "mypy"

    def test_jest_detection(self, tmp_path):
        """Test Jest test framework detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "jest.config.js").write_text("module.exports = {};")

        info = detect_project_type(project)

        assert info.tooling.test_framework == "jest"

    def test_vitest_detection(self, tmp_path):
        """Test Vitest detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "vitest.config.ts").write_text("export default {};")

        info = detect_project_type(project)

        assert info.tooling.test_framework == "vitest"

    def test_pytest_detection_from_pyproject(self, tmp_path):
        """Test Pytest detection from pyproject.toml."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("""
[project]
name = "test"

[tool.pytest.ini_options]
testpaths = ["tests"]
        """)

        info = detect_project_type(project)

        assert info.tooling.test_framework == "pytest"

    def test_pytest_detection_from_pytest_ini(self, tmp_path):
        """Test Pytest detection from pytest.ini."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / "pytest.ini").write_text("[pytest]\ntestpaths = tests")

        info = detect_project_type(project)

        assert info.tooling.test_framework == "pytest"

    def test_pytest_detection_from_conftest(self, tmp_path):
        """Test Pytest detection from conftest.py."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / "conftest.py").write_text("import pytest")

        info = detect_project_type(project)

        assert info.tooling.test_framework == "pytest"

    def test_test_directory_detection(self, tmp_path):
        """Test test directory detection."""
        for test_dir in ["tests", "__tests__", "test", "spec"]:
            project = tmp_path / f"project-{test_dir}"
            project.mkdir()
            (project / "pyproject.toml").write_text("[project]\nname='test'")
            (project / test_dir).mkdir()

            info = detect_project_type(project)

            assert info.tooling.test_directory == test_dir, f"Failed for {test_dir}"

    def test_pre_commit_detection(self, tmp_path):
        """Test pre-commit hooks detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / ".pre-commit-config.yaml").write_text("repos: []")

        info = detect_project_type(project)

        assert info.tooling.has_pre_commit is True

    def test_husky_detection(self, tmp_path):
        """Test Husky detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / ".husky").mkdir()

        info = detect_project_type(project)

        assert info.tooling.has_husky is True

    def test_github_actions_detection(self, tmp_path):
        """Test GitHub Actions CI detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        workflows = project / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: CI")

        info = detect_project_type(project)

        assert info.tooling.has_ci is True
        assert info.tooling.ci_provider == "github"

    def test_gitlab_ci_detection(self, tmp_path):
        """Test GitLab CI detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / ".gitlab-ci.yml").write_text("stages: [test]")

        info = detect_project_type(project)

        assert info.tooling.has_ci is True
        assert info.tooling.ci_provider == "gitlab"

    def test_circleci_detection(self, tmp_path):
        """Test CircleCI detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "pyproject.toml").write_text("[project]\nname='test'")
        (project / ".circleci").mkdir()

        info = detect_project_type(project)

        assert info.tooling.has_ci is True
        assert info.tooling.ci_provider == "circleci"


class TestDocumentationDetection:
    """Tests for documentation file detection."""

    def test_readme_detection_standard_case(self, tmp_path):
        """Test README.md detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "README.md").write_text("# Project")

        info = detect_project_type(project)

        assert info.has_readme is True

    def test_readme_detection_lowercase(self, tmp_path):
        """Test readme.md detection (lowercase)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "readme.md").write_text("# Project")

        info = detect_project_type(project)

        assert info.has_readme is True

    def test_readme_detection_uppercase_extension(self, tmp_path):
        """Test README.MD detection (uppercase extension)."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "README.MD").write_text("# Project")

        info = detect_project_type(project)

        assert info.has_readme is True

    def test_claude_md_detection(self, tmp_path):
        """Test CLAUDE.md detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "CLAUDE.md").write_text("# Claude Guidelines")

        info = detect_project_type(project)

        assert info.has_claude_md is True

    def test_architecture_md_detection(self, tmp_path):
        """Test ARCHITECTURE.md detection."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "ARCHITECTURE.md").write_text("# Architecture")

        info = detect_project_type(project)

        assert info.has_architecture_md is True

    def test_no_documentation_files(self, empty_project):
        """Test when no documentation files exist."""
        info = detect_project_type(empty_project)

        assert info.has_readme is False
        assert info.has_claude_md is False
        assert info.has_architecture_md is False


class TestFallbackExtensionDetection:
    """Tests for fallback file extension detection."""

    def test_python_from_extensions(self, tmp_path):
        """Test Python detection from .py file extensions."""
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")
        (src / "utils.py").write_text("# utils")

        info = detect_project_type(project)

        assert info.language == ProjectLanguage.PYTHON
        assert any(".py files" in note for note in info.detection_notes)

    def test_nodejs_from_extensions(self, tmp_path):
        """Test Node.js detection from .js file extensions."""
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "index.js").write_text("console.log('hello');")
        (src / "utils.js").write_text("// utils")

        info = detect_project_type(project)

        assert info.language == ProjectLanguage.NODEJS
        assert any(".js/.jsx files" in note for note in info.detection_notes)

    def test_typescript_from_extensions(self, tmp_path):
        """Test TypeScript detection from .ts file extensions."""
        project = tmp_path / "project"
        project.mkdir()
        src = project / "src"
        src.mkdir()
        (src / "index.ts").write_text("console.log('hello');")
        (src / "utils.ts").write_text("// utils")
        (src / "component.tsx").write_text("export {};")

        info = detect_project_type(project)

        assert info.language == ProjectLanguage.TYPESCRIPT
        assert info.has_typescript is True

    def test_fullstack_from_extensions(self, project_with_extensions):
        """Test fullstack detection from mixed file extensions."""
        info = detect_project_type(project_with_extensions)

        assert info.language == ProjectLanguage.FULLSTACK
        assert any("Fullstack detected from extensions" in note for note in info.detection_notes)

    def test_skips_hidden_directories(self, tmp_path):
        """Test that hidden directories are skipped in extension detection."""
        project = tmp_path / "project"
        project.mkdir()

        # Create hidden directory with Python files
        hidden = project / ".hidden"
        hidden.mkdir()
        (hidden / "ignored.py").write_text("# Should be ignored")

        # Create JS file in main directory
        (project / "index.js").write_text("console.log('test');")

        info = detect_project_type(project)

        # Should detect JS, not Python from hidden directory
        assert info.language == ProjectLanguage.NODEJS

    def test_skips_node_modules(self, tmp_path):
        """Test that node_modules directory is skipped."""
        project = tmp_path / "project"
        project.mkdir()

        # Create node_modules with lots of files
        nm = project / "node_modules"
        nm.mkdir()
        (nm / "package.js").write_text("// Should be ignored")

        # Create Python file in main directory
        (project / "main.py").write_text("print('test')")

        info = detect_project_type(project)

        # Should detect Python, not JS from node_modules
        assert info.language == ProjectLanguage.PYTHON

    def test_skips_common_build_directories(self, tmp_path):
        """Test that common build directories are skipped."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.py").write_text("print('test')")

        # Create build directories
        for dirname in ["venv", ".venv", "__pycache__", "dist", "build"]:
            dir_path = project / dirname
            dir_path.mkdir()
            (dir_path / "ignored.py").write_text("# Should be ignored")

        info = detect_project_type(project)

        # Should only count main.py
        assert info.language == ProjectLanguage.PYTHON


class TestGetProjectSummary:
    """Tests for get_project_summary() function."""

    def test_summary_includes_language(self, nodejs_project):
        """Test that summary includes language."""
        info = detect_project_type(nodejs_project)
        summary = get_project_summary(info)

        assert "Language: nodejs" in summary

    def test_summary_includes_typescript_flag(self, typescript_project):
        """Test that summary includes TypeScript flag when present."""
        info = detect_project_type(typescript_project)
        summary = get_project_summary(info)

        assert "TypeScript: Yes" in summary

    def test_summary_includes_framework(self, nextjs_project):
        """Test that summary includes framework."""
        info = detect_project_type(nextjs_project)
        summary = get_project_summary(info)

        assert "Framework: nextjs" in summary

    def test_summary_includes_package_manager(self, tmp_path):
        """Test that summary includes package manager."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name": "test"}')
        (project / "yarn.lock").write_text("")

        info = detect_project_type(project)
        summary = get_project_summary(info)

        assert "Package Manager: yarn" in summary

    def test_summary_fullstack_package_managers(self, project_with_lock_files):
        """Test summary for fullstack project with separate package managers."""
        info = detect_project_type(project_with_lock_files)
        summary = get_project_summary(info)

        assert "Node Package Manager: yarn" in summary
        assert "Python Package Manager: poetry" in summary

    def test_summary_includes_tooling(self, project_with_tools):
        """Test that summary includes detected tooling."""
        info = detect_project_type(project_with_tools)
        summary = get_project_summary(info)

        assert "Linter:" in summary
        assert "Formatter:" in summary
        assert "Test Framework:" in summary

    def test_summary_includes_confidence(self, nodejs_project):
        """Test that summary includes confidence score."""
        info = detect_project_type(nodejs_project)
        summary = get_project_summary(info)

        assert "Confidence:" in summary
        assert "%" in summary


class TestEnumClasses:
    """Tests for enum classes."""

    def test_project_language_values(self):
        """Test ProjectLanguage.values() returns all valid values."""
        values = ProjectLanguage.values()

        assert "python" in values
        assert "nodejs" in values
        assert "typescript" in values
        assert "fullstack" in values
        assert "unknown" in values

    def test_project_language_str(self):
        """Test ProjectLanguage string representation."""
        assert str(ProjectLanguage.PYTHON) == "python"
        assert str(ProjectLanguage.NODEJS) == "nodejs"

    def test_project_framework_values(self):
        """Test ProjectFramework.values() returns all valid values."""
        values = ProjectFramework.values()

        assert "nextjs" in values
        assert "django" in values
        assert "fastapi" in values
        assert "none" in values

    def test_package_manager_values(self):
        """Test PackageManager.values() returns all valid values."""
        values = PackageManager.values()

        assert "npm" in values
        assert "yarn" in values
        assert "pnpm" in values
        assert "pip" in values
        assert "poetry" in values
        assert "uv" in values


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_zero_confidence_for_unknown(self, empty_project):
        """Test zero confidence for unknown project."""
        info = detect_project_type(empty_project)

        # Should have low confidence with no detection signals
        assert info.confidence < 0.5

    def test_high_confidence_with_multiple_signals(self, project_with_tools):
        """Test high confidence with multiple detection signals."""
        info = detect_project_type(project_with_tools)

        # Should have high confidence
        assert info.confidence > 0.7

    def test_confidence_includes_language_detection(self, nodejs_project):
        """Test that language detection contributes to confidence."""
        info = detect_project_type(nodejs_project)

        # Should have at least 0.3 for language detection
        assert info.confidence >= 0.3

    def test_confidence_caps_at_100_percent(self):
        """Test that confidence never exceeds 1.0."""
        # Create a project with maximum detection signals
        info = ProjectInfo(
            language=ProjectLanguage.TYPESCRIPT,
            framework=ProjectFramework.NEXTJS,
            package_manager=PackageManager.PNPM,
            tooling=ExistingTooling(
                linter="eslint",
                formatter="prettier",
                test_framework="jest",
            ),
            detection_notes=["note"] * 10,  # Many notes
        )

        # Manually calculate confidence
        from solokit.adopt.project_detector import _calculate_confidence

        _calculate_confidence(info)

        assert info.confidence <= 1.0
