"""
Tests for merge_strategies module.

Validates smart merge strategies for config files during adoption.

Run tests:
    pytest tests/unit/adopt/test_merge_strategies.py -v

Target: 95%+ coverage
"""

# Check if tomli_w is available
import importlib.util
import json

import pytest
import yaml

from solokit.adopt.merge_strategies import (
    MERGE_FUNCTIONS,
    get_mergeable_files,
    merge_config_file,
    merge_eslint_config,
    merge_husky_pre_commit,
    merge_package_json,
    merge_pre_commit_config,
    merge_prettierrc,
    merge_pyproject_toml,
    merge_requirements_txt,
)

TOMLI_W_AVAILABLE = importlib.util.find_spec("tomli_w") is not None


class TestMergePackageJson:
    """Tests for merge_package_json() function."""

    def test_merges_dev_dependencies(self, temp_project):
        """Test that devDependencies are merged without overwriting."""
        existing = temp_project / "package.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "my-project",
                    "version": "1.0.0",
                    "devDependencies": {"existing-pkg": "^1.0.0"},
                }
            )
        )

        solokit_content = json.dumps(
            {
                "devDependencies": {
                    "new-pkg": "^2.0.0",
                    "another-pkg": "^3.0.0",
                }
            }
        )

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        assert "existing-pkg" in merged["devDependencies"]
        assert "new-pkg" in merged["devDependencies"]
        assert "another-pkg" in merged["devDependencies"]
        assert merged["devDependencies"]["existing-pkg"] == "^1.0.0"

    def test_keeps_existing_versions_in_dev_dependencies(self, temp_project):
        """Test that existing package versions are not overwritten."""
        existing = temp_project / "package.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "my-project",
                    "devDependencies": {"typescript": "^5.0.0"},
                }
            )
        )

        solokit_content = json.dumps({"devDependencies": {"typescript": "^4.0.0"}})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        # Should keep existing version
        assert merged["devDependencies"]["typescript"] == "^5.0.0"

    def test_merges_scripts(self, temp_project):
        """Test that scripts are merged without overwriting."""
        existing = temp_project / "package.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "my-project",
                    "scripts": {"build": "custom build command"},
                }
            )
        )

        solokit_content = json.dumps(
            {
                "scripts": {
                    "test": "jest",
                    "lint": "eslint .",
                }
            }
        )

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        assert "build" in merged["scripts"]
        assert "test" in merged["scripts"]
        assert "lint" in merged["scripts"]
        assert merged["scripts"]["build"] == "custom build command"

    def test_keeps_existing_scripts(self, temp_project):
        """Test that existing scripts are not overwritten."""
        existing = temp_project / "package.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "my-project",
                    "scripts": {"test": "my-custom-test"},
                }
            )
        )

        solokit_content = json.dumps({"scripts": {"test": "jest"}})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        # Should keep existing script
        assert merged["scripts"]["test"] == "my-custom-test"

    def test_preserves_all_existing_fields(self, temp_project):
        """Test that all existing fields are preserved."""
        existing = temp_project / "package.json"
        existing.write_text(
            json.dumps(
                {
                    "name": "my-project",
                    "version": "2.5.0",
                    "description": "My awesome project",
                    "author": "Test Author",
                    "license": "MIT",
                    "dependencies": {"react": "^18.0.0"},
                    "workspaces": ["packages/*"],
                }
            )
        )

        solokit_content = json.dumps({"devDependencies": {"jest": "^29.0.0"}})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        assert merged["name"] == "my-project"
        assert merged["version"] == "2.5.0"
        assert merged["description"] == "My awesome project"
        assert merged["author"] == "Test Author"
        assert merged["license"] == "MIT"
        assert merged["dependencies"] == {"react": "^18.0.0"}
        assert merged["workspaces"] == ["packages/*"]

    def test_creates_dev_dependencies_if_missing(self, temp_project):
        """Test that devDependencies section is created if missing."""
        existing = temp_project / "package.json"
        existing.write_text(json.dumps({"name": "my-project"}))

        solokit_content = json.dumps({"devDependencies": {"jest": "^29.0.0"}})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        assert "devDependencies" in merged
        assert merged["devDependencies"]["jest"] == "^29.0.0"

    def test_creates_scripts_if_missing(self, temp_project):
        """Test that scripts section is created if missing."""
        existing = temp_project / "package.json"
        existing.write_text(json.dumps({"name": "my-project"}))

        solokit_content = json.dumps({"scripts": {"test": "jest"}})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        assert "scripts" in merged
        assert merged["scripts"]["test"] == "jest"

    def test_preserves_json_formatting(self, temp_project):
        """Test that output uses 2-space indentation and trailing newline."""
        existing = temp_project / "package.json"
        existing.write_text(json.dumps({"name": "my-project"}))

        solokit_content = json.dumps({"devDependencies": {"jest": "^29.0.0"}})

        result = merge_package_json(existing, solokit_content)

        # Should have 2-space indentation
        assert '  "name"' in result
        # Should end with newline
        assert result.endswith("\n")

    def test_empty_solokit_content(self, temp_project):
        """Test merging with empty Solokit content."""
        existing = temp_project / "package.json"
        existing.write_text(json.dumps({"name": "my-project", "version": "1.0.0"}))

        solokit_content = json.dumps({})

        result = merge_package_json(existing, solokit_content)
        merged = json.loads(result)

        # Should preserve existing content
        assert merged["name"] == "my-project"
        assert merged["version"] == "1.0.0"


