"""
Adopt Module

Handles adoption of Solokit into existing projects with code.
Provides session management, quality gates, and learning capture
without modifying existing project code.
"""

from solokit.adopt.doc_appender import (
    append_documentation,
    append_to_claude_md,
    append_to_readme,
)
from solokit.adopt.orchestrator import run_adoption
from solokit.adopt.project_detector import (
    ExistingTooling,
    PackageManager,
    ProjectFramework,
    ProjectInfo,
    ProjectLanguage,
    detect_project_type,
    get_project_summary,
)

__all__ = [
    # Orchestrator
    "run_adoption",
    # Project detection
    "detect_project_type",
    "get_project_summary",
    "ProjectInfo",
    "ProjectLanguage",
    "ProjectFramework",
    "PackageManager",
    "ExistingTooling",
    # Documentation
    "append_to_readme",
    "append_to_claude_md",
    "append_documentation",
]
