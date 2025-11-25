"""
Project Type Detector

Auto-detects project type, language, framework, and existing tooling
for existing projects being adopted into Solokit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ProjectLanguage(str, Enum):
    """Primary language of the project."""

    PYTHON = "python"
    NODEJS = "nodejs"
    TYPESCRIPT = "typescript"
    FULLSTACK = "fullstack"  # Both Python and Node.js
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid language values."""
        return [item.value for item in cls]


class ProjectFramework(str, Enum):
    """Detected framework of the project."""

    # Node.js / TypeScript frameworks
    NEXTJS = "nextjs"
    REACT = "react"
    VUE = "vue"
    NUXT = "nuxt"
    EXPRESS = "express"
    FASTIFY = "fastify"
    NESTJS = "nestjs"

    # Python frameworks
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    STARLETTE = "starlette"

    # None/Unknown
    NONE = "none"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid framework values."""
        return [item.value for item in cls]


class PackageManager(str, Enum):
    """Package manager used by the project."""

    # Node.js
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"

    # Python
    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    UV = "uv"

    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid package manager values."""
        return [item.value for item in cls]


@dataclass
class ExistingTooling:
    """Existing development tooling detected in the project."""

    linter: str | None = None  # eslint, ruff, pylint, flake8
    formatter: str | None = None  # prettier, black, ruff
    type_checker: str | None = None  # typescript, mypy, pyright
    test_framework: str | None = None  # jest, vitest, pytest, unittest
    test_directory: str | None = None  # tests/, __tests__/, spec/
    has_pre_commit: bool = False
    has_husky: bool = False
    has_ci: bool = False
    ci_provider: str | None = None  # github, gitlab, circleci


@dataclass
class ProjectInfo:
    """Complete project information from detection."""

    language: ProjectLanguage = ProjectLanguage.UNKNOWN
    framework: ProjectFramework = ProjectFramework.NONE
    has_typescript: bool = False
    package_manager: PackageManager = PackageManager.UNKNOWN
    package_manager_node: PackageManager | None = None  # For fullstack projects
    package_manager_python: PackageManager | None = None  # For fullstack projects
    tooling: ExistingTooling = field(default_factory=ExistingTooling)
    confidence: float = 0.0
    detection_notes: list[str] = field(default_factory=list)

    # File existence flags for doc appender
    has_readme: bool = False
    has_claude_md: bool = False
    has_architecture_md: bool = False


def detect_project_type(project_root: Path | None = None) -> ProjectInfo:
    """
    Detect project type by analyzing manifest files, configs, and file extensions.

    Detection priority:
    1. Manifest files (highest confidence)
    2. Framework-specific config files
    3. File extensions (fallback)

    Args:
        project_root: Root directory to analyze. Defaults to current directory.

    Returns:
        ProjectInfo with detected language, framework, and tooling.
    """
    if project_root is None:
        project_root = Path.cwd()

    info = ProjectInfo()

    # Step 1: Detect from manifest files
    _detect_from_manifests(project_root, info)

    # Step 2: Detect framework
    _detect_framework(project_root, info)

    # Step 3: Detect package manager
    _detect_package_manager(project_root, info)

    # Step 4: Detect existing tooling
    _detect_existing_tooling(project_root, info)

    # Step 5: Check documentation files
    _detect_documentation(project_root, info)

    # Step 6: Fallback to file extension counting if still unknown
    if info.language == ProjectLanguage.UNKNOWN:
        _detect_from_extensions(project_root, info)

    # Calculate confidence
    _calculate_confidence(info)

    logger.info(f"Detected project: {info.language.value}")
    if info.framework != ProjectFramework.NONE:
        logger.info(f"Framework: {info.framework.value}")
    logger.info(f"Confidence: {info.confidence:.0%}")

    return info


