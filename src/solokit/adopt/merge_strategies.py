"""
Smart Merge Strategies for Config Files.

Implements intelligent merging for different file types during sk adopt.
Each strategy preserves existing project configuration while adding
Solokit-specific additions.
"""

from __future__ import annotations

import json
import logging
import re
import tomllib
from collections.abc import Callable
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# PACKAGE.JSON MERGE
# =============================================================================


def merge_package_json(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit additions into existing package.json.

    Strategy:
    - KEEP: name, version, description, author, license, repository, main, etc.
    - KEEP: dependencies (all existing versions preserved)
    - MERGE: devDependencies (add missing from Solokit, keep existing versions)
    - MERGE: scripts (add missing from Solokit, don't overwrite existing)
    - KEEP: All other fields (workspaces, engines, etc.)

    Args:
        existing_path: Path to existing package.json
        solokit_content: Content from Solokit template

    Returns:
        Merged JSON string with 2-space indentation
    """
    existing = json.loads(existing_path.read_text())
    solokit = json.loads(solokit_content)

    # Merge devDependencies (add missing only)
    if "devDependencies" in solokit:
        if "devDependencies" not in existing:
            existing["devDependencies"] = {}
        for dep, version in solokit["devDependencies"].items():
            if dep not in existing["devDependencies"]:
                existing["devDependencies"][dep] = version
                logger.debug(f"Added devDependency: {dep}@{version}")

    # Merge scripts (add missing only)
    if "scripts" in solokit:
        if "scripts" not in existing:
            existing["scripts"] = {}
        for script, command in solokit["scripts"].items():
            if script not in existing["scripts"]:
                existing["scripts"][script] = command
                logger.debug(f"Added script: {script}")

    return json.dumps(existing, indent=2) + "\n"


# =============================================================================
# PYPROJECT.TOML MERGE
# =============================================================================


def merge_pyproject_toml(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit additions into existing pyproject.toml.

    Strategy:
    - KEEP: [project] section (name, version, description, etc.)
    - KEEP: [build-system] section
    - KEEP: dependencies
    - MERGE: [project.optional-dependencies.dev] (add missing)
    - MERGE: [tool.*] sections (add missing tool configs)

    Args:
        existing_path: Path to existing pyproject.toml
        solokit_content: Content from Solokit template

    Returns:
        Merged TOML string

    Note:
        Uses tomllib for reading (Python 3.11+) and manual string building
        for writing to preserve formatting and comments where possible.
    """
    try:
        import tomli_w
    except ImportError:
        logger.warning(
            "tomli_w not available, skipping pyproject.toml merge. "
            "Install with: pip install tomli-w"
        )
        return existing_path.read_text()

    existing = tomllib.loads(existing_path.read_text())
    solokit = tomllib.loads(solokit_content)

    # Merge optional-dependencies.dev
    if "project" in solokit and "optional-dependencies" in solokit.get("project", {}):
        if "project" not in existing:
            existing["project"] = {}
        if "optional-dependencies" not in existing["project"]:
            existing["project"]["optional-dependencies"] = {}
        if "dev" not in existing["project"]["optional-dependencies"]:
            existing["project"]["optional-dependencies"]["dev"] = []

        existing_dev = set(existing["project"]["optional-dependencies"]["dev"])
        for dep in solokit["project"]["optional-dependencies"].get("dev", []):
            # Extract package name (before any version specifier)
            pkg_name = re.split(r"[<>=!~\[]", dep)[0].strip()
            # Check if package name is already in existing dependencies
            if not any(
                pkg_name.lower() == re.split(r"[<>=!~\[]", d)[0].strip().lower()
                for d in existing_dev
            ):
                existing["project"]["optional-dependencies"]["dev"].append(dep)
                logger.debug(f"Added dev dependency: {dep}")

    # Merge tool.* sections (add missing tool configs entirely)
    if "tool" in solokit:
        if "tool" not in existing:
            existing["tool"] = {}
        for tool_name, tool_config in solokit["tool"].items():
            if tool_name not in existing["tool"]:
                existing["tool"][tool_name] = tool_config
                logger.debug(f"Added tool config: [tool.{tool_name}]")

    return tomli_w.dumps(existing)


# =============================================================================
# ESLINT.CONFIG.MJS MERGE
# =============================================================================


def merge_eslint_config(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit ESLint rules into existing config.

    Strategy:
    - Append Solokit rules as a clearly marked section
    - Since ESLint flat config is JavaScript, we use text-based merging

    This is a conservative append strategy since proper AST manipulation
    would be complex and error-prone.

    Args:
        existing_path: Path to existing eslint.config.mjs
        solokit_content: Content from Solokit template

    Returns:
        Merged ESLint config string
    """
    existing = existing_path.read_text()

    # Check if Solokit config already added
    if "// Solokit quality rules" in existing or "// Added by Solokit" in existing:
        logger.info("ESLint config already contains Solokit rules, skipping")
        return existing

    # Extract rules from Solokit template
    rules_match = re.search(r"rules:\s*\{([^}]+)\}", solokit_content, re.DOTALL)
    if not rules_match:
        logger.warning("Could not extract rules from Solokit ESLint template")
        return existing

    rules_content = rules_match.group(1).strip()

    # Create Solokit config object to append
    solokit_config = f"""
// Solokit quality rules - added by sk adopt
const solokitRules = {{
  rules: {{
{_indent_lines(rules_content, 4)}
  }},
}};
"""

    # Try to integrate into the export
    if "export default [" in existing:
        # Array export format - try to append to array
        last_bracket = existing.rfind("];")
        if last_bracket != -1:
            # Insert the config object definition before export
            export_pos = existing.find("export default")
            if export_pos != -1:
                before_export = existing[:export_pos]
                after_export = existing[export_pos:]

                # Add to the array
                insert_pos = after_export.rfind("];")
                if insert_pos != -1:
                    modified_export = (
                        after_export[:insert_pos] + "  solokitRules,\n" + after_export[insert_pos:]
                    )
                    return before_export + solokit_config + modified_export

    elif "export default" in existing and "tseslint.config(" in existing:
        # TypeScript ESLint config format
        # Add before the closing parenthesis
        last_paren = existing.rfind(");")
        if last_paren != -1:
            export_pos = existing.find("export default")
            if export_pos != -1:
                before_export = existing[:export_pos]
                after_export = existing[export_pos:]
                insert_pos = after_export.rfind(");")
                if insert_pos != -1:
                    modified_export = (
                        after_export[:insert_pos] + "  solokitRules,\n" + after_export[insert_pos:]
                    )
                    return before_export + solokit_config + modified_export

    # Fallback: append as comment with instructions
    return (
        existing
        + f"""

// =============================================================================
// Solokit Quality Rules - Added by sk adopt
// =============================================================================
// Add the following rules to your ESLint configuration manually:
//
// {{
//   rules: {{
{_indent_lines(_comment_lines(rules_content), 0)}
//   }},
// }}
"""
    )


def _indent_lines(text: str, spaces: int) -> str:
    """Indent each line of text by specified spaces."""
    indent = " " * spaces
    return "\n".join(indent + line if line.strip() else line for line in text.split("\n"))


def _comment_lines(text: str) -> str:
    """Add // comment prefix to each line."""
    return "\n".join("// " + line if line.strip() else "//" for line in text.split("\n"))


# =============================================================================
# PRETTIERRC MERGE
# =============================================================================


def merge_prettierrc(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit Prettier options into existing config.

    Strategy:
    - Keep all existing options (user preferences take precedence)
    - Add missing options from Solokit defaults

    Args:
        existing_path: Path to existing .prettierrc
        solokit_content: Content from Solokit template

    Returns:
        Merged JSON string
    """
    try:
        existing = json.loads(existing_path.read_text())
    except json.JSONDecodeError:
        # Might be YAML format, JS format, or invalid - skip merge
        logger.warning("Could not parse existing .prettierrc as JSON, skipping merge")
        return existing_path.read_text()

    try:
        solokit = json.loads(solokit_content)
    except json.JSONDecodeError:
        logger.warning("Could not parse Solokit .prettierrc template as JSON")
        return existing_path.read_text()

    # Add missing options from Solokit (don't override existing)
    for key, value in solokit.items():
        if key not in existing:
            existing[key] = value
            logger.debug(f"Added Prettier option: {key}={value}")

    return json.dumps(existing, indent=2) + "\n"


# =============================================================================
# PRE-COMMIT CONFIG MERGE
# =============================================================================


def merge_pre_commit_config(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit pre-commit hooks into existing config.

    Strategy:
    - Keep all existing repos and hooks
    - Add missing repos from Solokit (by repo URL)

    Args:
        existing_path: Path to existing .pre-commit-config.yaml
        solokit_content: Content from Solokit template

    Returns:
        Merged YAML string
    """
    existing = yaml.safe_load(existing_path.read_text())
    solokit = yaml.safe_load(solokit_content)

    if not existing:
        existing = {"repos": []}
    if "repos" not in existing:
        existing["repos"] = []

    # Get existing repo URLs for deduplication
    existing_repos = {
        repo.get("repo") for repo in existing["repos"] if isinstance(repo, dict) and "repo" in repo
    }

    # Add missing repos from Solokit
    solokit_repos = solokit.get("repos", []) if solokit else []
    for repo in solokit_repos:
        if isinstance(repo, dict) and repo.get("repo") not in existing_repos:
            existing["repos"].append(repo)
            logger.debug(f"Added pre-commit repo: {repo.get('repo')}")

    return yaml.dump(existing, default_flow_style=False, sort_keys=False)


# =============================================================================
# REQUIREMENTS.TXT MERGE
# =============================================================================


def merge_requirements_txt(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit requirements into existing file.

    Strategy:
    - Keep all existing requirements with their versions
    - Add missing packages from Solokit
    - Clearly mark Solokit additions with a comment

    Args:
        existing_path: Path to existing requirements.txt
        solokit_content: Content from Solokit template

    Returns:
        Merged requirements string
    """
    existing_text = existing_path.read_text()
    existing_lines = existing_text.strip().split("\n") if existing_text.strip() else []

    solokit_lines = solokit_content.strip().split("\n") if solokit_content.strip() else []

    # Extract package names from existing (normalize to lowercase)
    existing_packages: set[str] = set()
    for line in existing_lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            # Extract package name (before version specifiers or extras)
            pkg_name = re.split(r"[<>=!@\[;]", line)[0].strip()
            if pkg_name:
                existing_packages.add(pkg_name.lower())

    # Find packages to add from Solokit
    added: list[str] = []
    for line in solokit_lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("-"):
            pkg_name = re.split(r"[<>=!@\[;]", line)[0].strip()
            if pkg_name and pkg_name.lower() not in existing_packages:
                added.append(line)
                logger.debug(f"Added requirement: {line}")

    if added:
        result = existing_text.rstrip()
        if result and not result.endswith("\n"):
            result += "\n"
        result += "\n# Added by Solokit\n"
        result += "\n".join(added) + "\n"
        return result

    return existing_text


# =============================================================================
# HUSKY PRE-COMMIT MERGE
# =============================================================================


def merge_husky_pre_commit(existing_path: Path, solokit_content: str) -> str:
    """
    Merge Solokit commands into existing husky pre-commit hook.

    Strategy:
    - Keep all existing commands
    - Append Solokit commands that don't already exist
    - Clearly mark Solokit additions

    Args:
        existing_path: Path to existing .husky/pre-commit
        solokit_content: Content from Solokit template

    Returns:
        Merged shell script string
    """
    existing = existing_path.read_text()

    # Check if Solokit commands already added
    if "# Solokit quality checks" in existing or "# Added by Solokit" in existing:
        logger.info("Husky pre-commit already contains Solokit commands, skipping")
        return existing

    # Extract commands from Solokit template (skip shebang, comments, empty lines)
    solokit_commands: list[str] = []
    for line in solokit_content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("#!/"):
            solokit_commands.append(line)

    if not solokit_commands:
        return existing

    # Filter out commands that already exist
    new_commands: list[str] = []
    for cmd in solokit_commands:
        # Check if command (or similar) already exists
        # Normalize for comparison (handle slight variations)
        cmd_normalized = cmd.lower().replace(" ", "")
        if not any(
            cmd_normalized in existing_line.lower().replace(" ", "")
            for existing_line in existing.split("\n")
        ):
            new_commands.append(cmd)
            logger.debug(f"Added husky command: {cmd}")

    if not new_commands:
        logger.info("All Solokit husky commands already present")
        return existing

    # Append Solokit commands
    result = existing.rstrip() + "\n\n"
    result += "# Solokit quality checks - added by sk adopt\n"
    for cmd in new_commands:
        result += cmd + "\n"

    return result


# =============================================================================
# DISPATCHER
# =============================================================================

# Type alias for merge functions
MergeFunc = Callable[[Path, str], str]

# Mapping of filenames/paths to their merge functions
MERGE_FUNCTIONS: dict[str, MergeFunc] = {
    "package.json": merge_package_json,
    "pyproject.toml": merge_pyproject_toml,
    "eslint.config.mjs": merge_eslint_config,
    ".prettierrc": merge_prettierrc,
    ".pre-commit-config.yaml": merge_pre_commit_config,
    "requirements.txt": merge_requirements_txt,
    ".husky/pre-commit": merge_husky_pre_commit,
    # Handle with just filename for nested paths
    "pre-commit": merge_husky_pre_commit,
}


def merge_config_file(
    filename: str,
    existing_path: Path,
    solokit_content: str,
) -> str:
    """
    Dispatch to the appropriate merge strategy based on filename.

    Args:
        filename: Name of the config file (can be path like ".husky/pre-commit")
        existing_path: Path to existing file
        solokit_content: Content from Solokit template

    Returns:
        Merged content string
    """
    # Try exact match first
    merge_func = MERGE_FUNCTIONS.get(filename)

    # If not found, try just the basename
    if merge_func is None:
        basename = Path(filename).name
        merge_func = MERGE_FUNCTIONS.get(basename)

    if merge_func:
        try:
            return merge_func(existing_path, solokit_content)
        except Exception as e:
            logger.warning(f"Merge failed for {filename}: {e}. Returning existing content.")
            return existing_path.read_text()

    logger.warning(f"No merge strategy for {filename}, returning existing content")
    return existing_path.read_text()


def get_mergeable_files() -> set[str]:
    """
    Return the set of files that can be merged.

    Returns:
        Set of filenames/paths that have merge strategies
    """
    return set(MERGE_FUNCTIONS.keys())
