#!/usr/bin/env python3
"""
Interactive Solokit Adoption

Provides both command-line argument and interactive modes for adopting
Solokit into existing projects. Unlike initialization, this does not
install templates but adds session management to existing code.
"""

from __future__ import annotations

import argparse
import logging

from solokit.core.cli_prompts import confirm_action, multi_select_list, select_from_list

logger = logging.getLogger(__name__)


def prompt_quality_tier() -> str:
    """
    Interactively prompt user to select quality tier.

    Returns:
        Selected tier ID (e.g., "tier-2-standard")
    """
    choices = [
        "Essential - Linting, formatting, type-check, basic tests",
        "Standard - Essential + Pre-commit hooks + Security foundation",
        "Comprehensive - Standard + Advanced quality + Testing",
        "Production-Ready - Comprehensive + Operations + Deployment",
    ]

    tier_map = {
        choices[0]: "tier-1-essential",
        choices[1]: "tier-2-standard",
        choices[2]: "tier-3-comprehensive",
        choices[3]: "tier-4-production",
    }

    print("\n🎯 Select quality tier:\n")
    selected = select_from_list(
        "Choose a quality tier:",
        choices,
        default=choices[1],  # Default to Standard
    )

    return tier_map.get(selected, "tier-2-standard")


def prompt_coverage_target() -> int:
    """
    Interactively prompt user to select coverage target.

    Returns:
        Coverage target percentage (60, 80, or 90)
    """
    choices = [
        "60% - Light coverage, fast iteration",
        "80% - Balanced coverage (recommended)",
        "90% - High coverage, maximum confidence",
    ]

    coverage_map = {
        choices[0]: 60,
        choices[1]: 80,
        choices[2]: 90,
    }

    print("\n📊 Select test coverage target:\n")
    selected = select_from_list(
        "Choose a coverage target:",
        choices,
        default=choices[1],  # Default to 80%
    )

    return coverage_map.get(selected, 80)


def prompt_additional_options() -> list[str]:
    """
    Interactively prompt user to select additional options.

    Returns:
        List of selected option IDs (e.g., ["ci_cd", "docker"])
    """
    choices = [
        "CI/CD - GitHub Actions workflows",
        "Docker - Container support with docker-compose",
        "Env Templates - .env files and .editorconfig",
    ]

    option_map = {
        choices[0]: "ci_cd",
        choices[1]: "docker",
        choices[2]: "env_templates",
    }

    print("\n⚙️  Select additional options (use space to select, enter to confirm):\n")
    selected_labels = multi_select_list("Choose additional options (optional):", choices)

    # Map selected labels back to option IDs
    return [option_map[label] for label in selected_labels if label in option_map]


