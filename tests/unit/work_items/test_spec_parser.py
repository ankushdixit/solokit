"""Unit tests for spec_parser module.

This module tests the spec_parser.py module's ability to extract structured data
from work item specification markdown files.
"""

import pytest

from solokit.core.exceptions import FileNotFoundError, ValidationError
from solokit.work_items import spec_parser


class TestStripHtmlComments:
    """Tests for strip_html_comments function."""

    def test_strip_html_comments_single_line(self):
        """Test that HTML comments are stripped from single line content."""
        # Arrange
        content = """# Feature: Test
<!-- This is a comment -->
## Overview
This is content."""

        # Act
        result = spec_parser.strip_html_comments(content)

        # Assert
        assert "<!--" not in result
        assert "-->" not in result
        assert "This is content." in result

    def test_strip_html_comments_multiline(self):
        """Test that multiline HTML comments are stripped correctly."""
        # Arrange
        content = """# Feature: Test
<!-- Another comment
spanning multiple lines -->
More content."""

        # Act
        result = spec_parser.strip_html_comments(content)

        # Assert
        assert "<!--" not in result
        assert "-->" not in result
        assert "More content." in result

    def test_strip_html_comments_multiple(self):
        """Test that multiple HTML comments are stripped."""
        # Arrange
        content = """<!-- Comment 1 -->
Content 1
<!-- Comment 2 -->
Content 2
<!-- Comment 3 -->"""

        # Act
        result = spec_parser.strip_html_comments(content)

        # Assert
        assert "<!--" not in result
        assert "-->" not in result
        assert "Content 1" in result
        assert "Content 2" in result


class TestParseSection:
    """Tests for parse_section function."""

    def test_parse_section_extracts_overview(self):
        """Test that parse_section correctly extracts Overview section."""
        # Arrange
        content = """# Feature: Test

## Overview
This is the overview section.
It has multiple lines.

## Rationale
This is the rationale section."""

        # Act
        overview = spec_parser.parse_section(content, "Overview")

        # Assert
        assert overview == "This is the overview section.\nIt has multiple lines."

    def test_parse_section_extracts_rationale(self):
        """Test that parse_section correctly extracts Rationale section."""
        # Arrange
        content = """# Feature: Test

## Overview
Overview content.

## Rationale
This is the rationale section.

## Implementation Details
Implementation content."""

        # Act
        rationale = spec_parser.parse_section(content, "Rationale")

        # Assert
        assert rationale == "This is the rationale section."

    def test_parse_section_returns_none_for_missing(self):
        """Test that parse_section returns None for missing section."""
        # Arrange
        content = """# Feature: Test

## Overview
Overview content."""

        # Act
        missing = spec_parser.parse_section(content, "NonExistent")

        # Assert
        assert missing is None

    def test_parse_section_handles_empty_section(self):
        """Test that parse_section handles empty sections."""
        # Arrange
        content = """# Feature: Test

## Overview

## Rationale
Rationale content."""

        # Act
        overview = spec_parser.parse_section(content, "Overview")

        # Assert
        assert overview == "" or overview is None


class TestExtractSubsection:
    """Tests for extract_subsection function."""

    def test_extract_subsection_approach(self):
        """Test that extract_subsection extracts Approach subsection."""
        # Arrange
        section_content = """### Approach
Use WebSockets for real-time updates.

### Components Affected
- Frontend
- Backend"""

        # Act
        approach = spec_parser.extract_subsection(section_content, "Approach")

        # Assert
        assert "WebSockets" in approach

    def test_extract_subsection_components(self):
        """Test that extract_subsection extracts Components Affected subsection."""
        # Arrange
        section_content = """### Approach
Use WebSockets.

### Components Affected
- Frontend
- Backend

### API Changes
New endpoints here."""

        # Act
        components = spec_parser.extract_subsection(section_content, "Components Affected")

        # Assert
        assert "Frontend" in components
        assert "Backend" in components

    def test_extract_subsection_returns_none_for_missing(self):
        """Test that extract_subsection returns None for missing subsection."""
        # Arrange
        section_content = """### Approach
Use WebSockets."""

        # Act
        missing = spec_parser.extract_subsection(section_content, "NonExistent")

        # Assert
        assert missing is None


