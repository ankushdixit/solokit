#!/usr/bin/env python3
"""
Briefing formatting and generation.
Part of the briefing module decomposition.
"""

import sys
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import SESSION_STATUS_TIMEOUT
from solokit.core.exceptions import (
    FileOperationError,
)
from solokit.core.logging_config import get_logger
from solokit.core.types import WorkItemStatus, WorkItemType

logger = get_logger(__name__)


class BriefingFormatter:
    """Format briefing content and generate output."""

    def __init__(self) -> None:
        """Initialize briefing formatter."""
        self.runner = CommandRunner(default_timeout=SESSION_STATUS_TIMEOUT)

    def shift_heading_levels(self, markdown_content: str, shift: int) -> str:
        r"""Shift all markdown heading levels by a specified amount.

        Args:
            markdown_content: The markdown text to process
            shift: Number of levels to shift (positive = deeper, e.g., H1 → H3 if shift=2)

        Returns:
            Modified markdown with shifted heading levels

        Example:
            shift_heading_levels("# Title\n## Section", 2)
            Returns: "### Title\n#### Section"
        """
        if not markdown_content or shift <= 0:
            return markdown_content

        lines = markdown_content.split("\n")
        result = []

        for line in lines:
            # Check if line starts with heading marker
            if line.startswith("#"):
                # Count existing heading level
                heading_level = 0
                for char in line:
                    if char == "#":
                        heading_level += 1
                    else:
                        break

                # Calculate new level (cap at 6 for markdown)
                new_level = min(heading_level + shift, 6)

                # Reconstruct line with new heading level
                rest_of_line = line[heading_level:]
                result.append("#" * new_level + rest_of_line)
            else:
                result.append(line)

        return "\n".join(result)

    def strip_template_comments(self, content: str) -> str:
        """Remove HTML comments and template placeholders from spec content.

        This cleans up specification files that contain template instructions
        and placeholder text, making the briefing output more concise and readable.

        Args:
            content: Raw spec file content

        Returns:
            Cleaned content without comments and obvious placeholders
        """
        import re

        # Remove HTML comments (including multi-line)
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # Remove common template placeholder patterns
        # These are generic placeholder lines that should not appear in real specs
        placeholders = [
            r"^Brief description of.*$",
            r"^Clear description of.*$",
            r"^Provide a \d+-\d+ sentence.*$",
            r"^As a \[type of user\].*$",
        ]
        for pattern in placeholders:
            content = re.sub(pattern, "", content, flags=re.MULTILINE)

        # Remove excessive blank lines (3+ consecutive newlines)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()

    def extract_section(self, markdown: str, heading: str) -> str:
        """Extract section from markdown between heading and next ## heading.

        Args:
            markdown: Full markdown content
            heading: Heading to find (e.g., "## Commits Made")

        Returns:
            Section content (without the heading itself)
        """
        lines = markdown.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if line.startswith(heading):
                in_section = True
                continue
            elif in_section and line.startswith("## "):
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip()

    def generate_previous_work_section(self, item_id: str, item: dict) -> str:
        """Generate previous work context from session summaries.

        Args:
            item_id: Work item identifier
            item: Work item dictionary with sessions list

        Returns:
            Markdown section with previous work context (empty string if none)
        """
        sessions = item.get("sessions", [])
        if not sessions:
            return ""

        section = "\n## Previous Work\n\n"
        section += f"This work item has been in progress across {len(sessions)} session(s).\n\n"

        for session_info in sessions:
            session_num = session_info["session_num"]
            started_at = session_info.get("started_at", "")

            summary_file = Path(f".session/history/session_{session_num:03d}_summary.md")
            if not summary_file.exists():
                continue

            try:
                summary_content = summary_file.read_text()
            except OSError as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(summary_file),
                    details=f"Failed to read session summary: {str(e)}",
                    cause=e,
                )
            section += f"### Session {session_num} ({started_at[:10]})\n\n"

            # Extract commits section
            if "## Commits Made" in summary_content:
                commits = self.extract_section(summary_content, "## Commits Made")
                if commits:
                    section += commits + "\n\n"

            # Extract quality gates
            if "## Quality Gates" in summary_content:
                gates = self.extract_section(summary_content, "## Quality Gates")
                if gates:
                    section += "**Quality Gates:**\n" + gates + "\n\n"

        return section

    def validate_environment(self) -> list[str]:
        """Validate development environment.

        Returns:
            List of environment check strings
        """
        checks = []

        # Check Python version
        checks.append(f"Python: {sys.version.split()[0]}")

        # Check git
        result = self.runner.run(["git", "--version"])
        if result.success:
            checks.append(f"Git: {result.stdout.strip()}")
        else:
            checks.append("Git: NOT FOUND")

        return checks

    def check_command_exists(self, command: str) -> bool:
        """Check if a command is available.

        Args:
            command: Command to check

        Returns:
            True if command exists, False otherwise
        """
        result = self.runner.run([command, "--version"])
        return result.success

    def generate_integration_test_briefing(self, work_item: dict) -> str:
        """Generate integration test specific briefing sections.

        Args:
            work_item: Integration test work item

        Returns:
            Additional briefing sections for integration tests
        """
        if work_item.get("type") != WorkItemType.INTEGRATION_TEST.value:
            return ""

        briefing = "\n## Integration Test Context\n\n"

        # 1. Components being integrated (from scope description)
        scope = work_item.get("scope", "")
        if scope and len(scope) > 20:
            briefing += "**Integration Scope:**\n"
            briefing += f"{scope[:200]}...\n\n" if len(scope) > 200 else f"{scope}\n\n"

        # 2. Environment requirements
        env_requirements = work_item.get("environment_requirements", {})
        services = env_requirements.get("services_required", [])

        if services:
            briefing += "**Required Services:**\n"
            for service in services:
                briefing += f"- {service}\n"
            briefing += "\n"

        # 3. Test scenarios summary
        scenarios = work_item.get("test_scenarios", [])
        if scenarios:
            briefing += f"**Test Scenarios ({len(scenarios)} total):**\n"
            for i, scenario in enumerate(scenarios[:5], 1):  # Show first 5
                scenario_name = scenario.get("name", scenario.get("description", f"Scenario {i}"))
                briefing += f"{i}. {scenario_name}\n"

            if len(scenarios) > 5:
                briefing += f"... and {len(scenarios) - 5} more scenarios\n"
            briefing += "\n"

        # 4. Performance benchmarks
        benchmarks = work_item.get("performance_benchmarks", {})
        if benchmarks:
            briefing += "**Performance Requirements:**\n"

            response_time = benchmarks.get("response_time", {})
            if response_time:
                briefing += f"- Response time: p95 < {response_time.get('p95', 'N/A')}ms\n"

            throughput = benchmarks.get("throughput", {})
            if throughput:
                briefing += f"- Throughput: > {throughput.get('minimum', 'N/A')} req/s\n"

            briefing += "\n"

        # 5. API contracts
        contracts = work_item.get("api_contracts", [])
        if contracts:
            briefing += f"**API Contracts ({len(contracts)} contracts):**\n"
            for contract in contracts:
                contract_file = contract.get("contract_file", "N/A")
                contract_version = contract.get("version", "N/A")
                briefing += f"- {contract_file} (version: {contract_version})\n"
            briefing += "\n"

        # 6. Environment validation status
        briefing += "**Pre-Session Checks:**\n"

        # Check Docker
        docker_available = self.check_command_exists("docker")
        briefing += f"- Docker: {'✓ Available' if docker_available else '✗ Not found'}\n"

        # Check Docker Compose
        compose_available = self.check_command_exists("docker-compose")
        briefing += f"- Docker Compose: {'✓ Available' if compose_available else '✗ Not found'}\n"

        # Check compose file
        compose_file = env_requirements.get("compose_file", "docker-compose.integration.yml")
        compose_exists = Path(compose_file).exists()
        status_text = "✓ Found" if compose_exists else "✗ Missing"
        briefing += f"- Compose file ({compose_file}): {status_text}\n"

        briefing += "\n"

        return briefing

    def generate_deployment_briefing(self, work_item: dict) -> str:
        """Generate deployment-specific briefing section.

        Args:
            work_item: Deployment work item

        Returns:
            Deployment briefing text
        """
        if work_item.get("type") != WorkItemType.DEPLOYMENT.value:
            return ""

        briefing = []
        briefing.append("\n" + "=" * 60)
        briefing.append("DEPLOYMENT CONTEXT")
        briefing.append("=" * 60)

        spec = work_item.get("specification", "")

        # Parse deployment scope
        briefing.append("\n**Deployment Scope:**")
        # NOTE: Framework stub - Parse deployment scope from spec using spec_parser.py
        # Extract "## Deployment Scope" section and parse Application/Environment/Version fields
        briefing.append("  Application: [parse from spec]")
        briefing.append("  Environment: [parse from spec]")
        briefing.append("  Version: [parse from spec]")

        # Parse deployment procedure
        briefing.append("\n**Deployment Procedure:**")
        # NOTE: Framework stub - Parse deployment steps from spec using spec_parser.py
        # Extract "## Deployment Steps" section and count pre/during/post steps
        briefing.append("  Pre-deployment: [X steps]")
        briefing.append("  Deployment: [Y steps]")
        briefing.append("  Post-deployment: [Z steps]")

        # Parse rollback procedure
        briefing.append("\n**Rollback Procedure:**")
        # NOTE: Framework stub - Parse rollback details from spec using spec_parser.py
        # Extract "## Rollback Procedure" section for triggers and time estimates
        has_rollback = "rollback procedure" in spec.lower()
        briefing.append(f"  Rollback triggers defined: {'Yes' if has_rollback else 'No'}")
        briefing.append("  Estimated rollback time: [X minutes]")

        # Environment pre-checks
        briefing.append("\n**Pre-Session Environment Checks:**")
        try:
            from solokit.quality.env_validator import EnvironmentValidator

            # NOTE: Framework stub - Parse target environment from spec using spec_parser.py
            # Extract from "## Deployment Scope" or "## Environment" section
            environment = "staging"  # Default fallback
            validator = EnvironmentValidator(environment)
            passed, results = validator.validate_all()

            briefing.append(f"  Environment validation: {'✓ PASSED' if passed else '✗ FAILED'}")
            for validation in results.get("validations", []):
                status = "✓" if validation["passed"] else "✗"
                briefing.append(f"    {status} {validation['name']}")
        except ImportError as e:
            logger.warning(
                "EnvironmentValidator module not available",
                extra={"error": str(e), "module": "solokit.quality.env_validator"},
            )
            briefing.append("  Environment validation: ✗ Module not available")
        except Exception as e:
            logger.error(
                "Environment validation failed",
                extra={"error": str(e), "environment": "staging"},
            )
            briefing.append(f"  Environment validation: ✗ Error ({str(e)})")

        briefing.append("\n" + "=" * 60)

        return "\n".join(briefing)

    def generate_briefing(
        self,
        item_id: str,
        item: dict,
        project_docs: dict[str, str],
        current_stack: str,
        current_tree: str,
        work_item_spec: str,
        env_checks: list[str],
        git_status: dict,
        spec_validation_warning: str | None,
        milestone_context: dict | None,
        relevant_learnings: list[dict],
    ) -> str:
        """Generate comprehensive markdown briefing with full project context.

        Args:
            item_id: Work item identifier
            item: Work item dictionary
            project_docs: Project documentation (dict of filename -> content)
            current_stack: Technology stack information
            current_tree: Project directory tree
            work_item_spec: Work item specification content
            env_checks: Environment validation checks
            git_status: Git status information
            spec_validation_warning: Optional spec validation warning
            milestone_context: Optional milestone context
            relevant_learnings: List of relevant learnings

        Returns:
            Complete briefing as markdown string
        """
        # Start briefing
        briefing = f"""# Session Briefing: {item["title"]}

## Quick Reference
- **Work Item ID:** {item_id}
- **Type:** {item["type"]}
- **Priority:** {item["priority"]}
- **Status:** {item["status"]}

## Environment Status
"""

        # Show environment checks
        for check in env_checks:
            briefing += f"- {check}\n"

        # Show git status
        briefing += "\n### Git Status\n"
        briefing += f"- Status: {git_status['status']}\n"
        if git_status.get("branch"):
            briefing += f"- Current Branch: {git_status['branch']}\n"

        # Project context section
        briefing += "\n## Project Context\n\n"

        # Vision (if available) - shift headings to maintain hierarchy under H3
        if "vision.md" in project_docs:
            shifted_vision = self.shift_heading_levels(project_docs["vision.md"], 3)
            briefing += f"### Vision\n\n{shifted_vision}\n\n"

        # Architecture (if available) - shift headings to maintain hierarchy under H3
        if "architecture.md" in project_docs:
            shifted_arch = self.shift_heading_levels(project_docs["architecture.md"], 3)
            briefing += f"### Architecture\n\n{shifted_arch}\n\n"

        # Current stack
        briefing += f"### Current Stack\n```\n{current_stack}\n```\n\n"

        # Project structure - full tree
        briefing += f"### Project Structure\n```\n{current_tree}\n```\n\n"

        # Spec validation warning (if spec is incomplete)
        if spec_validation_warning:
            briefing += f"""## ⚠️ Specification Validation Warning

{spec_validation_warning}

**Note:** Please review and complete the specification before proceeding with implementation.

"""

        # Add previous work section for in-progress items (Enhancement #11 Phase 3)
        if item.get("status") == WorkItemStatus.IN_PROGRESS.value:
            previous_work = self.generate_previous_work_section(item_id, item)
            if previous_work:
                briefing += previous_work

        # Work item specification - strip comments and shift headings to maintain hierarchy under H2
        cleaned_spec = self.strip_template_comments(work_item_spec)
        shifted_spec = self.shift_heading_levels(cleaned_spec, 2)
        briefing += f"""## Work Item Specification

{shifted_spec}

## Dependencies
"""

        # Show dependency status
        if item.get("dependencies"):
            for dep in item["dependencies"]:
                briefing += f"- {dep} ✓ completed\n"
        else:
            briefing += "No dependencies\n"

        # Add milestone context
        if milestone_context:
            briefing += f"""
## Milestone Context

**{milestone_context["title"]}**
{milestone_context["description"]}

Progress: {milestone_context["progress"]}% ({milestone_context["completed_items"]}"""
            briefing += f"""/{milestone_context["total_items"]} items complete)
"""
            if milestone_context["target_date"]:
                briefing += f"Target Date: {milestone_context['target_date']}\n"

            briefing += "\nRelated work items in this milestone:\n"
            # Show other items in same milestone
            for related_item in milestone_context["milestone_items"]:
                if related_item["id"] != item_id:
                    status_icon = (
                        "✓" if related_item["status"] == WorkItemStatus.COMPLETED.value else "○"
                    )
                    briefing += f"- {status_icon} {related_item['id']} - {related_item['title']}\n"
            briefing += "\n"

        # Relevant learnings
        if relevant_learnings:
            briefing += "\n## Relevant Learnings\n\n"
            for learning in relevant_learnings:
                briefing += f"**{learning.get('category', 'general')}:** {learning['content']}\n\n"

        return briefing
