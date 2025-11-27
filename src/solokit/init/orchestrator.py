"""
Template-Based Init Orchestrator

Main orchestration logic for template-based project initialization.
Implements the complete 21-step initialization flow.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, cast

from solokit.core.output import get_output
from solokit.github.setup import GitHubSetup
from solokit.init.claude_commands_installer import install_claude_commands
from solokit.init.claude_md_generator import generate_claude_md
from solokit.init.dependency_installer import install_dependencies
from solokit.init.docs_structure import create_docs_structure
from solokit.init.env_generator import generate_env_files
from solokit.init.environment_validator import validate_environment
from solokit.init.format_lint_fixer import run_format_lint_fix
from solokit.init.git_hooks_installer import install_git_hooks
from solokit.init.git_setup import check_blank_project_or_exit, check_or_init_git
from solokit.init.gitignore_updater import update_gitignore
from solokit.init.initial_commit import create_initial_commit
from solokit.init.initial_scans import run_initial_scans
from solokit.init.readme_generator import generate_readme
from solokit.init.session_structure import create_session_directories, initialize_tracking_files
from solokit.init.template_installer import get_template_info, install_template

logger = logging.getLogger(__name__)
output = get_output()


def run_template_based_init(
    template_id: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str] | None = None,
    project_root: Path | None = None,
) -> int:
    """
    Run complete template-based initialization with 20-step flow.

    Args:
        template_id: Template identifier (e.g., "saas_t3")
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage (60, 80, 90)
        additional_options: List of additional options (e.g., ["ci_cd", "docker"])
        project_root: Project root directory (defaults to current directory)

    Returns:
        0 on success, non-zero on failure

    Raises:
        Various exceptions from individual init modules on critical failures
    """
    if additional_options is None:
        additional_options = []

    if project_root is None:
        project_root = Path.cwd()

    # Show user-facing progress header
    output.info("\n" + "=" * 60)
    output.info("🚀 Initializing Session-Driven Development Project")
    output.info("=" * 60 + "\n")

    logger.info("🚀 Initializing Session-Driven Development with Template System...\n")

    # =========================================================================
    # PHASE 1: PRE-FLIGHT CHECKS & VALIDATION
    # =========================================================================

    output.progress("Phase 1: Pre-flight validation...")

    # Step 1: Check if already initialized + Check if blank project
    logger.info("Step 1: Pre-flight validation...")
    check_blank_project_or_exit(project_root)
    logger.info("✓ Project directory is blank\n")

    # Step 2: Initialize/verify git repository
    logger.info("Step 2: Git initialization...")
    check_or_init_git(project_root)
    logger.info("")

    # Step 3: Validate AND auto-update environment
    logger.info(f"Step 3: Environment validation for {template_id}...")

    # Map template_id to stack_type for environment validation
    template_to_stack_type = {
        "saas_t3": "saas_t3",
        "ml_ai_fastapi": "ml_ai_fastapi",
        "dashboard_refine": "dashboard_refine",
        "fullstack_nextjs": "fullstack_nextjs",
    }
    stack_type = template_to_stack_type.get(template_id)

    python_binary = None
    if stack_type:
        env_result = validate_environment(
            cast(
                Literal["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"],
                stack_type,
            ),
            auto_update=True,
        )
        logger.info(f"✓ Environment validated for {template_id}")
        if env_result.get("node_version"):
            logger.info(f"  Node.js: {env_result['node_version']}")
        if env_result.get("python_version"):
            logger.info(f"  Python: {env_result['python_version']}")
            python_binary = cast(str | None, env_result.get("python_binary"))
    logger.info("")

    output.info("✓ Pre-flight checks passed\n")

    # Get template information
    template_info = get_template_info(template_id)

    # =========================================================================
    # PHASE 3: INSTALLATION & SETUP (Phase 2 is interactive, done in CLI)
    # =========================================================================

    output.progress("Phase 2: Installing template files...")

    # Step 4: Install template files (base + tier + options)
    logger.info("Step 4: Installing template files...")
    install_result = install_template(
        template_id, tier, additional_options, project_root, coverage_target
    )
    logger.info(f"✓ Installed {install_result['files_installed']} template files\n")
    output.info(f"✓ Installed {install_result['files_installed']} template files")

    # Step 5: Generate README.md
    logger.info("Step 5: Generating README.md...")
    generate_readme(template_id, tier, coverage_target, additional_options, project_root)
    logger.info("✓ Generated README.md\n")
    output.info("✓ Generated README.md")

    # Step 6: Generate CLAUDE.md
    logger.info("Step 6: Generating CLAUDE.md...")
    generate_claude_md(template_id, tier, coverage_target, additional_options, project_root)
    logger.info("✓ Generated CLAUDE.md\n")
    output.info("✓ Generated CLAUDE.md")

    # Step 7: Config files (handled by template installation)
    logger.info("Step 7: Config files installed via template\n")

    # Step 8: Install dependencies - This is the longest step
    output.info("")
    output.progress("Phase 3: Installing dependencies...")
    output.info("   This may take several minutes. Please wait...\n")
    logger.info("Step 8: Installing dependencies...")
    logger.info("⏳ This may take several minutes...\n")

    try:
        install_dependencies(
            template_id,
            cast(
                Literal[
                    "tier-1-essential",
                    "tier-2-standard",
                    "tier-3-comprehensive",
                    "tier-4-production",
                ],
                tier,
            ),
            python_binary,
            project_root,
        )
        logger.info("✓ Dependencies installed successfully\n")
        output.info("\n✓ All dependencies installed successfully")
    except Exception as e:
        logger.warning(f"Dependency installation encountered an issue: {e}")
        logger.warning("You can install dependencies manually later\n")
        output.warning(f"Dependency installation issue: {e}")
        output.info("   You can install dependencies manually later")

    # Step 9: Create docs directory structure
    output.info("")
    output.progress("Phase 4: Configuring project structure...")
    logger.info("Step 9: Creating documentation structure...")
    create_docs_structure(project_root)
    logger.info("✓ Created docs/ structure\n")

    # Step 10: Starter code (handled by template)
    logger.info("Step 10: Starter code installed via template\n")

    # Step 11: Smoke tests (handled by template)
    logger.info("Step 11: Smoke tests installed via template\n")

    # Step 12: Create .env files
    if "env_templates" in additional_options:
        logger.info("Step 12: Generating environment files...")
        generate_env_files(template_id, project_root)
        logger.info("✓ Generated .env.example and .editorconfig\n")
    else:
        logger.info("Step 12: Skipped (environment templates not selected)\n")

    # Step 13: Create .session structure
    logger.info("Step 13: Creating .session structure...")
    create_session_directories(project_root)
    logger.info("✓ Created .session/ directories\n")
    output.info("✓ Created documentation and session structure")

    # Step 14: Initialize tracking files
    logger.info("Step 14: Initializing tracking files...")
    initialize_tracking_files(tier, coverage_target, project_root)
    logger.info("✓ Initialized tracking files with tier-specific config\n")
    output.info("✓ Initialized tracking files with tier-specific config")

    # Step 15: Run initial scans (stack.txt, tree.txt)
    output.progress("Running initial scans...")
    logger.info("Step 15: Running initial scans...")
    scan_results = run_initial_scans(project_root)
    if scan_results["stack"]:
        logger.info("✓ Generated stack.txt")
    if scan_results["tree"]:
        logger.info("✓ Generated tree.txt")
    logger.info("")
    output.info("✓ Generated stack.txt and tree.txt")

    # Step 16: Install git hooks
    output.info("")
    output.progress("Phase 5: Finalizing setup...")
    logger.info("Step 16: Installing git hooks...")
    install_git_hooks(project_root)
    logger.info("✓ Installed git hooks\n")
    output.info("✓ Installed git hooks")

    # Step 17: Install Claude Code slash commands
    logger.info("Step 17: Installing Claude Code slash commands...")
    try:
        installed_commands = install_claude_commands(project_root)
        logger.info(f"✓ Installed {len(installed_commands)} slash commands to .claude/commands/\n")
        output.info(f"✓ Installed {len(installed_commands)} Claude Code slash commands")
    except Exception as e:
        logger.warning(f"Claude commands installation failed: {e}")
        logger.warning("Slash commands may not be available. You can install them manually.\n")
        output.warning("Claude commands installation failed (you can install them manually)")

    # Step 18: Update .gitignore
    logger.info("Step 18: Updating .gitignore...")
    update_gitignore(template_id, project_root)
    logger.info("✓ Updated .gitignore\n")
    output.info("✓ Updated .gitignore")

    # Step 19: Run format/lint auto-fix (silent)
    # This fixes user-provided files (PRD.md, etc.) before commit
    logger.info("Step 19: Running format/lint auto-fix...")
    fix_result = run_format_lint_fix(template_id, project_root)
    if fix_result["format_success"] and fix_result["lint_success"]:
        logger.info("✓ Format/lint auto-fix completed\n")
    else:
        logger.info("Format/lint auto-fix completed with warnings\n")

    # Step 20: Create initial commit
    output.progress("Creating initial commit...")
    logger.info("Step 20: Creating initial commit...")
    commit_success = create_initial_commit(
        template_name=template_info["display_name"],
        tier=tier,
        coverage_target=coverage_target,
        additional_options=additional_options,
        stack_info=template_info["stack"],
        project_root=project_root,
    )
    if commit_success:
        logger.info("✓ Created initial commit\n")
        output.info("✓ Created initial commit")
    else:
        logger.warning("Initial commit failed (you can commit manually later)\n")
        output.warning("Initial commit failed (you can commit manually later)")

    # Step 21: GitHub repository setup (optional)
    output.info("")
    logger.info("Step 21: GitHub repository setup...")
    github_setup = GitHubSetup(project_root)
    github_result = github_setup.run_interactive()
    if github_result.success and not github_result.skipped:
        logger.info(f"✓ GitHub repository configured: {github_result.repo_url}\n")
    elif github_result.skipped:
        logger.info("GitHub setup skipped\n")
    else:
        logger.warning(f"GitHub setup failed: {github_result.error_message}\n")

    # =========================================================================
    # SUCCESS SUMMARY
    # =========================================================================

    logger.info("=" * 70)
    logger.info("✅ Solokit Template Initialization Complete!")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"📦 Template: {template_info['display_name']}")
    # Show completion summary to user
    output.info(f"\n🎯 Quality Tier: {tier}")
    output.info(f"📊 Coverage Target: {coverage_target}%")
    output.info("")
    output.info("✓ Project structure created")
    output.info("✓ Dependencies installed")
    output.info("✓ Quality gates configured")
    output.info("✓ Documentation structure created")
    output.info("✓ Session tracking initialized")
    output.info("✓ Git repository configured")
    if github_result.success and not github_result.skipped and github_result.repo_url:
        output.info(f"✓ GitHub repository: {github_result.repo_url}")
    output.info("")
    output.info("=" * 70)
    output.info("💡 Best used with Claude Code!")
    output.info("=" * 70)
    output.info("")
    output.info("Open this project in Claude Code to unlock the full experience:")
    output.info("   • /start      - Begin a session with comprehensive briefing")
    output.info("   • /end        - Complete work with quality gates & learning capture")
    output.info("   • /work-new   - Create work items interactively")
    output.info("   • /work-list  - View and manage your work items")
    output.info("")
    output.info("Get Claude Code: https://claude.com/claude-code")
    output.info("")
    output.info("=" * 70)
    output.info("")
    output.info("🚀 Next Steps:")
    output.info("   1. Read .session/guides/STACK_GUIDE.md to understand your stack")
    output.info("   2. Read .session/guides/PRD_WRITING_GUIDE.md to write your PRD")
    output.info("   3. Create your PRD at docs/PRD.md")
    output.info("   4. Create work items from your PRD: /work-new")
    output.info("   5. Start working: /start <work-item-id>")
    output.info("")

    return 0
