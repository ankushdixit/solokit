#!/usr/bin/env python3
"""
Test Suite for Phase 5.7.5: Spec File Validation System

Tests the spec_validator module and its integration with briefing_generator and quality_gates.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

from solokit.core.exceptions import FileNotFoundError, SpecValidationError
from solokit.quality.gates import QualityGates
from solokit.work_items.spec_validator import (
    check_acceptance_criteria,
    check_deployment_subsections,
    check_required_sections,
    check_test_scenarios,
    get_validation_rules,
    validate_spec_file,
)


class TestSpecValidator:
    """Test suite for spec_validator.py module."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary .session/specs directory
        self.temp_dir = tempfile.mkdtemp()
        self.specs_dir = Path(self.temp_dir) / ".session" / "specs"
        self.specs_dir.mkdir(parents=True)

        # Create config.json with spec_completeness enabled
        config_dir = Path(self.temp_dir) / ".session"
        config_file = config_dir / "config.json"
        import json

        config_data = {"quality_gates": {"spec_completeness": {"enabled": True, "required": True}}}
        config_file.write_text(json.dumps(config_data, indent=2))

        # Change to temp directory
        self.original_dir = Path.cwd()
        import os

        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import os

        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding="utf-8")

    def test_get_validation_rules_feature(self):
        """Test: get_validation_rules returns correct rules for feature."""
        rules = get_validation_rules("feature")

        assert "required_sections" in rules
        assert "Overview" in rules["required_sections"]
        assert "Rationale" in rules["required_sections"]
        assert "Acceptance Criteria" in rules["required_sections"]
        assert "Implementation Details" in rules["required_sections"]
        assert "Testing Strategy" in rules["required_sections"]
        assert rules["special_requirements"]["acceptance_criteria_min_items"] == 3

        print("✓ Test 1: get_validation_rules returns correct rules for feature")

    def test_get_validation_rules_deployment(self):
        """Test: get_validation_rules returns correct rules for deployment."""
        rules = get_validation_rules("deployment")

        assert "required_sections" in rules
        assert "Deployment Scope" in rules["required_sections"]
        assert "Deployment Procedure" in rules["required_sections"]
        assert "Rollback Procedure" in rules["required_sections"]
        assert "Smoke Tests" in rules["required_sections"]
        assert "Acceptance Criteria" in rules["required_sections"]

        assert "deployment_procedure_subsections" in rules["special_requirements"]
        assert (
            "Pre-Deployment Checklist"
            in rules["special_requirements"]["deployment_procedure_subsections"]
        )
        assert (
            "Deployment Steps" in rules["special_requirements"]["deployment_procedure_subsections"]
        )
        assert (
            "Post-Deployment Steps"
            in rules["special_requirements"]["deployment_procedure_subsections"]
        )

        print("✓ Test 2: get_validation_rules returns correct rules for deployment")

    def test_check_required_sections_valid(self):
        """Test: check_required_sections passes for valid feature spec."""
        spec_content = """
# Feature: Test Feature

## Overview
This is the overview section.

## Rationale
This is the rationale.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Implementation details here.

## Testing Strategy
Testing strategy here.
"""

        errors = check_required_sections(spec_content, "feature")
        assert len(errors) == 0

        print("✓ Test 3: check_required_sections passes for valid feature spec")

    def test_check_required_sections_missing(self):
        """Test: check_required_sections detects missing sections."""
        spec_content = """
# Feature: Test Feature

## Overview
This is the overview section.

## Rationale
This is the rationale.
"""

        errors = check_required_sections(spec_content, "feature")
        assert len(errors) > 0
        assert any("Acceptance Criteria" in error for error in errors)
        assert any("Implementation Details" in error for error in errors)

        print("✓ Test 4: check_required_sections detects missing sections")

    def test_check_acceptance_criteria_valid(self):
        """Test: check_acceptance_criteria passes with 3+ items."""
        spec_content = """
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"""

        error = check_acceptance_criteria(spec_content, min_items=3)
        assert error is None

        print("✓ Test 5: check_acceptance_criteria passes with 3+ items")

    def test_check_acceptance_criteria_insufficient(self):
        """Test: check_acceptance_criteria fails with < 3 items."""
        spec_content = """
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
"""

        error = check_acceptance_criteria(spec_content, min_items=3)
        assert error is not None
        assert "at least 3 items" in error
        assert "found 2" in error

        print("✓ Test 6: check_acceptance_criteria fails with < 3 items")

    def test_check_test_scenarios_valid(self):
        """Test: check_test_scenarios passes with scenarios present."""
        spec_content = """
## Test Scenarios

### Scenario 1: User Login
Description here.

### Scenario 2: User Logout
Description here.
"""

        error = check_test_scenarios(spec_content, min_scenarios=1)
        assert error is None

        print("✓ Test 7: check_test_scenarios passes with scenarios present")

    def test_check_deployment_subsections_valid(self):
        """Test: check_deployment_subsections passes with all required subsections."""
        spec_content = """
## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Check 1

### Deployment Steps
Step 1

### Post-Deployment Steps
Step 1
"""

        errors = check_deployment_subsections(spec_content)
        assert len(errors) == 0

        print("✓ Test 8: check_deployment_subsections passes with all required subsections")

    def test_validate_spec_file_valid_feature(self):
        """Test: validate_spec_file passes for complete feature spec."""
        work_item_id = "test_feature_123"
        spec_content = """
# Feature: Test Feature

## Overview
Complete overview of the feature.

## Rationale
Why this feature is needed.

## Acceptance Criteria
- [ ] Criterion 1: Must do X
- [ ] Criterion 2: Must do Y
- [ ] Criterion 3: Must do Z

## Implementation Details
How to implement this.

## Testing Strategy
How to test this.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should not raise any exception for valid spec
        validate_spec_file(work_item_id, "feature")

        print("✓ Test 9: validate_spec_file passes for complete feature spec")

    def test_validate_spec_file_incomplete_deployment(self):
        """Test: validate_spec_file fails for incomplete deployment spec."""
        work_item_id = "test_deployment_456"
        spec_content = """