def _detect_from_manifests(project_root: Path, info: ProjectInfo) -> None:
    """Detect language from manifest files (highest confidence)."""
    has_node = False
    has_python = False

    # Node.js detection
    package_json = project_root / "package.json"
    if package_json.exists():
        has_node = True
        info.detection_notes.append("Found package.json")

        # Check for TypeScript
        try:
            with open(package_json) as f:
                pkg_data = json.load(f)
                deps = pkg_data.get("dependencies", {})
                dev_deps = pkg_data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}

                if "typescript" in all_deps:
                    info.has_typescript = True
                    info.detection_notes.append("TypeScript detected in dependencies")
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Could not parse package.json: {e}")

    # TypeScript config also indicates TypeScript
    if (project_root / "tsconfig.json").exists():
        has_node = True
        info.has_typescript = True
        info.detection_notes.append("Found tsconfig.json")

    # Python detection
    python_manifests = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
    ]

    for manifest in python_manifests:
        if (project_root / manifest).exists():
            has_python = True
            info.detection_notes.append(f"Found {manifest}")
            break

    # Determine language
    if has_node and has_python:
        info.language = ProjectLanguage.FULLSTACK
    elif has_node:
        info.language = (
            ProjectLanguage.TYPESCRIPT if info.has_typescript else ProjectLanguage.NODEJS
        )
    elif has_python:
        info.language = ProjectLanguage.PYTHON


def _detect_framework(project_root: Path, info: ProjectInfo) -> None:
    """Detect specific framework from config files and dependencies."""
    # Node.js / TypeScript frameworks
    if info.language in (
        ProjectLanguage.NODEJS,
        ProjectLanguage.TYPESCRIPT,
        ProjectLanguage.FULLSTACK,
    ):
        _detect_node_framework(project_root, info)

    # Python frameworks
    if info.language in (ProjectLanguage.PYTHON, ProjectLanguage.FULLSTACK):
        _detect_python_framework(project_root, info)


def _detect_node_framework(project_root: Path, info: ProjectInfo) -> None:
    """Detect Node.js/TypeScript framework."""
    # Next.js
    if (project_root / "next.config.js").exists() or (project_root / "next.config.ts").exists():
        info.framework = ProjectFramework.NEXTJS
        info.detection_notes.append("Next.js detected (next.config)")
        return

    if (project_root / "next.config.mjs").exists():
        info.framework = ProjectFramework.NEXTJS
        info.detection_notes.append("Next.js detected (next.config.mjs)")
        return

    # Nuxt.js
    if (project_root / "nuxt.config.js").exists() or (project_root / "nuxt.config.ts").exists():
        info.framework = ProjectFramework.NUXT
        info.detection_notes.append("Nuxt.js detected (nuxt.config)")
        return

    # Check package.json for framework dependencies
    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                pkg_data = json.load(f)
                deps = pkg_data.get("dependencies", {})

                # Next.js (from deps)
                if "next" in deps:
                    info.framework = ProjectFramework.NEXTJS
                    info.detection_notes.append("Next.js detected (dependency)")
                    return

                # NestJS
                if "@nestjs/core" in deps:
                    info.framework = ProjectFramework.NESTJS
                    info.detection_notes.append("NestJS detected")
                    return

                # Vue
                if "vue" in deps:
                    info.framework = ProjectFramework.VUE
                    info.detection_notes.append("Vue.js detected")
                    return

                # Express
                if "express" in deps:
                    info.framework = ProjectFramework.EXPRESS
                    info.detection_notes.append("Express.js detected")
                    return

                # Fastify
                if "fastify" in deps:
                    info.framework = ProjectFramework.FASTIFY
                    info.detection_notes.append("Fastify detected")
                    return

                # React (standalone, not Next.js)
                if "react" in deps and info.framework == ProjectFramework.NONE:
                    info.framework = ProjectFramework.REACT
                    info.detection_notes.append("React detected")
                    return

        except (json.JSONDecodeError, OSError):
            pass


