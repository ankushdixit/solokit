"""Centralized configuration management with caching and validation.

This module provides a singleton ConfigManager that loads, validates, and caches
configuration from .session/config.json. It replaces the duplicated configuration
loading logic scattered across multiple modules.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from solokit.core.exceptions import (
    ConfigurationError,
    ConfigValidationError,
    ErrorCode,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Test execution configuration."""

    enabled: bool = True
    required: bool = True
    coverage_threshold: int = 80
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "pytest --cov=src/solokit --cov-report=json",
            "javascript": "npm test -- --coverage",
            "typescript": "npm test -- --coverage",
        }
    )


@dataclass
class LintingConfig:
    """Linting configuration."""

    enabled: bool = True
    required: bool = False
    auto_fix: bool = True
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "ruff check .",
            "javascript": "npx eslint .",
            "typescript": "npx eslint .",
        }
    )


@dataclass
class FormattingConfig:
    """Formatting configuration."""

    enabled: bool = True
    required: bool = False
    auto_fix: bool = True
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "ruff format .",
            "javascript": "npx prettier .",
            "typescript": "npx prettier .",
        }
    )


@dataclass
class SecurityConfig:
    """Security scanning configuration."""

    enabled: bool = True
    required: bool = True
    fail_on: str = "high"  # critical, high, medium, low


@dataclass
class DocumentationConfig:
    """Documentation validation configuration."""

    enabled: bool = True
    required: bool = False
    check_changelog: bool = True
    check_docstrings: bool = True
    check_readme: bool = False


@dataclass
class SpecCompletenessConfig:
    """Spec completeness validation configuration."""

    enabled: bool = True
    required: bool = True


@dataclass
class Context7Config:
    """Context7 library verification configuration."""

    enabled: bool = False
    important_libraries: list[str] = field(default_factory=list)


@dataclass
class IntegrationConfig:
    """Integration test validation configuration."""

    enabled: bool = True
    documentation: dict[str, bool] = field(
        default_factory=lambda: {
            "enabled": True,
            "architecture_diagrams": True,
            "sequence_diagrams": True,
            "contract_documentation": True,
            "performance_baseline_docs": True,
        }
    )


@dataclass
class DeploymentConfig:
    """Deployment quality gates configuration."""

    enabled: bool = True
    integration_tests: dict[str, bool] = field(default_factory=lambda: {"enabled": True})
    security_scans: dict[str, bool] = field(default_factory=lambda: {"enabled": True})


@dataclass
class QualityGatesConfig:
    """Quality gates configuration."""

    test_execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    linting: LintingConfig = field(default_factory=LintingConfig)
    formatting: FormattingConfig = field(default_factory=FormattingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    documentation: DocumentationConfig = field(default_factory=DocumentationConfig)
    spec_completeness: SpecCompletenessConfig = field(default_factory=SpecCompletenessConfig)
    context7: Context7Config = field(default_factory=Context7Config)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)


@dataclass
class GitWorkflowConfig:
    """Git workflow configuration."""

    mode: str = "pr"
    auto_push: bool = True
    auto_create_pr: bool = True
    delete_branch_after_merge: bool = True
    pr_title_template: str = "{type}: {title}"
    pr_body_template: str = "## Work Item: {work_item_id}\n\n{description}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"


@dataclass
class CurationConfig:
    """Learning curation configuration."""

    auto_curate: bool = False
    frequency: int = 5
    dry_run: bool = False
    similarity_threshold: float = 0.7


@dataclass
class SolokitConfig:
    """Main Solokit configuration."""

    quality_gates: QualityGatesConfig = field(default_factory=QualityGatesConfig)
    git_workflow: GitWorkflowConfig = field(default_factory=GitWorkflowConfig)
    curation: CurationConfig = field(default_factory=CurationConfig)