# Deployment: Test Deployment

## Deployment Scope
Scope here.

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Check 1

### Deployment Steps
Steps here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should raise SpecValidationError with multiple validation errors
        with pytest.raises(SpecValidationError) as exc_info:
            validate_spec_file(work_item_id, "deployment")

        error = exc_info.value
        validation_errors = error.context.get("validation_errors", [])
        assert len(validation_errors) > 0
        # Should be missing: Post-Deployment Steps, Rollback Procedure, Smoke Tests, Acceptance Criteria

        print("✓ Test 10: validate_spec_file fails for incomplete deployment spec")

    def test_validate_spec_file_not_found(self):
        """Test: validate_spec_file raises FileNotFoundError for missing spec."""
        work_item_id = "nonexistent_feature"

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            validate_spec_file(work_item_id, "feature")

        error = exc_info.value
        assert "nonexistent_feature" in str(error.context.get("file_path", ""))

        print("✓ Test 11: validate_spec_file raises FileNotFoundError for missing spec")

    def test_quality_gates_validate_spec_completeness(self):
        """Test: QualityGates.validate_spec_completeness integration."""
        work_item_id = "test_feature_789"
        spec_content = """
# Feature: Test Feature

## Overview
Complete overview.

## Rationale
Rationale here.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Create QualityGates instance with explicit config path
        config_path = Path(self.temp_dir) / ".session" / "config.json"
        gates = QualityGates(config_path=config_path)

        # Test with valid spec
        work_item = {"id": work_item_id, "type": "feature"}
        passed, results = gates.validate_spec_completeness(work_item)

        assert passed
        assert results["status"] == "passed"

        print("✓ Test 12 (BONUS): QualityGates.validate_spec_completeness integration works")

    def test_check_required_sections_empty_section(self):
        """Test: check_required_sections detects empty required sections."""
        spec_content = """
# Feature: Test Feature

## Overview


## Rationale
This is the rationale.