def _detect_python_framework(project_root: Path, info: ProjectInfo) -> None:
    """Detect Python framework."""
    # Django - look for manage.py and settings
    if (project_root / "manage.py").exists():
        info.framework = ProjectFramework.DJANGO
        info.detection_notes.append("Django detected (manage.py)")
        return

    # Check pyproject.toml for dependencies
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()

            if "fastapi" in content.lower():
                info.framework = ProjectFramework.FASTAPI
                info.detection_notes.append("FastAPI detected (pyproject.toml)")
                return

            if "flask" in content.lower():
                info.framework = ProjectFramework.FLASK
                info.detection_notes.append("Flask detected (pyproject.toml)")
                return

            if "django" in content.lower():
                info.framework = ProjectFramework.DJANGO
                info.detection_notes.append("Django detected (pyproject.toml)")
                return

            if "starlette" in content.lower():
                info.framework = ProjectFramework.STARLETTE
                info.detection_notes.append("Starlette detected (pyproject.toml)")
                return

        except OSError:
            pass

    # Check requirements.txt
    requirements = project_root / "requirements.txt"
    if requirements.exists():
        try:
            content = requirements.read_text().lower()

            if "fastapi" in content:
                info.framework = ProjectFramework.FASTAPI
                info.detection_notes.append("FastAPI detected (requirements.txt)")
                return

            if "flask" in content:
                info.framework = ProjectFramework.FLASK
                info.detection_notes.append("Flask detected (requirements.txt)")
                return

            if "django" in content:
                info.framework = ProjectFramework.DJANGO
                info.detection_notes.append("Django detected (requirements.txt)")
                return

        except OSError:
            pass


def _detect_package_manager(project_root: Path, info: ProjectInfo) -> None:
    """Detect package manager from lock files."""
    # Node.js package managers
    if info.language in (
        ProjectLanguage.NODEJS,
        ProjectLanguage.TYPESCRIPT,
        ProjectLanguage.FULLSTACK,
    ):
        if (project_root / "pnpm-lock.yaml").exists():
            pm = PackageManager.PNPM
            info.detection_notes.append("pnpm detected (pnpm-lock.yaml)")
        elif (project_root / "yarn.lock").exists():
            pm = PackageManager.YARN
            info.detection_notes.append("yarn detected (yarn.lock)")
        elif (project_root / "package-lock.json").exists():
            pm = PackageManager.NPM
            info.detection_notes.append("npm detected (package-lock.json)")
        elif (project_root / "package.json").exists():
            pm = PackageManager.NPM  # Default to npm if package.json exists
            info.detection_notes.append("npm assumed (package.json exists)")
        else:
            pm = PackageManager.UNKNOWN

        if info.language == ProjectLanguage.FULLSTACK:
            info.package_manager_node = pm
        else:
            info.package_manager = pm

    # Python package managers
    if info.language in (ProjectLanguage.PYTHON, ProjectLanguage.FULLSTACK):
        if (project_root / "uv.lock").exists():
            pm = PackageManager.UV
            info.detection_notes.append("uv detected (uv.lock)")
        elif (project_root / "poetry.lock").exists():
            pm = PackageManager.POETRY
            info.detection_notes.append("poetry detected (poetry.lock)")
        elif (project_root / "Pipfile.lock").exists():
            pm = PackageManager.PIPENV
            info.detection_notes.append("pipenv detected (Pipfile.lock)")
        elif (project_root / "Pipfile").exists():
            pm = PackageManager.PIPENV
            info.detection_notes.append("pipenv detected (Pipfile)")
        elif (project_root / "requirements.txt").exists():
            pm = PackageManager.PIP
            info.detection_notes.append("pip detected (requirements.txt)")
        elif (project_root / "pyproject.toml").exists():
            # Could be poetry, pip, or uv - check content
            pm = _detect_python_pm_from_pyproject(project_root)
            info.detection_notes.append(f"{pm.value} detected (pyproject.toml)")
        else:
            pm = PackageManager.UNKNOWN

        if info.language == ProjectLanguage.FULLSTACK:
            info.package_manager_python = pm
        else:
            info.package_manager = pm


