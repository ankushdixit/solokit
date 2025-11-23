"""
Dependency Installer Module

Handles dependency installation using exact versions from stack-versions.yaml.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from solokit.core.command_runner import CommandRunner
from solokit.core.exceptions import CommandExecutionError, FileOperationError
from solokit.core.output import get_output

logger = logging.getLogger(__name__)
output = get_output()


def load_stack_versions() -> dict[str, Any]:
    """
    Load validated versions from stack-versions.yaml.

    Returns:
        Stack versions dictionary

    Raises:
        FileOperationError: If file not found or invalid YAML
    """
    versions_file = Path(__file__).parent.parent / "templates" / "stack-versions.yaml"

    if not versions_file.exists():
        raise FileOperationError(
            operation="load",
            file_path=str(versions_file),
            details="stack-versions.yaml not found",
        )

    try:
        with open(versions_file) as f:
            return cast(dict[str, Any], yaml.safe_load(f))
    except yaml.YAMLError as e:
        raise FileOperationError(
            operation="parse",
            file_path=str(versions_file),
            details=f"Invalid YAML: {str(e)}",
            cause=e,
        )


def get_installation_commands(
    stack_id: str,
    tier: str,
) -> dict[str, Any]:
    """
    Get installation commands for a stack and tier.

    Args:
        stack_id: Stack identifier (e.g., "saas_t3")
        tier: Tier level (e.g., "tier-1")

    Returns:
        Installation commands dictionary from stack-versions.yaml

    Raises:
        FileOperationError: If stack or tier not found
    """
    versions = load_stack_versions()

    if stack_id not in versions["stacks"]:
        raise FileOperationError(
            operation="lookup",
            file_path="stack-versions.yaml",
            details=f"Stack '{stack_id}' not found in versions file",
        )

    stack = versions["stacks"][stack_id]

    if "installation" not in stack:
        raise FileOperationError(
            operation="lookup",
            file_path="stack-versions.yaml",
            details=f"No installation commands found for stack '{stack_id}'",
        )

    return cast(dict[str, Any], stack["installation"])


def install_npm_dependencies(
    template_id: str,
    tier: Literal[
        "tier-1-essential", "tier-2-standard", "tier-3-comprehensive", "tier-4-production"
    ],
    project_root: Path | None = None,
) -> bool:
    """
    Install npm dependencies for a Next.js-based stack.

    Args:
        template_id: Template identifier (e.g., "saas_t3")
        tier: Quality tier
        project_root: Project root directory

    Returns:
        True if installation succeeded

    Raises:
        CommandExecutionError: If npm installation fails critically
    """
    if project_root is None:
        project_root = Path.cwd()

    # Map template_id to stack_id
    template_to_stack = {
        "saas_t3": "saas_t3",
        "dashboard_refine": "dashboard_refine",
        "fullstack_nextjs": "fullstack_nextjs",
    }

    stack_id = template_to_stack.get(template_id)
    if not stack_id:
        logger.warning(f"Unknown template ID: {template_id}")
        return False

    # Get installation commands
    installation = get_installation_commands(stack_id, tier)

    logger.info("Installing npm dependencies...")
    logger.info("This may take several minutes...")

    runner = CommandRunner(default_timeout=600, working_dir=project_root)  # 10 min timeout

    # Map tier to command keys
    tier_to_command_key = {
        "tier-1-essential": ["base", "tier1"],
        "tier-2-standard": ["base", "tier1", "tier2"],
        "tier-3-comprehensive": ["base", "tier1", "tier2", "tier3"],
        "tier-4-production": ["base", "tier1", "tier2", "tier3", "tier4_dev", "tier4_prod"],
    }

    # Human-readable descriptions for each command key
    command_descriptions = {
        "base": "core framework packages",
        "tier1": "essential quality tools (ESLint, Prettier, Jest)",
        "tier2": "standard quality tools (Husky, lint-staged)",
        "tier3": "comprehensive quality tools (Playwright, Stryker)",
        "tier4_dev": "production dev tools (bundle analyzer)",
        "tier4_prod": "production monitoring (Sentry, OpenTelemetry)",
    }

    command_keys = tier_to_command_key.get(tier, ["base"])
    total_steps = len(command_keys)

    # Run installation commands sequentially
    for idx, command_key in enumerate(command_keys, 1):
        if command_key not in installation["commands"]:
            logger.warning(f"Command key '{command_key}' not found for {stack_id}")
            continue

        command_str = installation["commands"][command_key]
        description = command_descriptions.get(command_key, command_key)
        logger.info(f"Running: {command_key}...")
        output.info(f"   [{idx}/{total_steps}] Installing {description}...")

        # Parse command string and run
        result = runner.run(["sh", "-c", command_str], check=False)

        if not result.success:
            logger.error(f"Failed to install {command_key}: {result.stderr}")
            raise CommandExecutionError(
                command=command_str,
                returncode=result.returncode,
                stderr=result.stderr,
                context={"tier": tier, "command_key": command_key},
            )

        logger.info(f"✓ Installed {command_key}")

    # Install Playwright browsers for tier-3+ (required for E2E tests)
    if tier in ["tier-3-comprehensive", "tier-4-production"]:
        import os
        import platform

        if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
            # Browsers pre-installed globally (e.g., in CI environment)
            logger.info("✓ Using pre-installed Playwright browsers")
            output.info("   Using pre-installed Playwright browsers")
        else:
            is_linux = platform.system() == "Linux"

            if is_linux:
                # On Linux, we need system dependencies for browsers to launch
                # First fix the common apt_pkg Python module issue on Ubuntu
                logger.info("Installing Playwright system dependencies (Linux)...")
                output.info("   Installing Playwright system dependencies (Linux)...")

                # Fix apt_pkg module issue (common on Ubuntu 22.04 with Python version mismatch)
                # This creates a symlink so apt_pkg works with the current Python version
                fix_apt_pkg_cmd = (
                    "sudo apt-get install -y python3-apt > /dev/null 2>&1; "
                    "cd /usr/lib/python3/dist-packages && "
                    "sudo ln -sf apt_pkg.cpython-*-x86_64-linux-gnu.so apt_pkg.so 2>/dev/null; "
                    "cd -"
                )
                runner.run(["bash", "-c", fix_apt_pkg_cmd], check=False, timeout=60)

                # Now run playwright install-deps (the official way to install system deps)
                deps_result = runner.run(
                    ["sudo", "npx", "playwright", "install-deps"],
                    check=False,
                    timeout=300,
                )
                if deps_result.success:
                    logger.info("✓ Playwright system dependencies installed")
                else:
                    logger.warning("Could not install system dependencies (may need sudo)")
                    logger.debug(f"install-deps error: {deps_result.stderr}")

            logger.info("Installing Playwright browsers (required for E2E tests)...")
            logger.info("This may take a few minutes on first run...")
            output.info("   Installing Playwright browsers (this may take a few minutes)...")

            browser_result = runner.run(
                ["npx", "playwright", "install"],
                check=False,
                timeout=300,  # 5 minutes for browser download
            )

            if browser_result.success:
                logger.info("✓ Playwright browsers installed")
                output.info("   ✓ Playwright browsers installed")
            else:
                # Non-critical - warn but don't fail
                logger.warning("Playwright browser installation failed")
                logger.warning("Run 'npx playwright install' manually before E2E tests")
                output.warning(
                    "Playwright browsers not installed (run 'npx playwright install' later)"
                )
                if browser_result.stderr:
                    logger.debug(f"Playwright install error: {browser_result.stderr}")

    logger.info("✅ All npm dependencies installed successfully")
    return True


def install_python_dependencies(
    tier: Literal[
        "tier-1-essential", "tier-2-standard", "tier-3-comprehensive", "tier-4-production"
    ],
    python_binary: str | None = None,
    project_root: Path | None = None,
) -> bool:
    """
    Install Python dependencies for ML/AI FastAPI stack.

    Args:
        tier: Quality tier
        python_binary: Python binary to use (e.g., "python3.11")
        project_root: Project root directory

    Returns:
        True if installation succeeded

    Raises:
        CommandExecutionError: If pip installation fails critically
    """
    if project_root is None:
        project_root = Path.cwd()

    if python_binary is None:
        python_binary = sys.executable

    # Get installation commands
    installation = get_installation_commands("ml_ai_fastapi", tier)

    logger.info("Setting up Python virtual environment...")
    output.info("   Setting up Python virtual environment...")

    runner = CommandRunner(default_timeout=600, working_dir=project_root)

    # Create virtual environment
    venv_path = project_root / "venv"
    if not venv_path.exists():
        result = runner.run([python_binary, "-m", "venv", "venv"], check=False)
        if not result.success:
            raise CommandExecutionError(
                command=f"{python_binary} -m venv venv",
                returncode=result.returncode,
                stderr=result.stderr,
            )
        logger.info("✓ Created virtual environment")
        output.info("   ✓ Created virtual environment")
    else:
        logger.info("Virtual environment already exists")
        output.info("   ✓ Virtual environment already exists")

    # Determine pip path
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        # Windows
        pip_path = venv_path / "Scripts" / "pip"

    # Upgrade pip
    logger.info("Upgrading pip...")
    output.info("   Upgrading pip...")
    result = runner.run([str(pip_path), "install", "--upgrade", "pip"], check=False)
    if result.success:
        logger.info("✓ Upgraded pip")

    # Install dependencies
    logger.info("Installing Python dependencies...")
    logger.info("This may take several minutes...")

    # Map tier to command keys (incremental installation)
    tier_to_command_key = {
        "tier-1-essential": ["base", "tier1"],
        "tier-2-standard": ["base", "tier1", "tier2"],
        "tier-3-comprehensive": ["base", "tier1", "tier2", "tier3"],
        "tier-4-production": ["base", "tier1", "tier2", "tier3", "tier4_dev", "tier4_prod"],
    }

    # Human-readable descriptions for each command key
    command_descriptions = {
        "base": "core framework packages (FastAPI, SQLModel, Pydantic)",
        "tier1": "essential quality tools (pytest, ruff, mypy)",
        "tier2": "standard quality tools (pre-commit, coverage)",
        "tier3": "comprehensive quality tools (hypothesis, locust)",
        "tier4_dev": "production dev tools (profiling, debugging)",
        "tier4_prod": "production monitoring (Sentry, Prometheus)",
    }

    command_keys = tier_to_command_key.get(tier, ["base"])
    total_steps = len(command_keys)

    for idx, command_key in enumerate(command_keys, 1):
        if command_key not in installation["commands"]:
            logger.warning(f"Command key '{command_key}' not found for ml_ai_fastapi")
            continue

        command_str = installation["commands"][command_key]
        # Replace 'pip install' with full pip path
        command_str = command_str.replace("pip install", f"{pip_path} install")

        description = command_descriptions.get(command_key, command_key)
        logger.info(f"Running: {command_key}...")
        output.info(f"   [{idx}/{total_steps}] Installing {description}...")

        result = runner.run(["sh", "-c", command_str], check=False)

        if not result.success:
            logger.error(f"Failed to install {command_key}: {result.stderr}")
            raise CommandExecutionError(
                command=command_str,
                returncode=result.returncode,
                stderr=result.stderr,
                context={"tier": tier, "command_key": command_key},
            )

        logger.info(f"✓ Installed {command_key}")

    # Run security fixes if available
    if "security_fixes" in installation["commands"]:
        logger.info("Applying security fixes...")
        output.info("   Applying security fixes...")
        command_str = installation["commands"]["security_fixes"]
        command_str = command_str.replace("pip install", f"{pip_path} install")

        result = runner.run(["sh", "-c", command_str], check=False)
        if result.success:
            logger.info("✓ Applied security fixes")
        else:
            logger.warning("Security fixes failed (non-critical)")
            output.warning("Security fixes failed (non-critical)")

    logger.info("✅ All Python dependencies installed successfully")
    return True


def install_dependencies(
    template_id: str,
    tier: Literal[
        "tier-1-essential", "tier-2-standard", "tier-3-comprehensive", "tier-4-production"
    ],
    python_binary: str | None = None,
    project_root: Path | None = None,
) -> bool:
    """
    Install dependencies for a template based on its package manager.

    Args:
        template_id: Template identifier
        tier: Quality tier
        python_binary: Python binary for Python projects
        project_root: Project root directory

    Returns:
        True if installation succeeded

    Raises:
        CommandExecutionError: If installation fails critically
    """
    # Determine package manager from template ID
    if template_id == "ml_ai_fastapi":
        return install_python_dependencies(tier, python_binary, project_root)
    else:
        return install_npm_dependencies(template_id, tier, project_root)
