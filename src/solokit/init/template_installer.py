"""
Template Installer Module

Handles template file installation with tier-based structure.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any, cast

from solokit.core.exceptions import FileOperationError, TemplateNotFoundError

logger = logging.getLogger(__name__)


def load_template_registry() -> dict[str, Any]:
    """
    Load template registry from templates/template-registry.json.

    Returns:
        Template registry dictionary

    Raises:
        TemplateNotFoundError: If registry file not found
        FileOperationError: If registry file is invalid JSON
    """
    registry_path = Path(__file__).parent.parent / "templates" / "template-registry.json"

    if not registry_path.exists():
        raise TemplateNotFoundError(
            template_name="template-registry.json",
            template_path=str(registry_path.parent),
        )

    try:
        with open(registry_path) as f:
            return cast(dict[str, Any], json.load(f))
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="parse",
            file_path=str(registry_path),
            details=f"Invalid JSON in template registry: {str(e)}",
            cause=e,
        )


def get_template_info(template_id: str) -> dict[str, Any]:
    """
    Get template information from registry.

    Args:
        template_id: Template identifier (e.g., "saas_t3")

    Returns:
        Template metadata dictionary

    Raises:
        TemplateNotFoundError: If template not found in registry
    """
    registry = load_template_registry()

    if template_id not in registry["templates"]:
        available = ", ".join(registry["templates"].keys())
        raise TemplateNotFoundError(
            template_name=template_id,
            template_path=f"Available templates: {available}",
        )

    return cast(dict[str, Any], registry["templates"][template_id])


def get_template_directory(template_id: str) -> Path:
    """
    Get path to template directory.

    Args:
        template_id: Template identifier (e.g., "saas_t3")

    Returns:
        Path to template directory

    Raises:
        TemplateNotFoundError: If template directory doesn't exist
    """
    templates_root = Path(__file__).parent.parent / "templates"
    template_dir = templates_root / template_id

    if not template_dir.exists():
        raise TemplateNotFoundError(template_name=template_id, template_path=str(templates_root))

    return template_dir


def copy_directory_tree(src: Path, dst: Path, skip_patterns: list[str] | None = None) -> int:
    """
    Recursively copy directory tree from src to dst.

    Args:
        src: Source directory
        dst: Destination directory
        skip_patterns: List of filename patterns to skip (e.g., [".template", "__pycache__"])

    Returns:
        Number of files copied

    Raises:
        FileOperationError: If copy operation fails
    """
    if skip_patterns is None:
        skip_patterns = []

    files_copied = 0

    try:
        # Create destination directory
        dst.mkdir(parents=True, exist_ok=True)

        # Copy all files and subdirectories
        for item in src.iterdir():
            # Skip patterns
            if any(pattern in item.name for pattern in skip_patterns):
                continue

            src_item = src / item.name
            dst_item = dst / item.name

            if src_item.is_dir():
                files_copied += copy_directory_tree(src_item, dst_item, skip_patterns)
            else:
                shutil.copy2(src_item, dst_item)
                files_copied += 1
                logger.debug(f"Copied {src_item} -> {dst_item}")

    except Exception as e:
        raise FileOperationError(
            operation="copy",
            file_path=str(src),
            details=f"Failed to copy directory tree: {str(e)}",
            cause=e,
        )

    return files_copied


def replace_placeholders(content: str, replacements: dict[str, str]) -> str:
    """
    Replace placeholders in template content.

    Args:
        content: Template content with placeholders like {project_name}
        replacements: Dictionary of placeholder -> value

    Returns:
        Content with placeholders replaced
    """
    result = content
    for placeholder, value in replacements.items():
        result = result.replace(f"{{{placeholder}}}", value)
    return result


def install_base_template(
    template_id: str, project_root: Path, replacements: dict[str, str]
) -> int:
    """
    Install base template files.

    Args:
        template_id: Template identifier
        project_root: Project root directory
        replacements: Placeholder replacements (e.g., {"project_name": "my-app"})

    Returns:
        Number of files copied

    Raises:
        TemplateNotFoundError: If template not found
        FileOperationError: If installation fails
    """
    template_dir = get_template_directory(template_id)
    base_dir = template_dir / "base"

    if not base_dir.exists():
        raise TemplateNotFoundError(
            template_name=f"{template_id}/base", template_path=str(template_dir)
        )

    logger.info(f"Installing base template files from {template_id}...")

    # Copy base files
    files_copied = copy_directory_tree(
        base_dir, project_root, skip_patterns=[".template", "__pycache__", ".pyc"]
    )

    # Process template files (files ending in .template)
    for template_file in base_dir.rglob("*.template"):
        relative_path = template_file.relative_to(base_dir)
        # Remove .template extension for output file
        output_path = project_root / relative_path.parent / relative_path.stem

        try:
            content = template_file.read_text()
            processed_content = replace_placeholders(content, replacements)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(processed_content)
            logger.debug(f"Processed template: {template_file.name} -> {output_path.name}")
            files_copied += 1
        except Exception as e:
            raise FileOperationError(
                operation="process",
                file_path=str(template_file),
                details=f"Failed to process template file: {str(e)}",
                cause=e,
            )

    logger.info(f"Installed {files_copied} base files")
    return files_copied


def install_tier_files(
    template_id: str, tier: str, project_root: Path, replacements: dict[str, str]
) -> int:
    """
    Install tier-specific files.

    Args:
        template_id: Template identifier
        tier: Tier name (e.g., "tier-1-essential")
        project_root: Project root directory
        replacements: Placeholder replacements

    Returns:
        Number of files copied/processed

    Raises:
        TemplateNotFoundError: If tier directory not found
        FileOperationError: If installation fails
    """
    template_dir = get_template_directory(template_id)
    tier_dir = template_dir / tier

    if not tier_dir.exists():
        logger.warning(f"Tier directory not found: {tier_dir}")
        return 0

    logger.info(f"Installing {tier} files...")

    # Copy tier files
    files_copied = copy_directory_tree(
        tier_dir, project_root, skip_patterns=[".template", "__pycache__", ".pyc"]
    )

    # Process template files
    for template_file in tier_dir.rglob("*.template"):
        relative_path = template_file.relative_to(tier_dir)

        # Strip tier suffix from filename if present (e.g., package.json.tier4.template -> package.json)
        # This allows tier files to overwrite the base file instead of creating separate tier files
        filename_without_template = relative_path.stem  # Removes .template

        # Remove tier suffixes: .tier1, .tier2, .tier3, .tier4
        filename_without_tier = re.sub(r"\.tier[1-4]$", "", filename_without_template)

        output_path = project_root / relative_path.parent / filename_without_tier

        try:
            content = template_file.read_text()
            processed_content = replace_placeholders(content, replacements)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(processed_content)
            logger.debug(f"Processed template: {template_file.name} -> {output_path.name}")
            files_copied += 1
        except Exception as e:
            raise FileOperationError(
                operation="process",
                file_path=str(template_file),
                details=f"Failed to process template file: {str(e)}",
                cause=e,
            )

    logger.info(f"Installed {files_copied} files from {tier}")
    return files_copied


def install_additional_option(
    template_id: str, option: str, project_root: Path, replacements: dict[str, str]
) -> int:
    """
    Install additional option files (CI/CD, Docker, etc.).

    Args:
        template_id: Template identifier
        option: Option name (e.g., "ci-cd", "docker")
        project_root: Project root directory
        replacements: Placeholder replacements

    Returns:
        Number of files copied

    Raises:
        FileOperationError: If installation fails
    """
    template_dir = get_template_directory(template_id)
    option_dir = template_dir / option

    if not option_dir.exists():
        logger.warning(f"Option directory not found: {option_dir}")
        return 0

    logger.info(f"Installing {option} files...")

    # Copy option files
    files_copied = copy_directory_tree(
        option_dir, project_root, skip_patterns=[".template", "__pycache__", ".pyc"]
    )

    # Process template files
    for template_file in option_dir.rglob("*.template"):
        relative_path = template_file.relative_to(option_dir)
        output_path = project_root / relative_path.parent / relative_path.stem

        try:
            content = template_file.read_text()
            processed_content = replace_placeholders(content, replacements)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(processed_content)
            logger.debug(f"Processed template: {template_file.name} -> {output_path.name}")
            files_copied += 1
        except Exception as e:
            raise FileOperationError(
                operation="process",
                file_path=str(template_file),
                details=f"Failed to process template file: {str(e)}",
                cause=e,
            )

    logger.info(f"Installed {files_copied} files from {option}")
    return files_copied


def install_template(
    template_id: str,
    tier: str,
    additional_options: list[str],
    project_root: Path | None = None,
    coverage_target: int | None = None,
) -> dict[str, Any]:
    """
    Install complete template with base + tier + options.

    Args:
        template_id: Template identifier (e.g., "saas_t3")
        tier: Quality tier (e.g., "tier-2-standard")
        additional_options: List of option names (e.g., ["ci-cd", "docker"])
        project_root: Project root directory (defaults to current directory)
        coverage_target: Test coverage target percentage (e.g., 60, 80, 90)

    Returns:
        Installation summary dictionary with file counts and paths

    Raises:
        TemplateNotFoundError: If template not found
        FileOperationError: If installation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get template info
    template_info = get_template_info(template_id)

    # Prepare placeholder replacements
    project_name = project_root.name
    replacements = {
        "project_name": project_name,
        "project_description": f"A {template_info['display_name']} project",
        "template_id": template_id,
        "template_name": template_info["display_name"],
        "coverage_target": str(coverage_target) if coverage_target is not None else "80",
    }

    total_files = 0

    # Install base template
    total_files += install_base_template(template_id, project_root, replacements)

    # Install tier files (cumulative - install all tiers up to selected)
    tier_order = [
        "tier-1-essential",
        "tier-2-standard",
        "tier-3-comprehensive",
        "tier-4-production",
    ]
    selected_tier_index = tier_order.index(tier)

    for i in range(selected_tier_index + 1):
        tier_to_install = tier_order[i]
        total_files += install_tier_files(template_id, tier_to_install, project_root, replacements)

    # Install additional options
    for option in additional_options:
        # Map option keys to directory names
        option_dir_map = {
            "ci_cd": "ci-cd",
            "docker": "docker",
            "env_templates": "env-templates",
        }
        option_dir = option_dir_map.get(option, option)
        total_files += install_additional_option(
            template_id, option_dir, project_root, replacements
        )

    logger.info(f"Template installation complete: {total_files} files installed")

    return {
        "template_id": template_id,
        "template_name": template_info["display_name"],
        "tier": tier,
        "additional_options": additional_options,
        "files_installed": total_files,
        "project_root": str(project_root),
    }
