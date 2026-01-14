"""
Initial Commit Module

Creates initial git commit after template initialization.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import GIT_STANDARD_TIMEOUT

logger = logging.getLogger(__name__)


def create_commit_message(
    template_name: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str],
    stack_info: dict[str, str],
) -> str:
    """
    Create commit message for initial commit.

    Args:
        template_name: Template display name
        tier: Quality tier
        coverage_target: Coverage target percentage
        additional_options: List of additional options
        stack_info: Stack information dictionary

    Returns:
        Formatted commit message
    """
    # Format additional options
    options_str = ", ".join(
        opt.replace("_", " ").title() if isinstance(opt, str) else str(opt)
        for opt in additional_options
    )
    if not options_str:
        options_str = "None"

    # Format stack info
    stack_lines = []
    for key, value in stack_info.items():
        formatted_key = key.replace("_", " ").title()
        stack_lines.append(f"- {formatted_key}: {value}")
    stack_str = "\n".join(stack_lines)

    # Format tier name
    tier_name = tier.replace("tier-", "Tier ").replace("-", " ").title()

    message = f"""chore: Initialize project with Solokit template system

Template: {template_name}
Quality Tier: {tier_name}
Coverage Target: {coverage_target}%
Additional Options: {options_str}

Stack:
{stack_str}

Generated files:
- Project configuration and structure
- Quality gate configs ({tier_name})
- Session tracking infrastructure
- Documentation templates

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    return message


def create_initial_commit(
    template_name: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str],
    stack_info: dict[str, str],
    project_root: Path | None = None,
) -> bool:
    """
    Create initial commit after project initialization.

    Args:
        template_name: Template display name
        tier: Quality tier
        coverage_target: Coverage target percentage
        additional_options: List of additional options
        stack_info: Stack information dictionary
        project_root: Root directory of the project

    Returns:
        True if initial commit was created or already exists.
    """
    if project_root is None:
        project_root = Path.cwd()

    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT, working_dir=project_root)

    try:
        # Check if repository has any commits by trying to count them
        # This will fail gracefully if no commits exist yet
        result = runner.run(["git", "rev-list", "--count", "--all"], check=False)

        if result.success and result.stdout.strip() and int(result.stdout.strip()) > 0:
            logger.info("Git repository already has commits, skipping initial commit")
            return True

    except Exception:
        # If command fails (e.g., no commits yet), continue to create initial commit
        pass

    try:
        # Stage all initialized files
        result = runner.run(["git", "add", "-A"], check=True)
        if not result.success:
            logger.warning(f"Git add failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        # Create commit message
        commit_message = create_commit_message(
            template_name, tier, coverage_target, additional_options, stack_info
        )

        # Create initial commit
        result = runner.run(["git", "commit", "-m", commit_message], check=True)
        if not result.success:
            logger.warning(f"Git commit failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        logger.info("Created initial commit on main branch")
        return True

    except Exception as e:
        logger.warning(f"Failed to create initial commit: {e}")
        logger.warning("You may need to commit manually before starting sessions")
        return False


def create_minimal_initial_commit(project_root: Path | None = None) -> bool:
    """
    Create initial commit for minimal init mode.

    Args:
        project_root: Root directory of the project

    Returns:
        True if initial commit was created or already exists.
    """
    if project_root is None:
        project_root = Path.cwd()

    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT, working_dir=project_root)

    try:
        # Check if repository has any commits
        result = runner.run(["git", "rev-list", "--count", "--all"], check=False)

        if result.success and result.stdout.strip() and int(result.stdout.strip()) > 0:
            logger.info("Git repository already has commits, skipping initial commit")
            return True

    except Exception:
        pass

    try:
        # Stage all initialized files
        result = runner.run(["git", "add", "-A"], check=True)
        if not result.success:
            logger.warning(f"Git add failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        # Create minimal commit message
        commit_message = """chore: Initialize project with Solokit (minimal mode)

Session-driven development infrastructure:
- Session tracking (.session/)
- Claude Code slash commands (.claude/commands/)
- Documentation (CLAUDE.md, README.md, CHANGELOG.md)

Quality gates: disabled (minimal mode)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        # Create initial commit
        result = runner.run(["git", "commit", "-m", commit_message], check=True)
        if not result.success:
            logger.warning(f"Git commit failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        logger.info("Created initial commit on main branch")
        return True

    except Exception as e:
        logger.warning(f"Failed to create initial commit: {e}")
        logger.warning("You may need to commit manually before starting sessions")
        return False