class TestExtractChecklist:
    """Tests for extract_checklist function."""

    def test_extract_checklist_mixed_checked_unchecked(self):
        """Test that extract_checklist extracts items with correct checked state."""
        # Arrange
        content = """## Acceptance Criteria

- [ ] First item unchecked
- [x] Second item checked
- [ ] Third item unchecked
- [X] Fourth item checked (uppercase)"""

        # Act
        checklist = spec_parser.extract_checklist(content)

        # Assert
        assert len(checklist) == 4
        assert checklist[0] == {"text": "First item unchecked", "checked": False}
        assert checklist[1] == {"text": "Second item checked", "checked": True}
        assert checklist[2] == {"text": "Third item unchecked", "checked": False}
        assert checklist[3] == {"text": "Fourth item checked (uppercase)", "checked": True}

    def test_extract_checklist_empty_content(self):
        """Test that extract_checklist handles content without checklist items."""
        # Arrange
        content = """## Acceptance Criteria

Some other text without checkboxes."""

        # Act
        checklist = spec_parser.extract_checklist(content)

        # Assert
        assert len(checklist) == 0

    def test_extract_checklist_counts_checked_items(self):
        """Test that checklist correctly counts checked items."""
        # Arrange
        content = """- [ ] Item 1
- [x] Item 2
- [x] Item 3
- [ ] Item 4"""

        # Act
        checklist = spec_parser.extract_checklist(content)

        # Assert
        checked_count = sum(1 for item in checklist if item["checked"])
        assert checked_count == 2


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks function."""

    def test_extract_code_blocks_with_language(self):
        """Test that extract_code_blocks extracts code blocks with language specified."""
        # Arrange
        content = """## Implementation

```typescript
interface User {
  id: string;
  name: string;
}
```"""

        # Act
        code_blocks = spec_parser.extract_code_blocks(content)

        # Assert
        assert len(code_blocks) == 1
        assert code_blocks[0]["language"] == "typescript"
        assert "interface User" in code_blocks[0]["code"]

    def test_extract_code_blocks_without_language(self):
        """Test that extract_code_blocks handles code blocks without language."""
        # Arrange
        content = """```
Plain code block
```"""

        # Act
        code_blocks = spec_parser.extract_code_blocks(content)

        # Assert
        assert len(code_blocks) == 1
        assert code_blocks[0]["language"] == "text"

    def test_extract_code_blocks_multiple(self):
        """Test that extract_code_blocks extracts multiple code blocks."""
        # Arrange
        content = """```typescript
interface User {}
```

Some text here.

```bash
npm install
npm test
```"""

        # Act
        code_blocks = spec_parser.extract_code_blocks(content)

        # Assert
        assert len(code_blocks) == 2
        assert code_blocks[0]["language"] == "typescript"
        assert code_blocks[1]["language"] == "bash"
        assert "npm install" in code_blocks[1]["code"]


class TestExtractListItems:
    """Tests for extract_list_items function."""

    def test_extract_list_items_unordered(self):
        """Test that extract_list_items extracts unordered list items."""
        # Arrange
        content = """## Components

- Frontend module
- Backend API
* Database schema
+ Configuration"""

        # Act
        items = spec_parser.extract_list_items(content)

        # Assert
        assert "Frontend module" in items
        assert "Backend API" in items
        assert "Database schema" in items
        assert "Configuration" in items

    def test_extract_list_items_ordered(self):
        """Test that extract_list_items extracts ordered list items."""
        # Arrange
        content = """## Steps

1. First step
2. Second step
3. Third step"""

        # Act
        items = spec_parser.extract_list_items(content)

        # Assert
        assert "First step" in items
        assert "Second step" in items
        assert "Third step" in items

    def test_extract_list_items_mixed(self):
        """Test that extract_list_items extracts both ordered and unordered items."""
        # Arrange
        content = """## Items