class ConfigManager:
    """Centralized configuration management with caching and validation.

    This class implements the Singleton pattern to ensure a single source of truth
    for configuration across the entire application. It loads configuration from
    .session/config.json, validates it, and caches it for performance.

    Example:
        >>> config_mgr = get_config_manager()
        >>> config_mgr.load_config(Path(".session/config.json"))
        >>> quality_config = config_mgr.quality_gates
        >>> print(quality_config.test_execution.coverage_threshold)
        80
    """

    _instance: ConfigManager | None = None
    _config: SolokitConfig | None = None
    _config_path: Path | None = None

    def __new__(cls) -> ConfigManager:
        """Ensure only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize with default configuration if not already initialized."""
        if self._config is None:
            self._config = SolokitConfig()

    def load_config(self, config_path: Path, force_reload: bool = False) -> None:
        """Load configuration from file.

        Args:
            config_path: Path to config.json file
            force_reload: Force reload even if already cached

        Raises:
            ConfigurationError: If JSON is invalid or file cannot be read
            ConfigValidationError: If configuration structure is invalid

        Note:
            If the config file doesn't exist, default configuration is used.
        """
        # Skip if already loaded and not forcing reload
        if not force_reload and self._config_path == config_path:
            logger.debug("Config already loaded from %s, using cache", config_path)
            return

        self._config_path = config_path

        if not config_path.exists():
            logger.info("Config file not found at %s, using defaults", config_path)
            self._config = SolokitConfig()
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse config sections with defaults
            quality_gates_dict = data.get("quality_gates", {})

            # Handle integration_tests at top level (for backward compatibility)
            # Merge it into quality_gates if it exists
            if "integration_tests" in data:
                if "integration" not in quality_gates_dict:
                    quality_gates_dict["integration"] = data["integration_tests"]

            quality_gates_data = self._parse_quality_gates(quality_gates_dict)
            git_workflow_data = data.get("git_workflow", {})
            curation_data = data.get("curation", {})

            # Filter curation_data to only include valid CurationConfig fields
            # This maintains backward compatibility with old configs
            valid_curation_fields = {
                "auto_curate",
                "frequency",
                "dry_run",
                "similarity_threshold",
            }
            filtered_curation_data = (
                {k: v for k, v in curation_data.items() if k in valid_curation_fields}
                if curation_data
                else {}
            )

            # Create config with parsed data
            self._config = SolokitConfig(
                quality_gates=quality_gates_data,
                git_workflow=(
                    GitWorkflowConfig(**git_workflow_data)
                    if git_workflow_data
                    else GitWorkflowConfig()
                ),
                curation=(
                    CurationConfig(**filtered_curation_data)
                    if filtered_curation_data
                    else CurationConfig()
                ),
            )

            logger.info("Loaded configuration from %s", config_path)

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                message=f"Invalid JSON in configuration file: {config_path}",
                code=ErrorCode.INVALID_JSON,
                context={"config_path": str(config_path), "error": str(e)},
                remediation="Check the JSON syntax in your config file. Ensure all quotes, brackets, and commas are properly placed.",
                cause=e,
            )
        except TypeError as e:
            raise ConfigValidationError(
                config_path=str(config_path),
                errors=[f"Invalid configuration structure: {str(e)}"],
            )
        except PermissionError as e:
            raise ConfigurationError(
                message=f"Permission denied reading configuration file: {config_path}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={"config_path": str(config_path)},
                remediation="Check file permissions and ensure you have read access to the config file.",
                cause=e,
            )
        except OSError as e:
            raise ConfigurationError(
                message=f"Error reading configuration file: {config_path}",
                code=ErrorCode.FILE_OPERATION_FAILED,
                context={"config_path": str(config_path), "error": str(e)},
                remediation="Ensure the config file is not corrupted and the file system is accessible.",
                cause=e,
            )

    def _parse_quality_gates(self, data: dict) -> QualityGatesConfig:
        """Parse quality gates configuration with nested structures.

        Args:
            data: Raw quality gates configuration dict

        Returns:
            Validated QualityGatesConfig with defaults for missing values

        Raises:
            ConfigValidationError: If quality_gates structure is invalid
        """
        try:
            # Parse nested configs with field filtering
            # Helper to filter only valid fields for a dataclass
            def filter_fields(data: dict, config_class: type) -> dict:
                """Filter dict to only include fields that exist in the dataclass."""
                if not data:
                    return {}
                import dataclasses

                valid_fields = {f.name for f in dataclasses.fields(config_class)}
                return {k: v for k, v in data.items() if k in valid_fields}

            test_exec_data = filter_fields(data.get("test_execution", {}), ExecutionConfig)
            linting_data = filter_fields(data.get("linting", {}), LintingConfig)
            formatting_data = filter_fields(data.get("formatting", {}), FormattingConfig)
            security_data = filter_fields(data.get("security", {}), SecurityConfig)
            documentation_data = filter_fields(data.get("documentation", {}), DocumentationConfig)
            spec_completeness_data = filter_fields(
                data.get("spec_completeness", {}), SpecCompletenessConfig
            )
            context7_data = filter_fields(data.get("context7", {}), Context7Config)
            integration_data = filter_fields(data.get("integration", {}), IntegrationConfig)
            deployment_data = filter_fields(data.get("deployment", {}), DeploymentConfig)

            return QualityGatesConfig(
                test_execution=(
                    ExecutionConfig(**test_exec_data) if test_exec_data else ExecutionConfig()
                ),
                linting=(LintingConfig(**linting_data) if linting_data else LintingConfig()),
                formatting=(
                    FormattingConfig(**formatting_data) if formatting_data else FormattingConfig()
                ),
                security=(SecurityConfig(**security_data) if security_data else SecurityConfig()),
                documentation=(
                    DocumentationConfig(**documentation_data)
                    if documentation_data
                    else DocumentationConfig()
                ),
                spec_completeness=(
                    SpecCompletenessConfig(**spec_completeness_data)
                    if spec_completeness_data
                    else SpecCompletenessConfig()
                ),
                context7=(Context7Config(**context7_data) if context7_data else Context7Config()),
                integration=(
                    IntegrationConfig(**integration_data)
                    if integration_data
                    else IntegrationConfig()
                ),
                deployment=(
                    DeploymentConfig(**deployment_data) if deployment_data else DeploymentConfig()
                ),
            )
        except TypeError as e:
            # Collect validation errors
            errors = [f"Invalid quality_gates structure: {str(e)}"]
            raise ConfigValidationError(
                config_path=str(self._config_path) if self._config_path else "unknown",
                errors=errors,
            )

    @property
    def quality_gates(self) -> QualityGatesConfig:
        """Get quality gates configuration.

        Returns:
            Quality gates configuration with all sub-configurations
        """
        assert self._config is not None, "Config not initialized"
        return self._config.quality_gates

    @property
    def git_workflow(self) -> GitWorkflowConfig:
        """Get git workflow configuration.

        Returns:
            Git workflow configuration
        """
        assert self._config is not None, "Config not initialized"
        return self._config.git_workflow

    @property
    def curation(self) -> CurationConfig:
        """Get curation configuration.

        Returns:
            Learning curation configuration
        """
        assert self._config is not None, "Config not initialized"
        return self._config.curation

    def get_config(self) -> SolokitConfig:
        """Get full configuration.

        Returns:
            Complete Solokit configuration
        """
        assert self._config is not None, "Config not initialized"
        return self._config

    def invalidate_cache(self) -> None:
        """Invalidate cached configuration.

        Forces next load_config() call to reload from disk.
        Useful for testing and when config file changes.
        """
        self._config_path = None
        logger.debug("Configuration cache invalidated")


# Global instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get global ConfigManager instance.

    Returns:
        Singleton ConfigManager instance

    Example:
        >>> config = get_config_manager()
        >>> config.load_config(Path(".session/config.json"))
        >>> print(config.quality_gates.test_execution.enabled)
        True
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
