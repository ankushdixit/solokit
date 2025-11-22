#!/usr/bin/env python3
"""
Interactive Solokit Initialization

Provides both command-line argument and interactive modes for project initialization.
All initialization flows through the template-based system with quality tiers.
"""

from __future__ import annotations

import argparse
import logging

from solokit.core.cli_prompts import confirm_action, multi_select_list, select_from_list

logger = logging.getLogger(__name__)


def prompt_template_selection() -> str:
    """
    Interactively prompt user to select a project template.

    Returns:
        Selected template ID (e.g., "saas_t3")
    """
    choices = [
        "SaaS Application (T3 Stack) - Next.js 16, React 19, tRPC, Prisma",
        "ML/AI Tooling (FastAPI) - FastAPI, SQLModel, Pydantic, Alembic",
        "Internal Dashboard (Refine) - Refine, Next.js 16, shadcn/ui",
        "Full-Stack Product (Next.js) - Next.js 16, Prisma, Zod, Tailwind",
    ]

    template_map = {
        choices[0]: "saas_t3",
        choices[1]: "ml_ai_fastapi",
        choices[2]: "dashboard_refine",
        choices[3]: "fullstack_nextjs",
    }

    print("\n📋 Select your project template:\n")
    selected = select_from_list("Choose a template:", choices, default=choices[0])

    return template_map.get(selected, "saas_t3")


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


def main() -> int:
    """
    Main entry point for init command with interactive mode support.

    Supports both argument-based and interactive modes:
    - With arguments: Direct initialization
    - Without arguments: Interactive prompts

    Returns:
        0 on success, non-zero on failure
    """
    parser = argparse.ArgumentParser(description="Initialize Session-Driven Development project")
    parser.add_argument(
        "--template",
        choices=["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"],
        help="Template to use for initialization",
    )
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

    args = parser.parse_args()

    # Import here to avoid circular imports
    from solokit.init.orchestrator import run_template_based_init

    # Determine if we're in argument mode or interactive mode
    if args.template and args.tier and args.coverage:
        # Argument mode - all required params provided
        template_id = args.template
        tier = args.tier
        coverage_target = args.coverage
        additional_options = []
        if args.options:
            additional_options = [opt.strip() for opt in args.options.split(",")]

    elif args.template or args.tier or args.coverage:
        # Partial arguments provided - error
        logger.error("❌ When using arguments, --template, --tier, and --coverage are all required")
        logger.error("\nUsage:")
        logger.error("  sk init --template=saas_t3 --tier=tier-2-standard --coverage=80")
        logger.error(
            "  sk init --template=ml_ai_fastapi --tier=tier-3-comprehensive --coverage=90 --options=ci_cd,docker"
        )
        logger.error("\nOr run without arguments for interactive mode:")
        logger.error("  sk init")
        return 1

    else:
        # Interactive mode
        print("🚀 Welcome to Solokit Project Initialization!\n")
        print("This wizard will help you set up a new project with:")
        print("  • Modern development stack")
        print("  • Quality automation")
        print("  • Session-driven workflow")
        print("  • Claude Code integration")

        template_id = prompt_template_selection()
        tier = prompt_quality_tier()
        coverage_target = prompt_coverage_target()
        additional_options = prompt_additional_options()

        # Show summary
        print("\n" + "=" * 60)
        print("📋 Configuration Summary")
        print("=" * 60)
        print(f"Template:         {template_id}")
        print(f"Quality Tier:     {tier}")
        print(f"Coverage Target:  {coverage_target}%")
        if additional_options:
            print(f"Additional:       {', '.join(additional_options)}")
        else:
            print("Additional:       None")
        print("=" * 60 + "\n")

        if not confirm_action("Proceed with initialization?", default=False):
            print("\n❌ Initialization cancelled")
            return 1

    # Run template-based init
    return run_template_based_init(
        template_id=template_id,
        tier=tier,
        coverage_target=coverage_target,
        additional_options=additional_options,
    )


if __name__ == "__main__":
    exit(main())
