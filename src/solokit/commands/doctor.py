"""
Doctor command for Solokit CLI.

Runs comprehensive system diagnostics to verify setup and identify configuration issues.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from solokit.core.constants import SESSION_DIR_NAME
from solokit.core.output import get_output

output = get_output()

# Minimum required versions
MIN_PYTHON_VERSION = (3, 11, 0)


@dataclass
class DiagnosticCheck:
    """Result of a diagnostic check."""

    name: str
    passed: bool
    message: str
    suggestion: str | None = None


def parse_version(version_str: str) -> tuple[int, int, int]:
    """
    Parse version string into tuple of (major, minor, patch).

    Args:
        version_str: Version string like "3.11.7" or "v2.45.0"

    Returns:
        Tuple of (major, minor, patch) as integers

    Raises:
        ValueError: If version string is malformed
    """
    # Remove 'v' prefix if present
    clean_version = version_str.strip().lstrip("v")

    # Split by '.' and take first 3 parts
    parts = clean_version.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid version format: {version_str}")

    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid version format: {version_str}") from e


def check_python_version() -> DiagnosticCheck:
    """Check if Python version meets minimum requirements."""
    current_version = sys.version_info[:3]
    version_str = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"

    if current_version >= MIN_PYTHON_VERSION:
        min_version_str = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.{MIN_PYTHON_VERSION[2]}"
        return DiagnosticCheck(
            name="Python Version",
            passed=True,
            message=f"Python {version_str} (>= {min_version_str} required)",
        )
    else:
        min_version_str = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}.{MIN_PYTHON_VERSION[2]}"
        return DiagnosticCheck(
            name="Python Version",
            passed=False,
            message=f"Python {version_str} (< {min_version_str} minimum)",
            suggestion=f"Upgrade Python to version {min_version_str} or higher",
        )


def check_git_installed() -> DiagnosticCheck:
    """Check if git is installed and accessible."""
    git_path = shutil.which("git")

    if git_path:
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            version_line = result.stdout.strip()
            return DiagnosticCheck(
                name="Git Installation",
                passed=True,
                message=f"{version_line} installed",
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return DiagnosticCheck(
                name="Git Installation",
                passed=False,
                message="Git found but not working correctly",
                suggestion="Reinstall git or check PATH configuration",
            )
    else:
        return DiagnosticCheck(
            name="Git Installation",
            passed=False,
            message="Git not found in PATH",
            suggestion="Install git: https://git-scm.com/downloads",
        )


def check_session_directory() -> DiagnosticCheck:
    """Check if .session/ directory structure exists."""
    session_dir = Path.cwd() / SESSION_DIR_NAME

    if not session_dir.exists():
        return DiagnosticCheck(
            name="Project Structure",
            passed=False,
            message=f"{SESSION_DIR_NAME}/ directory not found",
            suggestion="Run 'sk init' to initialize a Solokit project",
        )

    # Check for essential files - config.json is the only truly required file
    # work_items.json and learnings.json are created as needed
    if not (session_dir / "config.json").exists():
        return DiagnosticCheck(
            name="Project Structure",
            passed=False,
            message=f"{SESSION_DIR_NAME}/ directory missing config.json",
            suggestion="Run 'sk init' to create configuration",
        )

    return DiagnosticCheck(
        name="Project Structure",
        passed=True,
        message=f"{SESSION_DIR_NAME}/ directory exists with config.json",
    )


def check_config_valid() -> DiagnosticCheck:
    """Check if config.json is valid JSON and follows schema."""
    config_path = Path.cwd() / SESSION_DIR_NAME / "config.json"

    if not config_path.exists():
        return DiagnosticCheck(
            name="Configuration",
            passed=False,
            message="config.json not found",
            suggestion=f"Create {SESSION_DIR_NAME}/config.json or run 'sk init'",
        )

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Basic validation - just check it's a valid dict
        if not isinstance(config, dict):
            return DiagnosticCheck(
                name="Configuration",
                passed=False,
                message="config.json is not a valid object",
                suggestion="Fix config.json structure",
            )

        # Check if it has at least some configuration
        if len(config) == 0:
            return DiagnosticCheck(
                name="Configuration",
                passed=False,
                message="config.json is empty",
                suggestion="Add configuration to config.json or run 'sk init'",
            )

        return DiagnosticCheck(
            name="Configuration",
            passed=True,
            message="config.json is valid",
        )

    except json.JSONDecodeError as e:
        return DiagnosticCheck(
            name="Configuration",
            passed=False,
            message=f"config.json has invalid JSON: {str(e)}",
            suggestion="Fix JSON syntax errors in config.json",
        )
    except Exception as e:
        return DiagnosticCheck(
            name="Configuration",
            passed=False,
            message=f"Error reading config.json: {str(e)}",
            suggestion="Check file permissions and format",
        )


def check_work_items_valid() -> DiagnosticCheck:
    """Check if work_items.json is valid JSON."""
    work_items_path = Path.cwd() / SESSION_DIR_NAME / "work_items.json"

    if not work_items_path.exists():
        return DiagnosticCheck(
            name="Work Items",
            passed=True,
            message="work_items.json will be created when needed",
        )

    try:
        with open(work_items_path) as f:
            work_items = json.load(f)

        # Check if it's a list
        if not isinstance(work_items, list):
            return DiagnosticCheck(
                name="Work Items",
                passed=False,
                message="work_items.json is not a valid list",
                suggestion="Regenerate work_items.json or fix format manually",
            )

        return DiagnosticCheck(
            name="Work Items",
            passed=True,
            message=f"work_items.json is valid ({len(work_items)} items)",
        )

    except json.JSONDecodeError as e:
        return DiagnosticCheck(
            name="Work Items",
            passed=False,
            message=f"work_items.json has invalid JSON: {str(e)}",
            suggestion="Run '/work-list' to regenerate work_items.json",
        )
    except Exception as e:
        return DiagnosticCheck(
            name="Work Items",
            passed=False,
            message=f"Error reading work_items.json: {str(e)}",
            suggestion="Check file permissions",
        )


def check_quality_tools() -> DiagnosticCheck:
    """Check if quality gate tools are available."""
    tools_to_check = [
        ("pytest", "Testing framework"),
        ("ruff", "Linter and formatter"),
    ]

    available_tools = []
    missing_tools = []

    for tool, description in tools_to_check:
        if shutil.which(tool):
            available_tools.append(tool)
        else:
            missing_tools.append(f"{tool} ({description})")

    if len(available_tools) == len(tools_to_check):
        return DiagnosticCheck(
            name="Quality Tools",
            passed=True,
            message=f"All quality tools available: {', '.join(available_tools)}",
        )
    elif available_tools:
        return DiagnosticCheck(
            name="Quality Tools",
            passed=False,
            message=f"Some tools missing: {', '.join(missing_tools)}",
            suggestion="Install missing tools: pip install pytest ruff",
        )
    else:
        return DiagnosticCheck(
            name="Quality Tools",
            passed=False,
            message="No quality tools found",
            suggestion="Install quality tools: pip install pytest ruff bandit safety",
        )


def print_diagnostic_results(checks: list[DiagnosticCheck], verbose: bool = False) -> None:
    """
    Print diagnostic results in a readable format.

    Args:
        checks: List of diagnostic check results
        verbose: Whether to show verbose output
    """
    output.info("Running system diagnostics...")
    output.info("")

    for check in checks:
        status = "✓" if check.passed else "✗"
        output.info(f"{status} {check.message}")

        if not check.passed and check.suggestion:
            output.info(f"  → {check.suggestion}")

    output.info("")

    passed_count = sum(1 for c in checks if c.passed)
    total_count = len(checks)

    if passed_count == total_count:
        output.info(f"✓ All {total_count} checks passed")
    else:
        failed_count = total_count - passed_count
        output.info(f"{passed_count}/{total_count} checks passed ({failed_count} failed)")

        if not verbose:
            output.info("")
            output.info("Run with --verbose for detailed diagnostic information")


def run_diagnostics(verbose: bool = False) -> int:
    """
    Run comprehensive system diagnostics.

    Args:
        verbose: Whether to show verbose output

    Returns:
        Exit code (0 if all checks pass, 1 if any fail)
    """
    checks = [
        check_python_version(),
        check_git_installed(),
        check_session_directory(),
        check_config_valid(),
        check_work_items_valid(),
        check_quality_tools(),
    ]

    print_diagnostic_results(checks, verbose=verbose)

    return 0 if all(c.passed for c in checks) else 1


def main() -> int:
    """Main entry point for doctor command."""
    # Check if --verbose flag is present
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    return run_diagnostics(verbose=verbose)


if __name__ == "__main__":
    sys.exit(main())