class TestMergePyprojectToml:
    """Tests for merge_pyproject_toml() function."""

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_merges_dev_dependencies(self, temp_project):
        """Test that dev dependencies are merged."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["ruff>=0.1.0", "mypy>=1.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should include both existing and new
        assert "pytest>=7.0.0" in result
        assert "ruff>=0.1.0" in result
        assert "mypy>=1.0.0" in result

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_avoids_duplicate_packages(self, temp_project):
        """Test that duplicate packages are not added."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=8.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should keep existing pytest version, not add duplicate
        assert result.count("pytest") == 1
        assert "pytest>=7.0.0" in result

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_handles_package_name_case_insensitively(self, temp_project):
        """Test that package names are matched case-insensitively."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[project.optional-dependencies]
dev = ["PyTest>=7.0.0"]
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=8.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should recognize PyTest and pytest as same package (case-insensitive)
        # Only the existing PyTest should be present, not a duplicate pytest
        assert result.lower().count("pytest") == 1

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_merges_tool_sections(self, temp_project):
        """Test that tool.* sections are merged."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[tool.mypy]
python_version = "3.11"
"""
        )

        solokit_content = """
[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should include all tool sections
        assert "[tool.mypy]" in result
        assert "[tool.ruff]" in result
        assert "[tool.pytest.ini_options]" in result

    def test_does_not_overwrite_existing_tool_sections(self, temp_project):
        """Test that existing tool sections are not overwritten."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[tool.ruff]
line-length = 88
custom-setting = "value"
"""
        )

        solokit_content = """
[tool.ruff]
line-length = 100
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should keep existing tool.ruff, not add duplicate
        assert result.count("[tool.ruff]") == 1
        assert "line-length = 88" in result
        assert "custom-setting" in result

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_creates_project_section_if_missing(self, temp_project):
        """Test that project section is created if missing."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[build-system]
requires = ["setuptools"]
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # tomli_w writes nested sections directly without parent header
        assert "[project.optional-dependencies]" in result
        assert "pytest>=7.0.0" in result

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_creates_optional_dependencies_if_missing(self, temp_project):
        """Test that optional-dependencies is created if missing."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        assert "[project.optional-dependencies]" in result or "optional-dependencies" in result
        assert "pytest>=7.0.0" in result

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_preserves_build_system(self, temp_project):
        """Test that build-system section is preserved."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        assert "[build-system]" in result
        assert "setuptools>=65.0" in result

    def test_handles_missing_tomli_w(self, temp_project, monkeypatch):
        """Test graceful handling when tomli_w is not available."""
        existing = temp_project / "pyproject.toml"
        existing_content = """
[project]
name = "my-project"
"""
        existing.write_text(existing_content)

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""

        # Temporarily remove tomli_w from sys.modules to simulate it not being installed
        import sys

        tomli_w_backup = sys.modules.get("tomli_w")
        if "tomli_w" in sys.modules:
            del sys.modules["tomli_w"]

        try:
            # Patch the import to raise ImportError
            import builtins

            real_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "tomli_w":
                    raise ImportError("No module named tomli_w")
                return real_import(name, *args, **kwargs)

            monkeypatch.setattr(builtins, "__import__", mock_import)

            # Should return existing content unchanged
            result = merge_pyproject_toml(existing, solokit_content)
            assert result == existing_content
        finally:
            # Restore tomli_w if it was there
            if tomli_w_backup:
                sys.modules["tomli_w"] = tomli_w_backup

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_handles_version_specifiers(self, temp_project):
        """Test handling various version specifiers."""
        existing = temp_project / "pyproject.toml"
        existing.write_text(
            """
[project]
name = "my-project"

[project.optional-dependencies]
dev = ["pytest>=7.0.0,<8.0.0", "black[jupyter]~=23.0"]
"""
        )

        solokit_content = """
[project.optional-dependencies]
dev = ["pytest>=8.0.0", "ruff>=0.1.0"]
"""

        result = merge_pyproject_toml(existing, solokit_content)

        # Should not add duplicate pytest
        assert "pytest>=7.0.0,<8.0.0" in result
        assert "black[jupyter]~=23.0" in result
        assert "ruff>=0.1.0" in result