def _detect_python_pm_from_pyproject(project_root: Path) -> PackageManager:
    """Detect Python package manager from pyproject.toml content."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return PackageManager.UNKNOWN

    try:
        content = pyproject.read_text()

        # Check for poetry markers
        if "[tool.poetry]" in content:
            return PackageManager.POETRY

        # Check for uv markers
        if "[tool.uv]" in content:
            return PackageManager.UV

        # Default to pip for standard pyproject.toml
        return PackageManager.PIP

    except OSError:
        return PackageManager.UNKNOWN


def _detect_existing_tooling(project_root: Path, info: ProjectInfo) -> None:
    """Detect existing linters, formatters, and other tooling."""
    tooling = ExistingTooling()

    # Linters
    eslint_configs = [
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        "eslint.config.js",
        "eslint.config.mjs",
    ]
    for config in eslint_configs:
        if (project_root / config).exists():
            tooling.linter = "eslint"
            info.detection_notes.append(f"ESLint detected ({config})")
            break

    # Check for ruff in pyproject.toml
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.ruff]" in content:
                tooling.linter = "ruff" if tooling.linter is None else tooling.linter
                info.detection_notes.append("Ruff detected (pyproject.toml)")
        except OSError:
            pass

    if (project_root / "ruff.toml").exists():
        tooling.linter = "ruff" if tooling.linter is None else tooling.linter
        info.detection_notes.append("Ruff detected (ruff.toml)")

    # Formatters
    prettier_configs = [".prettierrc", ".prettierrc.js", ".prettierrc.json", "prettier.config.js"]
    for config in prettier_configs:
        if (project_root / config).exists():
            tooling.formatter = "prettier"
            info.detection_notes.append(f"Prettier detected ({config})")
            break

    # Black formatter (Python)
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.black]" in content:
                tooling.formatter = "black" if tooling.formatter is None else tooling.formatter
                info.detection_notes.append("Black detected (pyproject.toml)")
        except OSError:
            pass

    # Type checkers
    if (project_root / "tsconfig.json").exists():
        tooling.type_checker = "typescript"

    if pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.mypy]" in content:
                tooling.type_checker = (
                    "mypy" if tooling.type_checker is None else tooling.type_checker
                )
                info.detection_notes.append("Mypy detected (pyproject.toml)")
        except OSError:
            pass

    if (project_root / "mypy.ini").exists():
        tooling.type_checker = "mypy" if tooling.type_checker is None else tooling.type_checker
        info.detection_notes.append("Mypy detected (mypy.ini)")

    # Test frameworks
    test_dirs = ["tests", "__tests__", "test", "spec"]
    for test_dir in test_dirs:
        if (project_root / test_dir).exists():
            tooling.test_directory = test_dir
            info.detection_notes.append(f"Test directory detected: {test_dir}/")
            break

    # Detect specific test framework
    if (project_root / "jest.config.js").exists() or (project_root / "jest.config.ts").exists():
        tooling.test_framework = "jest"
        info.detection_notes.append("Jest detected")
    elif (project_root / "vitest.config.ts").exists() or (
        project_root / "vitest.config.js"
    ).exists():
        tooling.test_framework = "vitest"
        info.detection_notes.append("Vitest detected")
    elif pyproject.exists():
        try:
            content = pyproject.read_text()
            if "[tool.pytest" in content:
                tooling.test_framework = "pytest"
                info.detection_notes.append("Pytest detected (pyproject.toml)")
        except OSError:
            pass

    if (project_root / "pytest.ini").exists():
        tooling.test_framework = "pytest"
        info.detection_notes.append("Pytest detected (pytest.ini)")

    if (project_root / "conftest.py").exists():
        tooling.test_framework = (
            "pytest" if tooling.test_framework is None else tooling.test_framework
        )
        info.detection_notes.append("Pytest detected (conftest.py)")

    # Git hooks
    if (project_root / ".pre-commit-config.yaml").exists():
        tooling.has_pre_commit = True
        info.detection_notes.append("pre-commit detected")

    if (project_root / ".husky").exists():
        tooling.has_husky = True
        info.detection_notes.append("Husky detected")

    # CI/CD
    if (project_root / ".github" / "workflows").exists():
        tooling.has_ci = True
        tooling.ci_provider = "github"
        info.detection_notes.append("GitHub Actions detected")
    elif (project_root / ".gitlab-ci.yml").exists():
        tooling.has_ci = True
        tooling.ci_provider = "gitlab"
        info.detection_notes.append("GitLab CI detected")
    elif (project_root / ".circleci").exists():
        tooling.has_ci = True
        tooling.ci_provider = "circleci"
        info.detection_notes.append("CircleCI detected")

    info.tooling = tooling


def _detect_documentation(project_root: Path, info: ProjectInfo) -> None:
    """Detect existing documentation files."""
    # Check for README (case-insensitive)
    readme_patterns = ["README.md", "readme.md", "Readme.md", "README.MD"]
    for pattern in readme_patterns:
        if (project_root / pattern).exists():
            info.has_readme = True
            break

    info.has_claude_md = (project_root / "CLAUDE.md").exists()
    info.has_architecture_md = (project_root / "ARCHITECTURE.md").exists()


def _detect_from_extensions(project_root: Path, info: ProjectInfo) -> None:
    """Fallback detection based on file extension counts."""
    extension_counts: dict[str, int] = {}

    # Count files by extension (limit depth to avoid huge repos)
    try:
        for path in project_root.rglob("*"):
            # Skip hidden dirs, node_modules, venv, etc.
            parts = path.parts
            if any(
                p.startswith(".")
                or p in ("node_modules", "venv", ".venv", "__pycache__", "dist", "build")
                for p in parts
            ):
                continue

            if path.is_file():
                ext = path.suffix.lower()
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1

    except (PermissionError, OSError) as e:
        logger.debug(f"Error scanning files: {e}")
        return

    # Analyze counts
    python_exts = extension_counts.get(".py", 0)
    js_exts = extension_counts.get(".js", 0) + extension_counts.get(".jsx", 0)
    ts_exts = extension_counts.get(".ts", 0) + extension_counts.get(".tsx", 0)
    node_total = js_exts + ts_exts

    if python_exts > 0 and node_total > 0:
        info.language = ProjectLanguage.FULLSTACK
        info.detection_notes.append(
            f"Fullstack detected from extensions (py: {python_exts}, js/ts: {node_total})"
        )
    elif python_exts > node_total:
        info.language = ProjectLanguage.PYTHON
        info.detection_notes.append(f"Python detected from extensions ({python_exts} .py files)")
    elif ts_exts > js_exts:
        info.language = ProjectLanguage.TYPESCRIPT
        info.has_typescript = True
        info.detection_notes.append(
            f"TypeScript detected from extensions ({ts_exts} .ts/.tsx files)"
        )
    elif node_total > 0:
        info.language = ProjectLanguage.NODEJS
        info.detection_notes.append(
            f"Node.js detected from extensions ({node_total} .js/.jsx files)"
        )


def _calculate_confidence(info: ProjectInfo) -> None:
    """Calculate confidence score based on detection signals."""
    score = 0.0

    # Language detection confidence
    if info.language != ProjectLanguage.UNKNOWN:
        score += 0.3

    # Framework detection adds confidence
    if info.framework != ProjectFramework.NONE:
        score += 0.2

    # Package manager detection
    if info.package_manager != PackageManager.UNKNOWN:
        score += 0.15

    # Existing tooling detection
    if info.tooling.linter:
        score += 0.1
    if info.tooling.test_framework:
        score += 0.1
    if info.tooling.formatter:
        score += 0.05

    # Multiple detection notes indicate stronger signals
    notes_count = len(info.detection_notes)
    if notes_count >= 5:
        score += 0.1

    info.confidence = min(score, 1.0)


def get_project_summary(info: ProjectInfo) -> str:
    """
    Generate a human-readable summary of detected project info.

    Args:
        info: ProjectInfo from detection.

    Returns:
        Formatted string summary.
    """
    lines = []

    lines.append(f"Language: {info.language.value}")

    if info.has_typescript:
        lines.append("TypeScript: Yes")

    if info.framework != ProjectFramework.NONE:
        lines.append(f"Framework: {info.framework.value}")

    if info.package_manager != PackageManager.UNKNOWN:
        lines.append(f"Package Manager: {info.package_manager.value}")
    elif info.package_manager_node or info.package_manager_python:
        if info.package_manager_node:
            lines.append(f"Node Package Manager: {info.package_manager_node.value}")
        if info.package_manager_python:
            lines.append(f"Python Package Manager: {info.package_manager_python.value}")

    if info.tooling.linter:
        lines.append(f"Linter: {info.tooling.linter}")
    if info.tooling.formatter:
        lines.append(f"Formatter: {info.tooling.formatter}")
    if info.tooling.test_framework:
        lines.append(f"Test Framework: {info.tooling.test_framework}")
    if info.tooling.has_ci:
        lines.append(f"CI/CD: {info.tooling.ci_provider}")

    lines.append(f"Confidence: {info.confidence:.0%}")

    return "\n".join(lines)
