"""
Adoption Orchestrator Module

Main orchestration logic for adopting Solokit into existing projects.
Implements the complete adoption flow without template installation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.adopt.doc_appender import append_to_claude_md, append_to_readme
from solokit.adopt.project_detector import (
    ProjectInfo,
    ProjectLanguage,
    detect_project_type,
    get_project_summary,
)
from solokit.core.exceptions import FileOperationError
from solokit.core.output import get_output

logger = logging.getLogger(__name__)
output = get_output()


def _get_template_id_for_language(language: ProjectLanguage) -> str:
    """
    Map detected project language to appropriate template_id for option installation.

    Args:
        language: Detected project language

    Returns:
        Template identifier (e.g., "saas_t3", "ml_ai_fastapi")
    """
    template_mapping = {
        ProjectLanguage.NODEJS: "saas_t3",
        ProjectLanguage.TYPESCRIPT: "saas_t3",
        ProjectLanguage.PYTHON: "ml_ai_fastapi",
        ProjectLanguage.FULLSTACK: "fullstack_nextjs",
        ProjectLanguage.UNKNOWN: "saas_t3",  # Default fallback
    }
    return template_mapping.get(language, "saas_t3")


# =============================================================================
# FILE CATEGORIZATION FOR SAFE ADOPTION
# =============================================================================
# Core Philosophy: "Do no harm to existing projects"
#
# Files are categorized into three groups based on how they should be handled
# when adopting Solokit into an existing project.

# Files that should NEVER be overwritten - they contain project-specific config
# that would break the project if replaced.
NEVER_OVERWRITE: set[str] = {
    # TypeScript/JavaScript - project structure
    "tsconfig.json",
    "next.config.ts",
    "tailwind.config.ts",
    "postcss.config.mjs",
    "components.json",
    "vercel.json",
    ".npmrc",
    # Python - project structure
    "alembic.ini",
    # Database (nested path)
    "prisma/schema.prisma",
}

# Files that can be intelligently merged if they exist.
# If they don't exist, they'll be installed fresh.
MERGE_IF_EXISTS: set[str] = {
    # Node.js/TypeScript
    "package.json",
    "eslint.config.mjs",
    ".prettierrc",
    ".husky/pre-commit",
    # Python
    "pyproject.toml",
    "requirements.txt",
    ".pre-commit-config.yaml",
}

# Files to install only if they don't already exist.
# These are quality/testing configs that shouldn't overwrite existing setups.
INSTALL_IF_MISSING: set[str] = {
    # Testing - Tier 1
    "jest.config.ts",
    "jest.setup.ts",
    "pyrightconfig.json",
    "pytest.ini",
    ".coveragerc",
    "requirements-dev.txt",
    # Quality - Tier 2
    ".prettierignore",
    ".lintstagedrc.json",
    ".git-secrets",
    ".bandit",
    ".secrets.baseline",
    # Advanced Testing - Tier 3
    "playwright.config.ts",
    "stryker.conf.json",
    "type-coverage.json",
    ".jscpd.json",
    ".axe-config.json",
    ".pylintrc",
    ".radon.cfg",
    ".vulture",
    "locustfile.py",
    # Production - Tier 4
    ".lighthouserc.json",
    "sentry.client.config.ts",
    "sentry.server.config.ts",
    "sentry.edge.config.ts",
    "instrumentation.ts",
    "requirements-prod.txt",
}

# Template files that produce merged output files
MERGE_TEMPLATE_FILES: dict[str, str] = {
    "package.json.tier1.template": "package.json",
    "package.json.tier2.template": "package.json",
    "package.json.tier3.template": "package.json",
    "package.json.tier4.template": "package.json",
    "pyproject.toml.template": "pyproject.toml",
    "pyproject.toml.tier1.template": "pyproject.toml",
    "pyproject.toml.tier2.template": "pyproject.toml",
    "pyproject.toml.tier3.template": "pyproject.toml",
    "pyproject.toml.tier4.template": "pyproject.toml",
    "requirements.txt.template": "requirements.txt",
}

# Template files that produce install-if-missing output files
INSTALL_TEMPLATE_FILES: dict[str, str] = {
    "jest.config.ts.tier3.template": "jest.config.ts",
    "jest.config.ts.tier4.template": "jest.config.ts",
    "pytest.ini.template": "pytest.ini",
    "requirements-dev.txt.template": "requirements-dev.txt",
    "requirements-prod.txt.template": "requirements-prod.txt",
    ".coveragerc.template": ".coveragerc",
}

# Combined set of all config files (for _is_config_file check)
ALL_CONFIG_FILES: set[str] = NEVER_OVERWRITE | MERGE_IF_EXISTS | INSTALL_IF_MISSING

# All template file names
ALL_TEMPLATE_FILES: set[str] = set(MERGE_TEMPLATE_FILES.keys()) | set(INSTALL_TEMPLATE_FILES.keys())

# Directories to skip entirely (source code, not configs)
SKIP_DIRECTORIES = {
    "app",
    "src",
    "server",
    "lib",
    "components",
    "tests",
    "scripts",
    "k6",
    "alembic",  # Skip alembic migrations, only take alembic.ini
    "__pycache__",
}


def _get_tier_order() -> list[str]:
    """Return tiers in order from lowest to highest."""
    return [
        "tier-1-essential",
        "tier-2-standard",
        "tier-3-comprehensive",
        "tier-4-production",
    ]


def _get_tiers_up_to(tier: str) -> list[str]:
    """
    Get list of tiers up to and including the specified tier.

    Args:
        tier: Target tier (e.g., "tier-3-comprehensive")

    Returns:
        List of tiers to install (cumulative)
    """
    all_tiers = _get_tier_order()
    if tier not in all_tiers:
        return ["tier-1-essential"]  # Default to tier-1 if invalid

    tier_index = all_tiers.index(tier)
    return all_tiers[: tier_index + 1]


def _normalize_path(relative_path: Path) -> str:
    """
    Normalize a path to use forward slashes for consistent matching.

    Args:
        relative_path: Relative path from template directory

    Returns:
        Normalized path string with forward slashes
    """
    return str(relative_path).replace("\\", "/")


def _is_config_file(file_path: Path, relative_path: Path | None = None) -> bool:
    """
    Check if a file is a config file that should be processed.

    Args:
        file_path: Path to the file
        relative_path: Optional relative path for nested file matching

    Returns:
        True if file should be processed
    """
    filename = file_path.name

    # Check template files first (they have specific filenames)
    if filename in ALL_TEMPLATE_FILES:
        return True

    # Check direct filename match in any category
    if filename in ALL_CONFIG_FILES:
        return True

    # Check nested path match (e.g., "prisma/schema.prisma", ".husky/pre-commit")
    if relative_path is not None:
        normalized = _normalize_path(relative_path)
        if normalized in ALL_CONFIG_FILES:
            return True

    return False


def _get_file_category(filename: str, relative_path: str | None = None) -> str:
    """
    Determine the category for a config file.

    Args:
        filename: Name of the file (basename)
        relative_path: Optional relative path for nested files

    Returns:
        Category string: "never_overwrite", "merge", "install_if_missing", or "unknown"
    """
    # Check nested path first (more specific match)
    if relative_path:
        normalized = relative_path.replace("\\", "/")
        if normalized in NEVER_OVERWRITE:
            return "never_overwrite"
        if normalized in MERGE_IF_EXISTS:
            return "merge"
        if normalized in INSTALL_IF_MISSING:
            return "install_if_missing"

    # Check by filename
    if filename in NEVER_OVERWRITE:
        return "never_overwrite"
    if filename in MERGE_IF_EXISTS:
        return "merge"
    if filename in INSTALL_IF_MISSING:
        return "install_if_missing"

    # Check template mappings to determine output file category
    if filename in MERGE_TEMPLATE_FILES:
        return "merge"
    if filename in INSTALL_TEMPLATE_FILES:
        return "install_if_missing"

    return "unknown"


def _get_output_filename(template_filename: str) -> str:
    """
    Get the output filename for a template file.

    Args:
        template_filename: Name of the template file

    Returns:
        Output filename (without .template and tier suffixes)
    """
    if not template_filename.endswith(".template"):
        return template_filename

    # Check template mappings first
    if template_filename in MERGE_TEMPLATE_FILES:
        return MERGE_TEMPLATE_FILES[template_filename]
    if template_filename in INSTALL_TEMPLATE_FILES:
        return INSTALL_TEMPLATE_FILES[template_filename]

    # Fallback: remove .template and tier suffixes
    output_name = template_filename.replace(".template", "")
    for tier in _get_tier_order():
        tier_suffix = f".{tier.replace('-', '')}"
        if tier_suffix in output_name:
            output_name = output_name.replace(tier_suffix, "")
            break
    output_name = (
        output_name.replace(".tier1", "")
        .replace(".tier2", "")
        .replace(".tier3", "")
        .replace(".tier4", "")
    )
    return output_name


def _install_config_file(
    src_path: Path,
    project_root: Path,
    relative_path: Path,
    replacements: dict[str, str],
    backup_dir: Path | None = None,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """
    Install a single config file with category-aware handling.

    Args:
        src_path: Source file path
        project_root: Project root directory
        relative_path: Relative path from template dir
        replacements: Placeholder replacements
        backup_dir: Directory for backups (if any)
        dry_run: If True, don't make changes, just report what would happen

    Returns:
        Tuple of (success: bool, action: str)
        action is one of: "installed", "merged", "skipped_exists",
        "skipped_never_overwrite", "would_install", "would_merge",
        "would_skip", "error:<message>"
    """
    import shutil

    from solokit.adopt.backup import backup_file
    from solokit.adopt.merge_strategies import merge_config_file

    filename = src_path.name

    # Determine output path and filename
    if filename.endswith(".template"):
        output_name = _get_output_filename(filename)
        output_path = project_root / relative_path.parent / output_name
        category_filename = output_name
    else:
        output_path = project_root / relative_path
        category_filename = filename

    # Normalize relative path for category lookup
    output_relative = str(relative_path.parent / category_filename).replace("\\", "/")
    if output_relative.startswith("./"):
        output_relative = output_relative[2:]

    # Determine category
    category = _get_file_category(category_filename, output_relative)
    file_exists = output_path.exists()

    # Handle based on category
    if category == "never_overwrite" and file_exists:
        logger.info(f"SKIP (never_overwrite): {category_filename} - preserving existing")
        return (True, "skipped_never_overwrite")

    if category == "install_if_missing" and file_exists:
        logger.info(f"SKIP (exists): {category_filename} - already exists")
        return (True, "skipped_exists")

    # Dry run handling
    if dry_run:
        if file_exists and category == "merge":
            return (True, f"would_merge:{category_filename}")
        elif file_exists:
            return (True, f"would_skip:{category_filename}")
        else:
            return (True, f"would_install:{category_filename}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read and process source content
        if filename.endswith(".template"):
            content = src_path.read_text()
            for placeholder, value in replacements.items():
                content = content.replace(f"{{{placeholder}}}", value)
        else:
            content = src_path.read_text()

        # Handle merge case
        if category == "merge" and file_exists:
            if backup_dir:
                backup_file(output_path, backup_dir)
            merged_content = merge_config_file(category_filename, output_path, content)
            output_path.write_text(merged_content)
            logger.info(f"MERGED: {category_filename}")
            return (True, "merged")

        # Handle install case (new file or unknown category)
        if file_exists and backup_dir:
            backup_file(output_path, backup_dir)

        if filename.endswith(".template"):
            output_path.write_text(content)
        else:
            shutil.copy2(src_path, output_path)

        logger.info(f"INSTALLED: {category_filename}")
        return (True, "installed")

    except Exception as e:
        logger.warning(f"Failed to install {filename}: {e}")
        return (False, f"error:{e}")


def _categorize_result(results: dict[str, list[str]], action: str, filename: str) -> None:
    """
    Helper to categorize installation results.

    Args:
        results: Results dictionary to update
        action: Action string from _install_config_file
        filename: File that was processed
    """
    if action == "installed":
        results["installed"].append(filename)
    elif action == "merged":
        results["merged"].append(filename)
    elif action == "skipped_exists":
        results["skipped_exists"].append(filename)
    elif action == "skipped_never_overwrite":
        results["skipped_never_overwrite"].append(filename)
    elif action.startswith("error:"):
        results["errors"].append(f"{filename}: {action[6:]}")
    elif action.startswith("would_"):
        # Dry run results
        if "merge" in action:
            results["merged"].append(filename)
        elif "install" in action:
            results["installed"].append(filename)
        elif "skip" in action:
            results["skipped_exists"].append(filename)


def install_tier_configs(
    template_id: str,
    tier: str,
    project_root: Path,
    coverage_target: int,
    backup_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """
    Install tier-specific configuration files for adoption.

    Uses category-aware installation:
    - NEVER_OVERWRITE files are skipped if they exist
    - MERGE_IF_EXISTS files are intelligently merged
    - INSTALL_IF_MISSING files only install if missing

    Args:
        template_id: Template to use for configs (e.g., "saas_t3")
        tier: Target tier (e.g., "tier-2-standard")
        project_root: Project root directory
        coverage_target: Coverage target for template replacements
        backup_dir: Directory for backups
        dry_run: If True, don't make changes

    Returns:
        Dict with keys: "installed", "merged", "skipped_exists",
        "skipped_never_overwrite", "errors"
    """
    from solokit.init.template_installer import get_template_directory

    template_dir = get_template_directory(template_id)
    project_name = project_root.name

    replacements = {
        "project_name": project_name,
        "project_description": f"A {project_name} project",
        "coverage_target": str(coverage_target),
    }

    results: dict[str, list[str]] = {
        "installed": [],
        "merged": [],
        "skipped_exists": [],
        "skipped_never_overwrite": [],
        "errors": [],
    }

    # Track processed files to avoid duplicates across tiers
    processed_files: set[str] = set()

    # Get tiers to install (cumulative)
    tiers_to_install = _get_tiers_up_to(tier)

    # Install from base directory first
    base_dir = template_dir / "base"
    if base_dir.exists():
        for file_path in base_dir.rglob("*"):
            if file_path.is_dir():
                continue
            # Skip files in source directories
            relative_path = file_path.relative_to(base_dir)
            if any(part in SKIP_DIRECTORIES for part in relative_path.parts):
                continue
            if _is_config_file(file_path, relative_path):
                # Get display name for tracking
                display_name = _get_output_filename(file_path.name)
                if display_name in processed_files:
                    continue
                processed_files.add(display_name)

                success, action = _install_config_file(
                    file_path,
                    project_root,
                    relative_path,
                    replacements,
                    backup_dir=backup_dir,
                    dry_run=dry_run,
                )
                _categorize_result(results, action, display_name)

    # Install from each tier directory (cumulative)
    for install_tier in tiers_to_install:
        tier_dir = template_dir / install_tier
        if not tier_dir.exists():
            continue

        for file_path in tier_dir.rglob("*"):
            if file_path.is_dir():
                continue
            # Skip files in source directories
            relative_path = file_path.relative_to(tier_dir)
            if any(part in SKIP_DIRECTORIES for part in relative_path.parts):
                continue
            if _is_config_file(file_path, relative_path):
                # Get display name for tracking
                display_name = _get_output_filename(file_path.name)
                if display_name in processed_files:
                    continue
                processed_files.add(display_name)

                success, action = _install_config_file(
                    file_path,
                    project_root,
                    relative_path,
                    replacements,
                    backup_dir=backup_dir,
                    dry_run=dry_run,
                )
                _categorize_result(results, action, display_name)

    return results


def get_config_files_to_install(template_id: str, tier: str) -> list[str]:
    """
    Get list of config files that would be installed for a given tier.

    Useful for showing warnings about potential overwrites.

    Args:
        template_id: Template identifier
        tier: Target tier

    Returns:
        List of config file names that would be installed
    """
    from solokit.init.template_installer import get_template_directory

    try:
        template_dir = get_template_directory(template_id)
    except Exception:
        return []

    config_files: set[str] = set()
    tiers_to_install = _get_tiers_up_to(tier)

    # Check base directory
    base_dir = template_dir / "base"
    if base_dir.exists():
        for file_path in base_dir.rglob("*"):
            if file_path.is_dir():
                continue
            relative_path = file_path.relative_to(base_dir)
            if any(part in SKIP_DIRECTORIES for part in relative_path.parts):
                continue
            if _is_config_file(file_path):
                name = file_path.name
                if name.endswith(".template"):
                    name = (
                        name.replace(".template", "")
                        .replace(".tier1", "")
                        .replace(".tier2", "")
                        .replace(".tier3", "")
                        .replace(".tier4", "")
                    )
                config_files.add(name)

    # Check tier directories
    for install_tier in tiers_to_install:
        tier_dir = template_dir / install_tier
        if not tier_dir.exists():
            continue
        for file_path in tier_dir.rglob("*"):
            if file_path.is_dir():
                continue
            relative_path = file_path.relative_to(tier_dir)
            if any(part in SKIP_DIRECTORIES for part in relative_path.parts):
                continue
            if _is_config_file(file_path):
                name = file_path.name
                if name.endswith(".template"):
                    name = (
                        name.replace(".template", "")
                        .replace(".tier1", "")
                        .replace(".tier2", "")
                        .replace(".tier3", "")
                        .replace(".tier4", "")
                    )
                config_files.add(name)

    return sorted(config_files)


def _get_language_gitignore_entries(project_info: ProjectInfo) -> list[str]:
    """
    Get language-specific .gitignore entries for adoption.

    Unlike template-based init, this uses detected language instead of template_id.

    Args:
        project_info: Detected project information

    Returns:
        List of gitignore patterns to add
    """
    # Common Solokit entries for all projects
    common_entries = [
        "# Solokit session files",
        ".session/briefings/",
        ".session/history/",
        "# Solokit adoption backups",
        ".solokit-backup/",
    ]

    language = project_info.language

    # Node.js/TypeScript entries
    node_entries = [
        "# Coverage",
        "coverage/",
        "coverage.json",
    ]

    # Python entries
    python_entries = [
        "# Coverage",
        ".coverage",
        "htmlcov/",
        "coverage.xml",
        "*.cover",
    ]

    if language == ProjectLanguage.FULLSTACK:
        return common_entries + node_entries + python_entries
    elif language in (ProjectLanguage.NODEJS, ProjectLanguage.TYPESCRIPT):
        return common_entries + node_entries
    elif language == ProjectLanguage.PYTHON:
        return common_entries + python_entries
    else:
        return common_entries


def _update_gitignore_for_adoption(
    project_info: ProjectInfo,
    project_root: Path,
) -> bool:
    """
    Update .gitignore with Solokit entries for adopted project.

    Args:
        project_info: Detected project information
        project_root: Project root directory

    Returns:
        True if gitignore was updated, False if already up to date

    Raises:
        FileOperationError: If gitignore update fails
    """
    gitignore = project_root / ".gitignore"
    entries_to_add = _get_language_gitignore_entries(project_info)

    try:
        existing_content = gitignore.read_text() if gitignore.exists() else ""
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(gitignore),
            details=f"Failed to read .gitignore: {str(e)}",
            cause=e,
        )

    # Filter out entries that already exist
    new_entries = []
    for entry in entries_to_add:
        # Skip comments when checking existence
        if entry.startswith("#"):
            # Only add comment if we're adding entries after it
            new_entries.append(entry)
        elif entry not in existing_content:
            new_entries.append(entry)

    # Clean up - only keep comments if there are actual entries after them
    cleaned_entries = []
    for i, entry in enumerate(new_entries):
        if entry.startswith("#"):
            # Check if there's a non-comment entry after this
            has_following_entry = any(not e.startswith("#") for e in new_entries[i + 1 :])
            if has_following_entry:
                cleaned_entries.append(entry)
        else:
            cleaned_entries.append(entry)

    if not cleaned_entries:
        logger.info(".gitignore already up to date for Solokit")
        return False

    try:
        with open(gitignore, "a") as f:
            # Add newline before new content if file doesn't end with one
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            if existing_content:
                f.write("\n")  # Extra blank line for separation

            for entry in cleaned_entries:
                f.write(f"{entry}\n")

        logger.info(f"Updated .gitignore with {len(cleaned_entries)} entries")
        return True

    except OSError as e:
        raise FileOperationError(
            operation="write",
            file_path=str(gitignore),
            details=f"Failed to update .gitignore: {str(e)}",
            cause=e,
        )


def _create_adoption_commit(
    tier: str,
    project_info: ProjectInfo,
    project_root: Path,
) -> bool:
    """
    Create git commit marking Solokit adoption.

    Args:
        tier: Quality tier
        project_info: Detected project information
        project_root: Project root directory

    Returns:
        True if commit was created, False if skipped

    Raises:
        GitError: If git operations fail
    """
    from solokit.core.command_runner import CommandRunner
    from solokit.core.constants import GIT_QUICK_TIMEOUT

    runner = CommandRunner(default_timeout=GIT_QUICK_TIMEOUT, working_dir=project_root)

    # Check if git repo exists
    git_dir = project_root / ".git"
    if not git_dir.exists():
        logger.info("No git repository found, skipping adoption commit")
        return False

    # Check if there are changes to commit
    result = runner.run(["git", "status", "--porcelain"], check=False)
    if not result.success or not result.stdout.strip():
        logger.info("No changes to commit")
        return False

    # Stage all Solokit-related changes
    files_to_stage = [
        ".session/",
        ".claude/commands/",
        ".gitignore",
        "README.md",
        "CLAUDE.md",
    ]

    for file_pattern in files_to_stage:
        file_path = project_root / file_pattern.rstrip("/")
        if file_path.exists():
            runner.run(["git", "add", file_pattern], check=False)

    # Check if anything was staged
    result = runner.run(["git", "diff", "--cached", "--quiet"], check=False)
    if result.success:
        # Exit code 0 means no diff = nothing staged
        logger.info("No Solokit files to commit")
        return False

    # Create commit
    tier_display = tier.replace("-", " ").replace("tier ", "Tier ").title()
    language_display = project_info.language.value.title()

    commit_message = f"""Add Solokit session management

