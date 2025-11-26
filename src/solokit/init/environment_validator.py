"""
Environment Validator Module

Validates and optionally auto-updates environment (Python, Node.js) for template installation.
"""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Literal

from solokit.core.command_runner import CommandRunner
from solokit.core.exceptions import ErrorCode, ValidationError

logger = logging.getLogger(__name__)

MIN_NODE_VERSION = (18, 0, 0)
MIN_PYTHON_VERSION = (3, 11, 0)


def parse_version(version_str: str) -> tuple[int, int, int]:
    """
    Parse version string into tuple of (major, minor, patch).

    Args:
        version_str: Version string like "18.0.0" or "v18.0.0" or "3.11.7" or "3.11.0rc1"

    Returns:
        Tuple of (major, minor, patch) as integers

    Raises:
        ValueError: If version string is malformed
    """
    # Remove 'v' prefix if present
    clean_version = version_str.strip().lstrip("v")

    # Remove pre-release suffixes (rc, alpha, beta, dev, etc.)
    # Match version numbers before any non-numeric suffix
    version_match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", clean_version)
    if not version_match:
        raise ValueError(f"Invalid version format: {version_str}")

    try:
        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        patch = int(version_match.group(3)) if version_match.group(3) else 0
        return (major, minor, patch)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid version format: {version_str}") from e


def check_node_version() -> tuple[bool, str | None]:
    """
    Check if Node.js is installed and meets minimum version requirement.

    Returns:
        Tuple of (meets_requirement: bool, current_version: str | None)
        - meets_requirement: True if Node.js >= 18.0.0
        - current_version: Version string or None if not installed
    """
    # Check if node is available
    node_path = shutil.which("node")
    if not node_path:
        return False, None

    # Use absolute path and increased timeout to avoid shell initialization issues
    runner = CommandRunner(default_timeout=15)
    result = runner.run([node_path, "--version"], check=False)

    if not result.success:
        return False, None

    version_str = result.stdout.strip()
    try:
        version = parse_version(version_str)
        meets_req = version >= MIN_NODE_VERSION
        return meets_req, version_str
    except ValueError:
        logger.warning(f"Could not parse Node.js version: {version_str}")
        return False, version_str


