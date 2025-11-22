#!/usr/bin/env python3
"""
Comprehensive End-to-End Template Testing Script for Solokit

This script tests all project setup combinations through the complete workflow:
1. Initialization (sk init)
2. Create work item (sk work-new)
3. Start session (sk start)
4. Create code and tests
5. Validate session (sk validate)
6. End session (sk end)
7. Push to remote repo
8. CI/CD checks (parses actual workflow files from .github/workflows/)

Requirements:
    pip install pyyaml

Usage:
    # Sequential execution
    python test_all_templates.py --phase 1 --complete
    python test_all_templates.py --phase 2 --incomplete
    python test_all_templates.py --phase 3 --complete --ci-checks
    python test_all_templates.py --phase 4 --incomplete  # Comprehensive 192 tests
    python test_all_templates.py --all --incomplete
    python test_all_templates.py --specific saas_t3 tier-2-standard ci_cd,docker --complete
    python test_all_templates.py --stack ml_ai_fastapi --incomplete --ci-checks  # All 48 phase-4 tests for ml_ai_fastapi

    # Parallel execution (faster!)
    python test_all_templates.py --phase 4 --incomplete --workers 8  # 192 tests in 8 parallel workers
    python test_all_templates.py --all --incomplete --workers 4      # All phases with 4 workers
    python test_all_templates.py --stack ml_ai_fastapi --incomplete --ci-checks --workers 4  # 48 ml_ai_fastapi tests with 4 workers
"""

import argparse
import json
import multiprocessing
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Optional

import yaml

# Global flag for interrupt handling
_interrupted = False