class TestMergeEslintConfig:
    """Tests for merge_eslint_config() function."""

    def test_appends_solokit_rules_to_array_export(self, temp_project):
        """Test appending rules to array-based export."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    rules: {
      'no-console': 'warn',
    },
  },
];
"""
        )

        solokit_content = """
export default [
  {
    rules: {
      'no-unused-vars': 'error',
      'prefer-const': 'error',
    },
  },
];
"""

        result = merge_eslint_config(existing, solokit_content)

        assert "solokitRules" in result
        assert "no-unused-vars" in result
        assert "prefer-const" in result
        assert "no-console" in result
        assert "Solokit quality rules" in result

    def test_skips_if_already_merged(self, temp_project):
        """Test that merge is skipped if Solokit rules already present."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
// Solokit quality rules
const solokitRules = {
  rules: {
    'no-unused-vars': 'error',
  },
};

export default [solokitRules];
"""
        )

        solokit_content = """
export default [
  {
    rules: {
      'prefer-const': 'error',
    },
  },
];
"""

        result = merge_eslint_config(existing, solokit_content)

        # Should return unchanged
        assert result == existing.read_text()
        # Should not have duplicate rules
        assert result.count("Solokit quality rules") == 1

    def test_handles_typescript_eslint_config_format(self, temp_project):
        """Test handling TypeScript ESLint config format."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist'] },
  {
    rules: {
      'no-console': 'warn',
    },
  }
);
"""
        )

        solokit_content = """
export default [
  {
    rules: {
      'no-unused-vars': 'error',
    },
  },
];
"""

        result = merge_eslint_config(existing, solokit_content)

        assert "solokitRules" in result
        assert "no-unused-vars" in result

    def test_fallback_when_cannot_parse_export(self, temp_project):
        """Test fallback to comment when export format is unrecognized."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
// Complex custom config
module.exports = customFunction();
"""
        )

        solokit_content = """
export default [
  {
    rules: {
      'no-unused-vars': 'error',
    },
  },
];
"""

        result = merge_eslint_config(existing, solokit_content)

        # Should append as comment with instructions
        assert "Solokit Quality Rules" in result
        assert "Add the following rules" in result
        assert "no-unused-vars" in result

    def test_handles_missing_rules_in_template(self, temp_project):
        """Test handling when Solokit template has no rules."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
export default [
  {
    rules: {
      'no-console': 'warn',
    },
  },
];
"""
        )

        solokit_content = """
export default [
  { ignores: ['dist'] }
];
"""

        result = merge_eslint_config(existing, solokit_content)

        # Should return existing unchanged (no rules to merge)
        assert result == existing.read_text()

    def test_preserves_existing_rules(self, temp_project):
        """Test that existing rules are preserved."""
        existing = temp_project / "eslint.config.mjs"
        existing.write_text(
            """
export default [
  {
    rules: {
      'no-console': 'warn',
      'no-debugger': 'error',
    },
  },
];
"""
        )

        solokit_content = """
export default [
  {
    rules: {
      'no-unused-vars': 'error',
    },
  },
];
"""

        result = merge_eslint_config(existing, solokit_content)

        assert "no-console" in result
        assert "no-debugger" in result
        assert "no-unused-vars" in result


