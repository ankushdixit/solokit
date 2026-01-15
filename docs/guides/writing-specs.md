# Writing Effective Specifications

**A guide to creating high-quality work item specifications for Session-Driven Development**

**Version:** 1.0.0
**Last Updated:** October 18, 2025
**Part of:** Phase 5.7 - Spec File First Architecture

---

## Table of Contents

1. [Why Good Specs Matter](#why-good-specs-matter)
2. [Spec-First Principles](#spec-first-principles)
3. [General Guidelines](#general-guidelines)
4. [Work Item Type Guides](#work-item-type-guides)
5. [Good vs Bad Examples](#good-vs-bad-examples)
6. [Tips and Best Practices](#tips-and-best-practices)
7. [Common Mistakes](#common-mistakes)

---

## Why Good Specs Matter

In Session-Driven Development, **spec files are the single source of truth** for work item content. A well-written spec:

✅ **Enables Claude to implement correctly** - Complete context means fewer mistakes
✅ **Saves time** - Clear requirements prevent back-and-forth clarifications
✅ **Ensures quality** - Detailed acceptance criteria make validation objective
✅ **Facilitates collaboration** - Future sessions start with complete understanding
✅ **Documents decisions** - Rationale and trade-offs are preserved

A poorly written spec leads to:
- ❌ Incomplete implementations
- ❌ Misunderstandings and rework
- ❌ Validation failures
- ❌ Lost context across sessions

---

## Spec-First Principles

### 1. Completeness Over Brevity

**Good:** Comprehensive details that leave no ambiguity
**Bad:** Vague descriptions that require interpretation

```markdown
❌ BAD:
## Overview
Add notifications to the app.

✅ GOOD:
## Overview
Implement a real-time notification system using WebSockets that allows the server to
push notifications to connected clients. Notifications will be displayed as
non-intrusive toast messages in the bottom-right corner of the application with support
for different severity levels (info, warning, error, success).
```

### 2. Specificity Over Generality

**Good:** Concrete examples, code snippets, API contracts
**Bad:** Abstract descriptions without examples

```markdown
❌ BAD:
## API Changes
Add an endpoint for notifications.

✅ GOOD:
## API Changes

### POST /api/notifications
```typescript
interface NotificationRequest {
  userId: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
}

interface NotificationResponse {
  id: string;
  delivered: boolean;
}
```
```

### 3. Testability Over Ambiguity

**Good:** Measurable acceptance criteria
**Bad:** Subjective or unmeasurable criteria

```markdown
❌ BAD:
- [ ] Notifications should work well
- [ ] System should be fast

✅ GOOD:
- [ ] Notifications are displayed within 100ms of server push
- [ ] Notification delivery rate > 99.5% under normal load
- [ ] Users can dismiss notifications individually or clear all
```

---

## General Guidelines

### Required Sections

Every spec must have **all required sections** for its work item type:
- See `docs/spec-template-structure.md` for complete requirements
- Validation will fail if required sections are missing or empty
- Follow the template structure exactly

### Writing Style

**Be Clear and Direct:**
- Use active voice: "The system sends..." not "A message is sent..."
- Use present tense for current state, future tense for changes
- Avoid jargon unless necessary (and define it if used)

**Provide Context:**
- Explain the "why" behind decisions
- Document trade-offs considered
- Link to related work items or external resources

**Use Examples Liberally:**
- Code snippets for API changes
- SQL for database schemas
- Mermaid diagrams for flows
- Bash commands for operations

### Formatting

**Code Blocks:**
```markdown
\```typescript
// Always specify language for syntax highlighting
function example(): void {
  // ...
}
\```
```

**Checklists:**
```markdown
- [ ] Use task list syntax for acceptance criteria
- [ ] Each item should be specific and measurable
- [ ] Minimum 3 items for most work types
```

**Mermaid Diagrams:**
```markdown
\```mermaid
sequenceDiagram
    participant Client
    participant Server
    Client->>Server: Connect WebSocket
    Server-->>Client: Connection Established
\```
```

---

## Work Item Type Guides

### Feature Specs

**Focus:** What new functionality is being added and why

**Key Sections:**
- **Overview:** High-level description of the feature
- **Rationale:** Why this feature is needed (business value, user impact)
- **User Story:** "As a [role], I want [goal] so that [benefit]"
- **Acceptance Criteria:** Minimum 3 specific, testable requirements
- **Implementation Details:** How to build it (approach, components, API changes)
- **Testing Strategy:** How to verify it works

**Tips:**
- Start with user value, not implementation
- Include API contracts and database schemas
- Think about edge cases and error handling
- Consider performance and scalability

**Example Overview:**
```markdown
## Overview

Implement a real-time notification system using WebSockets to enable instant
communication from server to clients. The system will:

1. Establish persistent WebSocket connections for authenticated users
2. Push notifications from server events to relevant clients
3. Display notifications as non-intrusive toast messages
4. Support notification history and read/unread tracking
5. Handle connection failures with automatic reconnection

This feature enables real-time collaboration features like live updates,
user presence, and instant alerts without polling.
```

#### LLM/Processing Configuration Subsection

**When to use:** For features involving LLM processing, complex algorithms, or external API integrations.

**Location:** Under "Implementation Details" section in feature specs.

**Purpose:** Document how the feature processes data, especially for:
- LLM-based features (e.g., DSPy agents)
- Features with non-trivial data processing
- External API integrations
- Distinguish deterministic vs. non-deterministic processing

**Example (LLM-based Feature):**
```markdown
### LLM/Processing Configuration

**Type:** LLM-based (DSPy)

**DSPy Signature:**
```python
class NotificationClassifier(dspy.Signature):
    """Classify notification urgency based on message content and context."""

    message = dspy.InputField(desc="Notification message text")
    context = dspy.InputField(desc="Additional context (user role, time, etc.)")
    urgency = dspy.OutputField(desc="Urgency level: low, medium, high, critical")
    suggested_action = dspy.OutputField(desc="Recommended user action")
```

**LLM Provider:** Google AI Studio (Gemini 2.5 Flash)

**LLM Usage:**
- Analyzes notification message content and context
- Classifies urgency to determine delivery priority and UI treatment
- Generates suggested actions for the user
- Fallback to keyword-based classification if LLM unavailable or rate-limited
- Caches classifications for identical messages (24h TTL)
```

**Example (Deterministic Feature):**
```markdown
### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Parse CSV file line-by-line using streaming parser
- Validate each row against JSON schema
- Transform dates from MM/DD/YYYY to ISO 8601 format
- Calculate running totals using reduce operations
- Sort results by timestamp (descending) using merge sort
- Batch insert into database (chunks of 1000 rows)
```

**Example (External API Integration):**
```markdown
### LLM/Processing Configuration

**Type:** External API Integration (No LLM)

**API Provider:** Stripe Payment API v2023-10-16

**Processing Type:**
- Create PaymentIntent via Stripe API
- Transform Stripe response to internal Order format
- Handle webhooks for async payment status updates
- Retry failed requests with exponential backoff (3 attempts max)
- Cache customer payment methods (Redis, 1h TTL)

**Rate Limits:** 100 requests/second per API key
**Error Handling:** Stripe webhook signature verification, idempotency keys for retries
```

**Example (Standard Feature):**
```markdown
### LLM/Processing Configuration

Not Applicable - Standard CRUD operations without LLM or special processing requirements.
```

**Tips:**
- Be specific about algorithms and data transformations
- For LLM features, include the complete DSPy signature
- Document fallback strategies for LLM failures
- Include rate limits and caching strategies
- Explain why LLM vs. deterministic approach was chosen

### Bug Specs

**Focus:** What's broken, why it's broken, how to fix it

**Key Sections:**
- **Description:** Clear explanation of the bug
- **Steps to Reproduce:** Exact steps to trigger the bug
- **Root Cause Analysis:** Investigation process and identified cause
- **Fix Approach:** How to fix the bug and why this approach
- **Prevention:** How to prevent similar bugs in the future

**Tips:**
- Include error logs and stack traces
- Document the investigation process
- Explain why the bug occurred (design flaw, edge case, regression)
- Test fix thoroughly with edge cases

**Example Root Cause Analysis:**
```markdown
## Root Cause Analysis

### Investigation

1. Reproduced bug on staging environment
2. Examined session token generation code in `auth/session.py:45`
3. Found that mobile clients use different token format than web clients
4. Reviewed token validation logic in `auth/middleware.py:128`

### Root Cause

The session token validator uses a hardcoded regex pattern that only matches
web client token format (UUID-based). Mobile clients generate shorter
alphanumeric tokens (8 chars) for performance reasons, which fail the regex
validation and are rejected.

```python
# Current (BROKEN):
TOKEN_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

# Should be:
TOKEN_PATTERN = r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-zA-Z]{8})$'
```

### Why It Happened

Mobile token format was added in Phase 2.3 but token validator was not updated.
No integration tests covered mobile-specific authentication flow.
```

### Refactor Specs

**Focus:** What's being changed structurally and why

**Key Sections:**
- **Current State:** What exists now (with code examples)
- **Problems:** Why current approach is problematic
- **Proposed Refactor:** What the new structure looks like
- **Scope:** What's in scope and out of scope
- **Benefits:** Why this refactor is worth doing

**Tips:**
- Show before/after code examples
- Quantify improvements if possible (performance, maintainability)
- Break large refactors into phases
- Consider migration strategy for existing code

### Security Specs

**Focus:** Security vulnerability and mitigation

**Key Sections:**
- **Security Issue:** What the vulnerability is
- **Threat Model:** Who might exploit it and how
- **Attack Vector:** How the attack would work (with PoC if safe)
- **Mitigation Strategy:** How to fix the vulnerability
- **Compliance:** OWASP, CWE, industry standards

**Tips:**
- Use CVSS scoring to assess severity
- Include proof-of-concept (if safe to document)
- Reference security standards (OWASP Top 10, CWE)
- Plan security testing and post-deployment monitoring

### Integration Test Specs

**Focus:** End-to-end test scenarios for system integration

**Key Sections:**
- **Scope:** What systems/components are being tested
- **Test Scenarios:** Detailed test cases with setup/actions/expectations
- **Performance Benchmarks:** Response time, throughput targets
- **Environment Requirements:** Docker services, databases, external APIs

**Tips:**
- Use mermaid sequence diagrams to visualize flows
- Include realistic test data
- Document environment setup completely
- Define clear pass/fail criteria

### Deployment Specs

**Focus:** How to deploy changes safely to production

**Key Sections:**
- **Deployment Scope:** What's being deployed
- **Deployment Procedure:** Step-by-step with commands
- **Rollback Procedure:** How to undo if things go wrong
- **Smoke Tests:** Post-deployment verification tests

**Tips:**
- Include all bash commands needed
- Document required secrets/env vars
- Plan for zero-downtime deployment
- Define rollback triggers clearly

---

## Good vs Bad Examples

### Acceptance Criteria

❌ **BAD - Vague and Unmeasurable:**
```markdown
- [ ] Feature should work correctly
- [ ] Performance should be good
- [ ] UI should look nice
```

✅ **GOOD - Specific and Measurable:**
```markdown
- [ ] Users can create, edit, and delete notifications via API
- [ ] Notification delivery latency < 100ms for 95th percentile
- [ ] Toast notifications auto-dismiss after 5 seconds unless error severity
- [ ] Users can view notification history for last 30 days
- [ ] System handles 10,000 concurrent WebSocket connections
```

### Implementation Details

❌ **BAD - Too High-Level:**
```markdown
## Implementation Details

Use WebSockets for notifications. Store in database.
```

✅ **GOOD - Specific and Actionable:**
```markdown
## Implementation Details

### Approach

1. **WebSocket Server**: Use `ws` library to create WebSocket server on port 3001
2. **Authentication**: Validate JWT tokens on connection handshake
3. **Message Protocol**: JSON messages with `type`, `payload`, `timestamp` fields
4. **Storage**: PostgreSQL table `notifications` with columns: id, user_id, message,
   severity, read_at, created_at

### Components Affected

- `server/websocket.ts` - New WebSocket server implementation
- `client/NotificationManager.tsx` - Client-side WebSocket connection and UI
- `database/migrations/005_notifications.sql` - Database schema
- `server/middleware/auth.ts` - JWT validation for WS handshake

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- WebSocket event routing based on message type
- JSON message serialization/deserialization
- Connection state management with heartbeat protocol
- Message queue with retry logic for failed deliveries

### API Changes

See detailed API contracts in API Changes section below.

### Database Changes

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message TEXT NOT NULL,
  severity VARCHAR(10) CHECK (severity IN ('info', 'warning', 'error', 'success')),
  read_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```
```

---

## Tips and Best Practices

### Start with Why

Always explain the rationale before diving into implementation:
- What problem does this solve?
- What's the business value?
- What are the alternatives and why weren't they chosen?

### Use Templates

Don't start from scratch:
1. Use `/work-new` to create work item with template
2. Follow template structure exactly
3. Fill in all sections completely
4. Remove HTML comment instructions when done

### Include Examples

Examples clarify intent:
- API request/response examples
- Code snippets showing usage
- Mermaid diagrams for complex flows
- Bash commands for operations
- SQL for database changes

### Think About Edge Cases

Consider failure scenarios:
- What if the network fails?
- What if the database is down?
- What if input is invalid?
- What if the user is offline?

### Make Criteria Measurable

Avoid subjective criteria:
- ❌ "Fast enough"
- ✅ "Response time < 200ms"
- ❌ "Works well"
- ✅ "Handles 1000 req/sec with < 1% error rate"

### Document Decisions

Future you (or Claude) will thank you:
- Why this approach over alternatives?
- What trade-offs were made?
- What constraints were considered?
- What assumptions are being made?

### Write Meaningful Tests, Not Just Coverage

Tests should validate real user scenarios, not just satisfy coverage metrics:

**The test quality question:** "If this feature broke in production, would this test catch it?"

```markdown
❌ BAD: Coverage-driven tests
- Tests that exercise code without meaningful assertions
- Mocking everything so nothing real is verified
- Tests that would pass even if the feature is broken
- Writing trivial tests just to hit coverage thresholds

✅ GOOD: Scenario-driven tests
- Tests derived directly from acceptance criteria
- Tests that verify actual user workflows end-to-end
- Tests for edge cases and error conditions users might hit
- Tests that would genuinely fail if functionality regressed
```

**Tip:** Each acceptance criterion should map to at least one meaningful test. If you can't write a test that would fail when the criterion isn't met, the criterion may be too vague.

---

## Common Mistakes

### 1. Empty or Placeholder Sections

❌ **Don't:**
```markdown
## Testing Strategy

TODO: Add testing strategy
```

✅ **Do:**
```markdown
## Testing Strategy

### Unit Tests
- Test WebSocket connection establishment and authentication
- Test notification message parsing and validation
- Test reconnection logic on connection loss

### Integration Tests
- Test end-to-end notification flow from server event to client display
- Test concurrent connections (simulate 1000 clients)
- Test message delivery guarantees

### Manual Testing
- Test on multiple browsers (Chrome, Firefox, Safari)
- Test on mobile devices (iOS, Android)
- Test with slow network conditions (throttle to 3G)
```

### 2. Assuming Too Much Context

❌ **Don't:**
```markdown
## Overview
Use the same approach as the other feature.
```

✅ **Do:**
```markdown
## Overview
Use the WebSocket approach implemented in Phase 3.2 (real-time chat),
adapting the connection management and reconnection logic for the
notification use case. Key differences:
- Notifications are one-way (server → client), not bidirectional
- Notifications persist in database, chat messages don't
- Notification UI is toast-based, chat UI is message thread
```

### 3. Insufficient Acceptance Criteria

❌ **Don't:**
```markdown
## Acceptance Criteria
- [ ] Feature works
- [ ] Tests pass
```

✅ **Do:**
```markdown
## Acceptance Criteria
- [ ] Users receive notifications within 100ms of server event
- [ ] Notifications display as toast messages with correct severity styling
- [ ] Users can dismiss notifications individually or clear all
- [ ] Notification history persists and is viewable in user dashboard
- [ ] WebSocket reconnects automatically on connection loss
- [ ] System handles 10,000 concurrent connections with < 1% error rate
- [ ] All unit tests pass with > 90% coverage
- [ ] Integration tests validate end-to-end notification flow
```

### 4. Missing Error Handling

❌ **Don't:**
Ignore error scenarios

✅ **Do:**
```markdown
## Implementation Details

### Error Handling

**Connection Failures:**
- Exponential backoff for reconnection (1s, 2s, 4s, 8s, max 30s)
- Display offline indicator in UI
- Queue notifications locally during offline period
- Sync queued notifications on reconnection

**Invalid Messages:**
- Log error with message ID and user ID
- Send error response to client
- Don't crash server on malformed message

**Authentication Failures:**
- Close WebSocket connection
- Return 401 Unauthorized with reason
- Prompt user to re-authenticate
```

### 5. Skipping Database Changes

❌ **Don't:**
```markdown
## Implementation Details
We'll need a database for notifications.
```

✅ **Do:**
```markdown
## Database Changes

```sql
-- Add notifications table
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  severity VARCHAR(10) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'success')),
  read_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
```

**Migration Plan:**
1. Run migration script: `npm run migrate:up 005_notifications`
2. Verify table created: `psql -c "\d notifications"`
3. No data migration needed (new feature)
```

---

## Validation Checklist

Before starting a session, verify your spec has:

- [ ] All required sections for the work item type
- [ ] No empty or placeholder sections
- [ ] Minimum 3 specific acceptance criteria (if required)
- [ ] Code examples for API changes
- [ ] Database schema if data changes involved
- [ ] Error handling considerations
- [ ] Testing strategy with specific test cases
- [ ] Clear rationale explaining why this work is needed

Run validation:
```bash
sk validate-spec {work_item_id} {type}
```

---

## Getting Help

- **Template Examples:** `templates/{type}_spec.md`
- **Template Structure:** `docs/spec-template-structure.md`
- **Session-Driven Development:** `docs/solokit-methodology.md`
- **Validation Rules:** `docs/spec-template-structure.md#validation-rules`

---

**Remember:** Time spent writing a comprehensive spec is time saved during implementation and validation. A well-written spec enables Claude to implement correctly the first time, avoiding rework and confusion.