def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully"""
    global _interrupted
    _interrupted = True
    print(f"\n\n{'='*80}")
    print("⚠ INTERRUPT SIGNAL RECEIVED (Ctrl+C)")
    print("Stopping test suite...")
    print(f"{'='*80}\n")
    # Raise KeyboardInterrupt to break out of current operation
    raise KeyboardInterrupt("Test suite interrupted by user")

# Test configuration
STACKS = ["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"]
TIERS = ["tier-1-essential", "tier-2-standard", "tier-3-comprehensive", "tier-4-production"]
OPTIONS = ["ci_cd", "docker", "env_templates", "a11y"]

# Test workspace
WORKSPACE_BASE = Path.home() / "solokit_test_workspace"
RESULTS_DIR = Path(__file__).parent / "test_results"


@dataclass
class TestCase:
    """Represents a single test case configuration"""
    id: str
    stack: str
    tier: str
    options: list[str]
    phase: int
    description: str


@dataclass
class TestResult:
    """Stores the result of a test execution"""
    test_id: str
    stack: str
    tier: str
    options: list[str]
    success: bool
    duration_seconds: float
    errors: list[str]
    warnings: list[str]
    steps_completed: list[str]
    timestamp: str
    project_path: Optional[str] = None


class TemplateTestRunner:
    """Runs end-to-end tests for solokit templates"""

    def __init__(self, workspace: Path, results_dir: Path, cleanup: bool = True, use_incomplete: bool = True, use_validate_fix: bool = False, run_ci_checks: bool = False, worker_id: int = 0):
        self.workspace = workspace
        self.results_dir = results_dir
        self.cleanup = cleanup
        self.use_incomplete = use_incomplete
        self.use_validate_fix = use_validate_fix
        self.run_ci_checks = run_ci_checks
        self.worker_id = worker_id
        self.results: list[TestResult] = []

        # Assign port range for this worker (each worker gets 1 port)
        # Worker 0: port 3000, Worker 1: port 3001, etc.
        self.worker_port = 3000 + worker_id

        # Create directories
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_directory_macos(self, path: Path) -> bool:
        """
        macOS-specific directory cleanup that handles .DS_Store and locked files.

        Args:
            path: Directory path to remove

        Returns:
            bool: True if cleanup successful, False otherwise
        """
        if not path.exists():
            return True

        try:
            # Method 1: Try Python's shutil first (fast)
            shutil.rmtree(path, ignore_errors=False)
            return True
        except (OSError, PermissionError):
            # Method 2: Fall back to system rm -rf (more forceful)
            try:
                # Small delay to let system release file handles
                time.sleep(0.1)

                # Use subprocess with rm -rf which handles macOS quirks better
                subprocess.run(
                    ["rm", "-rf", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Verify directory is gone
                if not path.exists():
                    return True

                # If still exists, try one more time with a longer delay
                time.sleep(0.5)
                subprocess.run(
                    ["rm", "-rf", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                return not path.exists()

            except Exception as e:
                print(f"⚠ Warning: Cleanup failed for {path}: {e}")
                return False

    def run_test(self, test_case: TestCase) -> TestResult:
        """Execute a single end-to-end test"""
        print(f"\n{'='*80}")
        print(f"Running Test: {test_case.id}")
        print(f"Stack: {test_case.stack}, Tier: {test_case.tier}, Options: {test_case.options}")
        print(f"Description: {test_case.description}")
        print(f"{'='*80}\n")

        start_time = time.time()
        errors = []
        warnings = []
        steps_completed = []
        success = False
        project_path = None

        try:
            # Step 1: Create test project directory
            project_name = f"test_{test_case.id}"
            project_path = self.workspace / project_name

            if project_path.exists():
                self._cleanup_directory_macos(project_path)
            project_path.mkdir(parents=True)

            print(f"✓ Created project directory: {project_path}")
            steps_completed.append("create_directory")

            # Step 2: Initialize project
            print("\n→ Initializing project...")
            init_success, init_errors = self._init_project(
                project_path, test_case.stack, test_case.tier, test_case.options
            )

            if not init_success:
                errors.extend(init_errors)
                raise Exception(f"Initialization failed: {init_errors}")

            print("✓ Project initialized successfully")
            steps_completed.append("initialize")

            # Step 3: Verify installation
            print("\n→ Verifying installation...")
            verify_success, verify_errors = self._verify_installation(project_path, test_case)

            if not verify_success:
                errors.extend(verify_errors)
                warnings.append(f"Installation verification had issues: {verify_errors}")
            else:
                print("✓ Installation verified")
                steps_completed.append("verify_installation")

            # NOTE: Dependency installation is handled by sk init (no separate step needed)
            # sk init already runs the proper tier-specific installation from stack-versions.yaml
            print("✓ Dependencies installed by sk init")
            steps_completed.append("install_dependencies")

            # Step 4: Create work item
            print("\n→ Creating work item...")
            work_item_id, work_errors = self._create_work_item(project_path)

            if not work_item_id:
                errors.extend(work_errors)
                raise Exception(f"Work item creation failed: {work_errors}")

            print(f"✓ Work item created: {work_item_id}")
            steps_completed.append("create_work_item")

            # Step 6: Start session
            print("\n→ Starting session...")
            start_success, start_errors = self._start_session(project_path, work_item_id)

            if not start_success:
                errors.extend(start_errors)
                raise Exception(f"Session start failed: {start_errors}")

            print("✓ Session started")
            steps_completed.append("start_session")

            # Step 7: Create sample code and tests
            print("\n→ Creating sample code and tests...")
            code_success, code_errors = self._create_sample_code(project_path, test_case.stack)

            if not code_success:
                errors.extend(code_errors)
                warnings.append(f"Code creation had issues: {code_errors}")
            else:
                print("✓ Sample code created")
                steps_completed.append("create_code")

            # Step 7.5: Update CHANGELOG (required for --complete mode)
            if not self.use_incomplete:
                print("\n→ Updating CHANGELOG...")
                changelog_success = self._update_changelog(project_path)
                if changelog_success:
                    print("✓ CHANGELOG updated")
                    steps_completed.append("update_changelog")

            # Step 8: Run quality checks (validate session)
            print("\n→ Validating session...")
            validate_success, validate_errors = self._validate_session(project_path)

            if not validate_success:
                errors.extend(validate_errors)
                warnings.append(f"Validation had issues: {validate_errors}")
            else:
                print("✓ Session validated")
                steps_completed.append("validate_session")

            # Step 8.5: Commit changes (ALWAYS required, even for --incomplete mode)
            # Note: sk end --incomplete still requires commits, it only skips quality gates
            print("\n→ Committing changes...")
            commit_success, commit_errors = self._commit_changes(project_path)

            if not commit_success:
                errors.extend(commit_errors)
                warnings.append(f"Commit had issues: {commit_errors}")
            else:
                print("✓ Changes committed")
                steps_completed.append("commit_changes")

            # Step 9: End session
            print("\n→ Ending session...")
            end_success, end_errors = self._end_session(project_path)

            if not end_success:
                errors.extend(end_errors)
                raise Exception(f"Session end failed: {end_errors}")

            print("✓ Session ended")
            steps_completed.append("end_session")

            # Step 10: Setup and push to remote repo (using local bare repo for testing)
            print("\n→ Setting up remote and pushing...")
            push_success, push_errors = self._push_to_remote(project_path, test_case.id)

            if not push_success:
                errors.extend(push_errors)
                warnings.append(f"Remote push had issues: {push_errors}")
            else:
                print("✓ Pushed to remote")
                steps_completed.append("push_to_remote")

            # Step 11: Run CI/CD checks (optional, mimics GitHub Actions)
            # Note: CI/CD workflows only exist if ci_cd option was selected, but lighthouse.yml
            # is installed directly from tier-4-production (no ci_cd option needed)
            if self.run_ci_checks:
                print("\n→ Running CI/CD checks (GitHub Actions simulation)...")

                # Check if ci_cd option was used
                has_ci_cd_option = "ci_cd" in test_case.options
                has_lighthouse = test_case.tier == "tier-4-production" and test_case.stack != "ml_ai_fastapi"

                if has_ci_cd_option:
                    print("  ℹ CI/CD workflows installed (ci_cd option selected)")
                elif has_lighthouse:
                    print("  ℹ CI/CD workflows NOT installed, but Lighthouse CI available (tier-4)")
                else:
                    print("  ℹ CI/CD workflows NOT installed (ci_cd option not selected)")
                    print("  → Running basic checks only (lint, type-check, format, test, build)")

                ci_success, ci_errors = self._run_ci_checks(
                    project_path, test_case.stack, test_case.tier, has_ci_cd_option, test_case.options
                )

                if not ci_success:
                    errors.extend(ci_errors)
                    # CI checks are critical - fail the test if they fail
                    raise Exception(f"CI/CD checks failed: {ci_errors}")
                else:
                    print("✓ CI/CD checks passed")
                    steps_completed.append("ci_checks")

            # If we got here, the test succeeded
            success = True
            print(f"\n{'='*80}")
            print(f"✓ Test PASSED: {test_case.id}")
            print(f"{'='*80}")

        except Exception as e:
            print(f"\n{'='*80}")
            print(f"✗ Test FAILED: {test_case.id}")
            print(f"Error: {str(e)}")
            print(f"{'='*80}")
            errors.append(str(e))

        finally:
            duration = time.time() - start_time

            # Create result
            result = TestResult(
                test_id=test_case.id,
                stack=test_case.stack,
                tier=test_case.tier,
                options=test_case.options,
                success=success,
                duration_seconds=round(duration, 2),
                errors=errors,
                warnings=warnings,
                steps_completed=steps_completed,
                timestamp=datetime.now().isoformat(),
                project_path=str(project_path) if project_path else None
            )

            self.results.append(result)

            # Cleanup if requested and test passed
            if self.cleanup and success and project_path and project_path.exists():
                print("\n→ Cleaning up test directory...")
                cleanup_success = self._cleanup_directory_macos(project_path)
                if cleanup_success:
                    print("✓ Cleaned up")
                else:
                    print("⚠ Cleanup incomplete - some files may remain")
            elif not success:
                print(f"\n⚠ Keeping failed test directory for inspection: {project_path}")

            return result

    def _run_command(self, cmd: list[str], cwd: Path, timeout: int = 300, env: Optional[dict[str, str]] = None) -> tuple[bool, str, str]:
        """Run a shell command and return success status and output"""
        try:
            # Merge custom env with current environment
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                env=run_env
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def _init_project(self, project_path: Path, stack: str, tier: str, options: list[str]) -> tuple[bool, list[str]]:
        """Initialize a solokit project"""
        errors = []

        # Build sk init command
        cmd = [
            "sk", "init",
            "--template", stack,
            "--tier", tier,
            "--coverage", "80"
        ]

        # Add options as comma-separated list
        if options:
            cmd.extend(["--options", ",".join(options)])

        success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)

        if not success:
            errors.append(f"Init command failed: {stderr}")

        # Check for critical files
        critical_files = [".session", ".git", "README.md"]
        for file in critical_files:
            if not (project_path / file).exists():
                errors.append(f"Critical file/directory missing: {file}")

        return len(errors) == 0, errors

    def _verify_installation(self, project_path: Path, test_case: TestCase) -> tuple[bool, list[str]]:
        """Verify that all expected files are installed"""
        errors = []

        # Check base files exist
        base_files = ["package.json"] if test_case.stack != "ml_ai_fastapi" else ["pyproject.toml", "requirements.txt"]

        for file in base_files:
            if not (project_path / file).exists():
                errors.append(f"Base file missing: {file}")

        # Check tier-specific files
        tier_markers = {
            "tier-1-essential": ["jest.config.ts"] if test_case.stack != "ml_ai_fastapi" else ["pytest.ini"],
            "tier-2-standard": [".husky"] if test_case.stack != "ml_ai_fastapi" else [".pre-commit-config.yaml"],
            "tier-3-comprehensive": ["playwright.config.ts"] if test_case.stack != "ml_ai_fastapi" else ["tests/integration"],
            "tier-4-production": ["instrumentation.ts"] if test_case.stack != "ml_ai_fastapi" else ["src/core/sentry.py"]
        }

        expected_files = tier_markers.get(test_case.tier, [])
        for file in expected_files:
            if not (project_path / file).exists():
                errors.append(f"Tier file missing: {file}")

        # Check optional features
        if "ci_cd" in test_case.options:
            if not (project_path / ".github" / "workflows").exists():
                errors.append("CI/CD workflows directory missing")

        if "docker" in test_case.options:
            if not (project_path / "Dockerfile").exists():
                errors.append("Dockerfile missing")

        if "env_templates" in test_case.options:
            if not (project_path / ".env.example").exists():
                errors.append(".env.example missing")

        if "a11y" in test_case.options:
            # a11y workflows should be in .github/workflows/
            if test_case.stack != "ml_ai_fastapi":  # a11y is only for frontend stacks
                a11y_workflow = project_path / ".github" / "workflows" / "a11y.yml"
                if not a11y_workflow.exists():
                    errors.append("a11y workflow missing")

        return len(errors) == 0, errors

    # NOTE: This method is no longer used!
    # Dependency installation is handled by sk init via dependency_installer.py
    # which properly installs tier-specific packages from stack-versions.yaml.
    # Running this method would UN-install the correct dependencies and replace
    # them with incomplete ones (missing tier-2 and tier-3 packages for Python).
    #
    # def _install_dependencies(self, project_path: Path, stack: str) -> tuple[bool, List[str]]:
    #     """[DEPRECATED] Install project dependencies - DO NOT USE"""
    #     # This was using pip install -e . which only installs from pyproject.toml
    #     # Missing tier-specific packages (radon, vulture, bandit for tier-3+)
    #     pass

    def _create_work_item(self, project_path: Path) -> tuple[Optional[str], list[str]]:
        """Create a work item for testing"""
        errors = []

        # Use sk work-new command to properly create the work item
        cmd = [
            "sk", "work-new",
            "--type", "feature",
            "--title", "Test Feature for Template Validation",
            "--priority", "high"
        ]

        success, stdout, stderr = self._run_command(cmd, project_path)

        if not success:
            errors.append(f"Work item creation failed: {stderr}")
            return None, errors

        # Extract work item ID from work_items.json
        # sk work-new creates IDs based on the title
        tracking_file = project_path / ".session" / "tracking" / "work_items.json"
        work_item_id = None

        try:
            if tracking_file.exists():
                work_items_data = json.loads(tracking_file.read_text())
                # Get the most recently created work item
                if "work_items" in work_items_data and work_items_data["work_items"]:
                    # Get the last work item (most recently created)
                    work_item_id = list(work_items_data["work_items"].keys())[-1]
        except Exception as e:
            errors.append(f"Failed to parse work items: {str(e)}")

        if not work_item_id:
            errors.append("Could not determine work item ID")
            return None, errors

        # Update the spec file with our detailed content
        spec_path = project_path / ".session" / "specs" / f"{work_item_id}.md"

        spec_content = """# Feature: Test Feature for Template Validation