class TestMergePrettierrc:
    """Tests for merge_prettierrc() function."""

    def test_adds_missing_options(self, temp_project):
        """Test that missing options are added."""
        existing = temp_project / ".prettierrc"
        existing.write_text(
            json.dumps(
                {
                    "semi": True,
                    "singleQuote": False,
                }
            )
        )

        solokit_content = json.dumps(
            {
                "semi": False,
                "tabWidth": 2,
                "printWidth": 100,
            }
        )

        result = merge_prettierrc(existing, solokit_content)
        merged = json.loads(result)

        assert merged["semi"] is True  # Keep existing
        assert merged["singleQuote"] is False  # Keep existing
        assert merged["tabWidth"] == 2  # Add missing
        assert merged["printWidth"] == 100  # Add missing

    def test_preserves_existing_options(self, temp_project):
        """Test that existing options are not overwritten."""
        existing = temp_project / ".prettierrc"
        existing.write_text(
            json.dumps(
                {
                    "printWidth": 80,
                    "tabWidth": 4,
                }
            )
        )

        solokit_content = json.dumps(
            {
                "printWidth": 100,
                "tabWidth": 2,
            }
        )

        result = merge_prettierrc(existing, solokit_content)
        merged = json.loads(result)

        # Should keep existing values
        assert merged["printWidth"] == 80
        assert merged["tabWidth"] == 4

    def test_handles_non_json_format(self, temp_project):
        """Test handling when .prettierrc is not JSON."""
        existing = temp_project / ".prettierrc"
        existing.write_text(
            """
module.exports = {
  semi: true
};
"""
        )

        solokit_content = json.dumps({"tabWidth": 2})

        result = merge_prettierrc(existing, solokit_content)

        # Should return existing content unchanged
        assert result == existing.read_text()

    def test_handles_invalid_json(self, temp_project):
        """Test handling when existing JSON is invalid."""
        existing = temp_project / ".prettierrc"
        existing.write_text('{ "semi": true, }')  # Invalid JSON (trailing comma)

        solokit_content = json.dumps({"tabWidth": 2})

        result = merge_prettierrc(existing, solokit_content)

        # Should return existing content unchanged
        assert result == existing.read_text()

    def test_handles_invalid_solokit_json(self, temp_project):
        """Test handling when Solokit JSON is invalid."""
        existing = temp_project / ".prettierrc"
        existing.write_text(json.dumps({"semi": True}))

        solokit_content = "{ invalid json }"

        result = merge_prettierrc(existing, solokit_content)

        # Should return existing content unchanged
        assert result == existing.read_text()

    def test_preserves_json_formatting(self, temp_project):
        """Test that output uses 2-space indentation."""
        existing = temp_project / ".prettierrc"
        existing.write_text(json.dumps({"semi": True}))

        solokit_content = json.dumps({"tabWidth": 2})

        result = merge_prettierrc(existing, solokit_content)

        assert '  "semi"' in result
        assert result.endswith("\n")


