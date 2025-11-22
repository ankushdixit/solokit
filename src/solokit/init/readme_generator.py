"""
README Generator Module

Generates project README.md with stack-specific information.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError
from solokit.init.template_installer import get_template_info, load_template_registry

logger = logging.getLogger(__name__)


def generate_readme(
    template_id: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str],
    project_root: Path | None = None,
) -> Path:
    """
    Generate README.md for the project.

    Args:
        template_id: Template identifier
        tier: Quality tier
        coverage_target: Test coverage target percentage
        additional_options: List of additional options installed
        project_root: Project root directory

    Returns:
        Path to generated README.md

    Raises:
        FileOperationError: If README generation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    template_info = get_template_info(template_id)
    registry = load_template_registry()

    tier_info = registry["quality_tiers"].get(tier, {})

    # Get project name from directory
    project_name = project_root.name

    # Build README content
    readme_content = f"""# {project_name}

A {template_info["display_name"]} project built with Session-Driven Development.

## Tech Stack

"""

    # Add stack information
    for key, value in template_info["stack"].items():
        formatted_key = key.replace("_", " ").title()
        readme_content += f"- **{formatted_key}**: {value}\n"

    readme_content += f"\n## Quality Gates: {tier_info.get('name', tier)}\n\n"

    if "includes" in tier_info:
        for item in tier_info["includes"]:
            readme_content += f"- ✓ {item}\n"

    if "adds" in tier_info:
        for item in tier_info["adds"]:
            readme_content += f"- ✓ {item}\n"

    readme_content += f"\n**Test Coverage Target**: {coverage_target}%\n"

    # Add getting started section
    readme_content += "\n## Getting Started\n\n"

    if template_info["package_manager"] == "npm":
        readme_content += """```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit http://localhost:3000

"""
    else:  # Python
        readme_content += """```bash
# Activate virtual environment
source venv/bin/activate  # Unix
# or
venv\\Scripts\\activate  # Windows

# Run development server
uvicorn main:app --reload
```

Visit http://localhost:8000

"""

    # Add testing section
    readme_content += "## Testing\n\n"

    if template_info["package_manager"] == "npm":
        readme_content += """```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Run type checking
npm run type-check
```
"""
        # Add E2E testing section for tier-3+
        if tier in ["tier-3-comprehensive", "tier-4-production"]:
            readme_content += """
### E2E Testing

Playwright browsers are installed during project setup. To run E2E tests:

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e -- --ui

# Run specific test file
npm run test:e2e -- tests/e2e/example.spec.ts
```

If browsers need to be reinstalled:

```bash
npx playwright install --with-deps
```
"""
        # Add A11y testing section if a11y option is enabled
        if "a11y" in additional_options:
            readme_content += """
### Accessibility Testing

```bash
# Run accessibility tests
npm run test:a11y
```
"""

        # Add Lighthouse CI section for tier-4
        if tier == "tier-4-production":
            readme_content += """
### Lighthouse CI (Performance Testing)

Lighthouse CI runs performance, accessibility, best practices, and SEO audits:

```bash
# Run Lighthouse CI
npm run lighthouse
```

This uses Playwright's Chromium browser automatically. Results are uploaded to temporary public storage.
"""
    else:  # Python
        readme_content += """```bash
# IMPORTANT: Activate virtual environment first
source venv/bin/activate  # Unix
# or: venv\\Scripts\\activate  # Windows

# Run tests
pytest

# Run tests with coverage
pytest --cov --cov-report=html

# Run linting
ruff check .

# Run type checking
pyright
```

**Note**: Session commands (`sk validate`, `sk end`) automatically use the virtual environment, so activation is optional when using those commands.
"""

    # Add additional options documentation
    if additional_options:
        readme_content += "\n## Additional Features\n\n"
        for option in additional_options:
            option_key = option.replace("_", " ").title()
            readme_content += f"- ✓ {option_key}\n"

    # Add known issues if any
    if template_info.get("known_issues"):
        critical_issues = [
            issue
            for issue in template_info["known_issues"]
            if issue["severity"] in ["CRITICAL", "HIGH"]
        ]
        if critical_issues:
            readme_content += "\n## Known Issues\n\n"
            for issue in critical_issues:
                readme_content += (
                    f"**{issue['package']}** ({issue['severity']}): {issue['description']}\n\n"
                )

    # Add Session-Driven Development section
    readme_content += """
## Session-Driven Development

This project uses Session-Driven Development (Solokit) for organized, AI-augmented development.

### Commands

- `/sk:work-new` - Create a new work item
- `/sk:work-list` - List all work items
- `/sk:start` - Start working on a work item
- `/sk:status` - Check current session status
- `/sk:validate` - Validate quality gates
- `/sk:end` - Complete current session
- `/sk:learn` - Capture a learning

### Documentation

See `.session/` directory for:

- Work item specifications (`.session/specs/`)
- Session briefings (`.session/briefings/`)
- Session summaries (`.session/history/`)
- Captured learnings (`.session/tracking/learnings.json`)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""

    # Write README
    readme_path = project_root / "README.md"

    try:
        readme_path.write_text(readme_content)
        logger.info(f"Generated {readme_path.name}")
        return readme_path
    except Exception as e:
        raise FileOperationError(
            operation="write",
            file_path=str(readme_path),
            details=f"Failed to write README.md: {str(e)}",
            cause=e,
        )
