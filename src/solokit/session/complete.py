#!/usr/bin/env python3
"""
Complete current session with quality gates and summary generation.
Enhanced with full tracking updates and git workflow.

Updated in Phase 5.7.3 to use spec_parser for reading work item rationale.
Migrated to standardized error handling pattern.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
from solokit.core.command_runner import CommandRunner
from solokit.core.constants import (
    GIT_QUICK_TIMEOUT,
    GIT_STANDARD_TIMEOUT,
    SESSION_COMPLETE_TIMEOUT,
)
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    FileOperationError,
)
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import WorkItemStatus, WorkItemType
from solokit.quality.gates import QualityGates
from solokit.work_items.repository import WorkItemRepository
from solokit.work_items.spec_parser import parse_spec_file
from solokit.work_items.updater import WorkItemUpdater

logger = get_logger(__name__)
output = get_output()


@log_errors()
def load_status() -> dict[str, Any] | None:
    """Load current session status.

    Returns:
        dict: Session status data, or None if no session exists

    Raises:
        FileOperationError: If file cannot be read or parsed
    """
    status_file = Path(".session/tracking/status_update.json")
    if not status_file.exists():
        return None

    try:
        with open(status_file) as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="parse",
            file_path=str(status_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        ) from e
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(status_file),
            details=str(e),
            cause=e,
        ) from e


@log_errors()
def load_work_items() -> dict[str, Any]:
    """Load work items.

    Returns:
        dict: Work items data

    Raises:
        FileOperationError: If file cannot be read or parsed
    """
    work_items_file = Path(".session/tracking/work_items.json")

    try:
        with open(work_items_file) as f:
            return json.load(f)  # type: ignore[no-any-return]
    except FileNotFoundError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(work_items_file),
            details="File not found",
            cause=e,
        ) from e
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="parse",
            file_path=str(work_items_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        ) from e
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(work_items_file),
            details=str(e),
            cause=e,
        ) from e


@log_errors()
def run_quality_gates(work_item: dict | None = None) -> tuple[dict, bool, list]:
    """Run comprehensive quality gates using QualityGates class.

    Args:
        work_item: Optional work item dict for custom validations

    Returns:
        tuple: (all_results dict, all_passed bool, failed_gates list)

    Raises:
        QualityGateError: If quality gates fail and are required
    """
    gates = QualityGates()
    all_results = {}
    all_passed = True
    failed_gates = []

    # Run tests
    passed, test_results = gates.run_tests()
    all_results["tests"] = test_results
    if not passed and gates.config.test_execution.required:
        all_passed = False
        failed_gates.append("tests")

    # Run security scanning
    passed, security_results = gates.run_security_scan()
    all_results["security"] = security_results
    if not passed and gates.config.security.required:
        all_passed = False
        failed_gates.append("security")

    # Run linting
    passed, linting_results = gates.run_linting()
    all_results["linting"] = linting_results
    if not passed and gates.config.linting.required:
        all_passed = False
        failed_gates.append("linting")

    # Run formatting
    passed, formatting_results = gates.run_formatting()
    all_results["formatting"] = formatting_results
    if not passed and gates.config.formatting.required:
        all_passed = False
        failed_gates.append("formatting")

    # Validate documentation
    passed, doc_results = gates.validate_documentation(work_item)
    all_results["documentation"] = doc_results
    if not passed and gates.config.documentation.required:
        all_passed = False
        failed_gates.append("documentation")

    # Verify Context7 libraries
    passed, context7_results = gates.verify_context7_libraries()
    all_results["context7"] = context7_results
    # Context7 is optional and not in QualityGatesConfig, always treat as optional
    if not passed:
        # Context7 failures are warnings, not failures
        logger.warning("Context7 library verification failed (non-blocking)")

    # Run custom validations
    if work_item:
        passed, custom_results = gates.run_custom_validations(work_item)
        all_results["custom"] = custom_results
        if not passed:
            all_passed = False
            failed_gates.append("custom")

    # Generate and print report
    report = gates.generate_report(all_results)
    output.info("\n" + report)

    # Print remediation guidance if any gates failed
    if failed_gates:
        guidance = gates.get_remediation_guidance(failed_gates)
        output.info(guidance)

    return all_results, all_passed, failed_gates


@log_errors()
def update_all_tracking(session_num: int) -> bool:
    """Update stack, tree, and other tracking files.

    Args:
        session_num: Current session number

    Returns:
        bool: True if tracking updates completed (may have warnings)

    Note:
        This function logs warnings but does not raise exceptions for
        tracking update failures, as they are non-critical.
    """
    logger.info(f"Updating tracking files for session {session_num}")

    # Get Solokit installation directory for absolute path resolution
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent / "project"

    runner = CommandRunner(default_timeout=SESSION_COMPLETE_TIMEOUT)

    # Update stack
    try:
        result = runner.run(
            [
                sys.executable,
                str(project_dir / "stack.py"),
                "--session",
                str(session_num),
                "--non-interactive",
            ]
        )
        if result.success:
            output.success("Stack updated")
            # Print output if there were changes
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        output.info(f"  {line}")
        else:
            logger.warning(f"Stack update failed (exit code {result.returncode})")
            output.warning(f"Stack update failed (exit code {result.returncode})")
            if result.stderr:
                logger.warning(f"Stack update error: {result.stderr}")
                output.info(f"  Error: {result.stderr}")
    except Exception as e:
        logger.warning(f"Stack update failed: {e}", exc_info=True)
        output.warning(f"Stack update failed: {e}")

    # Update tree
    try:
        result = runner.run(
            [
                sys.executable,
                str(project_dir / "tree.py"),
                "--session",
                str(session_num),
                "--non-interactive",
            ]
        )
        if result.success:
            output.success("Tree updated")
            # Print output if there were changes
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        output.info(f"  {line}")
        else:
            logger.warning(f"Tree update failed (exit code {result.returncode})")
            output.warning(f"Tree update failed (exit code {result.returncode})")
            if result.stderr:
                logger.warning(f"Tree update error: {result.stderr}")
                output.info(f"  Error: {result.stderr}")
    except Exception as e:
        logger.warning(f"Tree update failed: {e}", exc_info=True)
        output.warning(f"Tree update failed: {e}")

    return True


@log_errors()
def trigger_curation_if_needed(session_num: int) -> None:
    """Check if curation should run and trigger it.

    Args:
        session_num: Current session number

    Note:
        This function logs warnings but does not raise exceptions for
        curation failures, as they are non-critical.
    """
    # Use ConfigManager for centralized config management
    from solokit.core.config import get_config_manager

    config_path = Path(".session/config.json")
    config_manager = get_config_manager()
    config_manager.load_config(config_path)
    curation_config = config_manager.curation

    if not curation_config.auto_curate:
        logger.debug("Auto-curation disabled in config")
        return

    frequency = curation_config.frequency

    # Run curation every N sessions
    if session_num % frequency == 0:
        logger.info(f"Triggering automatic curation for session {session_num}")
        output.info(f"\n{'=' * 50}")
        output.info(f"Running automatic learning curation (session {session_num})...")
        output.info(f"{'=' * 50}\n")

        try:
            from solokit.learning.curator import LearningsCurator

            curator = LearningsCurator()
            curator.curate(dry_run=False)
            output.success("Learning curation completed\n")
            logger.info("Learning curation completed successfully")
        except Exception as e:
            logger.warning(f"Learning curation failed: {e}", exc_info=True)
            output.warning(f"Learning curation failed: {e}\n")


@log_errors()
def auto_extract_learnings(session_num: int) -> int:
    """Auto-extract learnings from session artifacts.

    Args:
        session_num: Current session number

    Returns:
        int: Number of new learnings extracted

    Note:
        This function logs warnings but does not raise exceptions for
        extraction failures, as they are non-critical.
    """
    logger.info(f"Auto-extracting learnings from session {session_num} artifacts")

    try:
        # Import learning curator
        from solokit.learning.curator import LearningsCurator

        curator = LearningsCurator()

        total_extracted = 0

        # Extract from session summary (if it exists)
        summary_file = Path(f".session/history/session_{session_num:03d}_summary.md")
        if summary_file.exists():
            from_summary = curator.extract_from_session_summary(summary_file)
            for learning in from_summary:
                if curator.add_learning_if_new(learning):
                    total_extracted += 1

        # Extract from git commits
        from_commits = curator.extract_from_git_commits()
        for learning in from_commits:
            if curator.add_learning_if_new(learning):
                total_extracted += 1

        # Extract from inline code comments
        from_code = curator.extract_from_code_comments()
        for learning in from_code:
            if curator.add_learning_if_new(learning):
                total_extracted += 1

        if total_extracted > 0:
            logger.info(f"Auto-extracted {total_extracted} new learnings")
            output.info(f"✓ Auto-extracted {total_extracted} new learning(s)\n")
        else:
            logger.info("No new learnings extracted from session artifacts")
            output.info("No new learnings extracted\n")

        return total_extracted

    except Exception as e:
        logger.warning(f"Auto-extraction failed: {e}", exc_info=True)
        output.warning(f"Auto-extraction failed: {e}\n")
        return 0


@log_errors()
def extract_learnings_from_session(learnings_file: Path | None = None) -> list[str]:
    """Extract learnings from work done in session (manual input or file).

    Args:
        learnings_file: Path to file containing learnings (one per line)

    Returns:
        list: List of learning strings

    Raises:
        FileOperationError: If learnings file cannot be read
    """
    # If learnings file provided, read from it
    if learnings_file:
        learnings_path = Path(learnings_file)
        if learnings_path.exists():
            try:
                logger.info(f"Reading learnings from {learnings_file}")
                with open(learnings_path) as f:
                    learnings = [line.strip() for line in f if line.strip()]
                output.info(f"✓ Loaded {len(learnings)} learnings from file")
                # Clean up temp file
                learnings_path.unlink()
                return learnings
            except OSError as e:
                logger.warning(f"Failed to read learnings file: {e}")
                output.warning(f"Failed to read learnings file: {e}")
                return []
        else:
            logger.warning(f"Learnings file not found: {learnings_file}")
            output.warning(f"Learnings file not found: {learnings_file}")
            return []

    # Skip manual input in non-interactive mode (e.g., when run by Claude Code)
    if not sys.stdin.isatty():
        logger.info("Skipping manual learning extraction (non-interactive mode)")
        output.info("\nSkipping manual learning extraction (non-interactive mode)")
        return []

    output.info("\nCapture additional learnings manually...")
    output.info("(Type each learning, or 'done' to finish, or 'skip' to skip):")

    learnings = []
    while True:
        try:
            learning = input("> ")
            if learning.lower() == "done":
                break
            if learning.lower() == "skip":
                return []
            if learning:
                learnings.append(learning)
        except EOFError:
            # Handle EOF gracefully in case stdin is closed
            logger.debug("EOF encountered during manual learning input")
            break

    return learnings


@log_errors()
def complete_git_workflow(
    work_item_id: str, commit_message: str, session_num: int
) -> dict[str, Any]:
    """Complete git workflow (verify commits, push, optionally merge or create PR).

    Note: As of the /end command improvements, commits should be created by Claude
    before calling this function. The commit_message parameter is deprecated and
    no longer used - it's kept for backward compatibility.

    Args:
        work_item_id: Work item identifier
        commit_message: Deprecated - no longer used (kept for backward compatibility)
        session_num: Current session number

    Returns:
        dict: Result dict with 'success' and 'message' keys

    Note:
        This function returns error dicts rather than raising exceptions
        to maintain compatibility with existing error handling.
    """
    try:
        # Import git workflow from new location
        from solokit.git.integration import GitWorkflow

        workflow = GitWorkflow()

        # Load work items to check status
        work_items_file = Path(".session/tracking/work_items.json")
        try:
            with open(work_items_file) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load work items: {e}")
            return {"success": False, "message": f"Failed to load work items: {e}"}

        if work_item_id not in data["work_items"]:
            logger.error(f"Work item not found: {work_item_id}")
            return {"success": False, "message": f"Work item not found: {work_item_id}"}

        work_item = data["work_items"][work_item_id]
        should_merge = work_item["status"] == WorkItemStatus.COMPLETED.value

        # Complete work item in git (with session_num for PR creation)
        result = workflow.complete_work_item(
            work_item_id, commit_message, merge=should_merge, session_num=session_num
        )

        return result
    except Exception as e:
        logger.error(f"Git workflow error: {e}", exc_info=True)
        return {"success": False, "message": f"Git workflow error: {e}"}


@log_errors()
def record_session_commits(work_item_id: str) -> None:
    """Record commits made during session to work item tracking (Bug #15 fix).

    Args:
        work_item_id: Work item identifier

    Note:
        This function logs warnings but does not raise exceptions, as commit
        recording is non-critical tracking functionality.
    """
    try:
        work_items_file = Path(".session/tracking/work_items.json")
        with open(work_items_file) as f:
            data = json.load(f)

        if work_item_id not in data["work_items"]:
            logger.warning(f"Work item not found for commit recording: {work_item_id}")
            return

        work_item = data["work_items"][work_item_id]
        git_info = work_item.get("git", {})

        # Get branch information
        branch_name = git_info.get("branch")
        parent_branch = git_info.get("parent_branch", "main")

        if not branch_name:
            # No git branch tracking for this work item
            logger.debug(f"No git branch tracking for work item: {work_item_id}")
            return

        # Get commits on session branch that aren't in parent branch
        runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT)
        result = runner.run(
            ["git", "log", "--pretty=format:%H|%s|%ai", f"{parent_branch}..{branch_name}"]
        )

        if not result.success:
            # Branch might not exist or other git error - skip silently
            logger.debug(f"Git log failed for branch {branch_name}: {result.stderr}")
            return

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    sha, message, timestamp = parts
                    commits.append({"sha": sha, "message": message, "timestamp": timestamp})

        # Update work_items.json with commits
        if commits:
            data["work_items"][work_item_id]["git"]["commits"] = commits
            with open(work_items_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Recorded {len(commits)} commits for work item {work_item_id}")

    except Exception as e:
        # Silently skip if there's any error - this is non-critical tracking
        logger.debug(f"Failed to record session commits: {e}", exc_info=True)


@log_errors()
def generate_commit_message(status: dict, work_item: dict) -> str:
    """Generate standardized commit message.

    Updated in Phase 5.7.3 to read rationale from spec file instead of
    deprecated JSON field.

    Args:
        status: Session status dict
        work_item: Work item dict

    Returns:
        str: Formatted commit message

    Note:
        Spec file errors are logged but don't prevent message generation.
    """
    session_num = status["current_session"]
    work_type = work_item["type"]
    title = work_item["title"]

    message = f"Session {session_num:03d}: {work_type.title()} - {title}\n\n"

    # Get rationale from spec file
    try:
        parsed_spec = parse_spec_file(work_item)
        rationale = parsed_spec.get("rationale")

        if rationale and rationale.strip():
            # Trim to first paragraph if too long
            first_para = rationale.split("\n\n")[0]
            if len(first_para) > 200:
                first_para = first_para[:197] + "..."
            message += f"{first_para}\n\n"
    except Exception as e:
        # If spec file not found or invalid, continue without rationale
        logger.debug(f"Could not read spec file rationale: {e}")

    if work_item["status"] == WorkItemStatus.COMPLETED.value:
        message += "✅ Work item completed\n"
    else:
        message += "🚧 Work in progress\n"

    message += "\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
    message += "\nCo-Authored-By: Claude <noreply@anthropic.com>"

    return message


@log_errors()
def generate_summary(
    status: dict, work_items_data: dict, gate_results: dict, learnings: list | None = None
) -> str:
    """Generate comprehensive session summary.

    Args:
        status: Session status dict
        work_items_data: Work items data dict
        gate_results: Quality gate results dict
        learnings: Optional list of learnings

    Returns:
        str: Formatted markdown summary

    Note:
        Git diff errors are logged but don't prevent summary generation.
    """
    work_item_id = status["current_work_item"]
    work_item = work_items_data["work_items"][work_item_id]

    summary = f"""# Session {status["current_session"]} Summary

{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Work Items
- **{work_item_id}**: {work_item["title"]} ({work_item["status"]})

"""

    # Add commit details with file stats (Enhancement #11 Phase 1)
    commits = work_item.get("git", {}).get("commits", [])
    if commits:
        summary += "## Commits Made\n\n"
        for commit in commits:
            # Show short SHA and first line of commit message
            message_lines = commit["message"].split("\n")
            first_line = message_lines[0] if message_lines else ""
            summary += f"**{commit['sha'][:7]}** - {first_line}\n"

            # Show full message if multi-line
            if len(message_lines) > 1:
                remaining_lines = "\n".join(message_lines[1:]).strip()
                if remaining_lines:
                    summary += "\n```\n"
                    summary += remaining_lines
                    summary += "\n```\n\n"

            # Get file stats using git diff
            try:
                runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT)
                result = runner.run(["git", "diff", "--stat", f"{commit['sha']}^..{commit['sha']}"])
                if result.success and result.stdout.strip():
                    summary += "\nFiles changed:\n```\n"
                    summary += result.stdout
                    summary += "```\n\n"
            except Exception as e:
                # Silently skip if git diff fails
                logger.debug(f"Git diff failed for commit {commit['sha']}: {e}")

        summary += "\n"

    summary += "## Quality Gates\n"

    # Add results for each gate
    for gate_name, gate_result in gate_results.items():
        status_text = gate_result.get("status", "unknown")
        if status_text == "skipped":
            summary += f"- {gate_name.title()}: ⊘ SKIPPED\n"
        elif status_text == "passed":
            summary += f"- {gate_name.title()}: ✓ PASSED\n"
        else:
            summary += f"- {gate_name.title()}: ✗ FAILED\n"

        # Add coverage for tests
        if gate_name == "tests" and gate_result.get("coverage"):
            summary += f"  - Coverage: {gate_result['coverage']}%\n"

        # Add severity counts for security
        if gate_name == "security" and gate_result.get("by_severity"):
            for severity, count in gate_result["by_severity"].items():
                summary += f"  - {severity}: {count}\n"

    if learnings:
        summary += "\n## Learnings Captured\n"
        for learning in learnings:
            summary += f"- {learning}\n"

    summary += "\n## Next Session\nTo be determined\n"

    # Add integration test summary if applicable
    integration_summary = generate_integration_test_summary(work_item, gate_results)
    if integration_summary:
        summary += integration_summary

    # Add deployment summary if applicable
    deployment_summary = generate_deployment_summary(work_item, gate_results)
    if deployment_summary:
        summary += deployment_summary

    return summary


def generate_integration_test_summary(work_item: dict, gate_results: dict) -> str:
    """
    Generate integration test summary for session completion.

    Args:
        work_item: Integration test work item
        gate_results: Results from quality gates

    Returns:
        Integration test summary section
    """
    if work_item.get("type") != WorkItemType.INTEGRATION_TEST.value:
        return ""

    summary = "\n## Integration Test Results\n\n"

    # Integration test execution results
    integration_results = gate_results.get("integration_tests", {})

    if integration_results:
        test_results = integration_results.get("integration_tests", {})

        if test_results:
            summary += "**Integration Tests:**\n"
            summary += f"- Passed: {test_results.get('passed', 0)}\n"
            summary += f"- Failed: {test_results.get('failed', 0)}\n"
            summary += f"- Skipped: {test_results.get('skipped', 0)}\n"
            summary += f"- Duration: {test_results.get('total_duration', 0):.2f}s\n\n"

        # Performance benchmarks
        perf_results = integration_results.get("performance_benchmarks", {})
        if perf_results:
            summary += "**Performance Benchmarks:**\n"

            latency = perf_results.get("load_test", {}).get("latency", {})
            if latency:
                summary += f"- p50 latency: {latency.get('p50', 'N/A')}ms\n"
                summary += f"- p95 latency: {latency.get('p95', 'N/A')}ms\n"
                summary += f"- p99 latency: {latency.get('p99', 'N/A')}ms\n"

            throughput = perf_results.get("load_test", {}).get("throughput", {})
            if throughput:
                summary += f"- Throughput: {throughput.get('requests_per_sec', 'N/A')} req/s\n"

            if perf_results.get("regression_detected"):
                summary += "- ⚠️  Performance regression detected!\n"

            summary += "\n"

        # API contracts
        contract_results = integration_results.get("api_contracts", {})
        if contract_results:
            summary += "**API Contract Validation:**\n"
            summary += f"- Contracts validated: {contract_results.get('contracts_validated', 0)}\n"

            breaking_changes = contract_results.get("breaking_changes", [])
            if breaking_changes:
                summary += f"- ⚠️  Breaking changes detected: {len(breaking_changes)}\n"
                for change in breaking_changes[:3]:  # Show first 3
                    summary += f"  - {change.get('message', 'Unknown')}\n"
            else:
                summary += "- ✓ No breaking changes\n"

            summary += "\n"

    return summary


def generate_deployment_summary(work_item: dict, gate_results: dict) -> str:
    """
    Generate deployment-specific summary section.

    Args:
        work_item: Deployment work item
        gate_results: Results from deployment quality gates

    Returns:
        Deployment summary text
    """
    if work_item.get("type") != WorkItemType.DEPLOYMENT.value:
        return ""

    summary = []
    summary.append("\n" + "=" * 60)
    summary.append("DEPLOYMENT RESULTS")
    summary.append("=" * 60)

    # Deployment execution results
    # NOTE: Framework stub - Parse actual results from deployment_executor
    # When implemented, extract from DeploymentExecutor.get_deployment_log()
    summary.append("\n**Deployment Execution:**")
    summary.append("  Status: [Success/Failed]")
    summary.append("  Steps completed: [X/Y]")
    summary.append("  Duration: [X minutes]")

    # Smoke test results
    summary.append("\n**Smoke Tests:**")
    summary.append("  Passed: [X]")
    summary.append("  Failed: [Y]")
    summary.append("  Skipped: [Z]")

    # Environment validation
    summary.append("\n**Environment Validation:**")
    for gate in gate_results.get("gates", []):
        if gate.get("name") == "Environment Validation":
            status = "✓ PASSED" if gate.get("passed") else "✗ FAILED"
            summary.append(f"  {status}")

    # Rollback status (if applicable)
    # NOTE: Framework stub - Check deployment results for rollback trigger
    # When implemented, check DeploymentExecutor results for rollback_triggered flag
    rollback_triggered = False
    if rollback_triggered:
        summary.append("\n⚠️  ROLLBACK TRIGGERED")
        summary.append("  Reason: [smoke test failure / error threshold]")
        summary.append("  Rollback status: [Success/Failed]")

    # Post-deployment metrics
    summary.append("\n**Post-Deployment Metrics:**")
    summary.append("  Error rate: [X%]")
    summary.append("  Response time p99: [X ms]")
    summary.append("  Active alerts: [X]")

    summary.append("\n" + "=" * 60)

    return "\n".join(summary)


@log_errors()
def check_uncommitted_changes() -> bool:
    """Check for uncommitted changes and guide user to commit first.

    Returns:
        bool: True if can proceed, False if should abort

    Note:
        This function logs warnings but does not raise exceptions.
        Git errors allow proceeding to avoid blocking workflows.
    """
    try:
        runner = CommandRunner(default_timeout=GIT_QUICK_TIMEOUT, working_dir=Path.cwd())
        result = runner.run(["git", "status", "--porcelain"])

        uncommitted = [line for line in result.stdout.split("\n") if line.strip()]

        # Filter out .session/tracking files (they're updated by sk end)
        user_changes = [
            line
            for line in uncommitted
            if ".session/tracking/" not in line and ".session/briefings/" not in line
        ]

        if not user_changes:
            logger.debug("No uncommitted changes detected")
            return True  # All good

        logger.warning(f"Detected {len(user_changes)} uncommitted changes")

        # Display uncommitted changes
        output.info("\n" + "=" * 60)
        output.warning("UNCOMMITTED CHANGES DETECTED")
        output.info("=" * 60)
        output.info("\nYou have uncommitted changes:")
        output.info("")

        for line in user_changes[:15]:  # Show first 15
            output.info(f"   {line}")

        if len(user_changes) > 15:
            output.info(f"   ... and {len(user_changes) - 15} more")

        output.info("\n" + "=" * 60)
        output.info("📋 REQUIRED STEPS BEFORE /sk:end:")
        output.info("=" * 60)
        output.info("")
        output.info("1. Review your changes:")
        output.info("   git status")
        output.info("")
        output.info("2. Update CHANGELOG.md with session changes:")
        output.info("   ## [Unreleased]")
        output.info("   ### Added")
        output.info("   - Your feature or change")
        output.info("")
        output.info("3. Commit everything:")
        output.info("   git add -A")
        output.info("   git commit -m 'Implement feature X")
        output.info("")
        output.info("   LEARNING: Key insight from implementation")
        output.info("")
        output.info("   🤖 Generated with [Claude Code](https://claude.com/claude-code)")
        output.info("   Co-Authored-By: Claude <noreply@anthropic.com>'")
        output.info("")
        output.info("4. Then run:")
        output.info("   /end")
        output.info("")
        output.info("=" * 60)

        # In interactive mode, allow override
        if sys.stdin.isatty():
            output.info("")
            response = input("Continue anyway? (y/n): ")
            user_override = response.lower() == "y"
            logger.info(
                f"User {'overrode' if user_override else 'aborted on'} uncommitted changes check"
            )
            return user_override
        else:
            logger.info("Non-interactive mode: aborting on uncommitted changes")
            output.info("\nNon-interactive mode: exiting")
            output.info("Please commit your changes and run '/end' again.")
            return False

    except Exception as e:
        logger.warning(f"Could not check git status: {e}", exc_info=True)
        output.info(f"Warning: Could not check git status: {e}")
        return True  # Don't block on errors


@log_errors()
def main() -> int:
    """Enhanced main entry point with full tracking updates.

    Returns:
        int: Exit code (0 for success, 1 for failure)

    Raises:
        SessionNotFoundError: If no active session exists
        WorkItemNotFoundError: If work item cannot be found
        QualityGateError: If quality gates fail
        FileOperationError: If file operations fail
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Complete Solokit session")
    parser.add_argument(
        "--learnings-file",
        type=str,
        help="Path to file containing learnings (one per line)",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Mark work item as complete",
    )
    parser.add_argument(
        "--incomplete",
        action="store_true",
        help="Keep work item as in-progress",
    )
    args = parser.parse_args()

    # Load current status
    try:
        status = load_status()
        if not status:
            logger.error("No active session found")
            output.info("Error: No active session found")
            return 1
    except FileOperationError as e:
        logger.error(f"Failed to load session status: {e}")
        output.info(f"Error: Failed to load session status: {e}")
        return 1

    try:
        work_items_data = load_work_items()
    except FileOperationError as e:
        logger.error(f"Failed to load work items: {e}")
        output.info(f"Error: Failed to load work items: {e}")
        return 1

    work_item_id = status["current_work_item"]
    session_num = status["current_session"]

    # Check if work_item_id is None (no active work item)
    if not work_item_id:
        logger.error("No active work item in session")

        # Provide context-aware message
        work_items = work_items_data.get("work_items", {})
        total_items = len(work_items)

        if total_items == 0:
            output.error("No active work item to complete")
            output.info("\nNo work items found. Create one first:")
            output.info("  1. Use /work-new to create a work item interactively")
            output.info(
                "  2. Or use CLI: sk work-new --type feature --title '...' --priority high\n"
            )
            output.info("💡 Use '/work-list' to see all work items")
        else:
            output.error("No active work item to complete")
            output.info(f"\nYou have {total_items} work items available.\n")
            output.info("To start a work item:")
            output.info("  1. View work items: /work-list")
            output.info("  2. Start a work item: /start <work_item_id>")
            output.info("  3. Or use /start to choose interactively\n")
            output.info("💡 Use '/work-next' to see recommended work items")
        return 1

    if work_item_id not in work_items_data["work_items"]:
        logger.error(f"Work item not found: {work_item_id}")
        output.error(f"Work item not found: {work_item_id}")
        output.info("\n💡 Use '/work-list' to see all work items")
        return 1

    work_item = work_items_data["work_items"][work_item_id]

    logger.info(f"Starting session {session_num} completion for work item {work_item_id}")

    # Pre-flight check - ensure changes are committed
    if not check_uncommitted_changes():
        logger.warning("Session completion aborted due to uncommitted changes")
        output.info("\n❌ Session completion aborted")
        output.info("Commit your changes and try again.\n")
        return 1

    output.info("Completing session...\n")

    # Determine if quality gates should be enforced based on flags
    # --incomplete skips quality gate enforcement (gates still run but don't block)
    # --complete enforces quality gates (gates must pass)
    enforce_quality_gates = args.complete

    if enforce_quality_gates:
        output.info("Running comprehensive quality gates...\n")
    else:
        output.info("Running quality gates (non-blocking for incomplete work)...\n")

    # Run quality gates with work item context
    gate_results, all_passed, failed_gates = run_quality_gates(work_item)

    if not all_passed and enforce_quality_gates:
        logger.error(f"Quality gates failed: {failed_gates}")
        output.info("\n❌ Required quality gates failed. Fix issues before completing session.")
        output.info(f"Failed gates: {', '.join(failed_gates)}")
        return 1

    if all_passed:
        logger.info("All required quality gates passed")
        output.info("\n✓ All required quality gates PASSED\n")
    elif not enforce_quality_gates:
        logger.warning(f"Quality gates failed but not enforced (--incomplete): {failed_gates}")
        output.info("\n⚠ Quality gates failed but not blocking (--incomplete flag)")
        output.info(f"Failed gates: {', '.join(failed_gates)}\n")

    # Update all tracking (stack, tree)
    update_all_tracking(session_num)

    # Trigger curation if needed (every N sessions)
    trigger_curation_if_needed(session_num)

    # Extract learnings manually or from file
    learnings = extract_learnings_from_session(args.learnings_file)

    # Process learnings with learning_curator if available
    if learnings:
        logger.info(f"Processing {len(learnings)} learnings")
        output.info(f"\nProcessing {len(learnings)} learnings...")
        try:
            from solokit.learning.curator import LearningsCurator

            curator = LearningsCurator()
            added_count = 0
            for learning in learnings:
                # Use standardized entry creator for consistent metadata structure
                # This ensures both 'learned_in' and 'context' fields are present
                source_type = "temp_file" if args.learnings_file else "manual"
                context = (
                    f"Temp file: {args.learnings_file}" if args.learnings_file else "Manual entry"
                )

                learning_dict = curator.create_learning_entry(
                    content=learning,
                    source=source_type,
                    session_id=f"session_{session_num:03d}",
                    context=context,
                )

                if curator.add_learning_if_new(learning_dict):
                    added_count += 1
                    output.info(f"  ✓ Added: {learning}")
                else:
                    output.info(f"  ⊘ Duplicate: {learning}")

            if added_count > 0:
                logger.info(f"Added {added_count} new learnings")
                output.info(f"\n✓ Added {added_count} new learning(s) to learnings.json")
            else:
                logger.info("No new learnings added (all duplicates)")
                output.info("\n⊘ No new learnings added (all were duplicates)")
        except Exception as e:
            logger.warning(f"Failed to process learnings: {e}", exc_info=True)
            output.warning(f"Failed to process learnings: {e}")

    # Determine work item completion status
    work_item_title = work_items_data["work_items"][work_item_id]["title"]

    if args.complete:
        output.info(f"\n✓ Marking work item '{work_item_title}' as complete (--complete flag)")
        is_complete = True
    elif args.incomplete:
        output.info(f"\n✓ Keeping work item '{work_item_title}' as in-progress (--incomplete flag)")
        is_complete = False
    else:
        # Must specify either --complete or --incomplete flag (no interactive fallback)
        logger.error("Must specify --complete or --incomplete flag")
        output.info("Error: Must specify either --complete or --incomplete flag")
        output.info("")
        output.info("Usage:")
        output.info("  sk end --complete              # Mark work item as completed")
        output.info("  sk end --incomplete            # Keep work item as in-progress")
        output.info("")
        output.info("For Claude Code users: Use /end slash command for interactive UI")
        return 1

    # Use WorkItemUpdater for status updates (includes auto-clear urgent flag)
    session_dir = Path(".session")
    repository = WorkItemRepository(session_dir)
    updater = WorkItemUpdater(repository)

    previous_status = work_items_data["work_items"][work_item_id]["status"]

    # Update work item status using updater
    if is_complete:
        new_status = WorkItemStatus.COMPLETED.value

        # Use updater to handle status change (auto-clears urgent flag)
        updater.update(work_item_id, status=new_status)

        # Add completion metadata using repository (to avoid reload/save issues)
        work_items_data_temp = repository.load_all()
        if "metadata" not in work_items_data_temp["work_items"][work_item_id]:
            work_items_data_temp["work_items"][work_item_id]["metadata"] = {}
        work_items_data_temp["work_items"][work_item_id]["metadata"]["completed_at"] = (
            datetime.now().isoformat()
        )
        repository.save_all(work_items_data_temp)

        logger.info(
            "Updated work item %s status: %s → %s (urgent flag auto-cleared if set)",
            work_item_id,
            previous_status,
            new_status,
        )
    else:
        new_status = WorkItemStatus.IN_PROGRESS.value

        # Use updater for consistency
        updater.update(work_item_id, status=new_status)

        logger.info(
            "Updated work item %s status: %s → %s",
            work_item_id,
            previous_status,
            new_status,
        )

    # Reload work items to get all updated data before calculating metadata counters
    # Use repository.load_all() instead of load_work_items() to avoid mock issues in tests
    work_items_data = repository.load_all()

    # Note: updater.update() handles update_history automatically
    # No need to manually append changes

    # Update metadata counters
    work_items = work_items_data.get("work_items", {})
    work_items_data["metadata"]["total_items"] = len(work_items)
    work_items_data["metadata"]["completed"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
    )
    work_items_data["metadata"]["in_progress"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
    )
    work_items_data["metadata"]["blocked"] = sum(
        1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
    )
    work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

    # Save updated work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Generate commit message (deprecated - commits should be made by Claude before /end)
    # Kept for backward compatibility with complete_git_workflow signature
    commit_message = generate_commit_message(status, work_item)

    # Complete git workflow (verify commits, push, optionally merge or create PR)
    # Note: This no longer creates commits - it verifies existing commits and pushes
    output.info("\nCompleting git workflow...")
    git_result = complete_git_workflow(work_item_id, commit_message, session_num)

    if git_result.get("success"):
        output.success(f"Git: {git_result.get('message', 'Success')}")
    else:
        output.warning(f"Git: {git_result.get('message', 'Failed')}")

    # Record commits to work item tracking (Bug #15 fix)
    record_session_commits(work_item_id)

    # Reload work_items_data to include newly recorded commits (Enhancement #11 Phase 1)
    work_items_data = load_work_items()

    # Generate comprehensive summary
    summary = generate_summary(status, work_items_data, gate_results, learnings)

    # Save summary
    history_dir = Path(".session/history")
    history_dir.mkdir(exist_ok=True)
    summary_file = history_dir / f"session_{session_num:03d}_summary.md"
    try:
        with open(summary_file, "w") as f:
            f.write(summary)
        logger.info(f"Saved session summary to {summary_file}")
    except OSError as e:
        logger.error(f"Failed to save session summary: {e}")
        output.warning(f"Failed to save session summary: {e}")

    # Auto-extract learnings from session artifacts (Bug #16 fix)
    # Now that commit and summary are created, we can extract from them
    auto_extract_learnings(session_num)

    # Print summary
    output.info("\n" + "=" * 50)
    output.info(summary)
    output.info("=" * 50)

    # Update status
    status["status"] = WorkItemStatus.COMPLETED.value
    status["completed_at"] = datetime.now().isoformat()
    try:
        with open(".session/tracking/status_update.json", "w") as f:
            json.dump(status, f, indent=2)
        logger.info("Updated session status to completed")
    except OSError as e:
        logger.error(f"Failed to update session status: {e}")
        output.warning(f"Failed to update session status: {e}")

    logger.info(f"Session {session_num} completed successfully")
    output.info("\n✓ Session completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