def show_adoption_warning(tier: str | None = None, language: str | None = None) -> bool:
    """
    Display adoption warning and get user confirmation.

    Args:
        tier: Selected quality tier (for showing config files that will be overwritten)
        language: Detected project language (for determining template)

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "=" * 60)
    print("⚠️  ADOPTION WARNING")
    print("=" * 60)
    print("")
    print("The following will happen:")
    print("")
    print("  • .session/ directory will be created")
    print("  • .claude/commands/ will be installed (overwrites existing)")
    print("  • CLAUDE.md will be appended (or created if missing)")
    print("  • README.md will be appended (or created if missing)")
    print("  • .gitignore will be appended with Solokit entries")
    print("  • Git hooks will be installed (overwrites existing)")

    # Show config files that will be overwritten based on tier
    if tier:
        try:
            from solokit.adopt.orchestrator import (
                _get_template_id_for_language,
                get_config_files_to_install,
            )
            from solokit.adopt.project_detector import ProjectLanguage

            # Map language string to enum if provided
            template_id = "saas_t3"  # Default
            if language:
                lang_map = {
                    "python": ProjectLanguage.PYTHON,
                    "nodejs": ProjectLanguage.NODEJS,
                    "typescript": ProjectLanguage.TYPESCRIPT,
                    "fullstack": ProjectLanguage.FULLSTACK,
                }
                lang_enum = lang_map.get(language.lower(), ProjectLanguage.UNKNOWN)
                template_id = _get_template_id_for_language(lang_enum)

            config_files = get_config_files_to_install(template_id, tier)
            if config_files:
                print("")
                print("  📦 Config files that will be installed/overwritten:")
                # Show first 8 files, then summarize
                for config_file in config_files[:8]:
                    print(f"     - {config_file}")
                if len(config_files) > 8:
                    print(f"     ... and {len(config_files) - 8} more")
        except Exception:
            # If we can't get config files, just continue without showing them
            pass

    print("")
    print("Existing source code files will NOT be modified.")
    print("")
    print("=" * 60)

    return confirm_action("Continue with adoption?", default=False)


def main() -> int:
    """
    Main entry point for adopt command with interactive mode support.

    Supports both argument-based and interactive modes:
    - With arguments: Direct adoption
    - Without arguments: Interactive prompts

    Returns:
        0 on success, non-zero on failure
    """
    parser = argparse.ArgumentParser(description="Adopt Solokit into an existing project")
    parser.add_argument(
        "--tier",
        choices=[
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
            "tier-4-production",
        ],
        help="Quality gates tier",
    )
    parser.add_argument(
        "--coverage",
        type=int,
        choices=[60, 80, 90],
        help="Test coverage target percentage",
    )
    parser.add_argument(
        "--options",
        help="Comma-separated list of additional options (ci_cd,docker,env_templates)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--skip-commit",
        action="store_true",
        help="Skip creating adoption commit",
    )

    args = parser.parse_args()

    # Import here to avoid circular imports
    from solokit.adopt.orchestrator import run_adoption

    # Note: Project detection is handled by the orchestrator (Step 1)
    # This avoids duplicate detection and provides a unified display

    # Determine if we're in argument mode or interactive mode
    if args.tier and args.coverage is not None:
        # Argument mode - required params provided
        tier = args.tier
        coverage_target = args.coverage
        additional_options = []
        if args.options:
            additional_options = [opt.strip() for opt in args.options.split(",")]

        # Show warning unless --yes flag is set
        if not args.yes:
            if not show_adoption_warning(tier=tier):
                print("\n❌ Adoption cancelled")
                return 1

    elif args.tier or args.coverage is not None:
        # Partial arguments provided - error
        logger.error("❌ When using arguments, --tier and --coverage are both required")
        logger.error("\nUsage:")
        logger.error("  sk adopt --tier=tier-2-standard --coverage=80")
        logger.error("  sk adopt --tier=tier-3-comprehensive --coverage=90 --options=ci_cd,docker")
        logger.error("\nOr run without arguments for interactive mode:")
        logger.error("  sk adopt")
        return 1

    else:
        # Interactive mode
        print("\n🔄 Welcome to Solokit Adoption!\n")
        print("This wizard will add Solokit session management to your existing project:")
        print("  • Session tracking and briefings")
        print("  • Work item management")
        print("  • Learning capture system")
        print("  • Quality gates")
        print("  • Claude Code slash commands")

        tier = prompt_quality_tier()
        coverage_target = prompt_coverage_target()
        additional_options = prompt_additional_options()

        # Show summary
        print("\n" + "=" * 60)
        print("📋 Configuration Summary")
        print("=" * 60)
        print(f"Quality Tier:     {tier}")
        print(f"Coverage Target:  {coverage_target}%")
        if additional_options:
            print(f"Additional:       {', '.join(additional_options)}")
        else:
            print("Additional:       None")
        print("=" * 60)

        # Show warning and get confirmation
        if not show_adoption_warning(tier=tier):
            print("\n❌ Adoption cancelled")
            return 1

    # Run adoption
    return run_adoption(
        tier=tier,
        coverage_target=coverage_target,
        additional_options=additional_options,
        skip_commit=args.skip_commit,
    )


if __name__ == "__main__":
    exit(main())