class TestMergePreCommitConfig:
    """Tests for merge_pre_commit_config() function."""

    def test_adds_missing_repos(self, temp_project):
        """Test that missing repos are added."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text(
            yaml.dump(
                {
                    "repos": [
                        {
                            "repo": "https://github.com/pre-commit/pre-commit-hooks",
                            "rev": "v4.0.0",
                            "hooks": [{"id": "trailing-whitespace"}],
                        }
                    ]
                }
            )
        )

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                        "hooks": [{"id": "ruff"}],
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        # Should include both repos
        assert "pre-commit/pre-commit-hooks" in result
        assert "astral-sh/ruff-pre-commit" in result

    def test_avoids_duplicate_repos(self, temp_project):
        """Test that duplicate repos are not added."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text(
            yaml.dump(
                {
                    "repos": [
                        {
                            "repo": "https://github.com/astral-sh/ruff-pre-commit",
                            "rev": "v0.1.0",
                            "hooks": [{"id": "ruff"}],
                        }
                    ]
                }
            )
        )

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.2.0",
                        "hooks": [{"id": "ruff"}, {"id": "ruff-format"}],
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        # Should not duplicate the repo
        assert result.count("astral-sh/ruff-pre-commit") == 1

    def test_creates_repos_list_if_missing(self, temp_project):
        """Test that repos list is created if missing."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text(yaml.dump({}))

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                        "hooks": [{"id": "ruff"}],
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        assert "repos:" in result
        assert "astral-sh/ruff-pre-commit" in result

    def test_handles_empty_existing_file(self, temp_project):
        """Test handling empty existing config."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text("")

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                        "hooks": [{"id": "ruff"}],
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        assert "repos:" in result
        assert "astral-sh/ruff-pre-commit" in result

    def test_preserves_existing_repo_order(self, temp_project):
        """Test that existing repos come before new ones."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text(
            yaml.dump(
                {
                    "repos": [
                        {
                            "repo": "https://github.com/pre-commit/pre-commit-hooks",
                            "rev": "v4.0.0",
                        }
                    ]
                }
            )
        )

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)
        merged = yaml.safe_load(result)

        # Existing repo should be first
        assert merged["repos"][0]["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
        assert merged["repos"][1]["repo"] == "https://github.com/astral-sh/ruff-pre-commit"

    def test_handles_invalid_repo_entries(self, temp_project):
        """Test handling repos list with invalid entries."""
        existing = temp_project / ".pre-commit-config.yaml"
        existing.write_text(
            yaml.dump(
                {
                    "repos": [
                        "invalid entry",  # Not a dict
                        {
                            "repo": "https://github.com/pre-commit/pre-commit-hooks",
                            "rev": "v4.0.0",
                        },
                    ]
                }
            )
        )

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        # Should still work, adding the new repo
        assert "astral-sh/ruff-pre-commit" in result

    def test_handles_null_existing_config(self, temp_project):
        """Test handling when existing config is None/null."""
        existing = temp_project / ".pre-commit-config.yaml"
        # Write a yaml file that parses to None
        existing.write_text("---\n")

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        # Should create repos list
        assert "repos:" in result
        assert "astral-sh/ruff-pre-commit" in result

    def test_handles_config_without_repos_key(self, temp_project):
        """Test handling when existing config has no repos key."""
        existing = temp_project / ".pre-commit-config.yaml"
        # Write a config with other keys but no repos
        existing.write_text(yaml.dump({"fail_fast": True, "default_stages": ["commit"]}))

        solokit_content = yaml.dump(
            {
                "repos": [
                    {
                        "repo": "https://github.com/astral-sh/ruff-pre-commit",
                        "rev": "v0.1.0",
                    }
                ]
            }
        )

        result = merge_pre_commit_config(existing, solokit_content)

        # Should add repos list
        assert "repos:" in result
        assert "astral-sh/ruff-pre-commit" in result
        assert "fail_fast" in result


class TestMergeRequirementsTxt:
    """Tests for merge_requirements_txt() function."""

    def test_adds_missing_packages(self, temp_project):
        """Test that missing packages are added."""
        existing = temp_project / "requirements.txt"
        existing.write_text("flask==2.0.0\nrequests>=2.28.0\n")

        solokit_content = "pytest>=7.0.0\nruff>=0.1.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        assert "flask==2.0.0" in result
        assert "requests>=2.28.0" in result
        assert "pytest>=7.0.0" in result
        assert "ruff>=0.1.0" in result

    def test_avoids_duplicate_packages(self, temp_project):
        """Test that duplicate packages are not added."""
        existing = temp_project / "requirements.txt"
        existing.write_text("pytest==7.4.0\n")

        solokit_content = "pytest>=7.0.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        # Should not add duplicate pytest
        assert result.count("pytest") == 1
        assert "pytest==7.4.0" in result

    def test_handles_case_insensitive_package_names(self, temp_project):
        """Test that package names are matched case-insensitively."""
        existing = temp_project / "requirements.txt"
        existing.write_text("Django==4.2.0\n")

        solokit_content = "django>=4.0.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        # Should recognize Django and django as same package
        assert result.count("jango") == 1  # Case-insensitive

    def test_adds_solokit_comment_marker(self, temp_project):
        """Test that added packages have Solokit comment marker."""
        existing = temp_project / "requirements.txt"
        existing.write_text("flask==2.0.0\n")

        solokit_content = "pytest>=7.0.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        assert "# Added by Solokit" in result

    def test_handles_empty_existing_file(self, temp_project):
        """Test handling empty existing requirements.txt."""
        existing = temp_project / "requirements.txt"
        existing.write_text("")

        solokit_content = "pytest>=7.0.0\nruff>=0.1.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        assert "pytest>=7.0.0" in result
        assert "ruff>=0.1.0" in result
        assert "# Added by Solokit" in result

    def test_handles_comments_in_existing_file(self, temp_project):
        """Test that comments in existing file are preserved."""
        existing = temp_project / "requirements.txt"
        existing.write_text(
            """
