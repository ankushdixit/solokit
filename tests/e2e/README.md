# End-to-End (E2E) Tests

## Overview

This directory contains end-to-end tests that validate the complete Solokit system integration by executing actual CLI commands and verifying full workflows.

## Test Coverage

The E2E test suite includes 88 tests across 8 test files:

- `test_init_workflow.py` (19 tests) - Project initialization and setup
- `test_core_session_workflow.py` (18 tests) - Core session workflows
- `test_work_item_system.py` (16 tests) - Work item management
- `test_learning_system.py` (14 tests) - Learning system integration
- `test_quality_validation.py` (12 tests) - Quality gate validation
- `test_dependency_visualization.py` (7 tests) - Dependency graph generation
- `test_session_lifecycle.py` (1 test) - Complete lifecycle scenarios
- `test_documentation_completeness.py` (1 test) - Documentation validation

## Why E2E Tests Are Slow

E2E tests run **80x slower** than unit tests due to:

### Primary Performance Bottlenecks

1. **Subprocess CLI Execution** (70% of time)
   - 110+ `subprocess.run()` calls executing actual `solokit` CLI commands
   - Each CLI command takes 200-500ms
   - Commands include: `sk init`, `sk start`, `sk work-new`, `sk learn`, `sk validate`

2. **Git Operations** (20% of time)
   - 44 git subprocess calls per test setup
   - Operations: `git init`, `git config`, `git add`, `git commit`, `git branch`
   - Each test creates a fresh git repository

3. **File I/O Operations** (5% of time)
   - 45+ JSON file read/write operations
   - Project structure creation in temporary directories
   - Spec file generation and validation

4. **Fixture Overhead** (5% of time)
   - 13 complex fixtures with nested dependencies
   - Each fixture creates a complete project environment
   - No test caching or state reuse

### Performance Statistics

- **Average E2E test runtime**: 47-80 seconds
- **Total E2E suite runtime**: 4-8 minutes
- **Comparison to unit tests**: 80x slower (unit tests average 10-50ms)

## CI/CD Strategy

### Why E2E Tests Are Skipped in CI

E2E tests are **intentionally skipped in GitHub workflows** because:

1. **Long Runtime**: 4-8 minutes for 88 tests adds significant CI time
2. **Redundant Validation**: Unit (2,980) and integration (165) tests provide 96% coverage
3. **Local Validation Sufficient**: Developers run full test suite locally via `sk validate`
4. **Fast Feedback**: CI runs complete in 1-2 minutes without E2E tests

### GitHub Workflow Configuration

The `.github/workflows/tests.yml` file is configured to skip E2E tests:

```yaml
- name: Run tests with pytest
  run: |
    # Skip e2e tests in CI - they run full CLI commands and take 4-8 minutes
    # E2E tests should be run locally before commits
    pytest tests/unit tests/integration -v --tb=short
```

## Running E2E Tests

### Local Execution

Run all tests including E2E:

```bash
pytest tests/
```

Run only E2E tests:

```bash
pytest tests/e2e/ -v
```

Run a specific E2E test file:

```bash
pytest tests/e2e/test_init_workflow.py -v
```

### During Development

E2E tests should be run:
- Before committing major changes
- During `sk validate` (automatic)
- When testing CLI functionality
- When verifying complete workflows

### Performance Tips

To speed up local E2E test runs:

1. **Run specific test files** instead of the entire suite
2. **Use pytest-xdist** for parallel execution (requires installation):
   ```bash
   pip install pytest-xdist
   pytest tests/e2e/ -n auto
   ```
3. **Focus on relevant tests** for your changes

## Test Architecture

### Fixture Pattern

E2E tests use fixtures to create isolated test environments:

```python
@pytest.fixture
def temp_solokit_project():
    """Create a temporary Solokit project with git and basic files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repository
        # Create basic project files
        # Run sk init
        yield project_dir
```

### Test Pattern

Tests follow the Arrange-Act-Assert pattern:

```python
def test_create_work_item(temp_solokit_project):
    # Arrange - project already initialized by fixture

    # Act - run actual CLI command
    result = subprocess.run(
        ["solokit", "work-new", "--type", "feature", "--title", "Test"],
        cwd=temp_solokit_project,
        capture_output=True
    )

    # Assert - verify expected outcomes
    assert result.returncode == 0
    assert work_item_created()
```

## Contributing

When adding new E2E tests:

1. **Keep tests focused** on integration scenarios, not unit functionality
2. **Reuse fixtures** when possible to reduce duplication
3. **Document slow operations** with comments
4. **Consider unit/integration tests first** for faster feedback
5. **Ensure tests are isolated** and don't depend on execution order

## Related Documentation

- [Test Infrastructure Progress](../../TEST_PROGRESS.md) - Complete test development journey
- [GitHub Workflows](../../.github/workflows/tests.yml) - CI configuration
- [Unit Tests](../unit/) - Fast, focused tests (2,980 tests)
- [Integration Tests](../integration/) - Workflow integration tests (165 tests)
