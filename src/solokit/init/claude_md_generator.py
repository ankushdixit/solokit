"""
CLAUDE.md Generator Module

Generates project CLAUDE.md with stack-specific guidance and project configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError
from solokit.init.template_installer import get_template_info, load_template_registry

logger = logging.getLogger(__name__)


def _get_solokit_version() -> str:
    """
    Get the current Solokit version.

    Returns:
        Version string
    """
    try:
        from importlib.metadata import version

        return version("solokit")
    except Exception:
        return "unknown"


def _format_additional_options(additional_options: list[str], registry: dict) -> str:
    """
    Format additional options for display.

    Args:
        additional_options: List of option IDs
        registry: Template registry

    Returns:
        Formatted options string or "None"
    """
    if not additional_options:
        return "None"

    additional_options_registry = registry.get("additional_options", {})
    option_names = []

    for option in additional_options:
        option_info = additional_options_registry.get(option, {})
        option_name = option_info.get("name", option.replace("_", " ").title())
        option_names.append(option_name)

    return ", ".join(option_names)


def _get_tier_specific_requirements(tier: str, registry: dict) -> str:
    """
    Generate tier-specific requirements section.

    Args:
        tier: Quality tier ID
        registry: Template registry

    Returns:
        Formatted tier requirements markdown
    """
    tier_order = [
        "tier-1-essential",
        "tier-2-standard",
        "tier-3-comprehensive",
        "tier-4-production",
    ]

    requirements = ""

    # Tier 2+: Pre-commit hooks
    if tier in tier_order[1:]:
        requirements += "**Tier 2+ (Standard and above)**:\n\n"
        requirements += "- [ ] Pre-commit hooks pass\n"
        requirements += "- [ ] No secrets in code (git-secrets)\n"
        requirements += "- [ ] No dependency vulnerabilities\n\n"

    # Tier 3+: Advanced testing
    if tier in tier_order[2:]:
        requirements += "**Tier 3+ (Comprehensive and above)**:\n\n"
        requirements += "- [ ] E2E tests pass (for JS stacks)\n"
        requirements += "- [ ] Load tests pass (for Python stacks)\n"
        requirements += "- [ ] Code complexity within limits\n"
        requirements += "- [ ] No code duplication detected\n"
        requirements += "- [ ] Mutation testing score >75%\n\n"

    # Tier 4: Production requirements
    if tier == "tier-4-production":
        requirements += "**Tier 4 (Production-Ready)**:\n\n"
        requirements += (
            "- [ ] Lighthouse CI passes (JS stacks: performance >90, accessibility >90)\n"
        )
        requirements += "- [ ] Security audit passes (no vulnerabilities)\n"
        requirements += "- [ ] Bundle size within limits (JS stacks)\n"
        requirements += "- [ ] API documentation complete (Python stacks)\n"

    return requirements.strip()


def generate_claude_md(
    template_id: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str],
    project_root: Path | None = None,
) -> Path:
    """
    Generate CLAUDE.md for the project.

    Args:
        template_id: Template identifier
        tier: Quality tier
        coverage_target: Test coverage target percentage
        additional_options: List of additional options installed
        project_root: Project root directory

    Returns:
        Path to generated CLAUDE.md

    Raises:
        FileOperationError: If CLAUDE.md generation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    template_info = get_template_info(template_id)
    registry = load_template_registry()

    tier_info = registry["quality_tiers"].get(tier, {})

    # Get project name from directory
    project_name = project_root.name

    # Read the CLAUDE.md.template file
    template_path = (
        Path(__file__).parent.parent / "templates" / template_id / "base" / "CLAUDE.md.template"
    )

    if not template_path.exists():
        raise FileOperationError(
            operation="read",
            file_path=str(template_path),
            details=f"CLAUDE.md.template not found for template {template_id}",
        )

    try:
        template_content = template_path.read_text()
    except Exception as e:
        raise FileOperationError(
            operation="read",
            file_path=str(template_path),
            details=f"Failed to read CLAUDE.md.template: {str(e)}",
            cause=e,
        )

    # Replace placeholders
    claude_content = template_content.replace("{project_name}", project_name)
    claude_content = claude_content.replace("{template_name}", template_info["display_name"])
    claude_content = claude_content.replace("{template_id}", template_id)
    claude_content = claude_content.replace("{tier}", tier)
    claude_content = claude_content.replace("{tier_name}", tier_info.get("name", tier))
    claude_content = claude_content.replace("{coverage_target}", str(coverage_target))
    claude_content = claude_content.replace("{package_manager}", template_info["package_manager"])
    claude_content = claude_content.replace(
        "{additional_options}",
        _format_additional_options(additional_options, registry),
    )
    claude_content = claude_content.replace("{solokit_version}", _get_solokit_version())
    claude_content = claude_content.replace(
        "{tier_specific_requirements}",
        _get_tier_specific_requirements(tier, registry),
    )

    # Ensure file ends with a single newline (prettier requirement)
    if not claude_content.endswith("\n"):
        claude_content += "\n"

    # Write CLAUDE.md
    claude_path = project_root / "CLAUDE.md"

    try:
        claude_path.write_text(claude_content)
        logger.info(f"Generated {claude_path.name}")
        return claude_path
    except Exception as e:
        raise FileOperationError(
            operation="write",
            file_path=str(claude_path),
            details=f"Failed to write CLAUDE.md: {str(e)}",
            cause=e,
        )


def generate_minimal_claude_md(project_root: Path | None = None) -> Path:
    """
    Generate minimal CLAUDE.md with Solokit usage guide only.

    This is used for minimal init mode - projects that don't need
    stack-specific instructions or quality tier requirements.

    Args:
        project_root: Project root directory

    Returns:
        Path to generated CLAUDE.md

    Raises:
        FileOperationError: If CLAUDE.md generation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get project name from directory
    project_name = project_root.name

    claude_content = f"""# {project_name}

> Add a brief description of your project here.

## Solokit Usage Guide

This project uses Solokit for session-driven development. Use the following slash commands in Claude Code:

### Session Management
- `/start <work-item-id>` - Begin a session with comprehensive briefing
- `/end` - Complete work with learning capture
- `/status` - View current session status
- `/validate` - Validate quality gates without ending

### Work Item Management
- `/work-new` - Create work items interactively
- `/work-list` - View and manage your work items
- `/work-show <id>` - Show detailed work item information
- `/work-update <id>` - Update work item fields
- `/work-delete <id>` - Delete a work item
- `/work-next` - Get the next recommended work item
- `/work-graph` - Generate dependency graph visualization

### Learning System
- `/learn` - Capture a learning during development
- `/learn-show` - Browse and filter learnings
- `/learn-search <keyword>` - Search learnings by keyword
- `/learn-curate` - Run learning curation process

### Project Structure

```
.session/
├── tracking/          # Work items, learnings, status
├── briefings/         # Generated session briefings
├── history/           # Session history
├── specs/             # Work item specifications
└── guides/            # Development guides
```

---

*Initialized with [Solokit](https://github.com/ankushdixit/solokit) v{_get_solokit_version()} (minimal mode)*
"""

    # Write CLAUDE.md
    claude_path = project_root / "CLAUDE.md"

    try:
        claude_path.write_text(claude_content)
        logger.info(f"Generated minimal {claude_path.name}")
        return claude_path
    except Exception as e:
        raise FileOperationError(
            operation="write",
            file_path=str(claude_path),
            details=f"Failed to write CLAUDE.md: {str(e)}",
            cause=e,
        )