Detected: {language_display} project
Quality tier: {tier_display}

Changes:
- Session tracking and briefings (.session/)
- Claude Code slash commands (.claude/commands/)
- Documentation updates (README.md, CLAUDE.md)
- Updated .gitignore

🤖 Adopted with Solokit
"""

    result = runner.run(
        ["git", "commit", "-m", commit_message],
        check=False,
    )

    if result.success:
        logger.info("Created adoption commit")
        return True
    else:
        logger.warning(f"Failed to create commit: {result.stderr}")
        return False


def run_adoption(
    tier: str,
    coverage_target: int,
    additional_options: list[str] | None = None,
    project_root: Path | None = None,
    skip_commit: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Run complete adoption flow for existing project.

    This is a streamlined flow compared to template-based init:
    - No template installation
    - No dependency installation (uses existing)
    - No starter code generation

    Safe config handling:
    - NEVER_OVERWRITE files are preserved if they exist
    - MERGE_IF_EXISTS files are intelligently merged
    - INSTALL_IF_MISSING files only install if missing
    - Backups are created before any modifications

    Args:
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage
        additional_options: List of additional options (ci_cd, docker, env_templates)
        project_root: Project root directory (defaults to current directory)
        skip_commit: Skip creating adoption commit
        dry_run: Preview changes without making modifications

    Returns:
        0 on success, non-zero on failure

    Raises:
        Various exceptions from individual modules on critical failures
    """
    from solokit.adopt.backup import create_backup_directory

    if additional_options is None:
        additional_options = []

    if project_root is None:
        project_root = Path.cwd()

    # Import reusable components from init
    from solokit.init.claude_commands_installer import install_claude_commands
    from solokit.init.git_hooks_installer import install_git_hooks
    from solokit.init.initial_scans import run_initial_scans
    from solokit.init.session_structure import (
        create_session_directories,
        initialize_tracking_files,
    )

    # Display dry-run banner if applicable
    if dry_run:
        output.info("\n" + "=" * 60)
        output.info("🔍 DRY RUN - No changes will be made")
        output.info("=" * 60 + "\n")
        logger.info("Running in dry-run mode - no changes will be made")

    output.info("\n" + "=" * 60)
    output.info("🔄 Adopting Solokit into Existing Project")
    output.info("=" * 60 + "\n")

    logger.info("🔄 Starting Solokit adoption for existing project...\n")

    # =========================================================================
    # STEP 1: Detect Project Type
    # =========================================================================

    output.progress("Step 1: Detecting project type...")
    logger.info("Step 1: Detecting project type...")

    project_info = detect_project_type(project_root)

    output.info(f"   Detected: {project_info.language.value}")
    if project_info.framework.value != "none":
        output.info(f"   Framework: {project_info.framework.value}")
    if project_info.package_manager.value != "unknown":
        output.info(f"   Package Manager: {project_info.package_manager.value}")
    output.info(f"   Confidence: {project_info.confidence:.0%}")
    output.info("")

    logger.info(f"Project detection summary:\n{get_project_summary(project_info)}\n")

    # =========================================================================
    # STEP 2: Check for existing Solokit installation
    # =========================================================================

    output.progress("Step 2: Checking for existing Solokit installation...")
    logger.info("Step 2: Checking for existing Solokit installation...")

    session_dir = project_root / ".session"
    if session_dir.exists():
        output.warning("   .session/ directory already exists!")
        output.warning("   Solokit may already be installed in this project.")
        output.info("   Continuing will update existing configuration.\n")
        logger.warning(".session/ directory already exists, will update")
    else:
        output.info("   ✓ No existing Solokit installation found\n")

    # =========================================================================
    # STEP 2.5: Create backup directory (if not dry run)
    # =========================================================================

    backup_dir = None
    if not dry_run:
        backup_dir = create_backup_directory(project_root)
        output.info(f"   📁 Backups will be saved to: {backup_dir.relative_to(project_root)}")
        output.info("")

    # =========================================================================
    # STEP 3: Install Tier-Specific Configuration Files
    # =========================================================================

    output.progress("Step 3: Installing tier-specific configuration files...")
    logger.info("Step 3: Installing tier-specific configuration files...")

    # Map detected language to template_id for config file sources
    detected_template_id = _get_template_id_for_language(project_info.language)
    logger.info(f"   Using template '{detected_template_id}' for config files")

    try:
        results = install_tier_configs(
            detected_template_id,
            tier,
            project_root,
            coverage_target,
            backup_dir=backup_dir,
            dry_run=dry_run,
        )

        # Display categorized results
        if results["installed"]:
            output.info(
                f"   ✓ {'Would install' if dry_run else 'Installed'} {len(results['installed'])} new config files"
            )
            for f in results["installed"][:5]:
                output.info(f"      + {f}")
            if len(results["installed"]) > 5:
                output.info(f"      ... and {len(results['installed']) - 5} more")

        if results["merged"]:
            output.info(
                f"   🔀 {'Would merge' if dry_run else 'Merged'} {len(results['merged'])} existing config files"
            )
            for f in results["merged"]:
                output.info(f"      ↔ {f}")

        if results["skipped_never_overwrite"]:
            output.warning(
                f"   ⊘ Preserved {len(results['skipped_never_overwrite'])} project-specific configs"
            )
            for f in results["skipped_never_overwrite"]:
                output.info(f"      ⊘ {f} (preserved)")

        if results["skipped_exists"]:
            output.info(f"   ⊘ Skipped {len(results['skipped_exists'])} existing files")

        if results["errors"]:
            output.warning(f"   ⚠ {len(results['errors'])} errors occurred")
            for err in results["errors"]:
                output.warning(f"      ! {err}")

        total_processed = len(results["installed"]) + len(results["merged"])
        if total_processed == 0 and not results["skipped_never_overwrite"]:
            output.info("   No configuration files to install for this template")

    except Exception as e:
        logger.warning(f"Config installation failed: {e}")
        output.warning(f"   Config installation failed: {e}")
        output.warning("   Continuing with adoption...")

    output.info("")

    # =========================================================================
    # STEP 4: Process Additional Options (CI/CD, Docker)
    # =========================================================================

    output.progress("Step 4: Processing additional options...")
    logger.info("Step 4: Processing additional options...")

    if dry_run:
        if additional_options:
            output.info(f"   Would install options: {', '.join(additional_options)}")
        else:
            output.info("   No additional options selected")
    elif additional_options:
        try:
            from solokit.init.template_installer import install_additional_option

            # Prepare replacements for template processing
            project_name = project_root.name
            replacements = {
                "project_name": project_name,
                "project_description": f"A {project_info.language.value} project",
            }

            # Map option keys to directory names
            option_dir_map = {
                "ci_cd": "ci-cd",
                "docker": "docker",
                "env_templates": "env-templates",
            }

            # Install CI/CD and Docker options (env_templates handled separately)
            for option in additional_options:
                if option == "env_templates":
                    # Handled in Step 5
                    continue

                option_dir = option_dir_map.get(option, option)

                try:
                    files_installed = install_additional_option(
                        detected_template_id, option_dir, project_root, replacements
                    )
                    if files_installed > 0:
                        logger.info(f"   Installed {files_installed} files for {option}")
                        output.info(f"   ✓ Installed {option} ({files_installed} files)")
                    else:
                        output.info(f"   ⚠ No files found for {option}")
                except Exception as e:
                    logger.warning(f"Failed to install {option}: {e}")
                    output.warning(f"   Failed to install {option}: {e}")

        except ImportError as e:
            logger.warning(f"Template installer not available: {e}")
            output.warning(f"   Template installer not available: {e}")
    else:
        output.info("   No additional options selected")
        logger.info("   No additional options selected")

    output.info("")

    # =========================================================================
    # STEP 5: Generate Environment Files (if env_templates selected)
    # =========================================================================

    if "env_templates" in additional_options:
        output.progress("Step 5: Generating environment files...")
        logger.info("Step 5: Generating environment files...")

        if dry_run:
            output.info("   Would generate .env.example and .editorconfig")
        else:
            try:
                from solokit.init.env_generator import generate_env_files

                generated_files = generate_env_files(detected_template_id, project_root)
                logger.info(f"Generated {len(generated_files)} environment files")
                output.info("   ✓ Generated .env.example and .editorconfig")
            except Exception as e:
                logger.warning(f"Environment file generation failed: {e}")
                output.warning(f"   Environment file generation failed: {e}")

        output.info("")
    else:
        logger.info("Step 5: Skipped (environment templates not selected)")

    # =========================================================================
    # STEP 6: Create .session structure
    # =========================================================================

    output.progress("Step 6: Creating .session structure...")
    logger.info("Step 6: Creating .session structure...")

    if dry_run:
        output.info("   Would create .session/ directories")
    else:
        create_session_directories(project_root)
        output.info("   ✓ Created .session/ directories")

    # =========================================================================
    # STEP 7: Initialize tracking files
    # =========================================================================

    output.progress("Step 7: Initializing tracking files...")
    logger.info("Step 7: Initializing tracking files...")

    if dry_run:
        output.info(f"   Would initialize tracking files with {tier}")
    else:
        initialize_tracking_files(tier, coverage_target, project_root)
        output.info(f"   ✓ Initialized tracking files with {tier}")

    # =========================================================================
    # STEP 8: Install Claude commands
    # =========================================================================

    output.progress("Step 8: Installing Claude Code slash commands...")
    logger.info("Step 8: Installing Claude Code slash commands...")

    if dry_run:
        output.info("   Would install slash commands")
    else:
        try:
            installed_commands = install_claude_commands(project_root)
            output.info(f"   ✓ Installed {len(installed_commands)} slash commands")
        except Exception as e:
            logger.warning(f"Claude commands installation failed: {e}")
            output.warning(f"   Claude commands installation failed: {e}")
            output.info("   You can install them manually later")

    # =========================================================================
    # STEP 9: Append to README.md
    # =========================================================================

    output.progress("Step 9: Updating README.md...")
    logger.info("Step 9: Updating README.md...")

    if dry_run:
        output.info("   Would append Solokit section to README.md")
    else:
        try:
            readme_updated = append_to_readme(project_root)
            if readme_updated:
                output.info("   ✓ Appended Solokit section to README.md")
            else:
                output.info("   ✓ README.md already contains Solokit section")
        except FileOperationError as e:
            logger.warning(f"README.md update failed: {e}")
            output.warning(f"   README.md update failed: {e}")

    # =========================================================================
    # STEP 10: Append to CLAUDE.md
    # =========================================================================

    output.progress("Step 10: Updating CLAUDE.md...")
    logger.info("Step 10: Updating CLAUDE.md...")

    if dry_run:
        output.info("   Would append Solokit section to CLAUDE.md")
    else:
        try:
            claude_md_updated = append_to_claude_md(tier, coverage_target, project_root)
            if claude_md_updated:
                output.info("   ✓ Appended Solokit section to CLAUDE.md")
            else:
                output.info("   ✓ CLAUDE.md already contains Solokit section")
        except FileOperationError as e:
            logger.warning(f"CLAUDE.md update failed: {e}")
            output.warning(f"   CLAUDE.md update failed: {e}")

    # =========================================================================
    # STEP 11: Update .gitignore
    # =========================================================================

    output.progress("Step 11: Updating .gitignore...")
    logger.info("Step 11: Updating .gitignore...")

    if dry_run:
        output.info("   Would update .gitignore with Solokit entries")
    else:
        try:
            gitignore_updated = _update_gitignore_for_adoption(project_info, project_root)
            if gitignore_updated:
                output.info("   ✓ Updated .gitignore with Solokit entries")
            else:
                output.info("   ✓ .gitignore already up to date")
        except FileOperationError as e:
            logger.warning(f".gitignore update failed: {e}")
            output.warning(f"   .gitignore update failed: {e}")

    # =========================================================================
    # STEP 12: Run initial scans (stack.txt, tree.txt)
    # =========================================================================

    output.progress("Step 12: Running initial scans...")
    logger.info("Step 12: Running initial scans...")

    if dry_run:
        output.info("   Would generate stack.txt and tree.txt")
    else:
        try:
            scan_results = run_initial_scans(project_root)
            if scan_results.get("stack"):
                output.info("   ✓ Generated stack.txt")
            if scan_results.get("tree"):
                output.info("   ✓ Generated tree.txt")
        except Exception as e:
            logger.warning(f"Initial scans failed: {e}")
            output.warning(f"   Initial scans failed: {e}")

    # =========================================================================
    # STEP 13: Install git hooks
    # =========================================================================

    output.progress("Step 13: Installing git hooks...")
    logger.info("Step 13: Installing git hooks...")

    if dry_run:
        output.info("   Would install git hooks")
    else:
        try:
            install_git_hooks(project_root)
            output.info("   ✓ Installed git hooks")
        except Exception as e:
            logger.warning(f"Git hooks installation failed: {e}")
            output.warning(f"   Git hooks installation failed: {e}")
            output.info("   You can install them manually later")

    # =========================================================================
    # STEP 14: Create adoption commit (optional)
    # =========================================================================

    if not skip_commit and not dry_run:
        output.progress("Step 14: Creating adoption commit...")
        logger.info("Step 14: Creating adoption commit...")

        try:
            commit_created = _create_adoption_commit(tier, project_info, project_root)
            if commit_created:
                output.info("   ✓ Created adoption commit")
            else:
                output.info("   ✓ Skipped commit (no changes or no git repo)")
        except Exception as e:
            logger.warning(f"Adoption commit failed: {e}")
            output.warning(f"   Adoption commit failed: {e}")
            output.info("   You can commit changes manually")
    elif dry_run and not skip_commit:
        output.progress("Step 14: Creating adoption commit...")
        output.info("   Would create adoption commit")

    # =========================================================================
    # SUCCESS SUMMARY
    # =========================================================================

    output.info("\n" + "=" * 60)
    if dry_run:
        output.info("🔍 DRY RUN Complete - No changes were made")
    else:
        output.info("✅ Solokit Adoption Complete!")
    output.info("=" * 60 + "\n")

    tier_display = tier.replace("-", " ").replace("tier ", "Tier ").title()

    output.info(f"📦 Project Type: {project_info.language.value.title()}")
    if project_info.framework.value != "none":
        output.info(f"🔧 Framework: {project_info.framework.value.title()}")
    output.info(f"🎯 Quality Tier: {tier_display}")
    output.info(f"📊 Coverage Target: {coverage_target}%")
    output.info("")

    if dry_run:
        output.info("To apply these changes, run:")
        output.info(f"   sk adopt --tier={tier} --coverage={coverage_target}")
        if additional_options:
            output.info(f"   --options={','.join(additional_options)}")
        output.info("")
    else:
        output.info("✓ Session management enabled")
        output.info("✓ Claude Code slash commands installed")
        output.info("✓ Documentation updated")
        if backup_dir:
            output.info(f"✓ Backups saved to: {backup_dir.relative_to(project_root)}")
        output.info("")

        output.info("=" * 60)
        output.info("🚀 Next Steps:")
        output.info("=" * 60)
        output.info("")
        output.info("1. Review the updated README.md and CLAUDE.md")
        output.info("2. Create your first work item: /work-new")
        output.info("3. Start a session: /start")
        output.info("")
        output.info("Available slash commands:")
        output.info("   /start      - Begin a session with briefing")
        output.info("   /end        - Complete session with quality gates")
        output.info("   /work-new   - Create work items interactively")
        output.info("   /status     - Check current session status")
        output.info("")

    return 0
