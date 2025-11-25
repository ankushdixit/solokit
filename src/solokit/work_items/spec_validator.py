#!/usr/bin/env python3
"""
Spec File Validation Module

Validates work item specification files for completeness and correctness.
Ensures specs have all required sections and meet quality standards.

Part of Phase 5.7.5: Spec File Validation System
"""

import re
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    FileNotFoundError,
    FileOperationError,
    SpecValidationError,
)
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import WorkItemType
from solokit.work_items.spec_parser import (
    extract_checklist,
    extract_subsection,
    parse_section,
    strip_html_comments,
)

logger = get_logger(__name__)
output = get_output()


def get_validation_rules(work_item_type: str) -> dict[str, Any]:
    """
    Get validation rules for a specific work item type.

    Args:
        work_item_type: Type of work item (feature, bug, refactor, security, integration_test, deployment)

    Returns:
        Dictionary with required_sections, optional_sections, and special_requirements
    """
    rules = {
        WorkItemType.FEATURE.value: {
            "required_sections": [
                "Overview",
                "Rationale",
                "Acceptance Criteria",
                "Implementation Details",
                "Testing Strategy",
            ],
            "optional_sections": [
                "User Story",
                "Documentation Updates",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {"acceptance_criteria_min_items": 3},
        },
        WorkItemType.BUG.value: {
            "required_sections": [
                "Description",
                "Steps to Reproduce",
                "Root Cause Analysis",
                "Fix Approach",
            ],
            "optional_sections": [
                "Expected Behavior",
                "Actual Behavior",
                "Impact",
                "Testing Strategy",
                "Prevention",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        WorkItemType.REFACTOR.value: {
            "required_sections": [
                "Overview",
                "Current State",
                "Proposed Refactor",
                "Scope",
            ],
            "optional_sections": [
                "Problems with Current Approach",
                "Implementation Plan",
                "Risk Assessment",
                "Success Criteria",
                "Testing Strategy",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        WorkItemType.SECURITY.value: {
            "required_sections": [
                "Security Issue",
                "Threat Model",
                "Attack Vector",
                "Mitigation Strategy",
                "Compliance",
            ],
            "optional_sections": [
                "Severity",
                "Affected Components",
                "Security Testing",
                "Post-Deployment",
                "Testing Strategy",
                "Acceptance Criteria",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        WorkItemType.INTEGRATION_TEST.value: {
            "required_sections": [
                "Scope",
                "Test Scenarios",
                "Performance Benchmarks",
                "Environment Requirements",
                "Acceptance Criteria",
            ],
            "optional_sections": ["API Contracts", "Dependencies", "Estimated Effort"],
            "special_requirements": {
                "test_scenarios_min": 1,
                "acceptance_criteria_min_items": 3,
            },
        },
        WorkItemType.DEPLOYMENT.value: {
            "required_sections": [
                "Deployment Scope",
                "Deployment Procedure",
                "Rollback Procedure",
                "Smoke Tests",
                "Acceptance Criteria",
            ],
            "optional_sections": [
                "Environment Configuration",
                "Monitoring & Alerting",
                "Post-Deployment Monitoring Period",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {
                "deployment_procedure_subsections": [
                    "Pre-Deployment Checklist",
                    "Deployment Steps",
                    "Post-Deployment Steps",
                ],
                "rollback_procedure_subsections": [
                    "Rollback Triggers",
                    "Rollback Steps",
                ],
                "smoke_tests_min": 1,
                "acceptance_criteria_min_items": 3,
            },
        },
    }

    return rules.get(
        work_item_type,
        {"required_sections": [], "optional_sections": [], "special_requirements": {}},
    )


def check_required_sections(spec_content: str, work_item_type: str) -> list[str]:
    """
    Check if all required sections are present and non-empty.

    Args:
        spec_content: Full spec file content
        work_item_type: Type of work item

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    rules = get_validation_rules(work_item_type)
    required_sections = rules.get("required_sections", [])

    # Strip HTML comments before parsing
    clean_content = strip_html_comments(spec_content)

    for section_name in required_sections:
        section_content = parse_section(clean_content, section_name)

        if section_content is None:
            errors.append(f"Missing required section: '{section_name}'")
        elif not section_content.strip():
            errors.append(f"Required section '{section_name}' is empty")

    return errors


def check_acceptance_criteria(spec_content: str, min_items: int = 3) -> str | None:
    """
    Check if Acceptance Criteria section has enough items.

    Args:
        spec_content: Full spec file content
        min_items: Minimum number of acceptance criteria items required (default: 3)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    ac_section = parse_section(clean_content, "Acceptance Criteria")

    if ac_section is None:
        return None  # Section doesn't exist, will be caught by check_required_sections

    checklist = extract_checklist(ac_section)

    if len(checklist) < min_items:
        return f"Acceptance Criteria must have at least {min_items} items (found {len(checklist)})"

    return None


def check_test_scenarios(spec_content: str, min_scenarios: int = 1) -> str | None:
    """
    Check if Test Scenarios section has enough scenarios.

    Args:
        spec_content: Full spec file content
        min_scenarios: Minimum number of test scenarios required (default: 1)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    scenarios_section = parse_section(clean_content, "Test Scenarios")

    if scenarios_section is None:
        return None  # Will be caught by check_required_sections

    # Count H3 headings that match "Scenario N:" pattern
    scenario_count = len(re.findall(r"###\s+Scenario\s+\d+:", scenarios_section, re.IGNORECASE))

    if scenario_count < min_scenarios:
        return f"Test Scenarios must have at least {min_scenarios} scenario(s) (found {scenario_count})"

    return None


def check_smoke_tests(spec_content: str, min_tests: int = 1) -> str | None:
    """
    Check if Smoke Tests section has enough test cases.

    Args:
        spec_content: Full spec file content
        min_tests: Minimum number of smoke tests required (default: 1)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    smoke_tests_section = parse_section(clean_content, "Smoke Tests")

    if smoke_tests_section is None:
        return None  # Will be caught by check_required_sections

    # Count H3 headings that match "Test N:" pattern
    test_count = len(re.findall(r"###\s+Test\s+\d+:", smoke_tests_section, re.IGNORECASE))

    if test_count < min_tests:
        return f"Smoke Tests must have at least {min_tests} test(s) (found {test_count})"

    return None


def check_deployment_subsections(spec_content: str) -> list[str]:
    """
    Check if Deployment Procedure has all required subsections.

    Args:
        spec_content: Full spec file content

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    clean_content = strip_html_comments(spec_content)
    deployment_section = parse_section(clean_content, "Deployment Procedure")

    if deployment_section is None:
        return []  # Will be caught by check_required_sections

    required_subsections = [
        "Pre-Deployment Checklist",
        "Deployment Steps",
        "Post-Deployment Steps",
    ]

    for subsection_name in required_subsections:
        subsection_content = extract_subsection(deployment_section, subsection_name)
        if subsection_content is None:
            errors.append(f"Deployment Procedure missing required subsection: '{subsection_name}'")
        elif not subsection_content.strip():
            errors.append(f"Deployment Procedure subsection '{subsection_name}' is empty")

    return errors


def check_rollback_subsections(spec_content: str) -> list[str]:
    """
    Check if Rollback Procedure has all required subsections.

    Args:
        spec_content: Full spec file content

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    clean_content = strip_html_comments(spec_content)
    rollback_section = parse_section(clean_content, "Rollback Procedure")

    if rollback_section is None:
        return []  # Will be caught by check_required_sections

    required_subsections = ["Rollback Triggers", "Rollback Steps"]

    for subsection_name in required_subsections:
        subsection_content = extract_subsection(rollback_section, subsection_name)
        if subsection_content is None:
            errors.append(f"Rollback Procedure missing required subsection: '{subsection_name}'")
        elif not subsection_content.strip():
            errors.append(f"Rollback Procedure subsection '{subsection_name}' is empty")

    return errors


@log_errors()
def validate_spec_file(work_item_id: str, work_item_type: str) -> None:
    """
    Validate a work item specification file for completeness and correctness.

    Args:
        work_item_id: ID of the work item
        work_item_type: Type of work item (feature, bug, refactor, security, integration_test, deployment)

    Raises:
        FileNotFoundError: If spec file doesn't exist
        FileOperationError: If spec file cannot be read
        SpecValidationError: If spec validation fails (contains list of validation errors)
    """
    # Try to load work items to get spec_file path
    # If work_items.json doesn't exist, fallback to default pattern (for backwards compatibility/tests)
    import json

    work_items_file = Path(".session/tracking/work_items.json")
    spec_file_path = None

    if work_items_file.exists():
        # Load from work_items.json (preferred method)
        try:
            with open(work_items_file) as f:
                work_items_data = json.load(f)

            if work_item_id in work_items_data.get("work_items", {}):
                work_item = work_items_data["work_items"][work_item_id]
                spec_file_path = work_item.get("spec_file")
        except (OSError, json.JSONDecodeError):
            # If loading fails, fallback to default pattern
            pass

    # Fallback to default pattern if not found in work_items.json
    if not spec_file_path:
        spec_file_path = f".session/specs/{work_item_id}.md"

    spec_path = Path(spec_file_path)

    if not spec_path.exists():
        raise FileNotFoundError(file_path=str(spec_path), file_type="spec")

    # Read spec content
    try:
        spec_content = spec_path.read_text(encoding="utf-8")
    except OSError as e:
        raise FileOperationError(
            operation="read", file_path=str(spec_path), details=str(e), cause=e
        )

    # Collect all errors
    errors = []

    # Check required sections
    errors.extend(check_required_sections(spec_content, work_item_type))

    # Get special requirements for this work item type
    rules = get_validation_rules(work_item_type)
    special_requirements = rules.get("special_requirements", {})

    # Check acceptance criteria (if required)
    if "acceptance_criteria_min_items" in special_requirements:
        min_items = special_requirements["acceptance_criteria_min_items"]
        ac_error = check_acceptance_criteria(spec_content, min_items)
        if ac_error:
            errors.append(ac_error)

    # Check test scenarios (for integration_test)
    if "test_scenarios_min" in special_requirements:
        min_scenarios = special_requirements["test_scenarios_min"]
        scenarios_error = check_test_scenarios(spec_content, min_scenarios)
        if scenarios_error:
            errors.append(scenarios_error)

    # Check smoke tests (for deployment)
    if "smoke_tests_min" in special_requirements:
        min_tests = special_requirements["smoke_tests_min"]
        smoke_error = check_smoke_tests(spec_content, min_tests)
        if smoke_error:
            errors.append(smoke_error)

    # Check deployment subsections (for deployment)
    if "deployment_procedure_subsections" in special_requirements:
        errors.extend(check_deployment_subsections(spec_content))

    # Check rollback subsections (for deployment)
    if "rollback_procedure_subsections" in special_requirements:
        errors.extend(check_rollback_subsections(spec_content))

    # Raise SpecValidationError if any validation errors found
    if errors:
        raise SpecValidationError(work_item_id=work_item_id, errors=errors)


def format_validation_report(
    work_item_id: str, work_item_type: str, validation_error: SpecValidationError | None = None
) -> str:
    """
    Format validation errors into a human-readable report.

    Args:
        work_item_id: ID of the work item
        work_item_type: Type of work item
        validation_error: SpecValidationError containing validation errors, None if valid

    Returns:
        Formatted validation report
    """
    if not validation_error:
        return f"✅ Spec file for '{work_item_id}' ({work_item_type}) is valid"

    errors = validation_error.context.get("validation_errors", [])

    report = f"❌ Spec file for '{work_item_id}' ({work_item_type}) has validation errors:\n\n"

    for i, error in enumerate(errors, 1):
        report += f"{i}. {error}\n"

    report += "\n💡 Suggestions:\n"
    report += f"- Review the template at templates/{work_item_type}_spec.md\n"
    report += "- Check docs/spec-template-structure.md for section requirements\n"
    report += f"- Edit .session/specs/{work_item_id}.md to add missing sections\n"

    return report


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        output.info("Usage: python3 spec_validator.py <work_item_id> <work_item_type>")
        output.info("Example: python3 spec_validator.py feature_websocket_notifications feature")
        sys.exit(1)

    work_item_id = sys.argv[1]
    work_item_type = sys.argv[2]

    try:
        logger.info("Validating spec file for %s (%s)", work_item_id, work_item_type)
        validate_spec_file(work_item_id, work_item_type)
        report = format_validation_report(work_item_id, work_item_type)
        output.info(report)
        logger.info("Spec validation successful")
        sys.exit(0)
    except SpecValidationError as e:
        logger.warning("Spec validation failed: %s", e.message)
        report = format_validation_report(work_item_id, work_item_type, e)
        output.info(report)
        sys.exit(e.exit_code)
    except (FileNotFoundError, FileOperationError) as e:
        logger.error("File operation error during validation", exc_info=True)
        output.error(f"Error: {e.message}")
        if e.remediation:
            output.info(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