## Acceptance Criteria
- [ ] Criterion 1

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        errors = check_required_sections(spec_content, "feature")
        assert len(errors) > 0
        assert any("Overview" in error and "empty" in error for error in errors)

        print("✓ Test 13: check_required_sections detects empty sections")

    def test_check_acceptance_criteria_missing_section(self):
        """Test: check_acceptance_criteria returns None when section missing."""
        from solokit.work_items.spec_validator import check_acceptance_criteria

        spec_content = """
# Feature: Test Feature

## Overview
Overview here.
"""

        error = check_acceptance_criteria(spec_content, min_items=3)
        assert error is None

        print("✓ Test 14: check_acceptance_criteria handles missing section")

    def test_check_test_scenarios_missing_section(self):
        """Test: check_test_scenarios returns None when section missing."""
        spec_content = """
# Integration Test: Test

## Scope
Scope here.
"""

        error = check_test_scenarios(spec_content, min_scenarios=1)
        assert error is None

        print("✓ Test 15: check_test_scenarios handles missing section")

    def test_check_test_scenarios_insufficient(self):
        """Test: check_test_scenarios fails when not enough scenarios."""
        spec_content = """
## Test Scenarios

Some text without scenarios.
"""

        error = check_test_scenarios(spec_content, min_scenarios=1)
        assert error is not None
        assert "at least 1 scenario" in error

        print("✓ Test 16: check_test_scenarios detects insufficient scenarios")

    def test_check_smoke_tests_valid(self):
        """Test: check_smoke_tests passes with sufficient tests."""
        from solokit.work_items.spec_validator import check_smoke_tests

        spec_content = """
## Smoke Tests

### Test 1: Basic Functionality
Test description here.

### Test 2: Error Handling
Test description here.
"""

        error = check_smoke_tests(spec_content, min_tests=1)
        assert error is None

        print("✓ Test 17: check_smoke_tests passes with sufficient tests")

    def test_check_smoke_tests_insufficient(self):
        """Test: check_smoke_tests fails when not enough tests."""
        from solokit.work_items.spec_validator import check_smoke_tests

        spec_content = """
## Smoke Tests

Some text without test cases.
"""

        error = check_smoke_tests(spec_content, min_tests=1)
        assert error is not None
        assert "at least 1 test" in error

        print("✓ Test 18: check_smoke_tests detects insufficient tests")

    def test_check_smoke_tests_missing_section(self):
        """Test: check_smoke_tests returns None when section missing."""
        from solokit.work_items.spec_validator import check_smoke_tests

        spec_content = """
# Deployment: Test

## Deployment Scope
Scope here.
"""

        error = check_smoke_tests(spec_content, min_tests=1)
        assert error is None

        print("✓ Test 19: check_smoke_tests handles missing section")

    def test_check_deployment_subsections_missing_section(self):
        """Test: check_deployment_subsections returns empty when section missing."""
        spec_content = """
# Deployment: Test

## Deployment Scope
Scope here.
"""

        errors = check_deployment_subsections(spec_content)
        assert len(errors) == 0

        print("✓ Test 20: check_deployment_subsections handles missing section")

    def test_check_deployment_subsections_empty_subsection(self):
        """Test: check_deployment_subsections detects empty subsections."""
        spec_content = """
## Deployment Procedure

### Pre-Deployment Checklist


### Deployment Steps
Steps here.

### Post-Deployment Steps
Steps here.
"""

        errors = check_deployment_subsections(spec_content)
        assert len(errors) > 0
        assert any("Pre-Deployment Checklist" in error and "empty" in error for error in errors)

        print("✓ Test 21: check_deployment_subsections detects empty subsections")

    def test_check_rollback_subsections_valid(self):
        """Test: check_rollback_subsections passes with all subsections."""
        from solokit.work_items.spec_validator import check_rollback_subsections

        spec_content = """
## Rollback Procedure

### Rollback Triggers
- Trigger 1

### Rollback Steps
Step 1
"""

        errors = check_rollback_subsections(spec_content)
        assert len(errors) == 0

        print("✓ Test 22: check_rollback_subsections passes with valid subsections")

    def test_check_rollback_subsections_missing_subsection(self):
        """Test: check_rollback_subsections detects missing subsections."""
        from solokit.work_items.spec_validator import check_rollback_subsections

        spec_content = """
## Rollback Procedure

### Rollback Triggers
- Trigger 1
"""

        errors = check_rollback_subsections(spec_content)
        assert len(errors) > 0
        assert any("Rollback Steps" in error and "missing" in error for error in errors)

        print("✓ Test 22b: check_rollback_subsections detects missing subsections")

    def test_check_rollback_subsections_missing_section(self):
        """Test: check_rollback_subsections returns empty when section missing."""
        from solokit.work_items.spec_validator import check_rollback_subsections

        spec_content = """
# Deployment: Test

## Deployment Scope
Scope here.
"""

        errors = check_rollback_subsections(spec_content)
        assert len(errors) == 0

        print("✓ Test 23: check_rollback_subsections handles missing section")

    def test_check_rollback_subsections_empty_subsection(self):
        """Test: check_rollback_subsections detects empty subsections."""
        from solokit.work_items.spec_validator import check_rollback_subsections

        spec_content = """
## Rollback Procedure

### Rollback Triggers


### Rollback Steps
Steps here.
"""

        errors = check_rollback_subsections(spec_content)
        assert len(errors) > 0
        assert any("Rollback Triggers" in error and "empty" in error for error in errors)

        print("✓ Test 24: check_rollback_subsections detects empty subsections")

    def test_validate_spec_file_with_work_items_json(self):
        """Test: validate_spec_file loads spec path from work_items.json."""
        import json

        work_item_id = "test_feature_custom"
        custom_spec_path = ".session/custom_specs/special.md"
        spec_content = """
# Feature: Custom Path Feature

## Overview
Complete overview.

## Rationale
Rationale here.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        # Create custom spec directory and file
        custom_specs_dir = Path(self.temp_dir) / ".session" / "custom_specs"
        custom_specs_dir.mkdir(parents=True)
        spec_path = custom_specs_dir / "special.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        # Create work_items.json with custom spec_file path
        tracking_dir = Path(self.temp_dir) / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)
        work_items_file = tracking_dir / "work_items.json"
        work_items_data = {
            "work_items": {
                work_item_id: {
                    "id": work_item_id,
                    "type": "feature",
                    "spec_file": custom_spec_path,
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data, indent=2))

        # Should not raise any exception
        validate_spec_file(work_item_id, "feature")

        print("✓ Test 25: validate_spec_file loads spec path from work_items.json")

    def test_validate_spec_file_file_read_error(self):
        """Test: validate_spec_file raises FileOperationError when spec cannot be read."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        work_item_id = "test_feature_read_error"
        spec_content = """
# Feature: Test Feature

## Overview
Overview here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Mock read_text to raise OSError
        with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                validate_spec_file(work_item_id, "feature")

            error = exc_info.value
            assert "read" in str(error.context.get("operation", ""))

        print("✓ Test 26: validate_spec_file handles file read errors")

    def test_validate_spec_file_with_json_decode_error(self):
        """Test: validate_spec_file handles work_items.json decode errors gracefully."""

        work_item_id = "test_feature_json_error"
        spec_content = """