- Unordered item
1. Ordered item
* Another unordered"""

        # Act
        items = spec_parser.extract_list_items(content)

        # Assert
        assert len(items) >= 3


class TestParseFeatureSpec:
    """Tests for parse_feature_spec function."""

    def test_parse_feature_spec_complete(self):
        """Test that parse_feature_spec parses complete feature specification."""
        # Arrange
        content = """# Feature: Real-time Notifications

## Overview
Add real-time notifications to the dashboard.

## User Story
As a user, I want real-time notifications so that I stay updated.

## Rationale
Users need immediate feedback.

## Acceptance Criteria

- [ ] Notifications appear in real-time
- [ ] Users can dismiss notifications
- [x] Tests pass

## Implementation Details

### Approach
Use WebSockets for bidirectional communication.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- WebSocket message routing based on event type
- JSON serialization/deserialization
- Event queue management

### API Changes

```typescript
interface Notification {
  id: string;
  message: string;
}
```

## Testing Strategy
Write integration tests for WebSocket connections.

## Dependencies
Requires Socket.IO library.

## Estimated Effort
2 sessions
"""

        # Act
        result = spec_parser.parse_feature_spec(content)

        # Assert
        assert result["overview"] == "Add real-time notifications to the dashboard."
        assert "real-time notifications" in result["user_story"]
        assert "immediate feedback" in result["rationale"]
        assert len(result["acceptance_criteria"]) == 3
        assert not result["acceptance_criteria"][0]["checked"]
        assert result["acceptance_criteria"][2]["checked"]
        assert result["implementation_details"] is not None
        assert "WebSockets" in result["implementation_details"]["approach"]
        assert result["implementation_details"]["llm_processing_config"] is not None
        assert "Deterministic" in result["implementation_details"]["llm_processing_config"]
        assert len(result["implementation_details"]["code_blocks"]) == 1
        assert "WebSocket" in result["testing_strategy"]
        assert "Socket.IO" in result["dependencies"]
        assert "2 sessions" in result["estimated_effort"]

    def test_parse_feature_spec_minimal(self):
        """Test that parse_feature_spec handles minimal feature spec."""
        # Arrange
        content = """# Feature: Minimal Feature

## Overview
Just an overview.

## Acceptance Criteria
- [ ] One criterion"""

        # Act
        result = spec_parser.parse_feature_spec(content)

        # Assert
        assert result["overview"] == "Just an overview."
        assert len(result["acceptance_criteria"]) == 1


class TestParseBugSpec:
    """Tests for parse_bug_spec function."""

    def test_parse_bug_spec_complete(self):
        """Test that parse_bug_spec parses complete bug specification."""
        # Arrange
        content = """# Bug: Session Timeout

## Description
Users are logged out unexpectedly.

## Steps to Reproduce
1. Login to the application
2. Wait 5 minutes
3. Try to perform an action

## Expected Behavior
Session should remain active.

## Actual Behavior
User is logged out after 5 minutes.

## Impact
**Severity:** High

## Root Cause Analysis

### Investigation
Reviewed session management code.

### Root Cause
Session timeout is set to 5 minutes instead of 30.

### Why It Happened
Configuration error during deployment.

## Fix Approach
Update session timeout configuration to 30 minutes.

## Prevention
Add configuration validation tests.

## Testing Strategy
Test session timeout with various durations.

## Dependencies
None

## Estimated Effort
1 session
"""

        # Act
        result = spec_parser.parse_bug_spec(content)

        # Assert
        assert "logged out unexpectedly" in result["description"]
        assert "Wait 5 minutes" in result["steps_to_reproduce"]
        assert "remain active" in result["expected_behavior"]
        assert "logged out after 5 minutes" in result["actual_behavior"]
        assert "High" in result["impact"]
        assert result["root_cause_analysis"] is not None
        assert "session management" in result["root_cause_analysis"]["investigation"]
        assert "5 minutes instead of 30" in result["root_cause_analysis"]["root_cause"]
        assert "Configuration error" in result["root_cause_analysis"]["why_it_happened"]
        assert "30 minutes" in result["fix_approach"]
        assert "validation tests" in result["prevention"]


class TestParseRefactorSpec:
    """Tests for parse_refactor_spec function."""

    def test_parse_refactor_spec_complete(self):
        """Test that parse_refactor_spec parses complete refactor specification."""
        # Arrange
        content = """# Refactor: Dependency Injection

