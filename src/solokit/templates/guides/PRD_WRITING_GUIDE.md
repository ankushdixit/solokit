# PRD Writing Guide for Claude-Driven Development

**A comprehensive guide for creating Product Requirements Documents optimized for AI-assisted implementation with Solokit**

---

## Table of Contents

1. [How This Guide Works with Claude](#how-this-guide-works-with-claude)
2. [Core Philosophy: Vertical Slices Over Horizontal Layers](#core-philosophy-vertical-slices-over-horizontal-layers)
3. [PRD Structure](#prd-structure)
4. [Technical Constraints](#technical-constraints)
5. [User Story Ordering](#user-story-ordering)
6. [Definition of Ready (DoR)](#definition-of-ready-dor)
7. [Acceptance Criteria](#acceptance-criteria)
8. [Testing Strategy](#testing-strategy)
9. [Mapping PRD to Solokit Work Items](#mapping-prd-to-solokit-work-items)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
11. [PRD Template](#prd-template)

---

## How This Guide Works with Claude

This guide is designed for a workflow where **Claude writes both the PRD and implements the code**. The user provides the product vision and requirements; Claude structures them into a well-organized PRD and then builds the application.

### The Claude-Driven Development Workflow

```
1. User describes what they want to build
2. Claude asks clarifying questions
3. Claude writes the PRD (following this guide)
4. User reviews and approves the PRD
5. Claude creates Solokit work items from the PRD
6. For each work item:
   a. User runs: /start <work-item-id>
   b. Claude implements the feature
   c. Claude writes tests
   d. User runs: /end
7. Repeat until product is complete
```

### What Claude Needs in a PRD

For Claude to implement effectively, the PRD must provide:

1. **Explicit acceptance criteria** - Claude follows instructions precisely. Ambiguous requirements lead to wrong implementations.

2. **Technical constraints upfront** - Stack choice, external APIs, performance requirements, security needs.

3. **Clear dependency order** - Claude works on one story at a time. Dependencies must be explicit.

4. **Testable outcomes** - Every feature needs clear pass/fail criteria that can be verified.

5. **What NOT to do** - Explicit exclusions prevent Claude from over-engineering or adding unwanted features.

### Claude's Responsibilities

When implementing from a PRD, Claude will:

- Follow the exact acceptance criteria
- Implement only what is specified (no "bonus" features)
- Write tests that verify the acceptance criteria
- Follow patterns documented in ARCHITECTURE.md
- Ask for clarification when requirements are ambiguous
- Use Solokit's session workflow (`/start`, `/end`)

---

## Core Philosophy: Vertical Slices Over Horizontal Layers

### The Problem with Horizontal Development

Building layer-by-layer creates integration problems:

```
Layer-by-Layer (AVOID):

Session 1: Build all database models
Session 2: Build all API endpoints
Session 3: Build all UI components
Session 4: Connect everything → Problems discovered here
```

This approach delays testing and creates "integration debt" - bugs that accumulate silently until everything connects.

### Vertical Slices: The Solution

Build one complete feature at a time, touching all layers:

```
Feature-by-Feature (CORRECT):

Session 1: User can view their profile (DB + API + UI + Tests)
Session 2: User can edit their profile (DB + API + UI + Tests)
Session 3: User can upload avatar (DB + API + UI + Tests)

Each session: Complete, tested, working feature
```

### Why Vertical Slices Work Better

| Aspect | Horizontal Layers | Vertical Slices |
|--------|-------------------|-----------------|
| **Testing** | Delayed until integration | Immediate, per feature |
| **Feedback** | Late (problems compound) | Early (problems isolated) |
| **Progress** | Hard to measure | Clear (features done/not done) |
| **Risk** | Hidden until late | Exposed early |
| **Quality Gates** | Can't run meaningfully | Pass after each feature |

### The INVEST Principle

Every user story should satisfy:

- **I**ndependent: Can be built and tested without other stories
- **N**egotiable: Details can be clarified through questions
- **V**aluable: Delivers visible value to users
- **E**stimable: Complexity is understood (S/M/L)
- **S**mall: Completable in one Solokit session
- **T**estable: Clear criteria for pass/fail

---

## PRD Structure

### Recommended Sections

```markdown
1. Executive Summary
2. Problem Statement & Goals
3. User Personas
4. Technical Constraints          ← NEW: Critical for Claude
5. MVP Definition (MoSCoW)
6. User Stories (Ordered by Dependency)
7. Data Models
8. API Specifications
9. Phased Development Plan
10. Testing Requirements
11. Success Metrics
12. Out of Scope                   ← NEW: What NOT to build
```

### Section Details

#### 1. Executive Summary
One paragraph describing:
- What the product does
- Who it's for
- Core value proposition

#### 2. Problem Statement & Goals
- What problem does this solve?
- What are the measurable success criteria?
- What does "done" look like for the entire project?

#### 3. User Personas
For each user type:
- Who are they?
- What do they need?
- What are their pain points?

#### 4. Technical Constraints
See [Technical Constraints](#technical-constraints) section below.

#### 5. MVP Definition (MoSCoW)

```markdown
Must Have (MVP):
- Features required for launch
- Without these, product is unusable

Should Have (Post-MVP):
- Important but not critical
- First priorities after MVP

Could Have (Future):
- Nice to have
- Build if time permits

Won't Have (Out of Scope):
- Explicitly excluded
- Prevents scope creep
```

#### 6-11. See detailed sections below

---

## Technical Constraints

**This section is critical.** It tells Claude what technology decisions have been made and what boundaries to work within.

### Required Information

```markdown
## Technical Constraints

### Stack
- **Framework**: [From STACK_GUIDE.md - e.g., saas_t3, ml_ai_fastapi]
- **Database**: [PostgreSQL, SQLite, etc.]
- **Deployment**: [Vercel, AWS, self-hosted, etc.]

### External Dependencies
- **APIs**: [List external APIs with rate limits, auth methods]
- **Services**: [Auth providers, email services, etc.]

### Performance Requirements
- **Response time**: [e.g., API responses < 200ms p95]
- **Concurrent users**: [Expected load]
- **Data volume**: [Expected data sizes]

### Security Requirements
- **Authentication**: [Method - email/password, OAuth, etc.]
- **Authorization**: [Role-based, attribute-based, etc.]
- **Data sensitivity**: [PII handling, encryption needs]

### Constraints
- **Must use**: [Required libraries, patterns, services]
- **Must not use**: [Prohibited approaches]
- **Budget**: [Any cost constraints for services]
```

### Stack Selection

Before writing the PRD, choose a stack from STACK_GUIDE.md:

| Project Type | Recommended Stack |
|--------------|-------------------|
| SaaS with complex data | `saas_t3` |
| ML/AI backend | `ml_ai_fastapi` |
| Admin dashboard | `dashboard_refine` |
| General web app | `fullstack_nextjs` |

The stack choice determines:
- Available patterns (documented in ARCHITECTURE.md)
- API style (tRPC, REST, Server Actions)
- Database access patterns
- Testing approaches

---

## User Story Ordering

### Rule 1: Start with Infrastructure Validation

The first story should prove the stack works:

```markdown
Story: Health Check Endpoint Works

Acceptance Criteria:
- GET /api/health returns { status: "ok" }
- Response time < 100ms
- Database connection verified

This validates: Stack setup, deployment, database connection
```

### Rule 2: Order by Dependency

Even if Feature B is more valuable, if it depends on Feature A, build A first.

```markdown
Dependency Chain Example:

1. User can view items (read) → no dependencies
2. User can create items (write) → depends on (1)
3. User can edit items → depends on (2)
4. User can delete items → depends on (2)
5. User can search items → depends on (1)
```

### Rule 3: Each Story Must Be Verifiable

After completing a story, it must be possible to verify it works. If you can't test it, the story is:
- Too technical (not user-facing)
- Too large (needs splitting)
- Missing dependencies

### Rule 4: Integrate External Dependencies Early

If the product depends on external APIs, validate them in the first phase:

```markdown
Phase 0: External Dependency Validation

Stories:
1. Can connect to [External API]
2. Can authenticate with [Auth Provider]
3. Can send email via [Email Service]

Why: If these fail, discover on Day 1, not Day 30.
```

### Recommended Story Sequence

```
1. Infrastructure validation (health check, DB connection)
2. First read-only feature (proves data flows work)
3. First write feature (proves mutations work)
4. Feature with business logic (proves algorithms work)
5. Feature with external integration (proves API calls work)
6. Features building on previous (proves composition works)
7. Polish and edge cases
```

---

## Definition of Ready (DoR)

A story is **Ready for Claude to implement** when:

### Required Information

```markdown
□ User story follows format: As a [persona], I want [action] so that [benefit]
□ Acceptance criteria are complete (Given-When-Then format)
□ All dependencies are identified and completed
□ Technical approach is clear (or explicitly needs discovery)
□ Data model changes are specified
□ API contract is defined (endpoints, request/response shapes)
□ UI requirements are clear (components, layouts, interactions)
□ Error cases are specified
□ Security requirements are stated
□ Testing requirements are listed
```

### Questions Claude Will Ask

If the DoR isn't met, Claude will need to ask:

- "What should happen when [edge case]?"
- "Should this be accessible to all users or specific roles?"
- "What validation rules apply to [field]?"
- "How should errors be displayed to the user?"
- "What's the expected behavior when [external service] is unavailable?"

**Better to answer these in the PRD than during implementation.**

---

## Acceptance Criteria

### Given-When-Then Format

Write acceptance criteria that translate directly to tests:

```markdown
Story: User can create a new project

Acceptance Criteria:

1. Given I am logged in
   When I click "New Project"
   Then I see a form with fields: name, description
   And the "Create" button is disabled

2. Given I am on the new project form
   When I enter a valid name (3-50 characters)
   And I enter an optional description
   And I click "Create"
   Then the project is created
   And I am redirected to the project page
   And I see a success message

3. Given I am on the new project form
   When I enter a name that already exists
   And I click "Create"
   Then I see an error: "Project name already exists"
   And the form is not submitted

4. Given I am not logged in
   When I try to access /projects/new
   Then I am redirected to /login
```

### What Makes Good Acceptance Criteria

| Good | Bad |
|------|-----|
| "Name must be 3-50 characters" | "Name should be reasonable length" |
| "Response within 200ms" | "Should be fast" |
| "Show error: 'Email invalid'" | "Show appropriate error" |
| "Redirect to /dashboard" | "Go to the main page" |

### Error Cases Are Required

Every story should specify:
- What errors can occur
- How each error is displayed
- What the user can do to recover

---

## Testing Strategy

### Testing Pyramid

```
Unit Tests (70%)
- Business logic, utilities, validation
- Written during implementation
- Run on every change

Integration Tests (20%)
- API endpoints, database queries
- Written after feature complete
- Run before session end

E2E Tests (10%)
- Critical user journeys only
- Written after related features complete
- Run before deployment
```

### Testing Requirements Per Story

Each story should specify:

```markdown
### Testing Requirements

Unit Tests:
- [ ] Validation logic for [fields]
- [ ] Business logic for [calculation/algorithm]
- [ ] Component renders correctly with [props]

Integration Tests:
- [ ] [Endpoint] returns correct data
- [ ] [Endpoint] handles errors correctly
- [ ] Database queries return expected results

E2E Tests (if completing a user journey):
- [ ] User can complete [full workflow]
```

### Quality Gates

Solokit's quality gates verify:

| Gate | What It Checks |
|------|----------------|
| Linting | Code follows style guide |
| Formatting | Consistent code format |
| Type Check | No type errors |
| Unit Tests | All pass, coverage threshold met |
| Integration Tests | All pass (if they exist) |
| E2E Tests | All pass (if they exist) |
| Security | No vulnerabilities detected |

Stories aren't complete until `/end` passes all gates.

---

## Mapping PRD to Solokit Work Items

### PRD Stories → Work Items

Each user story in the PRD becomes a Solokit work item:

```markdown
PRD Story:
"User can view their profile"

↓ Becomes ↓

sk work-new
Type: feature
ID: feat_user_profile_view
Title: User can view their profile
Priority: high
```

### Work Item Types

| PRD Element | Work Item Type |
|-------------|----------------|
| User story (new capability) | `feature` |
| Fix for existing functionality | `bug` |
| Code improvement (no new features) | `refactor` |
| Security enhancement | `security` |
| Test coverage improvement | `integration_test` |
| Release preparation | `deployment` |

### Phased Development → Milestones

PRD phases map to Solokit milestones:

```markdown
PRD:
Phase 1: Core User Features
Phase 2: Admin Dashboard
Phase 3: Integrations

↓ Becomes ↓

Milestones: phase-1-core, phase-2-admin, phase-3-integrations
```

### Session Workflow

For each work item:

```bash
# Start session
sk start feat_user_profile_view

# Claude implements the feature...

# End session (runs quality gates)
sk end

# If gates pass, work item marked complete
# If gates fail, fix issues and run /end again
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Horizontal Phases

```markdown
WRONG:
Phase 1: All database tables
Phase 2: All API endpoints
Phase 3: All UI components

CORRECT:
Phase 1: User can view items (DB + API + UI)
Phase 2: User can create items (DB + API + UI)
```

### Anti-Pattern 2: Vague Acceptance Criteria

```markdown
WRONG:
"User can search for items"

CORRECT:
"Given items exist in the database
 When user enters 'test' in the search box
 And clicks Search
 Then items with 'test' in title or description are shown
 And results are sorted by relevance
 And maximum 20 results are shown per page"
```

### Anti-Pattern 3: Missing Error Cases

```markdown
WRONG:
"User can submit the form"

CORRECT:
"User can submit the form"
+ "When name is empty, show 'Name is required'"
+ "When name > 100 chars, show 'Name too long'"
+ "When server error, show 'Please try again'"
```

### Anti-Pattern 4: Technical Stories Without User Value

```markdown
WRONG:
"Set up PostgreSQL database"
"Create Prisma schema"

CORRECT:
"User can view their profile"
  Technical tasks:
  - Create users table
  - Create /api/users/me endpoint
  - Create Profile component
```

### Anti-Pattern 5: Ambiguous Requirements (AI-Specific)

Claude interprets requirements literally. Ambiguity causes problems:

```markdown
WRONG:
"Make the form user-friendly"
"Add appropriate validation"
"Handle errors gracefully"

CORRECT:
"Form fields have placeholder text explaining expected format"
"Email must match pattern X, phone must match pattern Y"
"Network errors show retry button, validation errors show inline"
```

### Anti-Pattern 6: Missing Technical Constraints

```markdown
WRONG:
[No technical constraints section]
Claude chooses arbitrary technologies

CORRECT:
"Stack: saas_t3"
"Auth: NextAuth with email/password"
"API style: tRPC"
"Must use: Zod for validation"
```

### Anti-Pattern 7: Overly Large Stories

```markdown
WRONG:
"User can manage their account"
(Too large - authentication, profile, settings, billing all in one)

CORRECT:
"User can log in"
"User can view profile"
"User can update profile"
"User can change password"
"User can manage billing"
```

---

## PRD Template

Use this template for your PRD. Save it at `docs/PRD.md`.

```markdown
# [Product Name] - Product Requirements Document

## Executive Summary

[One paragraph: What is this product? Who is it for? What problem does it solve?]

## Problem Statement

### The Problem
[What problem are we solving?]

### Goals
[What does success look like? Measurable outcomes.]

### Non-Goals
[What are we explicitly NOT trying to do?]

## User Personas

### [Persona Name]
- **Who**: [Description]
- **Needs**: [What they need from this product]
- **Pain Points**: [Current frustrations]

[Repeat for each persona]

## Technical Constraints

### Stack
- **Framework**: [saas_t3 | ml_ai_fastapi | dashboard_refine | fullstack_nextjs]
- **Database**: [PostgreSQL | SQLite | etc.]
- **Deployment**: [Vercel | AWS | etc.]

### External Dependencies
| Service | Purpose | Rate Limits | Auth Method |
|---------|---------|-------------|-------------|
| [API] | [Purpose] | [Limits] | [Auth] |

### Performance Requirements
- API response time: [target]
- Concurrent users: [expected]
- Data volume: [expected]

### Security Requirements
- Authentication: [method]
- Authorization: [method]
- Data handling: [requirements]

### Technical Rules
- **Must use**: [required patterns/libraries]
- **Must not use**: [prohibited approaches]

## MVP Definition

### Must Have
- [ ] [Feature 1]
- [ ] [Feature 2]

### Should Have (Post-MVP)
- [ ] [Feature 3]
- [ ] [Feature 4]

### Won't Have (Out of Scope)
- [Excluded feature 1]
- [Excluded feature 2]

## User Stories

### Phase 0: Infrastructure

#### Story 0.1: Health Check
**As a** developer
**I want** a health check endpoint
**So that** I can verify the stack is working

**Acceptance Criteria:**
1. Given the server is running
   When I call GET /api/health
   Then I receive { status: "ok", timestamp: [ISO date] }
   And response time is < 100ms

**Dependencies:** None
**Complexity:** S

---

### Phase 1: [Phase Name]

#### Story 1.1: [Story Name]
**As a** [persona]
**I want to** [action]
**So that** [benefit]

**Acceptance Criteria:**
1. Given [context]
   When [action]
   Then [result]

2. Given [error context]
   When [action]
   Then [error handling]

**Technical Notes:**
- Database: [tables/changes]
- API: [endpoints]
- UI: [components]

**Testing Requirements:**
- Unit: [what to test]
- Integration: [what to test]
- E2E: [if applicable]

**Dependencies:** [Story IDs]
**Complexity:** S | M | L

---

[Continue with more stories...]

## Data Models

### [Model Name]
```
Field       | Type     | Constraints
------------|----------|------------
id          | string   | Primary key, CUID
name        | string   | Required, 3-100 chars
createdAt   | datetime | Auto-generated
updatedAt   | datetime | Auto-updated
```

[Repeat for each model]

## API Specifications

### [Endpoint Name]
- **Method**: GET | POST | PUT | DELETE
- **Path**: /api/[path]
- **Auth**: Required | Public
- **Request**: [shape]
- **Response**: [shape]
- **Errors**: [error codes and meanings]

[Repeat for each endpoint]

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| [Metric] | [Target] | [Method] |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk] | H/M/L | H/M/L | [Plan] |

---

*PRD Version: 1.0*
*Last Updated: [Date]*
*Status: Draft | In Review | Approved*
```

---

## Summary: PRD Checklist

Before finalizing your PRD, verify:

### Structure
- [ ] Executive summary is clear and concise
- [ ] Problem statement has measurable goals
- [ ] User personas are defined
- [ ] Technical constraints are complete
- [ ] MVP scope is explicitly defined
- [ ] Out of scope items are listed

### User Stories
- [ ] All stories follow INVEST criteria
- [ ] Stories are ordered by dependency
- [ ] Each story has Given-When-Then acceptance criteria
- [ ] Error cases are specified for each story
- [ ] No horizontal/technical-only stories
- [ ] Complexity is estimated (S/M/L)

### Technical
- [ ] Stack choice is specified
- [ ] Data models are defined
- [ ] API specifications are complete
- [ ] External dependencies are documented
- [ ] Security requirements are stated

### Testing
- [ ] Testing requirements specified per story
- [ ] Unit test scope identified
- [ ] Integration test points identified
- [ ] E2E test journeys mapped (for critical paths)

### Ready for Implementation
- [ ] PRD saved at docs/PRD.md
- [ ] All questions answered (no ambiguity)
- [ ] User has reviewed and approved
- [ ] Ready to create Solokit work items

---

## Next Steps

After completing your PRD:

1. **Save PRD** at `docs/PRD.md`
2. **Create work items** using `/work-new` for each story
3. **Set dependencies** between work items
4. **Start first session** with `/start <work-item-id>`
5. **Implement** following ARCHITECTURE.md patterns
6. **Complete session** with `/end`
7. **Repeat** until MVP is complete
