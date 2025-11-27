"""
Tests for scaffolding detection module.

Tests the minimal scaffolding detection functions.

Run tests:
    pytest tests/unit/quality/test_scaffolding.py -v

Target: 90%+ coverage
"""

import json

from solokit.quality.scaffolding import (
    has_e2e_test_files,
    has_integration_test_files,
    is_minimal_scaffolding,
)


class TestIsMinimalScaffolding:
    """Tests for is_minimal_scaffolding()."""

    def test_empty_project_is_minimal(self, tmp_path):
        """Test that an empty project is considered minimal scaffolding."""
        result = is_minimal_scaffolding(tmp_path)
        assert result is True

    def test_project_with_health_check_only(self, tmp_path):
        """Test project with only health check is minimal."""
        # Create minimal structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "health.py").write_text("def health(): return {'status': 'ok'}")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_health.py").write_text("def test_health(): pass")

        result = is_minimal_scaffolding(tmp_path)
        assert result is True

    def test_project_with_many_source_files_not_minimal(self, tmp_path):
        """Test project with many source files is not minimal."""
        src = tmp_path / "src"
        src.mkdir()

        # Create more than 5 substantial source files
        for i in range(10):
            (src / f"feature_{i}.py").write_text(f"def feature_{i}(): pass")

        result = is_minimal_scaffolding(tmp_path)
        assert result is False

    def test_project_with_started_work_items_not_minimal(self, tmp_path):
        """Test project with in_progress work items is not minimal."""
        # Create session structure
        session = tmp_path / ".session" / "tracking"
        session.mkdir(parents=True)

        work_items = {
            "work_items": {
                "WI-001": {"id": "WI-001", "status": "in_progress", "title": "Feature"},
            }
        }
        (session / "work_items.json").write_text(json.dumps(work_items))

        result = is_minimal_scaffolding(tmp_path)
        assert result is False

    def test_project_with_not_started_work_items_is_minimal(self, tmp_path):
        """Test project with only not_started work items is minimal."""
        session = tmp_path / ".session" / "tracking"
        session.mkdir(parents=True)

        work_items = {
            "work_items": {
                "WI-001": {"id": "WI-001", "status": "not_started", "title": "Feature"},
            }
        }
        (session / "work_items.json").write_text(json.dumps(work_items))

        result = is_minimal_scaffolding(tmp_path)
        assert result is True

    def test_project_with_empty_work_items_list(self, tmp_path):
        """Test project with empty work items list is minimal."""
        session = tmp_path / ".session" / "tracking"
        session.mkdir(parents=True)

        work_items = {"work_items": []}
        (session / "work_items.json").write_text(json.dumps(work_items))

        result = is_minimal_scaffolding(tmp_path)
        assert result is True

    def test_config_files_are_ignored(self, tmp_path):
        """Test that config files don't count as substantial source."""
        src = tmp_path / "src"
        src.mkdir()

        # Create config files that should be ignored
        (src / "config.py").write_text("CONFIG = {}")
        (src / "settings.py").write_text("SETTINGS = {}")
        (src / "__init__.py").write_text("")
        (src / "constants.py").write_text("CONST = 1")
        (src / "types.py").write_text("MyType = str")

        # Plus one health check
        (src / "health.py").write_text("def health(): pass")

        result = is_minimal_scaffolding(tmp_path)
        assert result is True

    def test_many_test_files_not_minimal(self, tmp_path):
        """Test project with many test files is not minimal."""
        tests = tmp_path / "tests"
        tests.mkdir()

        # Create more than 3 test files (beyond health check tests)
        for i in range(10):
            (tests / f"test_feature_{i}.py").write_text(f"def test_{i}(): pass")

        result = is_minimal_scaffolding(tmp_path)
        assert result is False

    def test_default_project_root(self, tmp_path, monkeypatch):
        """Test using default project root (cwd)."""
        monkeypatch.chdir(tmp_path)

        # Empty directory should be minimal
        result = is_minimal_scaffolding()
        assert result is True

    def test_invalid_work_items_json(self, tmp_path):
        """Test handling of invalid work_items.json."""
        session = tmp_path / ".session" / "tracking"
        session.mkdir(parents=True)

        # Invalid JSON
        (session / "work_items.json").write_text("not valid json")

        # Should still return True (assumes minimal if can't read)
        result = is_minimal_scaffolding(tmp_path)
        assert result is True