# Production dependencies
flask==2.0.0
# Testing tools
pytest==7.4.0
"""
        )

        solokit_content = "ruff>=0.1.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        assert "# Production dependencies" in result
        assert "# Testing tools" in result
        assert "ruff>=0.1.0" in result

    def test_handles_package_extras(self, temp_project):
        """Test handling packages with extras."""
        existing = temp_project / "requirements.txt"
        existing.write_text("black[jupyter]==23.0.0\n")

        solokit_content = "black>=23.0.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        # Should recognize black[jupyter] and black as same package
        assert result.count("black") == 1

    def test_handles_version_specifiers(self, temp_project):
        """Test handling various version specifiers."""
        existing = temp_project / "requirements.txt"
        existing.write_text(
            """
package1>=1.0.0,<2.0.0
package2~=1.5.0
package3==1.2.3
"""
        )

        solokit_content = "package4>=2.0.0\npackage1>=1.5.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        # Should keep existing package1 version
        assert "package1>=1.0.0,<2.0.0" in result
        # Should add package4
        assert "package4>=2.0.0" in result

    def test_preserves_trailing_newline(self, temp_project):
        """Test that result ends with newline."""
        existing = temp_project / "requirements.txt"
        existing.write_text("flask==2.0.0\n")

        solokit_content = "pytest>=7.0.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        assert result.endswith("\n")

    def test_handles_no_new_packages_to_add(self, temp_project):
        """Test when all Solokit packages already exist."""
        existing = temp_project / "requirements.txt"
        existing.write_text("pytest>=7.0.0\nruff>=0.1.0\n")

        solokit_content = "pytest>=7.0.0\nruff>=0.1.0\n"

        result = merge_requirements_txt(existing, solokit_content)

        # Should return existing content unchanged
        assert result == existing.read_text()


class TestMergeHuskyPreCommit:
    """Tests for merge_husky_pre_commit() function."""

    def test_appends_missing_commands(self, temp_project):
        """Test that missing commands are appended."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint
"""
        )

        solokit_content = """#!/bin/sh
npm test
npm run type-check
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        assert "npm run lint" in result
        assert "npm test" in result
        assert "npm run type-check" in result
        assert "Solokit quality checks" in result

    def test_skips_existing_commands(self, temp_project):
        """Test that existing commands are not duplicated."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm test
npm run lint
"""
        )

        solokit_content = """#!/bin/sh
npm test
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        # Should not duplicate npm test
        assert result.count("npm test") == 1

    def test_skips_if_already_merged(self, temp_project):
        """Test that merge is skipped if Solokit commands already present."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm run lint

# Solokit quality checks - added by sk adopt
npm test
"""
        )

        solokit_content = """#!/bin/sh
npm run type-check
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        # Should return unchanged
        assert result == existing.read_text()

    def test_normalizes_command_comparison(self, temp_project):
        """Test that command comparison handles spacing variations."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm  run  lint
"""
        )

        solokit_content = """#!/bin/sh
npm run lint
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        # Should recognize as same command despite spacing
        assert result.count("lint") == 1

    def test_filters_shebang_and_comments(self, temp_project):
        """Test that shebang and comments are not added as commands."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm run lint
"""
        )

        solokit_content = """#!/bin/sh
# This is a comment
npm test
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        # Should add npm test but not comment or shebang
        assert "npm test" in result
        # Should not duplicate shebang or add comment as command
        assert result.count("#!/bin/sh") == 1

    def test_handles_empty_solokit_commands(self, temp_project):
        """Test handling when Solokit template has no commands."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm run lint
"""
        )

        solokit_content = """#!/bin/sh
# Only comments
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        # Should return existing unchanged
        assert result == existing.read_text()

    def test_adds_solokit_comment_marker(self, temp_project):
        """Test that added commands have Solokit comment marker."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
npm run lint
"""
        )

        solokit_content = """#!/bin/sh
npm test
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        assert "# Solokit quality checks - added by sk adopt" in result

    def test_preserves_existing_structure(self, temp_project):
        """Test that existing structure is preserved."""
        existing = temp_project / "pre-commit"
        existing.write_text(
            """#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run linting
npm run lint

# Run tests
npm test
"""
        )

        solokit_content = """#!/bin/sh
npm run type-check
"""

        result = merge_husky_pre_commit(existing, solokit_content)

        assert '. "$(dirname "$0")/_/husky.sh"' in result
        assert "# Run linting" in result
        assert "# Run tests" in result