## Overview
Refactor service instantiation to use dependency injection.

## Current State
Services are instantiated with `new` keyword throughout the codebase.

## Problems with Current Approach
- Hard to test
- Tight coupling
- No lifecycle management

## Proposed Refactor

### New Approach
Use a DI container to manage service instances.

### Benefits
- Easier testing with mocks
- Loose coupling
- Better lifecycle control

### Trade-offs
- Additional complexity
- Learning curve

## Implementation Plan
1. Install DI library
2. Create container configuration
3. Refactor services one by one

## Scope

### In Scope
- User service
- Auth service
- Database service

### Out of Scope
- UI components
- External libraries

## Risk Assessment
**Risk Level:** Medium

## Acceptance Criteria
- [ ] All services use DI
- [ ] Tests pass
- [x] Documentation updated

## Testing Strategy
Mock services in unit tests.

## Dependencies
Requires DI library installation.

## Estimated Effort
3 sessions
"""

        # Act
        result = spec_parser.parse_refactor_spec(content)

        # Assert
        assert "dependency injection" in result["overview"]
        assert "new` keyword" in result["current_state"]
        assert "Hard to test" in result["problems"]
        assert result["proposed_refactor"] is not None
        assert "DI container" in result["proposed_refactor"]["new_approach"]
        assert "Easier testing" in result["proposed_refactor"]["benefits"]
        assert "complexity" in result["proposed_refactor"]["trade_offs"]
        assert "Install DI library" in result["implementation_plan"]
        assert result["scope"] is not None
        assert "User service" in result["scope"]["in_scope"]
        assert "UI components" in result["scope"]["out_of_scope"]
        assert "Medium" in result["risk_assessment"]
        assert len(result["acceptance_criteria"]) == 3


class TestParseSecuritySpec:
    """Tests for parse_security_spec function."""

    def test_parse_security_spec_complete(self):
        """Test that parse_security_spec parses complete security specification."""
        # Arrange
        content = """# Security: SQL Injection Vulnerability

## Security Issue
SQL injection vulnerability in user search endpoint.

## Severity
**CVSS Score:** 8.5 (High)

- [x] Critical
- [ ] High
- [ ] Medium

## Affected Components
- User API v2.1.0
- Database layer

## Threat Model

### Assets at Risk
- User database
- Personal information

### Threat Actors
- External attackers
- Malicious users

### Attack Scenarios
SQL injection through search parameter.

## Attack Vector
Unsanitized input in SQL query.

## Mitigation Strategy
Use parameterized queries for all database operations.

## Security Testing

### Automated Security Testing
Run SQL injection scanners.

### Manual Security Testing
Attempt injection attacks manually.

### Test Cases
- [ ] Test with malicious SQL
- [ ] Test with special characters
- [x] Verify parameterized queries

## Compliance
- [ ] OWASP Top 10
- [x] CWE-89
- [ ] PCI DSS

## Acceptance Criteria
- [ ] No SQL injection vulnerabilities
- [ ] All queries parameterized

## Post-Deployment
- [ ] Monitor for suspicious queries
- [ ] Set up alerts

## Dependencies
None