class TestHasIntegrationTestFiles:
    """Tests for has_integration_test_files()."""

    def test_no_integration_tests(self, tmp_path):
        """Test when no integration tests exist."""
        result = has_integration_test_files(tmp_path)
        assert result is False

    def test_has_integration_tests_in_tests_integration(self, tmp_path):
        """Test detection of integration tests in tests/integration/."""
        int_dir = tmp_path / "tests" / "integration"
        int_dir.mkdir(parents=True)
        (int_dir / "test_api.py").write_text("def test_api(): pass")

        result = has_integration_test_files(tmp_path)
        assert result is True

    def test_has_integration_tests_typescript(self, tmp_path):
        """Test detection of TypeScript integration tests."""
        int_dir = tmp_path / "tests" / "integration"
        int_dir.mkdir(parents=True)
        (int_dir / "api.test.ts").write_text("test('api', () => {});")

        result = has_integration_test_files(tmp_path)
        assert result is True

    def test_empty_integration_directory(self, tmp_path):
        """Test when integration directory exists but is empty."""
        int_dir = tmp_path / "tests" / "integration"
        int_dir.mkdir(parents=True)

        result = has_integration_test_files(tmp_path)
        assert result is False

    def test_default_project_root(self, tmp_path, monkeypatch):
        """Test using default project root (cwd)."""
        monkeypatch.chdir(tmp_path)

        result = has_integration_test_files()
        assert result is False


class TestHasE2ETestFiles:
    """Tests for has_e2e_test_files()."""

    def test_no_e2e_tests(self, tmp_path):
        """Test when no E2E tests exist."""
        result = has_e2e_test_files(tmp_path)
        assert result is False

    def test_has_e2e_tests_in_tests_e2e(self, tmp_path):
        """Test detection of E2E tests in tests/e2e/."""
        e2e_dir = tmp_path / "tests" / "e2e"
        e2e_dir.mkdir(parents=True)
        (e2e_dir / "flow.spec.ts").write_text("test('flow', () => {});")

        result = has_e2e_test_files(tmp_path)
        assert result is True

    def test_has_e2e_tests_in_cypress(self, tmp_path):
        """Test detection of Cypress E2E tests."""
        cypress_dir = tmp_path / "cypress" / "e2e"
        cypress_dir.mkdir(parents=True)
        (cypress_dir / "spec.cy.ts").write_text("describe('test', () => {});")

        # Also need cypress config
        (tmp_path / "cypress.config.ts").write_text("export default {}")

        result = has_e2e_test_files(tmp_path)
        assert result is True

    def test_playwright_with_tests(self, tmp_path):
        """Test detection of Playwright E2E tests."""
        e2e_dir = tmp_path / "tests" / "e2e"
        e2e_dir.mkdir(parents=True)
        (e2e_dir / "home.spec.ts").write_text("test('home', () => {});")

        # Playwright config
        (tmp_path / "playwright.config.ts").write_text("export default {}")

        result = has_e2e_test_files(tmp_path)
        assert result is True

    def test_playwright_config_without_tests(self, tmp_path):
        """Test that Playwright config alone doesn't indicate E2E tests."""
        # Only config, no test files
        (tmp_path / "playwright.config.ts").write_text("export default {}")

        result = has_e2e_test_files(tmp_path)
        assert result is False

    def test_empty_e2e_directory(self, tmp_path):
        """Test when E2E directory exists but is empty."""
        e2e_dir = tmp_path / "tests" / "e2e"
        e2e_dir.mkdir(parents=True)

        result = has_e2e_test_files(tmp_path)
        assert result is False

    def test_e2e_in_root_directory(self, tmp_path):
        """Test detection of E2E tests in root e2e/ directory."""
        e2e_dir = tmp_path / "e2e"
        e2e_dir.mkdir()
        (e2e_dir / "test.spec.ts").write_text("test('e2e', () => {});")

        result = has_e2e_test_files(tmp_path)
        assert result is True

    def test_default_project_root(self, tmp_path, monkeypatch):
        """Test using default project root (cwd)."""
        monkeypatch.chdir(tmp_path)

        result = has_e2e_test_files()
        assert result is False