## Overview
Test feature for end-to-end testing of the solokit template workflow.

## Rationale
Validate that the initialized project structure supports the complete development workflow from session start to completion.

## User Story
As a developer, I want to test the solokit workflow to ensure all templates are properly configured.

## Acceptance Criteria
- [ ] Code is written and follows project conventions
- [ ] Tests pass with required coverage threshold
- [ ] All quality gates pass successfully
- [ ] Session can be completed without errors

## Implementation Details

### Approach
Create a minimal but complete implementation that exercises the project structure.

### Components Affected
- Core library files
- Test suite
- Configuration files

### API Changes
None - this is a test implementation.

### Database Changes
None - no database operations required.

## Testing Strategy
Unit tests with coverage reporting to validate the test infrastructure is properly configured.
"""

        if spec_path.exists():
            spec_path.write_text(spec_content)

        return work_item_id, errors

    def _start_session(self, project_path: Path, work_item_id: str) -> tuple[bool, list[str]]:
        """Start a development session"""
        errors = []

        cmd = ["sk", "start", work_item_id]
        success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)

        if not success:
            errors.append(f"Session start failed: {stderr}")

        # Session start is verified by command exit code
        # No need to check for directory existence

        return len(errors) == 0, errors

    def _create_sample_code(self, project_path: Path, stack: str) -> tuple[bool, list[str]]:
        """Create sample code and tests"""
        errors = []

        try:
            if stack == "ml_ai_fastapi":
                # Python code
                code_file = project_path / "src" / "test_feature.py"
                code_file.parent.mkdir(parents=True, exist_ok=True)
                code_file.write_text("""
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b
""")

                test_file = project_path / "tests" / "test_feature.py"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text("""
from src.test_feature import add

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
""")
            else:
                # TypeScript/JavaScript code
                code_file = project_path / "lib" / "test-feature.ts"
                code_file.parent.mkdir(parents=True, exist_ok=True)
                code_file.write_text("""
/**
 * Add two numbers together
 * @param a - First number
 * @param b - Second number
 * @returns Sum of a and b
 */
export function add(a: number, b: number): number {
  return a + b;
}
""")

                test_file = project_path / "tests" / "test-feature.test.ts"
                test_file.parent.mkdir(parents=True, exist_ok=True)
                test_file.write_text("""
import { add } from '../lib/test-feature';

/**
 * Test suite for the add function
 */
