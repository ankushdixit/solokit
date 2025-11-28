"""
Documentation Appender Module

Appends Solokit-specific sections to existing README.md and CLAUDE.md files
during project adoption. Only adds session management content, not stack-specific
templates or configurations.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError

logger = logging.getLogger(__name__)

# Markers for idempotency - detect if section already exists
SOLOKIT_README_MARKER = "<!-- SOLOKIT_SESSION_MANAGEMENT -->"
SOLOKIT_CLAUDE_MD_MARKER = "<!-- SOLOKIT_GUIDANCE -->"


def _get_solokit_version() -> str:
    """Get the current Solokit version."""
    try:
        from importlib.metadata import version

        return version("solokit")
    except Exception:
        return "unknown"


def _get_readme_solokit_section() -> str:
    """
    Return the Solokit section content for README.md.

    This is a stack-agnostic section focused on session management commands.
    """
    return f"""{SOLOKIT_README_MARKER}

## Session-Driven Development

This project uses [Solokit](https://github.com/anthropics/solokit) for Session-Driven Development with AI assistants.

### Quick Start

```bash
sk start           # Begin a session with context briefing
sk end             # Complete session with quality gates
sk work-new        # Create a new work item
sk work-list       # View all work items
sk status          # Check current session status
```

### Session Commands

| Command | Description |
|---------|-------------|
| `sk start [id]` | Start session with comprehensive briefing |
| `sk end` | Complete session with quality gates |
| `sk status` | View current session status |
| `sk validate` | Run quality checks without ending session |

### Work Item Commands

| Command | Description |
|---------|-------------|
| `sk work-new` | Create new work item interactively |
| `sk work-list` | List all work items |
| `sk work-show <id>` | Show work item details |
| `sk work-update <id>` | Update work item fields |
| `sk work-next` | Get recommended next item |
| `sk work-delete <id>` | Delete a work item |
| `sk work-graph` | Visualize work item dependencies |

### Learning Commands

| Command | Description |
|---------|-------------|
| `sk learn` | Capture a learning |
| `sk learn-show` | Browse captured learnings |
| `sk learn-search <query>` | Search learnings by keyword |
| `sk learn-curate` | Deduplicate and organize learnings |

### Session Files

The `.session/` directory contains:

- **specs/** - Work item specifications
- **briefings/** - Session context briefings
- **history/** - Session summaries
- **tracking/** - Work items and learnings data

---

Adopted with Solokit v{_get_solokit_version()}
"""


def _get_claude_md_solokit_section(tier: str, coverage_target: int) -> str:
    """
    Return the Solokit section content for CLAUDE.md.

    This is a stack-agnostic section focused on Solokit usage and guidelines.

    Args:
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage
    """
    tier_name = tier.replace("-", " ").replace("tier ", "Tier ").title()

    return f"""{SOLOKIT_CLAUDE_MD_MARKER}

---

## Solokit Session Management

This project uses Solokit for Session-Driven Development. Follow these guidelines for consistent and effective usage.

**Quality Tier**: {tier_name}
**Test Coverage Target**: {coverage_target}%
**Adopted With**: Solokit v{_get_solokit_version()}

### Understanding Solokit Commands

Solokit commands are available as **slash commands** in Claude Code (e.g., `/start`, `/end`, `/work-new`) or via the `sk` CLI in terminal. **Slash commands are preferred** as they provide interactive prompts.

For CLI usage with specific arguments, use `--help` to discover options:

```bash
sk <command> --help
```

### Work Item Management

#### Creating Work Items

**When asked to create a work item, ALWAYS use the CLI:**

```bash
# Check available options first
sk work-new --help

# Create with required fields
sk work-new --type feature --title "Add user authentication" --priority high

# With dependencies
sk work-new --type feature --title "Add OAuth" --priority high --dependencies feat_user_auth

# Mark as urgent
sk work-new --type bug --title "Fix critical login error" --priority critical --urgent
```

**NEVER create work items by directly editing `work_items.json`.**

**Valid Types**: feature, bug, refactor, security, integration_test, deployment
**Valid Priorities**: critical, high, medium, low

#### Listing and Viewing Work Items

```bash
# List all work items
sk work-list

# Filter by status
sk work-list --status not_started
sk work-list --status in_progress

# Filter by type
sk work-list --type bug

# View details
sk work-show <work_item_id>
```

#### Updating Work Items

```bash
# Update status
sk work-update feat_001 --status in_progress

# Update priority
sk work-update feat_001 --priority critical

# Add dependency
sk work-update feat_001 --add-dependency feat_002

# Mark as urgent
sk work-update feat_001 --set-urgent
```

### Spec File Guidelines

#### Spec File Location
- Spec files are stored in `.session/specs/`
- Each work item gets a spec file: `.session/specs/{{work_item_id}}.md`

#### Spec File Best Practices

1. **Always use the template structure** - Don't create spec files from scratch
2. **Be thorough and consistent** - Give equal attention to each spec file
3. **Include acceptance criteria** - Every spec must have clear, testable criteria
4. **Link related work items** - Reference dependencies in the spec

### Session Workflow

#### Starting a Session

Use `/start` to begin a session:

```bash
/start                    # Interactive - select from available work items
/start <work_item_id>     # Start specific work item
```

The start command:
- Updates work item status to `in_progress`
- Generates a session briefing with full context
- Provides information about dependencies and related learnings

#### Checking Status

Use `/status` to check current session:

```bash
/status
```

Shows current work item, session duration, and quality gate status.

#### Validating Quality

Use `/validate` to check quality gates:

```bash
/validate
```

Runs quality gates without ending the session. Use frequently during development.

#### Ending a Session

Use `/end` to complete a session:

```bash
/end
```

The end command:
- Runs all quality gate validations
- Prompts for session summary
- Updates work item status if complete
- Prompts for learning capture

**IMPORTANT**: Always end sessions properly. Don't abandon sessions.

### Learning Capture

#### When to Capture Learnings

Capture learnings when you:
- Solve a tricky problem
- Discover a better pattern
- Find an important gotcha
- Learn something about the codebase

#### How to Capture Learnings

**Method 1: During Session End (Preferred)**
When running `/end`, you'll be prompted to capture learnings.

**Method 2: Explicit Command**
```bash
/learn
```

#### Searching and Viewing Learnings

```bash
/learn-search "authentication"          # Search learnings
/learn-show                             # Show all learnings
/learn-show --category debugging        # Filter by category
```

### Dependency Graph

```bash
/work-graph                       # Generate dependency graph
/work-graph --focus feat_001      # Focus on specific work item
/work-graph --critical-path       # Show critical path
```

---

## Claude Behavior Guidelines

### Be Thorough

1. **Complete all tasks fully** - Don't rush through multiple items
2. **Don't make assumptions** - Ask clarifying questions when ambiguous
3. **Follow established patterns** - Check existing code before writing new code
4. **Validate your work** - Run `/validate` after making changes

### Ask Clarifying Questions When

- Requirements are vague or could be interpreted multiple ways
- You're unsure which of several approaches to take
- The task might affect other parts of the codebase
- You need to make architectural decisions

### Reference Documentation

- **ARCHITECTURE.md** - For architecture patterns and conventions
- **README.md** - For project-specific configuration
- **.session/specs/** - For work item requirements
- **Slash commands** (`/start`, `/end`, `/work-new`, etc.) - For Solokit operations

---

## What NOT to Do

1. **Don't edit tracking files directly**
   - NEVER edit `.session/tracking/work_items.json` manually
   - NEVER edit `.session/tracking/learnings.json` manually
   - Always use `sk` commands to modify these files

2. **Don't skip the spec file template**
   - ALWAYS use the template structure in `.session/specs/`
   - ALWAYS fill in all sections of the template

3. **Don't be inconsistent with multiple items**
   - If creating multiple work items, give equal attention to each
   - Each item deserves equal thoroughness

4. **Don't put learnings in wrong places**
   - NEVER add learnings to commit messages
   - ALWAYS use `/learn` or capture during `/end`

5. **Don't abandon sessions**
   - NEVER leave a session without running `/end`
   - ALWAYS complete the session workflow properly

6. **Don't skip quality gates**
   - NEVER commit code that fails linting or type checking
   - NEVER bypass pre-commit hooks with `--no-verify`

---

## Quick Reference

### Solokit Commands (Slash Commands)

| Command | Description |
|---------|-------------|
| `/work-list` | List all work items |
| `/work-show <id>` | Show work item details |
| `/work-new` | Create new work item |
| `/work-update <id>` | Update work item |
| `/work-delete <id>` | Delete work item |
| `/work-graph` | Visualize dependencies |
| `/work-next` | Get next recommended work item |
| `/start [id]` | Start a session |
| `/status` | Check session status |
| `/validate` | Validate quality gates |
| `/end` | End session |
| `/learn` | Capture a learning |
| `/learn-show` | View learnings |
| `/learn-search <query>` | Search learnings |

### Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI guidance (this file) |
| `ARCHITECTURE.md` | Architecture documentation |
| `README.md` | Project overview |
| `.session/tracking/work_items.json` | Work item data (use `sk` commands) |
| `.session/tracking/learnings.json` | Captured learnings (use `sk` commands) |
| `.session/specs/` | Work item specifications |
| `.session/briefings/` | Session briefings |
| `.session/history/` | Session summaries |
"""


def _check_section_exists(file_path: Path, marker: str) -> bool:
    """
    Check if Solokit section already exists in file (for idempotency).

    Args:
        file_path: Path to the file to check
        marker: The marker string to look for

    Returns:
        True if marker exists in file, False otherwise
    """
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text()
        return marker in content
    except OSError:
        return False


def append_to_readme(project_root: Path | None = None) -> bool:
    """
    Append Solokit session management section to README.md.

    Creates README.md if it doesn't exist.
    Idempotent - won't append if section already exists.

    Args:
        project_root: Project root directory. Defaults to current directory.

    Returns:
        True if content was appended/created, False if already exists.

    Raises:
        FileOperationError: If file operation fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    # Find existing README (case-insensitive)
    readme_path = None
    readme_patterns = ["README.md", "readme.md", "Readme.md", "README.MD"]

    for pattern in readme_patterns:
        candidate = project_root / pattern
        if candidate.exists():
            readme_path = candidate
            break

    # Default to README.md if not found
    if readme_path is None:
        readme_path = project_root / "README.md"

    # Check idempotency
    if _check_section_exists(readme_path, SOLOKIT_README_MARKER):
        logger.info("README.md already contains Solokit section, skipping")
        return False

    solokit_section = _get_readme_solokit_section()

    try:
        if readme_path.exists():
            # Append to existing file
            existing_content = readme_path.read_text()
            # Ensure there's a blank line before the new section
            if not existing_content.endswith("\n\n"):
                if existing_content.endswith("\n"):
                    existing_content += "\n"
                else:
                    existing_content += "\n\n"
            new_content = existing_content + solokit_section
            readme_path.write_text(new_content)
            logger.info(f"Appended Solokit section to {readme_path.name}")
        else:
            # Create new file with project name header
            project_name = project_root.name
            new_content = f"# {project_name}\n\n{solokit_section}"
            readme_path.write_text(new_content)
            logger.info(f"Created {readme_path.name} with Solokit section")

        return True

    except OSError as e:
        raise FileOperationError(
            operation="write",
            file_path=str(readme_path),
            details=f"Failed to update README.md: {str(e)}",
            cause=e,
        )


def append_to_claude_md(
    tier: str = "tier-2-standard",
    coverage_target: int = 80,
    project_root: Path | None = None,
) -> bool:
    """
    Append Solokit guidance section to CLAUDE.md.

    Creates CLAUDE.md if it doesn't exist.
    Idempotent - won't append if section already exists.

    Args:
        tier: Quality tier for documentation
        coverage_target: Test coverage target percentage
        project_root: Project root directory. Defaults to current directory.

    Returns:
        True if content was appended/created, False if already exists.

    Raises:
        FileOperationError: If file operation fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    claude_md_path = project_root / "CLAUDE.md"

    # Check idempotency
    if _check_section_exists(claude_md_path, SOLOKIT_CLAUDE_MD_MARKER):
        logger.info("CLAUDE.md already contains Solokit section, skipping")
        return False

    solokit_section = _get_claude_md_solokit_section(tier, coverage_target)

    try:
        if claude_md_path.exists():
            # Append to existing file
            existing_content = claude_md_path.read_text()
            # Ensure there's a blank line before the new section
            if not existing_content.endswith("\n\n"):
                if existing_content.endswith("\n"):
                    existing_content += "\n"
                else:
                    existing_content += "\n\n"
            new_content = existing_content + solokit_section
            claude_md_path.write_text(new_content)
            logger.info("Appended Solokit section to CLAUDE.md")
        else:
            # Create new file with header
            project_name = project_root.name
            header = f"""# CLAUDE.md - AI Assistant Guidelines for {project_name}

This file provides guidance for AI assistants working on this project.

"""
            new_content = header + solokit_section
            claude_md_path.write_text(new_content)
            logger.info("Created CLAUDE.md with Solokit section")

        return True

    except OSError as e:
        raise FileOperationError(
            operation="write",
            file_path=str(claude_md_path),
            details=f"Failed to update CLAUDE.md: {str(e)}",
            cause=e,
        )


def append_documentation(
    tier: str = "tier-2-standard",
    coverage_target: int = 80,
    project_root: Path | None = None,
) -> dict[str, bool]:
    """
    Append Solokit sections to both README.md and CLAUDE.md.

    Convenience function that calls both append_to_readme and append_to_claude_md.

    Args:
        tier: Quality tier for CLAUDE.md documentation
        coverage_target: Test coverage target percentage
        project_root: Project root directory. Defaults to current directory.

    Returns:
        Dict with 'readme' and 'claude_md' keys indicating if each was updated.

    Raises:
        FileOperationError: If any file operation fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    return {
        "readme": append_to_readme(project_root),
        "claude_md": append_to_claude_md(tier, coverage_target, project_root),
    }
