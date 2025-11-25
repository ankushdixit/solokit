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


# Config files to install during adoption (whitelist approach)
# These are configuration files, NOT source code
ADOPT_CONFIG_FILES = {
    # TypeScript/JavaScript configs
    "tsconfig.json",
    "next.config.ts",
    "tailwind.config.ts",
    "postcss.config.mjs",
    "components.json",
    "eslint.config.mjs",
    "jest.config.ts",
    "jest.setup.ts",
    ".prettierrc",
    ".prettierignore",
    "playwright.config.ts",
    "stryker.conf.json",
    "type-coverage.json",
    ".jscpd.json",
    ".axe-config.json",
    "vercel.json",
    # Python configs
    "pyrightconfig.json",
    "alembic.ini",
    # Sentry configs (tier-4)
    "sentry.client.config.ts",
    "sentry.server.config.ts",
    "sentry.edge.config.ts",
    "instrumentation.ts",
}

# Template files that need processing (remove .template suffix)
ADOPT_TEMPLATE_FILES = {
    "package.json.tier1.template",
    "package.json.tier2.template",
    "package.json.tier3.template",
    "package.json.tier4.template",
    "jest.config.ts.tier3.template",
    "jest.config.ts.tier4.template",
    "pyproject.toml.template",
    "pyproject.toml.tier1.template",
    "pyproject.toml.tier2.template",
    "pyproject.toml.tier3.template",
    "pyproject.toml.tier4.template",
    "pytest.ini.template",
    "requirements.txt.template",
    "requirements-dev.txt.template",
    "requirements-prod.txt.template",
}

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


def _is_config_file(file_path: Path) -> bool:
    """
    Check if a file is a config file that should be installed.

    Args:
        file_path: Path to the file

    Returns:
        True if file should be installed
    """
    filename = file_path.name

    # Check direct match
    if filename in ADOPT_CONFIG_FILES:
        return True

    # Check template files
    if filename in ADOPT_TEMPLATE_FILES:
        return True

    return False


def _install_config_file(
    src_path: Path,
    project_root: Path,
    relative_path: Path,
    replacements: dict[str, str],
) -> bool:
    """
    Install a single config file, processing templates if needed.

    Args:
        src_path: Source file path
        project_root: Project root directory
        relative_path: Relative path from template dir
        replacements: Placeholder replacements

    Returns:
        True if file was installed
    """
    import shutil

    filename = src_path.name

    # Determine output path
    if filename.endswith(".template"):
        # Remove .template and tier suffix for output
        output_name = filename.replace(".template", "")
        # Handle tier-specific templates (e.g., package.json.tier3.template -> package.json)
        for tier in _get_tier_order():
            tier_suffix = f".{tier.replace('-', '')}"
            if tier_suffix in output_name:
                output_name = output_name.replace(tier_suffix, "")
                break
        # Also handle simpler patterns like jest.config.ts.tier3.template
        output_name = (
            output_name.replace(".tier1", "")
            .replace(".tier2", "")
            .replace(".tier3", "")
            .replace(".tier4", "")
        )
        output_path = project_root / relative_path.parent / output_name
    else:
        output_path = project_root / relative_path

    try:
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if filename.endswith(".template"):
            # Process template file
            content = src_path.read_text()
            for placeholder, value in replacements.items():
                content = content.replace(f"{{{placeholder}}}", value)
            output_path.write_text(content)
        else:
            # Direct copy
            shutil.copy2(src_path, output_path)

        logger.debug(f"Installed config: {output_path}")
        return True

    except Exception as e:
        logger.warning(f"Failed to install {src_path.name}: {e}")
        return False