## Estimated Effort
1 session
"""

        # Act
        result = spec_parser.parse_security_spec(content)

        # Assert
        assert "SQL injection" in result["security_issue"]
        assert "8.5" in result["severity"]
        assert "User API" in result["affected_components"]
        assert result["threat_model"] is not None
        assert "User database" in result["threat_model"]["assets_at_risk"]
        assert "External attackers" in result["threat_model"]["threat_actors"]
        assert "search parameter" in result["threat_model"]["attack_scenarios"]
        assert "Unsanitized input" in result["attack_vector"]
        assert "parameterized queries" in result["mitigation_strategy"]
        assert result["security_testing"] is not None
        assert "SQL injection scanners" in result["security_testing"]["automated"]
        assert len(result["security_testing"]["checklist"]) == 3
        assert len(result["compliance"]) >= 2
        assert len(result["acceptance_criteria"]) == 2
        assert len(result["post_deployment"]) == 2


class TestParseIntegrationTestSpec:
    """Tests for parse_integration_test_spec function."""

    def test_parse_integration_test_spec_complete(self):
        """Test that parse_integration_test_spec parses complete integration test specification."""
        # Arrange
        content = """# Integration Test: Order Processing Flow

## Scope
Test the complete order processing workflow.

## Test Scenarios

### Scenario 1: Successful Order
User places an order and receives confirmation.

### Scenario 2: Payment Failure
User's payment fails and order is cancelled.

### Scenario 3: Inventory Check
Order fails if item is out of stock.

## Performance Benchmarks
**Response Time:** < 200ms
**Throughput:** 100 orders/second

## API Contracts
Order API v2.0 contracts.

## Environment Requirements
- PostgreSQL 14
- Redis 6.2
- Node.js 18

## Acceptance Criteria
- [ ] All scenarios pass
- [ ] Performance benchmarks met
- [x] Environment setup automated

## Dependencies
Requires order service deployment.

## Estimated Effort
2 sessions
"""

        # Act
        result = spec_parser.parse_integration_test_spec(content)

        # Assert
        assert "order processing workflow" in result["scope"]
        assert len(result["test_scenarios"]) == 3
        assert result["test_scenarios"][0]["name"] == "Scenario 1: Successful Order"
        assert "confirmation" in result["test_scenarios"][0]["content"]
        assert result["test_scenarios"][1]["name"] == "Scenario 2: Payment Failure"
        assert result["test_scenarios"][2]["name"] == "Scenario 3: Inventory Check"
        assert "200ms" in result["performance_benchmarks"]
        assert "100 orders/second" in result["performance_benchmarks"]
        assert "Order API" in result["api_contracts"]
        assert "PostgreSQL" in result["environment_requirements"]
        assert len(result["acceptance_criteria"]) == 3


class TestParseDeploymentSpec:
    """Tests for parse_deployment_spec function."""

    def test_parse_deployment_spec_complete(self):
        """Test that parse_deployment_spec parses complete deployment specification."""
        # Arrange
        content = """# Deployment: Production Release v2.0

## Deployment Scope
**Application:** Order API
**Version:** 2.0.0
**Environment:** Production

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database
- [ ] Notify stakeholders

### Deployment Steps
1. Pull latest code
2. Build Docker image
3. Deploy to production

### Post-Deployment Steps
1. Run smoke tests
2. Verify metrics

## Environment Configuration
**Database URL:** postgresql://prod.example.com
**Redis URL:** redis://prod-cache.example.com

## Rollback Procedure

### Rollback Triggers
- Critical bugs detected
- Performance degradation

### Rollback Steps
1. Revert to previous Docker image
2. Clear cache
3. Verify rollback successful

## Smoke Tests

### Test 1: Health Check
Check /health endpoint returns 200.

### Test 2: Order Creation
Create a test order and verify response.

## Monitoring & Alerting
**Dashboard:** https://grafana.example.com/dashboard
**Alerts:** PagerDuty

## Post-Deployment Monitoring Period
**Soak Time:** 24 hours

## Acceptance Criteria
- [ ] All smoke tests pass
- [ ] No critical errors in logs
- [x] Monitoring configured

## Dependencies
None