# Feature: Test Feature

## Overview
Overview here.

## Rationale
Rationale here.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Create invalid work_items.json
        tracking_dir = Path(self.temp_dir) / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)
        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text("invalid json content")

        # Should fall back to default spec path and pass validation
        validate_spec_file(work_item_id, "feature")

        print("✓ Test 27: validate_spec_file handles JSON decode errors gracefully")

    def test_format_validation_report_with_errors(self):
        """Test: format_validation_report creates detailed error report."""
        from solokit.work_items.spec_validator import format_validation_report

        work_item_id = "test_feature"
        work_item_type = "feature"
        errors = ["Missing section: Overview", "Section 'Rationale' is empty"]
        validation_error = SpecValidationError(work_item_id=work_item_id, errors=errors)

        report = format_validation_report(work_item_id, work_item_type, validation_error)

        assert work_item_id in report
        assert work_item_type in report
        assert "Missing section: Overview" in report
        assert "Section 'Rationale' is empty" in report
        assert "Suggestions" in report

        print("✓ Test 28: format_validation_report creates detailed error report")

    def test_format_validation_report_valid_spec(self):
        """Test: format_validation_report shows success message for valid spec."""
        from solokit.work_items.spec_validator import format_validation_report

        work_item_id = "test_feature"
        work_item_type = "feature"

        report = format_validation_report(work_item_id, work_item_type, None)

        assert work_item_id in report
        assert work_item_type in report
        assert "valid" in report.lower()

        print("✓ Test 29: format_validation_report shows success for valid spec")

    def test_get_validation_rules_unknown_type(self):
        """Test: get_validation_rules returns empty rules for unknown type."""
        rules = get_validation_rules("unknown_type")

        assert rules["required_sections"] == []
        assert rules["optional_sections"] == []
        assert rules["special_requirements"] == {}

        print("✓ Test 30: get_validation_rules handles unknown types")

    def test_validate_spec_file_integration_test_type(self):
        """Test: validate_spec_file validates integration_test type correctly."""
        work_item_id = "test_integration"
        spec_content = """
# Integration Test: API Tests

## Scope
Full API integration testing.

## Test Scenarios

### Scenario 1: User Registration
Test user registration flow.

## Performance Benchmarks
Response time < 200ms

## Environment Requirements
Docker, PostgreSQL

## Acceptance Criteria
- [ ] All endpoints tested
- [ ] Performance benchmarks met
- [ ] Error handling verified
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should not raise any exception
        validate_spec_file(work_item_id, "integration_test")

        print("✓ Test 31: validate_spec_file validates integration_test type")

    def test_validate_spec_file_integration_test_missing_scenarios(self):
        """Test: validate_spec_file fails for integration_test with missing scenarios."""
        work_item_id = "test_integration_bad"
        spec_content = """
