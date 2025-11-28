"""
Session Structure Module

Creates .session directory structure and tracking files.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from solokit.core.exceptions import FileOperationError

logger = logging.getLogger(__name__)


def create_session_directories(project_root: Path | None = None) -> list[Path]:
    """
    Create .session directory structure.

    Args:
        project_root: Project root directory

    Returns:
        List of created directory paths

    Raises:
        FileOperationError: If directory creation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    session_dir = project_root / ".session"
    created_dirs = []

    directories = [
        session_dir / "tracking",
        session_dir / "briefings",
        session_dir / "history",
        session_dir / "specs",
        session_dir / "guides",
    ]

    try:
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.debug(f"Created {dir_path.relative_to(project_root)}")

        logger.info(f"Created .session/ structure with {len(created_dirs)} directories")
        return created_dirs

    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir),
            details=f"Failed to create .session directory structure: {str(e)}",
            cause=e,
        )


def initialize_tracking_files(
    tier: str, coverage_target: int, project_root: Path | None = None
) -> list[Path]:
    """
    Initialize tracking files from templates with tier-specific config.

    Args:
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage
        project_root: Project root directory

    Returns:
        List of created file paths

    Raises:
        FileOperationError: If file operations fail
        TemplateNotFoundError: If required template files are missing
    """
    if project_root is None:
        project_root = Path.cwd()

    session_dir = project_root / ".session"
    template_dir = Path(__file__).parent.parent / "templates"
    created_files = []

    logger.info("Initializing tracking files...")

    # Copy template tracking files
    tracking_files = [
        ("work_items.json", "tracking/work_items.json"),
        ("learnings.json", "tracking/learnings.json"),
        ("status_update.json", "tracking/status_update.json"),
    ]

    for src, dst in tracking_files:
        src_path = template_dir / src
        dst_path = session_dir / dst
        if src_path.exists():
            try:
                shutil.copy(src_path, dst_path)
                created_files.append(dst_path)
                logger.debug(f"Created {dst}")
            except Exception as e:
                raise FileOperationError(
                    operation="copy",
                    file_path=str(dst_path),
                    details=f"Failed to copy tracking file template: {str(e)}",
                    cause=e,
                )

    # Create empty update tracking files
    try:
        updates_files = [
            session_dir / "tracking" / "stack_updates.json",
            session_dir / "tracking" / "tree_updates.json",
        ]
        for update_file in updates_files:
            update_file.write_text(json.dumps({"updates": []}, indent=2))
            created_files.append(update_file)
            logger.debug(f"Created {update_file.name}")
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir / "tracking"),
            details=f"Failed to create tracking files: {str(e)}",
            cause=e,
        )

    # Create config.json with tier-specific settings
    config_data = {
        "curation": {
            "auto_curate": True,
            "frequency": 5,
            "dry_run": False,
            "similarity_threshold": 0.7,
            "categories": [
                "architecture_patterns",
                "gotchas",
                "best_practices",
                "technical_debt",
                "performance_insights",
                "security",
            ],
        },
        "quality_gates": {
            "tier": tier,
            "coverage_threshold": coverage_target,
            "test_execution": {"enabled": True, "required": True},
            "linting": {
                "enabled": True,
                "required": True,
                "commands": {
                    "python": "ruff check .",
                    "javascript": "npm run lint",
                    "typescript": "npm run lint",
                },
                "auto_fix": False,
            },
            "formatting": {
                "enabled": True,
                "required": True,
                "commands": {
                    "python": "ruff format .",
                    "javascript": "npx prettier .",
                    "typescript": "npx prettier .",
                },
                "auto_fix": False,
            },
            "security": {"enabled": True, "required": True},
            "documentation": {
                "enabled": True,
                "required": True,
                "check_changelog": True,
                "check_docstrings": True,
                "check_readme": False,
            },
            "context7": {
                "enabled": False,
                "required": True,
                "important_libraries": [],
            },
            "custom_validations": {"rules": []},
        },
        "integration_tests": {
            "enabled": True,
            "docker_compose_file": "docker-compose.integration.yml",
            "environment_validation": True,
            "health_check_timeout": 300,
            "test_data_fixtures": True,
            "parallel_execution": True,
            "performance_benchmarks": {
                "enabled": True,
                "required": True,
                "regression_threshold": 0.10,
                "baseline_storage": ".session/tracking/performance_baselines.json",
                "load_test_tool": "wrk",
                "metrics": ["response_time", "throughput", "resource_usage"],
            },
            "api_contracts": {
                "enabled": True,
                "required": True,
                "contract_format": "openapi",
                "breaking_change_detection": True,
                "version_storage": ".session/tracking/api_contracts/",
                "fail_on_breaking_changes": True,
            },
            "documentation": {
                "architecture_diagrams": True,
                "sequence_diagrams": True,
                "contract_documentation": True,
                "performance_baseline_docs": True,
            },
        },
        "git_workflow": {
            "mode": "pr",
            "auto_push": True,
            "auto_create_pr": True,
            "delete_branch_after_merge": True,
            "pr_title_template": "{type}: {title}",
            "pr_body_template": "## Summary\n\n{description}\n\n## Work Item\n- ID: {work_item_id}\n- Type: {type}\n- Session: {session_num}\n\n## Changes\n{commit_messages}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        },
    }

    try:
        config_path = session_dir / "config.json"
        config_path.write_text(json.dumps(config_data, indent=2))
        created_files.append(config_path)
        logger.info("Created config.json with tier-specific settings")
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir / "config.json"),
            details=f"Failed to create config.json: {str(e)}",
            cause=e,
        )

    # Copy config schema file
    schema_source = template_dir / "config.schema.json"
    schema_dest = session_dir / "config.schema.json"

    if schema_source.exists() and not schema_dest.exists():
        try:
            shutil.copy(schema_source, schema_dest)
            created_files.append(schema_dest)
            logger.info("Created config.schema.json")
        except Exception as e:
            raise FileOperationError(
                operation="copy",
                file_path=str(schema_dest),
                details=f"Failed to copy config schema: {str(e)}",
                cause=e,
            )

    # Copy guide templates to .session/guides/
    guides_source = template_dir / "guides"
    guides_dest = session_dir / "guides"

    if guides_source.exists():
        try:
            for guide_file in guides_source.glob("*.md"):
                dest_file = guides_dest / guide_file.name
                shutil.copy(guide_file, dest_file)
                created_files.append(dest_file)
                logger.debug(f"Created guide: {guide_file.name}")
            logger.info(f"Copied {len(list(guides_source.glob('*.md')))} guide files")
        except Exception as e:
            raise FileOperationError(
                operation="copy",
                file_path=str(guides_dest),
                details=f"Failed to copy guide templates: {str(e)}",
                cause=e,
            )

    # Copy CHANGELOG.md to project root (if not already present)
    changelog_source = template_dir / "CHANGELOG.md"
    changelog_dest = project_root / "CHANGELOG.md"

    if changelog_source.exists() and not changelog_dest.exists():
        try:
            shutil.copy(changelog_source, changelog_dest)
            created_files.append(changelog_dest)
            logger.info("Created CHANGELOG.md")
        except Exception as e:
            raise FileOperationError(
                operation="copy",
                file_path=str(changelog_dest),
                details=f"Failed to copy CHANGELOG.md: {str(e)}",
                cause=e,
            )

    logger.info(f"Initialized {len(created_files)} tracking files")
    return created_files