## Estimated Effort
1 session
"""

        # Act
        result = spec_parser.parse_deployment_spec(content)

        # Assert
        assert "Order API" in result["deployment_scope"]
        assert result["deployment_procedure"] is not None
        assert "Backup database" in result["deployment_procedure"]["pre_deployment"]
        assert "Pull latest code" in result["deployment_procedure"]["deployment_steps"]
        assert "Run smoke tests" in result["deployment_procedure"]["post_deployment"]
        assert "postgresql://" in result["environment_configuration"]
        assert result["rollback_procedure"] is not None
        assert "Critical bugs" in result["rollback_procedure"]["triggers"]
        assert "Revert to previous" in result["rollback_procedure"]["steps"]
        assert len(result["smoke_tests"]) == 2
        assert result["smoke_tests"][0]["name"] == "Test 1: Health Check"
        assert "/health" in result["smoke_tests"][0]["content"]
        assert "grafana" in result["monitoring"]
        assert "24 hours" in result["monitoring_period"]
        assert len(result["acceptance_criteria"]) == 3


class TestParseSpecFile:
    """Tests for parse_spec_file function."""

    def test_parse_spec_file_feature(self, temp_project_dir, monkeypatch):
        """Test that parse_spec_file parses feature spec file end-to-end."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# Feature: Test Feature

<!-- Template instructions here -->

## Overview
This is a test feature.

## Acceptance Criteria
- [ ] First criterion
- [ ] Second criterion

## Dependencies
None
"""

        spec_file = specs_dir / "feature_test.md"
        spec_file.write_text(spec_content)

        # Act
        result = spec_parser.parse_spec_file("feature_test")

        # Assert
        assert result["_meta"]["work_item_id"] == "feature_test"
        assert result["_meta"]["work_type"] == "feature"
        assert result["_meta"]["name"] == "Test Feature"
        assert result["overview"] == "This is a test feature."
        assert len(result["acceptance_criteria"]) == 2
        assert result["dependencies"] == "None"

    def test_parse_spec_file_not_found(self, temp_project_dir, monkeypatch):
        """Test that parse_spec_file raises FileNotFoundError for missing file."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            spec_parser.parse_spec_file("nonexistent_file")

        # Verify exception details
        assert "nonexistent_file.md" in str(exc_info.value)

    def test_parse_spec_file_invalid_heading(self, temp_project_dir, monkeypatch):
        """Test that parse_spec_file raises ValidationError for invalid heading format."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "invalid_test.md"
        spec_file.write_text("Invalid content without proper heading")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            spec_parser.parse_spec_file("invalid_test")

        # Verify exception details
        assert "Missing H1 heading" in str(exc_info.value)
        assert exc_info.value.code.name == "SPEC_VALIDATION_FAILED"

    def test_parse_spec_file_unknown_type(self, temp_project_dir, monkeypatch):
        """Test that parse_spec_file raises ValidationError for unknown work item type."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "unknown_test.md"
        spec_file.write_text("# UnknownType: Test\n\nSome content")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            spec_parser.parse_spec_file("unknown_test")

        # Verify exception details
        assert "Unknown work item type" in str(exc_info.value)
        assert exc_info.value.code.name == "INVALID_WORK_ITEM_TYPE"
        assert "unknowntype" in exc_info.value.context["work_type"]