describe('add', () => {
  /**
   * Tests that add correctly adds two numbers
   */
  it('should add two numbers', () => {
    expect(add(2, 3)).toBe(5);
    expect(add(0, 0)).toBe(0);
    expect(add(-1, 1)).toBe(0);
  });
});
""")

            # Git commit the changes
            cmd = ["git", "add", "."]
            self._run_command(cmd, project_path)

            cmd = ["git", "commit", "-m", "Add test feature"]
            self._run_command(cmd, project_path)

        except Exception as e:
            errors.append(f"Failed to create sample code: {str(e)}")

        return len(errors) == 0, errors

    def _validate_session(self, project_path: Path) -> tuple[bool, list[str]]:
        """Validate the development session (with optional auto-fix)"""
        errors = []

        cmd = ["sk", "validate"]
        if self.use_validate_fix:
            cmd.append("--fix")

        success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)

        if not success:
            # Validation might fail due to quality gates, which is OK for testing
            # We just want to ensure the command runs
            errors.append(f"Validation had issues (may be expected): {stderr}")

        return True, errors  # Always return True since we just want to test the command runs

    def _update_changelog(self, project_path: Path) -> bool:
        """Update CHANGELOG.md (required for documentation quality gate)"""
        changelog_path = project_path / "CHANGELOG.md"

        try:
            if not changelog_path.exists():
                # Create CHANGELOG if it doesn't exist
                changelog_path.write_text("""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Test feature: add function for arithmetic operations

""")
            else:
                current_content = changelog_path.read_text()
                # Add entry under [Unreleased] section
                new_entry = """## [Unreleased]
### Added
- Test feature: add function for arithmetic operations

"""
                # Replace the [Unreleased] section
                if "[Unreleased]" in current_content:
                    updated_content = current_content.replace("## [Unreleased]\n", new_entry)
                else:
                    # If no [Unreleased] section, add it at the top
                    updated_content = new_entry + "\n" + current_content

                changelog_path.write_text(updated_content)

            return True
        except Exception:
            return False

    def _commit_changes(self, project_path: Path) -> tuple[bool, list[str]]:
        """Commit all changes (required for --complete mode)"""
        errors = []

        # Stage all changes
        cmd = ["git", "add", "-A"]
        success, stdout, stderr = self._run_command(cmd, project_path)

        if not success:
            errors.append(f"Git add failed: {stderr}")
            return False, errors

        # Commit with a test message
        commit_msg = """Implement test feature

