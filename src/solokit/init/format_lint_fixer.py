"""
Format and Lint Fixer Module

Runs format and lint auto-fix commands before initial commit to ensure
user-provided files (PRD.md, ROADMAP.md, etc.) pass CI quality checks.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.command_runner import CommandRunner

logger = logging.getLogger(__name__)


def run_format_lint_fix(
    template_id: str,
    project_root: Path | None = None,
) -> dict[str, bool]:
    """
    Run format and lint auto-fix commands for the project.

    This step runs silently before the initial commit to fix common issues
    in user-provided files (trailing whitespace, formatting inconsistencies).

    Args:
        template_id: Template identifier (e.g., "saas_t3", "ml_ai_fastapi")
        project_root: Project root directory (defaults to current directory)

    Returns:
        Dictionary with results:
        - format_success: True if formatting succeeded or was skipped
        - lint_success: True if linting succeeded or was skipped
    """
    if project_root is None:
        project_root = Path.cwd()

    result = {
        "format_success": True,
        "lint_success": True,
    }

    # Determine project type from template ID
    if template_id == "ml_ai_fastapi":
        result = _run_python_fixes(project_root)
    else:
        # Node.js-based templates (saas_t3, dashboard_refine, fullstack_nextjs)
        result = _run_nodejs_fixes(project_root)

    return result


def _run_nodejs_fixes(project_root: Path) -> dict[str, bool]:
    """
    Run format and lint fixes for Node.js projects.

    Uses npm scripts defined in package.json:
    - npm run format (Prettier)
    - npm run lint:fix (ESLint)
    """
    result = {
        "format_success": True,
        "lint_success": True,
    }

    # Check if package.json exists
    package_json = project_root / "package.json"
    if not package_json.exists():
        logger.debug("No package.json found, skipping Node.js format/lint fix")
        return result

    runner = CommandRunner(default_timeout=120, working_dir=project_root)

    # Run prettier format
    logger.debug("Running Prettier format...")
    format_result = runner.run(
        ["npm", "run", "format"],
        check=False,
    )

    if format_result.success:
        logger.debug("Prettier format completed successfully")
    else:
        result["format_success"] = False
        logger.warning("Prettier format failed (non-critical)")
        logger.debug(f"Format error: {format_result.stderr}")

    # Run ESLint fix
    logger.debug("Running ESLint fix...")
    lint_result = runner.run(
        ["npm", "run", "lint:fix"],
        check=False,
    )

    if lint_result.success:
        logger.debug("ESLint fix completed successfully")
    else:
        result["lint_success"] = False
        logger.warning("ESLint fix failed (non-critical)")
        logger.debug(f"Lint error: {lint_result.stderr}")

    return result


def _run_python_fixes(project_root: Path) -> dict[str, bool]:
    """
    Run format and lint fixes for Python projects.

    Uses ruff for both formatting and linting:
    - ruff format . (formatting)
    - ruff check --fix . (linting)

    Runs within the virtual environment if available.
    """
    result = {
        "format_success": True,
        "lint_success": True,
    }

    runner = CommandRunner(default_timeout=120, working_dir=project_root)

    # Determine ruff path (prefer venv if available)
    venv_path = project_root / "venv"
    if venv_path.exists():
        ruff_path = venv_path / "bin" / "ruff"
        if not ruff_path.exists():
            # Windows
            ruff_path = venv_path / "Scripts" / "ruff"
        if not ruff_path.exists():
            # Fall back to system ruff
            ruff_path = Path("ruff")
    else:
        ruff_path = Path("ruff")

    ruff_cmd = str(ruff_path)

    # Run ruff format
    logger.debug("Running ruff format...")
    format_result = runner.run(
        [ruff_cmd, "format", "."],
        check=False,
    )

    if format_result.success:
        logger.debug("Ruff format completed successfully")
    else:
        result["format_success"] = False
        logger.warning("Ruff format failed (non-critical)")
        logger.debug(f"Format error: {format_result.stderr}")

    # Run ruff check --fix
    logger.debug("Running ruff check --fix...")
    lint_result = runner.run(
        [ruff_cmd, "check", "--fix", "."],
        check=False,
    )

    if lint_result.success:
        logger.debug("Ruff lint fix completed successfully")
    else:
        result["lint_success"] = False
        logger.warning("Ruff lint fix failed (non-critical)")
        logger.debug(f"Lint error: {lint_result.stderr}")

    return result