class TestLlmProcessingConfigVariations:
    """Tests for LLM/Processing Configuration subsection variations."""

    def test_llm_based_configuration(self):
        """Test that parse_feature_spec handles LLM-based configuration."""
        # Arrange
        llm_content = """# Feature: LLM-based Feature

## Overview
Test feature with LLM processing.

## Acceptance Criteria
- [ ] Test criterion

## Implementation Details

### Approach
Use LLM for processing.

### LLM/Processing Configuration

**Type:** LLM-based (DSPy)

**DSPy Signature:**
```python
class TestSignature(dspy.Signature):
    \"\"\"Test signature.\"\"\"

    input_field = dspy.InputField(desc="Input")
    output_field = dspy.OutputField(desc="Output")
```

**LLM Provider:** Google AI Studio (Gemini 2.5 Flash)

**LLM Usage:**
- Processes input data
- Generates structured output
"""

        # Act
        result = spec_parser.parse_feature_spec(llm_content)

        # Assert
        assert result["implementation_details"]["llm_processing_config"] is not None
        assert "LLM-based" in result["implementation_details"]["llm_processing_config"]
        assert "DSPy" in result["implementation_details"]["llm_processing_config"]
        assert "Google AI Studio" in result["implementation_details"]["llm_processing_config"]

    def test_deterministic_configuration(self):
        """Test that parse_feature_spec handles deterministic configuration."""
        # Arrange
        deterministic_content = """# Feature: Deterministic Feature

## Overview
Test feature with deterministic processing.

## Acceptance Criteria
- [ ] Test criterion

## Implementation Details

### Approach
Use algorithms for processing.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Parse data using regex
- Apply business rules
- Transform output
"""

        # Act
        result = spec_parser.parse_feature_spec(deterministic_content)

        # Assert
        assert result["implementation_details"]["llm_processing_config"] is not None
        assert "Deterministic" in result["implementation_details"]["llm_processing_config"]
        assert "No LLM" in result["implementation_details"]["llm_processing_config"]
        assert "regex" in result["implementation_details"]["llm_processing_config"]

    def test_external_api_configuration(self):
        """Test that parse_feature_spec handles external API configuration."""
        # Arrange
        api_content = """# Feature: API Integration Feature

## Overview
Test feature with external API.

## Acceptance Criteria
- [ ] Test criterion

## Implementation Details

### Approach
Integrate with external API.

### LLM/Processing Configuration

**Type:** External API Integration (No LLM)

**API Provider:** ExternalService API

**Processing Type:**
- Make API calls to external service
- Transform API responses
- Handle rate limiting

**Rate Limits:** 1000 requests/hour
"""

        # Act
        result = spec_parser.parse_feature_spec(api_content)

        # Assert
        assert result["implementation_details"]["llm_processing_config"] is not None
        assert (
            "External API Integration" in result["implementation_details"]["llm_processing_config"]
        )
        assert "ExternalService API" in result["implementation_details"]["llm_processing_config"]
        assert "Rate Limits" in result["implementation_details"]["llm_processing_config"]

    def test_not_applicable_configuration(self):
        """Test that parse_feature_spec handles Not Applicable configuration."""
        # Arrange
        na_content = """# Feature: Standard Feature

## Overview
Test feature without special processing.

## Acceptance Criteria
- [ ] Test criterion

## Implementation Details

### Approach
Standard CRUD operations.

### LLM/Processing Configuration

Not Applicable - Standard application logic without LLM or special processing requirements.
"""

        # Act
        result = spec_parser.parse_feature_spec(na_content)

        # Assert
        assert result["implementation_details"]["llm_processing_config"] is not None
        assert "Not Applicable" in result["implementation_details"]["llm_processing_config"]

    def test_missing_llm_config_subsection(self):
        """Test that parse_feature_spec handles missing LLM/Processing Configuration subsection (backward compatibility)."""
        # Arrange
        missing_content = """# Feature: Legacy Feature

## Overview
Test feature without LLM/Processing Configuration subsection.

## Acceptance Criteria
- [ ] Test criterion

## Implementation Details

### Approach
Legacy approach without LLM config subsection.

### Components Affected
- Some component
"""

        # Act
        result = spec_parser.parse_feature_spec(missing_content)

        # Assert
        assert result["implementation_details"]["llm_processing_config"] is None


class TestMissingSectionsReturnNone:
    """Tests for missing sections returning None gracefully."""

    def test_minimal_feature_spec(self):
        """Test that parse_feature_spec handles minimal spec with missing sections."""
        # Arrange
        content = """# Feature: Minimal Feature

## Overview
Just an overview.

## Acceptance Criteria
- [ ] One criterion
"""

        # Act
        result = spec_parser.parse_feature_spec(content)

        # Assert
        assert result["overview"] == "Just an overview."
        assert result["user_story"] is None
        assert result["rationale"] is None
        assert len(result["acceptance_criteria"]) == 1
        assert result["implementation_details"] is None
        assert result["testing_strategy"] is None
        assert result["documentation_updates"] == []
        assert result["dependencies"] is None
        assert result["estimated_effort"] is None