LEARNING: Template validation completed successfully with all quality gates passing

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"""

        cmd = ["git", "commit", "-m", commit_msg]
        success, stdout, stderr = self._run_command(cmd, project_path)

        if not success:
            errors.append(f"Git commit failed: {stderr}")
            return False, errors

        return True, errors

    def _end_session(self, project_path: Path) -> tuple[bool, list[str]]:
        """End the development session"""
        errors = []

        cmd = ["sk", "end"]
        if self.use_incomplete:
            cmd.append("--incomplete")  # Skip quality gates for faster testing
        else:
            cmd.append("--complete")  # Use full quality gates

        success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)

        if not success:
            errors.append(f"Session end failed: {stderr}")

        return len(errors) == 0, errors

    def _push_to_remote(self, project_path: Path, test_id: str) -> tuple[bool, list[str]]:
        """Setup a test remote and push changes"""
        errors = []

        try:
            # Create a bare git repo to act as remote
            remote_path = self.workspace / f"remote_{test_id}.git"
            if remote_path.exists():
                self._cleanup_directory_macos(remote_path)
            remote_path.mkdir()

            # Initialize bare repo
            cmd = ["git", "init", "--bare"]
            success, stdout, stderr = self._run_command(cmd, remote_path)
            if not success:
                errors.append(f"Failed to create remote: {stderr}")
                return False, errors

            # Add remote
            cmd = ["git", "remote", "add", "origin", str(remote_path)]
            success, stdout, stderr = self._run_command(cmd, project_path)
            if not success:
                errors.append(f"Failed to add remote: {stderr}")

            # Push
            cmd = ["git", "push", "-u", "origin", "main"]
            success, stdout, stderr = self._run_command(cmd, project_path)
            if not success:
                # Try master branch
                cmd = ["git", "push", "-u", "origin", "master"]
                success, stdout, stderr = self._run_command(cmd, project_path)
                if not success:
                    errors.append(f"Failed to push: {stderr}")

        except Exception as e:
            errors.append(f"Remote setup failed: {str(e)}")

        return len(errors) == 0, errors

    def _evaluate_github_actions_condition(self, condition: str, project_path: Path) -> bool:
        """
        Evaluate a GitHub Actions 'if' condition.

        Currently supports:
        - hashFiles('pattern') != '' - Returns True if file exists
        - Simple boolean expressions

        Args:
            condition: The condition string (e.g., "hashFiles('.pylintrc') != ''")
            project_path: Path to the project for file checks

        Returns:
            True if condition passes, False otherwise
        """
        if not condition:
            return True  # No condition means always run

        # Handle hashFiles() function
        if 'hashFiles' in condition:
            import re
            # Extract file pattern from hashFiles('pattern')
            match = re.search(r"hashFiles\(['\"]([^'\"]+)['\"]\)", condition)
            if match:
                file_pattern = match.group(1)
                file_path = project_path / file_pattern
                file_exists = file_path.exists()

                # Check if condition is checking for non-empty (file exists)
                if "!= ''" in condition or '!= ""' in condition:
                    return file_exists
                # Check if condition is checking for empty (file doesn't exist)
                elif "== ''" in condition or '== ""' in condition:
                    return not file_exists

        # Handle steps.*.outputs.* conditions
        if 'steps.' in condition and '.outputs.' in condition:
            # For now, we can't evaluate step outputs, so skip these steps
            return False

        # Default: assume condition passes
        return True

    def _parse_workflow_commands(self, workflow_path: Path, stack: str, project_path: Path = None) -> tuple[list[tuple[list[str], str, bool]], list[str]]:
        """
        Parse a GitHub Actions workflow file and extract commands to run.

        Args:
            workflow_path: Path to the workflow YAML file
            stack: Stack name to determine command parser (npm vs python)
            project_path: Path to the project (for evaluating conditions)

        Returns:
            Tuple of:
            - List of tuples: (command_list, description, is_optional)
            - List of pip packages to install (for Python stacks)
        """
        commands = []
        pip_packages = []

        try:
            # Read workflow file and handle template variables
            with open(workflow_path) as f:
                content = f.read()

            # Replace common template variables with defaults
            content = content.replace('{coverage_target}', '80')

            workflow = yaml.safe_load(content)

            # Extract jobs
            jobs = workflow.get('jobs', {})

            for job_name, job_config in jobs.items():
                steps = job_config.get('steps', [])

                for step in steps:
                    run_cmd = step.get('run', '')
                    step_name = step.get('name', '')
                    continue_on_error = step.get('continue-on-error', False)
                    step_condition = step.get('if', '')

                    if not run_cmd or not step_name:
                        continue

                    # Evaluate GitHub Actions 'if' condition
                    if project_path and step_condition:
                        if not self._evaluate_github_actions_condition(step_condition, project_path):
                            # Skip this step as condition is not met
                            continue

                    # Skip setup, installation, and upload steps
                    # Note: 'install playwright' removed - browsers now installed by sk init
                    skip_keywords = [
                        'checkout', 'setup', 'install dependencies',
                        'upload', 'show mutation results',
                        'prisma migrate', 'set up python', 'check if'
                    ]
                    if any(skip in step_name.lower() for skip in skip_keywords):
                        continue

                    # Skip build only if it's in test setup jobs (where it's just setup, not a quality check)
                    # But keep build if it's a dedicated build check job (like in quality-check.yml)
                    setup_jobs = ['e2e-tests', 'accessibility', 'lighthouse']
                    if 'build' in step_name.lower() and job_name in setup_jobs:
                        continue

                    # Extract pip install commands for Python stacks
                    if stack == "ml_ai_fastapi":
                        pip_packages.extend(self._extract_pip_packages(run_cmd))

                    # Parse the command
                    cmd_list = self._parse_command_string(run_cmd, stack)

                    if cmd_list:
                        commands.append((cmd_list, step_name, continue_on_error))

        except yaml.YAMLError as e:
            print(f"  ⚠ Warning: YAML parsing error in {workflow_path.name}: {e}")
        except Exception as e:
            print(f"  ⚠ Warning: Could not parse workflow {workflow_path.name}: {e}")

        return commands, pip_packages

    def _extract_pip_packages(self, run_cmd: str) -> list[str]:
        """
        Extract pip package names from pip install commands in a run block.

        Args:
            run_cmd: The command string from the workflow

        Returns:
            List of package names to install
        """
        packages = []
        lines = [line.strip() for line in run_cmd.split('\n') if line.strip()]

        for line in lines:
            # Match "pip install package1 package2 ..." or "python -m pip install ..."
            if 'pip install' in line:
                # Extract everything after "install"
                parts = line.split('install', 1)
                if len(parts) > 1:
                    # Split by whitespace and filter out flags
                    pkg_parts = parts[1].strip().split()
                    for pkg in pkg_parts:
                        # Skip flags like --upgrade, --no-cache-dir, etc.
                        if not pkg.startswith('-'):
                            packages.append(pkg)

        return packages

    def _parse_command_string(self, run_cmd: str, stack: str) -> Optional[list[str]]:
        """
        Parse a command string from a workflow into a command list.

        Args:
            run_cmd: The command string from the workflow
            stack: Stack name to determine parsing strategy

        Returns:
            Command list or None if command should be skipped
        """
        # Handle multi-line commands (take the main command, skip setup)
        lines = [line.strip() for line in run_cmd.split('\n') if line.strip()]

        # Filter out pip install, setup commands
        main_lines = [line for line in lines if not any(skip in line for skip in ['pip install', 'python -m pip'])]

        if not main_lines:
            return None

        # Take the first main command
        cmd_str = main_lines[0]

        # Parse npm commands (both "npm run" and direct commands like "npm audit", "npm build")
        if cmd_str.startswith('npm'):
            parts = shlex.split(cmd_str)
            # Handle "npm run", "npm audit", "npm build", etc.
            # Also handles flags like "--if-present" or "--audit-level"
            return parts

        # Parse python tool commands (ruff, pyright, etc.)
        if stack == "ml_ai_fastapi":
            # Handle commands that start with venv binaries
            # We'll need to update these to use the actual venv path
            for tool in ['ruff', 'pyright', 'radon', 'vulture', 'bandit', 'pytest', 'pylint', 'mypy', 'cosmic-ray', 'cr-report']:
                if tool in cmd_str:
                    # Extract the full command using shlex to properly handle quoted strings
                    return shlex.split(cmd_str)

        return None

    def _run_ci_checks(self, project_path: Path, stack: str, tier: str, has_ci_cd_workflows: bool = True, options: list[str] = []) -> tuple[bool, list[str]]:
        """
        Run the same CI/CD checks that would run on GitHub Actions by parsing actual workflow files.

        This simulates the GitHub Actions workflows to catch issues before pushing to remote.

        Args:
            project_path: Path to the project
            stack: Stack name (e.g., "saas_t3")
            tier: Tier name (e.g., "tier-1-essential")
            has_ci_cd_workflows: Whether CI/CD workflows were installed (ci_cd option selected)
            options: List of selected options (e.g., ["ci_cd", "docker", "a11y"])

        Note:
            This method now parses actual workflow files from .github/workflows/ instead of
            hardcoding checks. This ensures tests perfectly match what users get.
        """
        errors = []
        warnings = []

        workflows_dir = project_path / ".github" / "workflows"

        if not workflows_dir.exists():
            print("  ℹ No workflows directory found, skipping CI checks")
            return True, []

        # Determine which workflow files to check
        # Note: CI/CD workflows (quality-check, test, security, build) only exist if ci_cd option selected
        # But lighthouse.yml is installed directly from tier-4-production (no ci_cd option needed)
        workflow_files = {
            'quality-check.yml': 'Quality checks' if has_ci_cd_workflows else None,
            'test.yml': 'Tests' if has_ci_cd_workflows else None,
            'security.yml': 'Security' if has_ci_cd_workflows else None,
            'build.yml': 'Build & Bundle Analysis' if has_ci_cd_workflows else None,
            'a11y.yml': 'Accessibility' if 'a11y' in options else None,
            # Lighthouse CI is only available in tier-4 for Next.js stacks (has .lighthouserc.json)
            # This is installed from tier-4-production directly, not from ci_cd option
            'lighthouse.yml': 'Lighthouse CI' if tier == 'tier-4-production' and stack != 'ml_ai_fastapi' else None,
        }

        all_commands = []
        all_pip_packages = []

        # Parse each workflow file
        for workflow_file, description in workflow_files.items():
            if description is None:
                continue

            # Check for regular file and .template file (Python stack uses .template)
            workflow_path = workflows_dir / workflow_file
            workflow_template_path = workflows_dir / f"{workflow_file}.template"

            # Use template file if it exists, otherwise use regular file
            if workflow_template_path.exists():
                workflow_path = workflow_template_path

            if workflow_path.exists():
                print(f"  → Running {description} (from {workflow_path.name})...")
                commands, pip_packages = self._parse_workflow_commands(workflow_path, stack, project_path)
                all_commands.extend(commands)
                all_pip_packages.extend(pip_packages)

        # If no workflows found, fall back to basic checks
        if not all_commands:
            print("  ℹ No workflow commands found, running basic checks")
            return self._run_basic_fallback_checks(project_path, stack, errors, warnings)

        # Prepare venv path for Python commands
        venv_bin = project_path / "venv" / "bin" if stack == "ml_ai_fastapi" else None

        # Install pip packages for Python stack (if any found in workflows)
        if venv_bin and all_pip_packages:
            # Deduplicate packages
            unique_packages = list(set(all_pip_packages))
            if unique_packages:
                print(f"  → Installing required Python tools: {', '.join(unique_packages)}")
                pip_cmd = [str(venv_bin / "pip"), "install"] + unique_packages
                success, stdout, stderr = self._run_command(pip_cmd, project_path, timeout=600)
                if not success:
                    print(f"    ⚠ Warning: Failed to install some packages: {stderr[:100]}")

        # Run all parsed commands
        for cmd_list, step_name, is_optional in all_commands:
            print(f"    • {step_name}...", end=" ")

            # Update Python commands to use venv binaries
            if venv_bin and cmd_list:
                # Replace bare tool names with venv paths
                if cmd_list[0] in ['ruff', 'pyright', 'radon', 'vulture', 'bandit', 'pytest', 'pylint', 'mypy', 'cosmic-ray', 'cr-report']:
                    cmd_list[0] = str(venv_bin / cmd_list[0])

            # Check for directory existence before running pytest (tier-based logic)
            cmd_str = " ".join(cmd_list)
            skip_command = False
            if "pytest" in cmd_str:
                # Check if testing integration or e2e directories
                for test_dir in ["tests/integration", "tests/e2e"]:
                    if test_dir in cmd_str:
                        test_dir_path = project_path / test_dir
                        if not test_dir_path.exists():
                            # Tier-based handling
                            if tier in ['tier-1-essential', 'tier-2-standard']:
                                print(f"ℹ SKIP ({test_dir} not expected in {tier})")
                                skip_command = True
                                break
                            else:
                                # tier-3 or tier-4 - directory should exist
                                print("✗ FAILED")
                                errors.append(f"{step_name} failed: {test_dir} directory expected but not found (template issue)")
                                skip_command = True
                                break

            if skip_command:
                continue

            # Set environment variables
            test_env = {}

            # Set DATABASE_URL for all tests (SQLite for testing)
            # This is needed for Next.js apps to start (dev server for E2E tests, Jest for mutation tests)
            # For Python/FastAPI, use proper SQLite URL format
            # Include worker_id for explicit isolation (defensive, already isolated by workspace)
            if stack == "ml_ai_fastapi":
                test_env["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
            else:
                test_env["DATABASE_URL"] = f"file:./test_worker_{self.worker_id}.db"

            # Set CI=true for E2E tests
            if "test:e2e" in cmd_str or "playwright" in cmd_str or "test:a11y" in cmd_str:
                test_env["CI"] = "true"
                # Set PORT for worker-specific port assignment
                test_env["PORT"] = str(self.worker_port)

            # Set timeout based on test type
            # Optimized timeouts: generous for real work, but fail faster when broken
            if "test:mutation" in cmd_str or "stryker" in cmd_str:
                timeout = 600   # 10 minutes for mutation testing (enough for real runs)
            elif any(test in cmd_str for test in ['test', 'build', 'e2e', 'a11y']):
                timeout = 300   # 5 minutes for regular tests (plenty for working tests)
            else:
                timeout = 120   # 2 minutes default

            # Run the command
            success, stdout, stderr = self._run_command(cmd_list, project_path, timeout=timeout, env=test_env if test_env else None)

            if success:
                print("✓")
            else:
                if is_optional:
                    print("⚠ (optional)")
                    warnings.append(f"{step_name} failed (optional): {stderr[:500] if stderr else 'No error output'}")
                else:
                    # Special handling for npm audit - always treat as warning
                    if "audit" in " ".join(cmd_list):
                        print("⚠ (expected)")
                    else:
                        print("✗ FAILED")
                        # Enhanced debugging: Print both stdout and stderr for failed commands
                        if stderr:
                            print(f"\n      DEBUG - stderr: {stderr[:1000]}")
                        if stdout:
                            print(f"\n      DEBUG - stdout: {stdout[:1000]}")
                        if not stderr and not stdout:
                            print(f"\n      DEBUG - Command: {' '.join(cmd_list)}")
                            print("      DEBUG - No output captured (process may have crashed)")
                        errors.append(f"{step_name} failed: {stderr[:500] if stderr else stdout[:500] if stdout else 'No error output'}")

        # Print summary
        if warnings:
            print(f"\n  ⚠ {len(warnings)} optional check(s) had issues")

        return len(errors) == 0, errors

    def _run_basic_fallback_checks(self, project_path: Path, stack: str, errors: list[str], warnings: list[str]) -> tuple[bool, list[str]]:
        """
        Fallback to basic checks when no workflows are found.

        Args:
            project_path: Path to the project
            stack: Stack name
            errors: List to append errors to
            warnings: List to append warnings to

        Returns:
            Tuple of (success, errors)
        """
        print("  → Running basic fallback checks...")

        if stack == "ml_ai_fastapi":
            venv_bin = project_path / "venv" / "bin"
            basic_checks = [
                ([str(venv_bin / "ruff"), "check", "src/", "tests/"], "Ruff lint"),
                ([str(venv_bin / "pytest"), "-v"], "Tests"),
            ]
        else:
            basic_checks = [
                (["npm", "run", "lint"], "ESLint"),
                (["npm", "run", "test"], "Tests"),
                (["npm", "run", "build"], "Build"),
            ]

        for cmd, name in basic_checks:
            print(f"    • {name}...", end=" ")
            success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)
            if success:
                print("✓")
            else:
                print("✗ FAILED")
                errors.append(f"{name} failed: {stderr[:200] if stderr else 'No error output'}")

        return len(errors) == 0, errors

    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"test_results_{timestamp}.json"

        results_data = {
            "timestamp": timestamp,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "total_duration_seconds": sum(r.duration_seconds for r in self.results),
            "results": [asdict(r) for r in self.results]
        }

        results_file.write_text(json.dumps(results_data, indent=2))
        print(f"\n✓ Results saved to: {results_file}")

        return results_file

    def print_summary(self, total_planned: int = None):
        """Print a summary of test results"""
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        print(f"Total Tests Run: {total}")
        if total_planned and total_planned > total:
            print(f"Tests Planned: {total_planned}")
            print(f"Tests Skipped: {total_planned - total} (interrupted)")

        print(f"Passed: {passed} ({100*passed//total if total > 0 else 0}%)")
        print(f"Failed: {failed} ({100*failed//total if total > 0 else 0}%)")
        print(f"Total Duration: {sum(r.duration_seconds for r in self.results):.2f}s")

        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.success:
                    print(f"  - {r.test_id}")
                    print(f"    Stack: {r.stack}, Tier: {r.tier}, Options: {r.options}")
                    print(f"    Errors: {r.errors}")
                    print(f"    Steps Completed: {r.steps_completed}")

        print(f"{'='*80}\n")


def run_worker(worker_id: int, tests: list[TestCase], workspace_base: Path, results_dir: Path,
               cleanup: bool, use_incomplete: bool, use_validate_fix: bool, run_ci_checks: bool) -> list[TestResult]:
    """
    Worker function to run a batch of tests in parallel.
    Each worker gets its own isolated workspace.

    Args:
        worker_id: Unique identifier for this worker (0-indexed)
        tests: List of test cases to run
        workspace_base: Base workspace directory
        results_dir: Directory to save results
        cleanup: Whether to cleanup after successful tests
        use_incomplete: Whether to use --incomplete mode
        use_validate_fix: Whether to use --fix mode
        run_ci_checks: Whether to run CI checks

    Returns:
        List of TestResult objects
    """
    # Create worker-specific workspace to avoid conflicts
    worker_workspace = workspace_base / f"worker_{worker_id}"
    worker_workspace.mkdir(parents=True, exist_ok=True)

    # Create runner for this worker
    runner = TemplateTestRunner(
        workspace=worker_workspace,
        results_dir=results_dir,
        cleanup=cleanup,
        use_incomplete=use_incomplete,
        use_validate_fix=use_validate_fix,
        run_ci_checks=run_ci_checks,
        worker_id=worker_id
    )

    print(f"\n[Worker {worker_id}] Starting with {len(tests)} tests")

    # Run tests
    for i, test_case in enumerate(tests, 1):
        print(f"\n[Worker {worker_id}] Running test {i}/{len(tests)}: {test_case.id}")
        runner.run_test(test_case)

    print(f"\n[Worker {worker_id}] Completed {len(runner.results)} tests")

    return runner.results


def generate_test_cases() -> dict[int, list[TestCase]]:
    """Generate all test cases organized by phase"""

    test_cases = {1: [], 2: [], 3: [], 4: []}
    test_id = 1

    # Phase 1: Core Matrix (16 tests - all stack+tier combinations without options)
    print("Generating Phase 1 test cases...")
    for stack in STACKS:
        for tier in TIERS:
            test_cases[1].append(TestCase(
                id=f"p1_{test_id:03d}_{stack}_{tier}",
                stack=stack,
                tier=tier,
                options=[],
                phase=1,
                description=f"Core matrix: {stack} with {tier}"
            ))
            test_id += 1

    # Phase 2: Options Coverage (9 tests)
    print("Generating Phase 2 test cases...")

    # Each option individually (4 tests)
    for option in OPTIONS:
        test_cases[2].append(TestCase(
            id=f"p2_{test_id:03d}_saas_t3_tier-2_{option}",
            stack="saas_t3",
            tier="tier-2-standard",
            options=[option],
            phase=2,
            description=f"Option test: {option} only"
        ))
        test_id += 1

    # All options combined across tiers (3 tests - excluding tier-4 which is in Phase 3)
    for tier in TIERS:
        if tier == "tier-4-production":
            continue  # Skip tier-4, it's tested in Phase 3

        # For tier-1 and tier-2, exclude a11y from options
        if tier in ['tier-1-essential', 'tier-2-standard']:
            options_for_tier = [opt for opt in OPTIONS if opt != 'a11y']
        else:
            options_for_tier = OPTIONS.copy()

        test_cases[2].append(TestCase(
            id=f"p2_{test_id:03d}_saas_t3_{tier}_all_opts",
            stack="saas_t3",
            tier=tier,
            options=options_for_tier,
            phase=2,
            description=f"All options with {tier}"
        ))
        test_id += 1

    # All options combined across stacks (2 tests - excluding ml_ai_fastapi tier-4 which is in Phase 3)
    for stack in STACKS:
        if stack == "saas_t3":
            continue  # Already tested above
        if stack == "ml_ai_fastapi":
            continue  # ml_ai_fastapi tier-4 is tested in Phase 3
        test_cases[2].append(TestCase(
            id=f"p2_{test_id:03d}_{stack}_tier-3_all_opts",
            stack=stack,
            tier="tier-3-comprehensive",
            options=OPTIONS.copy(),
            phase=2,
            description=f"All options with {stack}"
        ))
        test_id += 1

    # Phase 3: Critical Paths (4 tests - production-ready combinations)
    print("Generating Phase 3 test cases...")
    critical_combinations = [
        ("saas_t3", "tier-4-production"),
        ("ml_ai_fastapi", "tier-4-production"),
        ("dashboard_refine", "tier-4-production"),
        ("fullstack_nextjs", "tier-4-production"),
    ]

    for stack, tier in critical_combinations:
        test_cases[3].append(TestCase(
            id=f"p3_{test_id:03d}_{stack}_{tier}_production",
            stack=stack,
            tier=tier,
            options=OPTIONS.copy(),
            phase=3,
            description=f"Production-ready: {stack} with {tier}"
        ))
        test_id += 1

    # Phase 4: Comprehensive Matrix (256 tests - ALL combinations)
    print("Generating Phase 4 test cases...")
    print("  → This will generate all 256 combinations (4 stacks × 4 tiers × 16 option subsets)")

    # Generate all possible option subsets (2^4 = 16 subsets)
    all_option_subsets = []
    for r in range(len(OPTIONS) + 1):  # r from 0 to 4 (inclusive)
        for subset in combinations(OPTIONS, r):
            all_option_subsets.append(list(subset))

    # Generate test case for each stack × tier × option_subset combination
    for stack in STACKS:
        for tier in TIERS:
            for option_subset in all_option_subsets:
                # Skip invalid combinations: a11y is only available in tier-3 and tier-4
                if 'a11y' in option_subset and tier in ['tier-1-essential', 'tier-2-standard']:
                    continue  # Skip this combination

                # Create a short description for the options
                if not option_subset:
                    opts_desc = "no_opts"
                elif len(option_subset) == len(OPTIONS):
                    opts_desc = "all_opts"
                else:
                    opts_desc = "_".join(option_subset)

                test_cases[4].append(TestCase(
                    id=f"p4_{test_id:03d}_{stack}_{tier}_{opts_desc}",
                    stack=stack,
                    tier=tier,
                    options=option_subset.copy(),
                    phase=4,
                    description=f"Comprehensive: {stack} + {tier} + {opts_desc}"
                ))
                test_id += 1

    print(f"  → Generated {len(test_cases[4])} comprehensive test cases")

    return test_cases


def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Solokit Template Testing")

    # Test selection arguments
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run specific phase (1=Core 16 tests, 2=Options 9 tests, 3=Critical 4 tests, 4=Comprehensive 256 tests)")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    parser.add_argument("--stack", type=str, choices=STACKS, help="Run all phase 4 tests for a specific stack (48 tests per stack)")
    parser.add_argument("--specific", nargs=3, metavar=("STACK", "TIER", "OPTIONS"),
                       help="Run specific combination (options comma-separated)")

    # Configuration arguments
    parser.add_argument("--no-cleanup", action="store_true", help="Keep test directories after success")
    parser.add_argument("--workspace", type=str, help="Custom workspace directory")
    parser.add_argument("--fix", action="store_true",
                       help="Run 'sk validate --fix' to auto-fix linting/formatting issues")
    parser.add_argument("--ci-checks", action="store_true",
                       help="Run CI/CD checks (lint, type-check, format, test, build) to simulate GitHub Actions")
    parser.add_argument("--workers", type=int, default=1,
                       help="Number of parallel workers (default: 1). Use 8 for 8x speedup on 256 tests")

    # Session completion mode (REQUIRED - mutually exclusive)
    completion_group = parser.add_mutually_exclusive_group(required=True)
    completion_group.add_argument("--complete", action="store_true",
                                 help="Run 'sk end' with full quality gates")
    completion_group.add_argument("--incomplete", action="store_true",
                                 help="Run 'sk end --incomplete' to skip quality gates")

    args = parser.parse_args()

    # Setup workspace
    workspace = Path(args.workspace) if args.workspace else WORKSPACE_BASE

    # Determine completion mode
    use_incomplete = args.incomplete  # True if --incomplete, False if --complete

    # Initialize runner
    runner = TemplateTestRunner(
        workspace=workspace,
        results_dir=RESULTS_DIR,
        cleanup=not args.no_cleanup,
        use_incomplete=use_incomplete,
        use_validate_fix=args.fix,
        run_ci_checks=args.ci_checks
    )

    # Generate test cases
    all_test_cases = generate_test_cases()

    # Determine which tests to run
    tests_to_run = []

    if args.specific:
        stack, tier, options_str = args.specific
        options = options_str.split(",") if options_str else []
        tests_to_run = [TestCase(
            id=f"custom_{stack}_{tier}",
            stack=stack,
            tier=tier,
            options=options,
            phase=0,
            description="Custom test case"
        )]
    elif args.stack:
        # Run all phase 4 tests for a specific stack (comprehensive matrix, avoids duplicates)
        tests_to_run = [test for test in all_test_cases[4] if test.stack == args.stack]
    elif args.all:
        for phase_tests in all_test_cases.values():
            tests_to_run.extend(phase_tests)
    elif args.phase:
        tests_to_run = all_test_cases[args.phase]
    else:
        parser.print_help()
        return

    # Print test plan
    print(f"\n{'='*80}")
    print("TEST EXECUTION PLAN")
    print(f"{'='*80}")
    print(f"Total tests to run: {len(tests_to_run)}")
    print(f"Workspace: {workspace}")
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Cleanup after success: {not args.no_cleanup}")
    print(f"Validate mode: {'sk validate --fix (auto-fix issues)' if args.fix else 'sk validate (check only)'}")
    print(f"Session completion mode: {'incomplete (skip quality gates)' if use_incomplete else 'complete (full quality gates)'}")
    print(f"CI/CD checks: {'enabled (simulates GitHub Actions)' if args.ci_checks else 'disabled'}")
    print(f"Parallel workers: {args.workers}")
    if args.workers > 1:
        print(f"Each worker runs ~{len(tests_to_run) // args.workers} tests")
    print(f"{'='*80}\n")

    # Run tests (sequential or parallel based on --workers)
    global _interrupted
    interrupted = False
    all_results = []

    try:
        if args.workers == 1:
            # Sequential execution (original behavior)
            for i, test_case in enumerate(tests_to_run, 1):
                if _interrupted:
                    raise KeyboardInterrupt("Interrupted by signal handler")

                print(f"\n[{i}/{len(tests_to_run)}] Running test: {test_case.id}")
                runner.run_test(test_case)

                if _interrupted:
                    raise KeyboardInterrupt("Interrupted by signal handler")

            all_results = runner.results

        else:
            # Parallel execution with multiple workers
            print(f"Splitting {len(tests_to_run)} tests across {args.workers} workers...\n")

            # Split tests using round-robin for better load balancing
            # Each worker gets every Nth test (e.g., worker 0 gets tests 0,8,16,24...)
            # This ensures all workers get a mix of fast and slow tests
            test_batches = [
                tests_to_run[i::args.workers]
                for i in range(args.workers)
            ]

            # Create worker arguments
            worker_args = [
                (
                    worker_id,
                    batch,
                    workspace,
                    RESULTS_DIR,
                    not args.no_cleanup,
                    use_incomplete,
                    args.fix,
                    args.ci_checks
                )
                for worker_id, batch in enumerate(test_batches)
            ]

            # Run workers in parallel
            with multiprocessing.Pool(processes=args.workers) as pool:
                # Use starmap to pass multiple arguments
                worker_results = pool.starmap(run_worker, worker_args)

            # Flatten results from all workers
            for results in worker_results:
                all_results.extend(results)

            print(f"\n{'='*80}")
            print(f"All {args.workers} workers completed!")
            print(f"Total tests run: {len(all_results)}")
            print(f"{'='*80}\n")

    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print("⚠ TEST SUITE INTERRUPTED BY USER (Ctrl+C)")
        print(f"{'='*80}")
        print(f"\nCompleted {len(all_results)}/{len(tests_to_run)} tests before interruption")
        interrupted = True
        _interrupted = True

    # Create a temporary runner just for saving results and printing summary
    temp_runner = TemplateTestRunner(
        workspace=workspace,
        results_dir=RESULTS_DIR,
        cleanup=not args.no_cleanup,
        use_incomplete=use_incomplete,
        use_validate_fix=args.fix,
        run_ci_checks=args.ci_checks
    )
    temp_runner.results = all_results

    # Save results
    results_file = temp_runner.save_results()

    # Print summary
    temp_runner.print_summary(total_planned=len(tests_to_run))

    if interrupted:
        print(f"\n{'='*80}")
        print("ℹ️  Test suite was interrupted - partial results saved")
        print(f"Results file: {results_file}")
        print(f"{'='*80}\n")
        sys.exit(130)  # Standard exit code for SIGINT

    # Exit with appropriate code
    failed_count = sum(1 for r in runner.results if not r.success)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
