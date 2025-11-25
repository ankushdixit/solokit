"""
Git Setup Module

Handles git initialization and pre-flight validation checks for template-based init.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import GIT_QUICK_TIMEOUT
from solokit.core.exceptions import ErrorCode, GitError, ValidationError

logger = logging.getLogger(__name__)


def is_blank_project(project_root: Path | None = None) -> tuple[bool, list[str]]:
    """
    Check if the current directory is blank enough for initialization.

    A blank project can have:
    - .git directory
    - .gitignore, README.md, LICENSE, .gitattributes
    - docs/ directory
    - Empty directories with .gitkeep

    Args:
        project_root: Root directory to check. Defaults to current working directory.

    Returns:
        Tuple of (is_blank: bool, blocking_files: list[str])
        - is_blank: True if project is blank/safe to initialize
        - blocking_files: List of files/directories that block initialization
    """
    if project_root is None:
        project_root = Path.cwd()

    blocking_files: list[str] = []

    # Check for existing project files that indicate non-blank project
    blocking_file_patterns = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
        "tsconfig.json",
        ".eslintrc.js",
        ".eslintrc.json",
        ".prettierrc",
        "jest.config.js",
        "vitest.config.ts",
        ".session",
    ]

    # Check for blocking files
    for file_pattern in blocking_file_patterns:
        file_path = project_root / file_pattern
        if file_path.exists():
            # Add description for better error messages
            if file_pattern == "package.json":
                blocking_files.append("package.json (Node.js project detected)")
            elif file_pattern == "pyproject.toml":
                blocking_files.append("pyproject.toml (Python project detected)")
            elif file_pattern == ".session":
                blocking_files.append(".session/ (Solokit already initialized)")
            else:
                blocking_files.append(file_pattern)

    # Check for source directories (strong signal of existing project)
    blocking_dir_patterns = [
        "src",
        "app",
        "pages",
        "components",
        "lib",
        "utils",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
    ]

    for dir_pattern in blocking_dir_patterns:
        dir_path = project_root / dir_pattern
        if dir_path.exists() and dir_path.is_dir():
            # Check if directory has actual content (not just .gitkeep)
            try:
                contents = list(dir_path.iterdir())
                if contents and not (len(contents) == 1 and contents[0].name == ".gitkeep"):
                    blocking_files.append(f"{dir_pattern}/ directory")
            except PermissionError:
                # Can't read directory - treat as blocking
                blocking_files.append(f"{dir_pattern}/ directory (permission denied)")

    is_blank = len(blocking_files) == 0
    return is_blank, blocking_files


def check_blank_project_or_exit(project_root: Path | None = None) -> None:
    """
    Check if project is blank, raise exception with helpful error message if not.

    Args:
        project_root: Root directory to check. Defaults to current working directory.

    Raises:
        ValidationError: If project is not blank with helpful error message and remediation steps.
    """
    is_blank, blocking_files = is_blank_project(project_root)

    if not is_blank:
        error_msg = (
            "Cannot initialize: Project directory is not blank.\n\n"
            "Found existing project files:\n"
            + "\n".join(f"  - {f}" for f in blocking_files)
            + "\n\n"
            "Solutions:\n"
            "  1. Use 'sk adopt' to add Solokit to this existing project\n"
            "  2. Create a new directory: mkdir my-project && cd my-project\n"
            "  3. Clone an empty repo: git clone <repo-url> && cd <repo>\n"
        )

        raise ValidationError(
            message=error_msg,
            code=ErrorCode.PROJECT_NOT_BLANK,
            context={"existing_files": blocking_files},
            remediation="Use 'sk adopt' for existing projects, or use a blank directory for 'sk init'",
        )


def check_or_init_git(project_root: Path | None = None) -> bool:
    """
    Check if git is initialized, if not initialize it.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        True if git repository exists or was successfully initialized.

    Raises:
        GitError: If git initialization or branch configuration fails.

    Note:
        This function logs success messages but raises exceptions on errors.
    """
    if project_root is None:
        project_root = Path.cwd()

    git_dir = project_root / ".git"

    if git_dir.exists():
        logger.info("Git repository already initialized")
        return True

    runner = CommandRunner(default_timeout=GIT_QUICK_TIMEOUT, working_dir=project_root)

    # Initialize git
    result = runner.run(["git", "init"], check=True)
    if not result.success:
        raise GitError(
            message="Failed to initialize git repository",
            code=ErrorCode.GIT_COMMAND_FAILED,
            context={"stderr": result.stderr, "command": "git init"},
            remediation="Ensure git is installed and you have write permissions in the directory",
        )
    logger.info("Initialized git repository")

    # Set default branch to main (modern convention)
    result = runner.run(["git", "branch", "-m", "main"], check=True)
    if not result.success:
        raise GitError(
            message="Failed to set default branch to 'main'",
            code=ErrorCode.GIT_COMMAND_FAILED,
            context={"stderr": result.stderr, "command": "git branch -m main"},
            remediation="Manually run 'git branch -m main' in the repository",
        )
    logger.info("Set default branch to 'main'")

    return True