def check_python_version(
    specific_binary: str | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Check if Python is installed and meets minimum version requirement.

    Args:
        specific_binary: Specific Python binary to check (e.g., "python3.11").
                        If None, checks "python3" and "python".

    Returns:
        Tuple of (meets_requirement: bool, current_version: str | None, binary_path: str | None)
        - meets_requirement: True if Python >= 3.11.0
        - current_version: Version string or None if not installed
        - binary_path: Path to the Python binary or None
    """
    binaries_to_check = (
        [specific_binary] if specific_binary else ["python3", "python", "python3.11"]
    )

    for binary in binaries_to_check:
        binary_path = shutil.which(binary)
        if not binary_path:
            continue

        # Use absolute path and increased timeout to avoid shell initialization issues
        runner = CommandRunner(default_timeout=15)
        result = runner.run([binary_path, "--version"], check=False)

        if not result.success:
            continue

        # Python --version outputs to stdout (Python 3.x) or stderr (Python 2.x)
        version_output = result.stdout or result.stderr
        version_str = version_output.strip().replace("Python ", "")

        try:
            version = parse_version(version_str)
            meets_req = version >= MIN_PYTHON_VERSION
            return meets_req, version_str, binary_path
        except ValueError:
            logger.warning(f"Could not parse Python version from {binary}: {version_str}")
            continue

    return False, None, None


def check_git_installed() -> tuple[bool, str | None]:
    """
    Check if git is installed and return version.

    Returns:
        Tuple of (installed: bool, version: str | None)
        - installed: True if git is available
        - version: Version string or None if not installed
    """
    git_path = shutil.which("git")
    if not git_path:
        return False, None

    runner = CommandRunner(default_timeout=15)
    result = runner.run([git_path, "--version"], check=False)

    if not result.success:
        return False, None

    # git --version outputs "git version 2.39.0" or similar
    version_output = result.stdout.strip()
    version_match = re.search(r"git version (\d+\.\d+(?:\.\d+)?)", version_output)
    if version_match:
        return True, version_match.group(1)

    return True, version_output  # Return raw output if parsing fails


def check_gh_installed() -> tuple[bool, str | None, bool]:
    """
    Check if GitHub CLI (gh) is installed and authenticated.

    Returns:
        Tuple of (installed: bool, version: str | None, authenticated: bool)
        - installed: True if gh CLI is available
        - version: Version string or None if not installed
        - authenticated: True if user is logged in to GitHub
    """
    gh_path = shutil.which("gh")
    if not gh_path:
        return False, None, False

    runner = CommandRunner(default_timeout=15)

    # Get version
    version_result = runner.run([gh_path, "--version"], check=False)
    version = None
    if version_result.success:
        # gh version 2.40.0 (2023-12-13)
        version_match = re.search(r"gh version (\d+\.\d+\.\d+)", version_result.stdout)
        if version_match:
            version = version_match.group(1)

    # Check authentication status
    auth_result = runner.run([gh_path, "auth", "status"], check=False)
    authenticated = auth_result.returncode == 0

    return True, version, authenticated


def attempt_node_install_with_nvm() -> tuple[bool, str]:
    """
    Attempt to install Node.js >= 18.0.0 using nvm if available.

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if nvm is available
    nvm_dir = Path.home() / ".nvm"
    if not nvm_dir.exists():
        return (
            False,
            "nvm not found. Please install Node.js 18+ manually:\n"
            "  macOS:   brew install node      # Latest LTS (Node 20+)\n"
            "  Ubuntu:  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -\n"
            "           sudo apt-get install -y nodejs",
        )

    # Try to source nvm and install Node.js 18
    runner = CommandRunner(default_timeout=300)

    # nvm install command needs to be run in a shell environment
    nvm_script = f"""
    export NVM_DIR="{nvm_dir}"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
    """

    result = runner.run(["bash", "-c", nvm_script], check=False)

    if result.success:
        logger.info("Successfully installed Node.js 18 via nvm")
        return True, "Node.js 18 installed successfully via nvm"
    else:
        return (
            False,
            f"nvm installation failed: {result.stderr}\n\n"
            "Please install Node.js 18+ manually:\n"
            "  macOS:   brew install node      # Latest LTS (Node 20+)\n"
            "  Ubuntu:  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -\n"
            "           sudo apt-get install -y nodejs",
        )


def attempt_python_install_with_pyenv(version: str = "3.11") -> tuple[bool, str]:
    """
    Attempt to install Python using pyenv if available.

    Args:
        version: Python version to install (e.g., "3.11")

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if pyenv is available
    if not shutil.which("pyenv"):
        return (
            False,
            f"pyenv not found. Please install Python {version}+ manually:\n"
            f"  macOS:   brew install python@{version}\n"
            f"  Ubuntu:  sudo apt install python{version} python{version}-venv",
        )

    # Try to install Python via pyenv
    runner = CommandRunner(default_timeout=600)  # Python builds can take time

    # Install latest 3.11.x
    result = runner.run(["pyenv", "install", "-s", version], check=False)

    if result.success:
        logger.info(f"Successfully installed Python {version} via pyenv")
        return True, f"Python {version} installed successfully via pyenv"
    else:
        return (
            False,
            f"pyenv installation failed: {result.stderr}\n\n"
            f"Please install Python {version}+ manually:\n"
            f"  macOS:   brew install python@{version}\n"
            f"  Ubuntu:  sudo apt install python{version} python{version}-venv",
        )


def validate_environment(
    stack_type: Literal["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"],
    auto_update: bool = True,
) -> dict[str, bool | str | None | list[str]]:
    """
    Validate environment for a specific stack and optionally auto-update.

    Args:
        stack_type: Type of stack to validate for
        auto_update: If True, attempt to auto-install missing requirements

    Returns:
        Dictionary with validation results:
        {
            "git_ok": bool,
            "git_version": str | None,
            "node_ok": bool,
            "node_version": str | None,
            "python_ok": bool,
            "python_version": str | None,
            "python_binary": str | None,
            "errors": list[str],
            "warnings": list[str]
        }

    Raises:
        ValidationError: If required environment cannot be satisfied
    """
    errors: list[str] = []
    warnings: list[str] = []

    result: dict[str, bool | str | None | list[str]] = {
        "git_ok": True,
        "git_version": None,
        "node_ok": True,
        "node_version": None,
        "python_ok": True,
        "python_version": None,
        "python_binary": None,
        "errors": errors,
        "warnings": warnings,
    }

    # Check git (required for all stacks)
    git_ok, git_version = check_git_installed()
    result["git_ok"] = git_ok
    result["git_version"] = git_version

    if not git_ok:
        errors.append(
            "git is required but not installed.\n"
            "Please install git:\n"
            "  macOS:   xcode-select --install   # or: brew install git\n"
            "  Ubuntu:  sudo apt install git\n"
            "  Windows: https://git-scm.com/download/win"
        )

    # Check Node.js for Next.js-based stacks
    if stack_type in ["saas_t3", "dashboard_refine", "fullstack_nextjs"]:
        node_ok, node_version = check_node_version()
        result["node_ok"] = node_ok
        result["node_version"] = node_version

        if not node_ok:
            if auto_update:
                logger.info("Node.js 18+ not found, attempting to install via nvm...")
                success, message = attempt_node_install_with_nvm()
                if success:
                    # Re-check after installation
                    node_ok, node_version = check_node_version()
                    result["node_ok"] = node_ok
                    result["node_version"] = node_version
                    if node_ok:
                        logger.info(f"Node.js {node_version} is now available")
                    else:
                        errors.append(
                            f"Auto-installation succeeded but Node.js still not detected\n{message}"
                        )
                else:
                    errors.append(message)
            else:
                errors.append(
                    f"Node.js 18+ required but {'not installed' if node_version is None else f'found {node_version}'}\n"
                    "Install Node.js 18+ and try again"
                )

    # Check Python for ML/AI stack
    if stack_type == "ml_ai_fastapi":
        python_ok, python_version, python_binary = check_python_version()
        result["python_ok"] = python_ok
        result["python_version"] = python_version
        result["python_binary"] = python_binary

        if not python_ok:
            # Try to find python3.11 specifically
            python_ok_311, python_version_311, python_binary_311 = check_python_version(
                "python3.11"
            )
            if python_ok_311:
                result["python_ok"] = True
                result["python_version"] = python_version_311
                result["python_binary"] = python_binary_311
                logger.info(f"Found Python {python_version_311} at {python_binary_311}")
            elif auto_update:
                logger.info("Python 3.11+ not found, attempting to install via pyenv...")
                success, message = attempt_python_install_with_pyenv()
                if success:
                    # Re-check after installation
                    python_ok, python_version, python_binary = check_python_version("python3.11")
                    result["python_ok"] = python_ok
                    result["python_version"] = python_version
                    result["python_binary"] = python_binary
                    if python_ok:
                        logger.info(f"Python {python_version} is now available")
                    else:
                        errors.append(
                            f"Auto-installation succeeded but Python 3.11+ still not detected\n{message}"
                        )
                else:
                    errors.append(message)
            else:
                errors.append(
                    f"Python 3.11+ required but {'not installed' if python_version is None else f'found {python_version}'}\n"
                    "Install Python 3.11+ and try again"
                )

    # Raise validation error if there are blocking errors
    if errors:
        error_msg = "Environment validation failed:\n\n" + "\n\n".join(errors)

        raise ValidationError(
            message=error_msg,
            code=ErrorCode.INVALID_CONFIGURATION,
            context={
                "stack_type": stack_type,
                "git_ok": result["git_ok"],
                "node_ok": result["node_ok"],
                "python_ok": result["python_ok"],
            },
            remediation="Install required tools and try again",
        )

    return result
