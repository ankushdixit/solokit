#!/usr/bin/env python3
"""
Minimal scaffolding detection.

Detects if a project is in "minimal scaffolding" state, meaning it has
the basic project structure but no actual application code yet.

This is used by quality gates to adjust expectations for freshly initialized
projects that haven't been built out yet.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_minimal_scaffolding(project_root: Path | None = None) -> bool:
    """
    Detect if project is in minimal scaffolding state.

    A project is considered "minimal scaffolding" if:
    - No source files beyond health check (or equivalent per stack)
    - No test files beyond health check test
    - Work items count is 0 or all are `not_started`

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if project is in minimal scaffolding state
    """
    if project_root is None:
        project_root = Path.cwd()

    logger.debug(f"Checking minimal scaffolding state for {project_root}")

    # Check 1: Work items state
    if not _work_items_are_empty_or_not_started(project_root):
        logger.debug("Work items indicate active development")
        return False

    # Check 2: Source code state
    if not _has_minimal_source_code(project_root):
        logger.debug("Source code indicates active development")
        return False

    # Check 3: Test files state
    if not _has_minimal_test_files(project_root):
        logger.debug("Test files indicate active development")
        return False

    logger.info("Project is in minimal scaffolding state")
    return True


def _work_items_are_empty_or_not_started(project_root: Path) -> bool:
    """
    Check if work items are empty or all not started.

    Args:
        project_root: Project root directory

    Returns:
        True if no work items or all are not_started
    """
    work_items_file = project_root / ".session" / "tracking" / "work_items.json"

    if not work_items_file.exists():
        return True

    try:
        with open(work_items_file) as f:
            data = json.load(f)

        work_items = data.get("work_items", {})

        if not work_items:
            return True

        # If it's a dict, check values
        if isinstance(work_items, dict):
            for item in work_items.values():
                status = item.get("status", "not_started")
                if status != "not_started":
                    return False
        # If it's a list
        elif isinstance(work_items, list):
            for item in work_items:
                status = item.get("status", "not_started")
                if status != "not_started":
                    return False

        return True

    except (OSError, json.JSONDecodeError) as e:
        logger.debug(f"Failed to read work items: {e}")
        return True


def _has_minimal_source_code(project_root: Path) -> bool:
    """
    Check if source code is minimal (health check only).

    Checks for common source directories and counts non-config/non-health files.

    Args:
        project_root: Project root directory

    Returns:
        True if source code is minimal
    """
    # Maximum number of substantial source files for minimal scaffolding
    max_source_files = 5

    # Patterns for health check files (these are expected in minimal scaffolding)
    health_check_patterns = [
        "health",
        "healthcheck",
        "health_check",
        "health-check",
        "ping",
        "status",
    ]

    # Config and setup files to ignore
    config_patterns = [
        "config",
        "settings",
        "__init__",
        "setup",
        "conftest",
        "fixtures",
        "constants",
        "types",
        "schema",
    ]

    source_dirs = [
        project_root / "src",
        project_root / "app",
        project_root / "server",
        project_root / "lib",
        project_root / "pages",
        project_root / "components",
    ]

    substantial_files = 0

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue

        # Count Python and TypeScript/JavaScript files
        for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file_path in source_dir.rglob(ext):
                file_name = file_path.stem.lower()

                # Skip health check files
                if any(pattern in file_name for pattern in health_check_patterns):
                    continue

                # Skip config files
                if any(pattern in file_name for pattern in config_patterns):
                    continue

                # Skip test files in source (shouldn't be here but check anyway)
                if "test" in file_name or "spec" in file_name:
                    continue

                # Skip layout/root files (Next.js)
                if file_name in ["layout", "page", "error", "loading", "not-found"]:
                    continue

                # This is a substantial source file
                substantial_files += 1

                if substantial_files > max_source_files:
                    return False

    return substantial_files <= max_source_files


def _has_minimal_test_files(project_root: Path) -> bool:
    """
    Check if test files are minimal (health check test only).

    Args:
        project_root: Project root directory

    Returns:
        True if test files are minimal
    """
    # Maximum number of test files for minimal scaffolding
    max_test_files = 3

    # Patterns for health check test files
    health_check_patterns = [
        "health",
        "healthcheck",
        "health_check",
        "health-check",
        "smoke",
        "sanity",
    ]

    test_dirs = [
        project_root / "tests",
        project_root / "test",
        project_root / "__tests__",
        project_root / "spec",
    ]

    test_file_count = 0

    for test_dir in test_dirs:
        if not test_dir.exists():
            continue

        # Count test files
        for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
            for file_path in test_dir.rglob(ext):
                file_name = file_path.stem.lower()

                # Skip conftest and fixture files
                if file_name in ["conftest", "fixtures", "setup", "helpers"]:
                    continue

                # Skip health check tests (these are expected)
                if any(pattern in file_name for pattern in health_check_patterns):
                    continue

                # This is a test file
                test_file_count += 1

                if test_file_count > max_test_files:
                    return False

    return test_file_count <= max_test_files


def has_integration_test_files(project_root: Path | None = None) -> bool:
    """
    Check if integration test files exist.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if integration test files exist
    """
    if project_root is None:
        project_root = Path.cwd()

    integration_dirs = [
        project_root / "tests" / "integration",
        project_root / "test" / "integration",
        project_root / "__tests__" / "integration",
    ]

    for int_dir in integration_dirs:
        if int_dir.exists():
            # Check for actual test files
            for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
                if list(int_dir.rglob(ext)):
                    return True

    return False


def has_e2e_test_files(project_root: Path | None = None) -> bool:
    """
    Check if E2E test files exist.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if E2E test files exist
    """
    if project_root is None:
        project_root = Path.cwd()

    e2e_dirs = [
        project_root / "tests" / "e2e",
        project_root / "test" / "e2e",
        project_root / "__tests__" / "e2e",
        project_root / "e2e",
        project_root / "cypress",
        project_root / "playwright",
    ]

    for e2e_dir in e2e_dirs:
        if e2e_dir.exists():
            # Check for actual test files
            for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]:
                if list(e2e_dir.rglob(ext)):
                    return True

    # Also check for Playwright/Cypress config files as indicators
    playwright_config = project_root / "playwright.config.ts"
    cypress_config = project_root / "cypress.config.ts"

    # Config file alone doesn't mean tests exist, but combined with test dir it does
    if playwright_config.exists():
        e2e_dir = project_root / "tests" / "e2e"
        if e2e_dir.exists() and any(e2e_dir.rglob("*.spec.ts")):
            return True

    if cypress_config.exists():
        cypress_dir = project_root / "cypress" / "e2e"
        if cypress_dir.exists() and any(cypress_dir.rglob("*.cy.*")):
            return True

    return False