class TestExtractSubsectionEdgeCases:
    """Tests for extract_subsection edge cases."""

    def test_extract_subsection_empty_content(self):
        """Test extract_subsection returns None for empty content."""
        result = spec_parser.extract_subsection("", "Approach")
        assert result is None

    def test_extract_subsection_none_content(self):
        """Test extract_subsection returns None for None content."""
        result = spec_parser.extract_subsection(None, "Approach")
        assert result is None

    def test_extract_subsection_stopped_by_h2(self):
        """Test extract_subsection stops at H2 heading."""
        content = """### Approach
Some approach content here.

## Next Section
This should not be included."""

        result = spec_parser.extract_subsection(content, "Approach")
        assert "approach content" in result
        assert "Next Section" not in result
        assert "should not be included" not in result


class TestExtractChecklistEdgeCases:
    """Tests for extract_checklist edge cases."""

    def test_extract_checklist_empty_content(self):
        """Test extract_checklist returns empty list for empty content."""
        result = spec_parser.extract_checklist("")
        assert result == []

    def test_extract_checklist_none_content(self):
        """Test extract_checklist returns empty list for None content."""
        result = spec_parser.extract_checklist(None)
        assert result == []


class TestExtractCodeBlocksEdgeCases:
    """Tests for extract_code_blocks edge cases."""

    def test_extract_code_blocks_empty_content(self):
        """Test extract_code_blocks returns empty list for empty content."""
        result = spec_parser.extract_code_blocks("")
        assert result == []

    def test_extract_code_blocks_none_content(self):
        """Test extract_code_blocks returns empty list for None content."""
        result = spec_parser.extract_code_blocks(None)
        assert result == []


class TestParseSpecFileEdgeCases:
    """Tests for parse_spec_file edge cases."""

    def test_parse_spec_file_os_error(self, temp_project_dir, monkeypatch):
        """Test parse_spec_file raises ValidationError on OSError."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create spec file
        spec_file = specs_dir / "test_file.md"
        spec_file.write_text("# Feature: Test")

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(ValidationError) as exc_info:
                spec_parser.parse_spec_file("test_file")

            assert exc_info.value.code.name == "FILE_OPERATION_FAILED"

    def test_parse_spec_file_invalid_heading_format(self, temp_project_dir, monkeypatch):
        """Test parse_spec_file raises error for heading without colon."""
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create spec file with invalid heading (no colon)
        spec_file = specs_dir / "invalid_heading.md"
        spec_file.write_text("# FeatureWithoutColon\n\n## Overview\nContent")

        with pytest.raises(ValidationError) as exc_info:
            spec_parser.parse_spec_file("invalid_heading")

        assert "Type: Name" in exc_info.value.remediation

    def test_parse_spec_file_parser_exception(self, temp_project_dir, monkeypatch):
        """Test parse_spec_file wraps unexpected parser errors."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create valid spec file
        spec_file = specs_dir / "feature_test.md"
        spec_file.write_text("# Feature: Test\n\n## Overview\nTest content")

        # Mock the parser to raise an unexpected exception
        with patch.object(
            spec_parser, "parse_feature_spec", side_effect=RuntimeError("Unexpected")
        ):
            with pytest.raises(ValidationError) as exc_info:
                spec_parser.parse_spec_file("feature_test")

            assert exc_info.value.code.name == "SPEC_VALIDATION_FAILED"
            assert "Unexpected" in str(exc_info.value.context.get("error", ""))

    def test_parse_spec_file_reraises_validation_error(self, temp_project_dir, monkeypatch):
        """Test parse_spec_file re-raises ValidationError from parser."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create valid spec file
        spec_file = specs_dir / "feature_test2.md"
        spec_file.write_text("# Feature: Test\n\n## Overview\nTest content")

        # Mock the parser to raise a ValidationError
        original_error = ValidationError(
            message="Parser validation failed", code=spec_parser.ErrorCode.SPEC_VALIDATION_FAILED
        )
        with patch.object(spec_parser, "parse_feature_spec", side_effect=original_error):
            with pytest.raises(ValidationError) as exc_info:
                spec_parser.parse_spec_file("feature_test2")

            # Should be the same error, re-raised
            assert exc_info.value.message == "Parser validation failed"