def install_tier_configs(
    template_id: str,
    tier: str,
    project_root: Path,
    coverage_target: int,
) -> tuple[int, list[str]]:
    """
    Install tier-specific configuration files for adoption.

    Only installs config files (eslint, jest, prettier, etc.),
    NOT source code files.

    Args:
        template_id: Template to use for configs (e.g., "saas_t3")
        tier: Target tier (e.g., "tier-2-standard")
        project_root: Project root directory
        coverage_target: Coverage target for template replacements

    Returns:
        Tuple of (files_installed, list_of_installed_files)
    """
    from solokit.init.template_installer import get_template_directory

    template_dir = get_template_directory(template_id)
    project_name = project_root.name

    replacements = {
        "project_name": project_name,
        "project_description": f"A {project_name} project",
        "coverage_target": str(coverage_target),
    }

    files_installed = 0
    installed_files: list[str] = []

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
            if _is_config_file(file_path):
                if _install_config_file(file_path, project_root, relative_path, replacements):
                    files_installed += 1
                    installed_files.append(str(relative_path))

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
            if _is_config_file(file_path):
                if _install_config_file(file_path, project_root, relative_path, replacements):
                    files_installed += 1
                    # Show processed name for template files
                    display_name = str(relative_path)
                    if ".template" in display_name:
                        display_name = (
                            display_name.replace(".template", "")
                            .replace(".tier1", "")
                            .replace(".tier2", "")
                            .replace(".tier3", "")
                            .replace(".tier4", "")
                        )
                    installed_files.append(display_name)

    return files_installed, installed_files


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
) -> int:
    """
    Run complete adoption flow for existing project.

    This is a streamlined flow compared to template-based init:
    - No template installation
    - No dependency installation (uses existing)
    - No starter code generation

    Args:
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage
        additional_options: List of additional options (ci_cd, docker, env_templates)
        project_root: Project root directory (defaults to current directory)
        skip_commit: Skip creating adoption commit

    Returns:
        0 on success, non-zero on failure

    Raises:
        Various exceptions from individual modules on critical failures
    """
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
    # STEP 3: Install Tier-Specific Configuration Files
    # =========================================================================

    output.progress("Step 3: Installing tier-specific configuration files...")
    logger.info("Step 3: Installing tier-specific configuration files...")

    # Map detected language to template_id for config file sources
    detected_template_id = _get_template_id_for_language(project_info.language)
    logger.info(f"   Using template '{detected_template_id}' for config files")

    try:
        config_count, config_files = install_tier_configs(
            detected_template_id, tier, project_root, coverage_target
        )
        if config_count > 0:
            output.info(f"   ✓ Installed {config_count} configuration files")
            for config_file in config_files[:5]:  # Show first 5
                output.info(f"      - {config_file}")
            if len(config_files) > 5:
                output.info(f"      ... and {len(config_files) - 5} more")
        else:
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

    if additional_options:
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
                    # Handled in Step 4
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

    create_session_directories(project_root)
    output.info("   ✓ Created .session/ directories")

    # =========================================================================
    # STEP 7: Initialize tracking files
    # =========================================================================

    output.progress("Step 7: Initializing tracking files...")
    logger.info("Step 7: Initializing tracking files...")

    initialize_tracking_files(tier, coverage_target, project_root)
    output.info(f"   ✓ Initialized tracking files with {tier}")

    # =========================================================================
    # STEP 8: Install Claude commands
    # =========================================================================

    output.progress("Step 8: Installing Claude Code slash commands...")
    logger.info("Step 8: Installing Claude Code slash commands...")

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

    if not skip_commit:
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

    # =========================================================================
    # SUCCESS SUMMARY
    # =========================================================================

    output.info("\n" + "=" * 60)
    output.info("✅ Solokit Adoption Complete!")
    output.info("=" * 60 + "\n")

    tier_display = tier.replace("-", " ").replace("tier ", "Tier ").title()

    output.info(f"📦 Project Type: {project_info.language.value.title()}")
    if project_info.framework.value != "none":
        output.info(f"🔧 Framework: {project_info.framework.value.title()}")
    output.info(f"🎯 Quality Tier: {tier_display}")
    output.info(f"📊 Coverage Target: {coverage_target}%")
    output.info("")

    output.info("✓ Session management enabled")
    output.info("✓ Claude Code slash commands installed")
    output.info("✓ Documentation updated")
    output.info("")

    output.info("=" * 60)
    output.info("🚀 Next Steps:")
    output.info("=" * 60)
    output.info("")
    output.info("1. Review the updated README.md and CLAUDE.md")
    output.info("2. Create your first work item:")
    output.info('   sk work-new --type feature --title "My first feature"')
    output.info("3. Start a session:")
    output.info("   sk start")
    output.info("")
    output.info("In Claude Code, use these slash commands:")
    output.info("   /start      - Begin a session with briefing")
    output.info("   /end        - Complete session with quality gates")
    output.info("   /work-new   - Create work items interactively")
    output.info("   /status     - Check current session status")
    output.info("")

    return 0