class TestMergeConfigFile:
    """Tests for merge_config_file() dispatcher function."""

    def test_dispatches_package_json(self, temp_project):
        """Test that package.json is dispatched correctly."""
        existing = temp_project / "package.json"
        existing.write_text(json.dumps({"name": "test"}))

        solokit_content = json.dumps({"devDependencies": {"jest": "^29.0.0"}})

        result = merge_config_file("package.json", existing, solokit_content)

        merged = json.loads(result)
        assert "devDependencies" in merged
        assert merged["devDependencies"]["jest"] == "^29.0.0"

    @pytest.mark.skipif(not TOMLI_W_AVAILABLE, reason="tomli_w not installed")
    def test_dispatches_pyproject_toml(self, temp_project):
        """Test that pyproject.toml is dispatched correctly."""
        existing = temp_project / "pyproject.toml"
        existing.write_text("[project]\nname = 'test'")

        solokit_content = "[project.optional-dependencies]\ndev = ['pytest>=7.0.0']"

        result = merge_config_file("pyproject.toml", existing, solokit_content)

        assert "pytest>=7.0.0" in result

    def test_dispatches_with_path(self, temp_project):
        """Test dispatching with path like .husky/pre-commit."""
        existing = temp_project / "pre-commit"
        existing.write_text("#!/bin/sh\nnpm run lint\n")

        solokit_content = "#!/bin/sh\nnpm test\n"

        result = merge_config_file(".husky/pre-commit", existing, solokit_content)

        assert "npm test" in result

    def test_handles_unknown_file_type(self, temp_project):
        """Test handling unknown file type."""
        existing = temp_project / "unknown.config"
        existing.write_text("unknown content")

        solokit_content = "solokit content"

        result = merge_config_file("unknown.config", existing, solokit_content)

        # Should return existing content unchanged
        assert result == "unknown content"

    def test_handles_merge_exception(self, temp_project):
        """Test graceful handling when merge function raises exception."""
        existing = temp_project / "package.json"
        existing.write_text("invalid json {")

        solokit_content = json.dumps({"devDependencies": {}})

        # Should not raise exception
        result = merge_config_file("package.json", existing, solokit_content)

        # Should return existing content on error
        assert result == "invalid json {"

    def test_tries_basename_when_exact_match_fails(self, temp_project):
        """Test that basename is tried when exact match fails."""
        existing = temp_project / "pre-commit"
        existing.write_text("#!/bin/sh\nnpm run lint\n")

        solokit_content = "#!/bin/sh\nnpm test\n"

        # Use full path that's not in MERGE_FUNCTIONS
        result = merge_config_file("some/path/to/pre-commit", existing, solokit_content)

        # Should still work by matching basename
        assert "npm test" in result


class TestGetMergeableFiles:
    """Tests for get_mergeable_files() function."""

    def test_returns_set(self):
        """Test that function returns a set."""
        files = get_mergeable_files()
        assert isinstance(files, set)

    def test_includes_package_json(self):
        """Test that package.json is included."""
        files = get_mergeable_files()
        assert "package.json" in files

    def test_includes_pyproject_toml(self):
        """Test that pyproject.toml is included."""
        files = get_mergeable_files()
        assert "pyproject.toml" in files

    def test_includes_eslint_config(self):
        """Test that eslint.config.mjs is included."""
        files = get_mergeable_files()
        assert "eslint.config.mjs" in files

    def test_includes_prettierrc(self):
        """Test that .prettierrc is included."""
        files = get_mergeable_files()
        assert ".prettierrc" in files

    def test_includes_pre_commit_config(self):
        """Test that .pre-commit-config.yaml is included."""
        files = get_mergeable_files()
        assert ".pre-commit-config.yaml" in files

    def test_includes_requirements_txt(self):
        """Test that requirements.txt is included."""
        files = get_mergeable_files()
        assert "requirements.txt" in files

    def test_includes_husky_pre_commit(self):
        """Test that .husky/pre-commit is included."""
        files = get_mergeable_files()
        assert ".husky/pre-commit" in files or "pre-commit" in files

    def test_matches_merge_functions_keys(self):
        """Test that returned set matches MERGE_FUNCTIONS keys."""
        files = get_mergeable_files()
        assert files == set(MERGE_FUNCTIONS.keys())