# Integration Test: API Tests

## Scope
Full API integration testing.

## Test Scenarios

No scenarios here.

## Performance Benchmarks
Response time < 200ms

## Environment Requirements
Docker, PostgreSQL

## Acceptance Criteria
- [ ] All endpoints tested
- [ ] Performance benchmarks met
- [ ] Error handling verified
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should raise SpecValidationError
        with pytest.raises(SpecValidationError) as exc_info:
            validate_spec_file(work_item_id, "integration_test")

        error = exc_info.value
        validation_errors = error.context.get("validation_errors", [])
        assert any("scenario" in err.lower() for err in validation_errors)

        print("✓ Test 31b: validate_spec_file detects missing scenarios in integration_test")

    def test_validate_spec_file_deployment_missing_smoke_tests(self):
        """Test: validate_spec_file fails for deployment with missing smoke tests."""
        work_item_id = "test_deployment_bad"
        spec_content = """
# Deployment: Production Release

## Deployment Scope
Deploy v1.0 to production.

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database

### Deployment Steps
1. Deploy code

### Post-Deployment Steps
1. Verify functionality

## Rollback Procedure

### Rollback Triggers
- Service unavailable

### Rollback Steps
1. Restore backup

## Smoke Tests

No actual tests here.

## Acceptance Criteria
- [ ] All services running
- [ ] Smoke tests passing
- [ ] Monitoring active
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should raise SpecValidationError
        with pytest.raises(SpecValidationError) as exc_info:
            validate_spec_file(work_item_id, "deployment")

        error = exc_info.value
        validation_errors = error.context.get("validation_errors", [])
        assert any("smoke test" in err.lower() for err in validation_errors)

        print("✓ Test 31c: validate_spec_file detects missing smoke tests in deployment")

    def test_validate_spec_file_feature_insufficient_acceptance_criteria(self):
        """Test: validate_spec_file fails for feature with insufficient acceptance criteria."""
        work_item_id = "test_feature_bad_ac"
        spec_content = """
# Feature: Test Feature

## Overview
Complete overview.

## Rationale
Rationale here.

## Acceptance Criteria
- [ ] Only one criterion

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should raise SpecValidationError
        with pytest.raises(SpecValidationError) as exc_info:
            validate_spec_file(work_item_id, "feature")

        error = exc_info.value
        validation_errors = error.context.get("validation_errors", [])
        assert any("acceptance criteria" in err.lower() for err in validation_errors)

        print("✓ Test 31d: validate_spec_file detects insufficient acceptance criteria")

    def test_validate_spec_file_deployment_complete(self):
        """Test: validate_spec_file validates complete deployment spec."""
        work_item_id = "test_deployment_complete"
        spec_content = """
# Deployment: Production Release

## Deployment Scope
Deploy v1.0 to production.

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database
- [ ] Notify team

### Deployment Steps
1. Stop services
2. Deploy code
3. Run migrations

### Post-Deployment Steps
1. Start services
2. Verify functionality

## Rollback Procedure

### Rollback Triggers
- Service unavailable
- Data corruption

### Rollback Steps
1. Restore backup
2. Restart services

## Smoke Tests

### Test 1: Health Check
Verify service is responding.

### Test 2: Database Connection
Verify database connectivity.

## Acceptance Criteria
- [ ] All services running
- [ ] Smoke tests passing
- [ ] Monitoring active
"""

        self.create_spec_file(work_item_id, spec_content)

        # Should not raise any exception
        validate_spec_file(work_item_id, "deployment")

        print("✓ Test 32: validate_spec_file validates complete deployment spec")


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestSpecValidator()

    tests = [
        test_instance.test_get_validation_rules_feature,
        test_instance.test_get_validation_rules_deployment,
        test_instance.test_check_required_sections_valid,
        test_instance.test_check_required_sections_missing,
        test_instance.test_check_acceptance_criteria_valid,
        test_instance.test_check_acceptance_criteria_insufficient,
        test_instance.test_check_test_scenarios_valid,
        test_instance.test_check_deployment_subsections_valid,
        test_instance.test_validate_spec_file_valid_feature,
        test_instance.test_validate_spec_file_incomplete_deployment,
        test_instance.test_validate_spec_file_not_found,
        test_instance.test_quality_gates_validate_spec_completeness,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            test_instance.teardown_method()
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} errored: {e}")
            test_instance.teardown_method()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
