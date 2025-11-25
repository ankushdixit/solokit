# Solokit Framework
## A Universal Methodology for AI-Augmented Software Development

---

## Executive Summary

**Session-Driven Development (Solokit)** is a comprehensive methodology that enables AI coding assistants (like Claude Code) to work on software projects across multiple sessions with perfect context continuity, enforced quality standards, and accumulated institutional knowledge.

This framework transforms ephemeral AI interactions into a **stateful, rigorous development process** with the same handoff quality as professional development teams.

### Core Innovation

Traditional AI coding sessions suffer from:
- **Context loss** between sessions
- **Quality entropy** over time
- **Knowledge fragmentation** across interactions
- **Lack of process rigor**

Solokit solves this through:
- **Automated state tracking** (work items, dependencies, progress)
- **Validation gates** (pre/post-session quality enforcement)
- **Knowledge accumulation** (learnings, patterns, decisions)
- **Deterministic handoffs** (briefings, status updates, structured documentation)

### Target Audience

- Solo developers building complex products
- Small teams using AI assistants
- Long-running projects (weeks to months, 50+ sessions)
- Projects requiring team-level quality with solo resources

---

## Part 1: Conceptual Foundation

### What is a "Session"?

A **session** is a single Claude Code conversation instance where development work occurs. Sessions are:
- **Stateless by default** - Claude doesn't remember previous sessions
- **Time-bounded** - Typically 30 minutes to 2 hours of focused work
- **Task-focused** - Should accomplish specific, defined objectives

### The Session Continuity Problem

**Without Solokit:**
```
Session 1: Builds feature A, makes decisions, learns patterns
  ↓ [Context lost]
Session 2: Doesn't know what was built, why, or what was learned
  ↓ [Quality degrades]
Session 3: Rediscovers same issues, makes inconsistent decisions
```

**With Solokit:**
```
Session 1: Work + Documentation → Status/Learnings/Stack updates
  ↓ [Perfect handoff]
Session 2: Reads briefing, understands context, continues seamlessly
  ↓ [Quality maintained]
Session 3: Builds on patterns, references learnings, consistent decisions
```

### Core Principles

1. **Stateful Development**: Each session inherits complete context from previous sessions
2. **Enforced Quality**: Validation gates prevent broken states from propagating
3. **Knowledge Accumulation**: Learnings, decisions, and patterns are captured and curated
4. **Dependency-Driven Workflow**: Work items ordered by logical dependencies, not arbitrary sequences
5. **Deterministic Automation**: Scripts provide reliable, repeatable session management
6. **Documentation as Foundation**: Living documentation updated continuously, not retroactively

---

## Part 2: System Architecture

### Directory Structure

When Solokit is installed in a project, it creates:

```
project-root/
├── .sessionrc.json              # Configuration file (optional)
├── CLAUDE.md                    # AI instructions (optional)
│
├── .session/
│   ├── tracking/
│   │   ├── work_items.json      # Work item definitions & status
│   │   ├── status_update.json   # Latest session summary
│   │   ├── learnings.json       # Accumulated knowledge
│   │   └── [other tracking files...]
│   │
│   ├── briefings/
│   │   └── session_NNN_briefing.md  # Generated session instructions
│   │
│   ├── history/
│   │   └── session_NNN_summary.md   # Completed session reports
│   │
│   └── specs/
│       └── work_item_specs/         # Detailed work item specifications
│
├── docs/                        # Project documentation
│   ├── vision.md
│   ├── prd.md
│   ├── architecture.md
│   └── development_plan.md
│
└── [your project files...]
```

**Note:** The Session plugin provides the automation through Claude Code commands (`/sk:start`, `/sk:end`, etc.). No scripts directory is needed in your project - all automation is handled by the plugin.

### Key Files Explained

#### 1. `.sessionrc.json` - Project Configuration

Defines project-specific Solokit settings:

```json
{
  "framework_version": "1.0.0",
  "project": {
    "name": "my-awesome-app",
    "type": "web_application",
    "work_item_model": "feature_based"
  },

  "session_protocol": {
    "start_trigger": "/start",
    "end_trigger": "/end",
    "auto_briefing": true
  },

  "validation_rules": {
    "pre_session": {
      "git_clean": true,
      "dependencies_met": true,
      "environment_valid": true
    },
    "post_session": {
      "tests_pass": true,
      "linting_pass": true,
      "documentation_updated": true
    }
  },

  "work_item_types": {
    "feature": {
      "template": "feature_spec.md",
      "typical_sessions": "2-4"
    },
    "bug": {
      "template": "bug_report.md",
      "typical_sessions": "1-2"
    },
    "refactor": {
      "template": "refactor_plan.md",
      "typical_sessions": "1-3"
    }
  }
}
```

#### 2. `CLAUDE.md` - AI Instructions

Auto-generated file that Claude Code reads automatically. Contains:
- Session start/end protocols
- Project-specific guidance
- Command references
- Quality standards

**Example structure:**
```markdown
# Project Instructions for Claude Code

### Spec File Architecture (Phase 5.7)

**The spec file is the single source of truth for work item content.**

Starting in Phase 5.7, Solokit implements a spec-first architecture where all work item implementation details, acceptance criteria, and testing strategies are documented in markdown specification files, not in JSON tracking files.

#### Architecture Overview

```
.session/
├── specs/
│   ├── feature_xyz.md           ← Content (single source of truth)
│   ├── bug_abc.md
│   └── deployment_123.md
└── tracking/
    └── work_items.json           ← Tracking only (metadata, status, dependencies)
```

#### Separation of Concerns

**Spec Files** (`.session/specs/{work_item_id}.md`):
- **Purpose**: Complete implementation specifications
- **Content**: Overview, rationale, acceptance criteria, implementation details, testing strategy
- **Format**: Structured markdown with standardized sections
- **Workflow**: Read and passed in full to Claude during briefings (no compression)
- **Validation**: Checked for completeness before sessions start

**Work Items JSON** (`work_items.json`):
- **Purpose**: Work item tracking and coordination
- **Content**: ID, type, status, priority, dependencies, milestone, sessions
- **Format**: JSON for programmatic access
- **Workflow**: Updated by Solokit automation (status changes, session tracking)
- **Pruned Fields**: No longer stores content fields (rationale, acceptance_criteria, etc.)

#### Why Spec-First?

**The Problem (Pre-Phase 5.7):**
- Developers wrote detailed specs in markdown files
- System read minimal JSON fields (`rationale`, `acceptance_criteria`) from `work_items.json`
- **Result**: Claude only saw empty/minimal content in briefings, not the rich specifications

**The Solution (Phase 5.7+):**
- Spec files are the authoritative source
- Briefings include **full spec content** (no truncation, no compression)
- `work_items.json` reduced to pure tracking/metadata
- **Result**: Claude receives complete context for perfect implementations

#### Spec File Flow

```
1. Create Work Item
   ↓
   /work-new → Creates .session/specs/{work_item_id}.md from template
   ↓
2. Fill Out Specification
   ↓
   Developer edits spec file with complete implementation details
   ↓
3. Start Session
   ↓
   /start → Loads full spec into briefing + validates completeness
   ↓
4. Claude Implements
   ↓
   Full spec content available (acceptance criteria, implementation plan)
   ↓
5. End Session
   ↓
   /end → Validates spec completeness as quality gate
```

#### Spec Templates

Solokit provides 6 work item type templates:

| Type | Template | Required Sections |
|------|----------|-------------------|
| **Feature** | `templates/feature_spec.md` | Overview, Rationale, Acceptance Criteria, Implementation Details, Testing Strategy |
| **Bug** | `templates/bug_spec.md` | Description, Steps to Reproduce, Root Cause Analysis, Fix Approach |
| **Refactor** | `templates/refactor_spec.md` | Overview, Current State, Proposed Refactor, Scope |
| **Security** | `templates/security_spec.md` | Security Issue, Threat Model, Attack Vector, Mitigation Strategy, Compliance |
| **Integration Test** | `templates/integration_test_spec.md` | Scope, Test Scenarios, Performance Benchmarks, Environment Requirements |
| **Deployment** | `templates/deployment_spec.md` | Deployment Scope, Procedure, Rollback, Smoke Tests |

#### Spec Validation

Specs are automatically validated for:
- ✅ All required sections present and non-empty
- ✅ Minimum acceptance criteria items (3 for most types)
- ✅ Required subsections (e.g., deployment steps)
- ✅ Proper markdown structure

**Validation occurs at:**
1. **Session start** (`/start`): Warning displayed in briefing if spec incomplete
2. **Session end** (`/end`): Quality gate fails if spec incomplete
3. **Manual**: `sk validate-spec {work_item_id} {type}`

#### Benefits

- **Zero Context Loss**: Full specs passed to Claude, not truncated JSON
- **Better Quality**: Comprehensive specs → better implementations
- **Single Source of Truth**: No confusion about where content lives
- **Validation**: Catch incomplete specs before starting work
- **Templates**: Standardized structure ensures consistency

**For more information:**
- Writing specs: `docs/writing-specs.md`
- Template structure: `docs/spec-template-structure.md`
- Validation rules: See `docs/spec-template-structure.md#validation-rules`

---

## Session Protocol

### Starting a Session
When you run `/start`:
1. Run: `sk start --next` (or `/sk:start`)
2. Read generated briefing
3. Validate environment
4. Begin work

### Ending a Session
When you run `/end`:
1. Run tests
2. Run: `sk end` (or `/sk:end`)
3. Update documentation
4. Create commit

## Project Context
[Auto-populated from vision.md, architecture.md]

## Development Guidelines
[Auto-populated from .sessionrc.json]

## Runtime Development Standards

### Code Quality Enforcement
**All code must meet quality standards before session completion**

- **Linting**: Code must pass configured linter
  - Python: `ruff check` or `pylint`
  - TypeScript/JavaScript: `eslint`
  - Rust: `cargo clippy`
  - Go: `golangci-lint`

- **Formatting**: Code must be properly formatted
  - Python: `black` or `ruff format`
  - TypeScript/JavaScript: `prettier`
  - Rust: `cargo fmt`
  - Go: `gofmt`

- **Type Checking** (if enabled):
  - Python: `mypy`
  - TypeScript: `tsc --noEmit`

### Library Documentation - MANDATORY

**ALWAYS use Context7 MCP for up-to-date library documentation**

Before using ANY external library, you MUST:

1. **Resolve library ID**:
   mcp__context7__resolve-library-id "<library-name>"

2. **Get current documentation**:
   mcp__context7__get-library-docs "<library-id>" --topic "<topic>"

3. **Implement using latest API patterns** from Context7, not training data

**NEVER**:
- ❌ Rely solely on training data for library APIs
- ❌ Guess at API signatures
- ❌ Use patterns without verifying they're current
- ❌ Assume APIs haven't changed since training cutoff

**ALWAYS**:
- ✅ Check Context7 before first use of any library
- ✅ Verify API changes on library version upgrades
- ✅ Reference Context7 docs when encountering unexpected behavior
- ✅ Capture library version info in learnings

**Examples:**

# Before implementing FastAPI endpoint
mcp__context7__resolve-library-id "fastapi"
mcp__context7__get-library-docs "/tiangolo/fastapi" --topic "routing"
# Now implement using current patterns

# Before using SQLAlchemy queries
mcp__context7__resolve-library-id "sqlalchemy"
mcp__context7__get-library-docs "/sqlalchemy/sqlalchemy" --topic "orm"
# Verify current query syntax

# Before implementing React hooks
mcp__context7__resolve-library-id "react"
mcp__context7__get-library-docs "/facebook/react" --topic "hooks"
# Confirm latest hook patterns

### Session Runtime Rules

**During every session:**

1. **Before writing code**: Check Context7 for library documentation updates
2. **During implementation**:
   - Run linter frequently (every 10-15 minutes)
   - Format code before committing
   - Add inline documentation for complex logic
3. **Before committing**:
   - Ensure all quality checks pass
   - Update relevant documentation
   - Capture learnings if discovered new patterns
4. **On completion**: Quality gates run with behavior depending on completion mode

### Quality Gate Order

Session completion runs checks in this order:
1. **Tests**: All tests must pass
2. **Linting**: No linting errors (auto-fix if configured)
3. **Formatting**: All files properly formatted
4. **Type Checking**: No type errors (if enabled)
5. **Documentation**: Updated as needed
6. **Library Verification**: All libraries checked via Context7

### Completion Modes

**Complete Mode (`sk end --complete`):**
- Quality gates are **enforced/blocking**
- All gates must pass to end session
- Work item marked as "completed"
- Use when work is truly finished

**Incomplete Mode (`sk end --incomplete`):**
- Quality gates **run but are non-blocking**
- Shows warnings but doesn't prevent session end
- Work item stays "in_progress" for resumption
- Extremely useful when running out of Claude context with failing gates
- Allows checkpointing work-in-progress without losing progress
```

#### 3. `work_items.json` - Work Tracking

Central state file tracking all work items:

```json
{
  "metadata": {
    "total_items": 45,
    "completed": 12,
    "in_progress": 1,
    "blocked": 2,
    "last_updated": "2025-10-09"
  },

  "milestones": {
    "mvp_auth": {
      "name": "MVP Authentication System",
      "work_items": ["feature_oauth", "feature_sessions", "feature_2fa"],
      "completed": 2,
      "target_date": "2025-10-15"
    }
  },

  "work_items": {
    "feature_oauth": {
      "id": "feature_oauth",
      "type": "feature",
      "title": "OAuth2 Authentication",
      "status": "completed",
      "priority": "high",

      "sessions": [3, 5],
      "milestone": "mvp_auth",

      "git": {
        "branch": "session-003-feature-oauth",
        "created_at": "2025-10-05T10:00:00Z",
        "status": "merged",
        "commits": ["abc123f", "def456a", "789ghi0"]
      },

      "dependencies": ["feature_user_model"],
      "dependents": ["feature_profile_sync"],

      "specification_path": "specs/auth/oauth.md",
      "implementation_paths": ["auth/oauth.py"],
      "test_paths": ["tests/test_oauth.py"],

      "outputs": [
        "OAuth2 authentication flow",
        "Token refresh mechanism"
      ],

      "validation_criteria": {
        "tests_pass": true,
        "coverage_min": 80
      },

      "metadata": {
        "created_at": "2025-10-01T10:00:00Z",
        "completed_at": "2025-10-05T16:30:00Z",
        "time_estimate": "4-6 hours",
        "actual_time": "5.5 hours"
      },

      "session_notes": {
        "session_003": "Started implementation, basic flow working",
        "session_005": "Completed with token refresh"
      }
    }
  }
}
```

**Git Tracking Field:**

The `git` field tracks branch information for work items that span multiple sessions or require significant work:

- **`branch`**: Name of the git branch created for this work item
- **`created_at`**: When the branch was created  
- **`status`**: Current branch status
  - `"in_progress"`: Work continuing, branch open
  - `"ready_to_merge"`: Work complete, ready for merge
  - `"merged"`: Branch merged to main
- **`commits`**: Array of commit SHAs on this branch

**Notes:**
- Not all work items need branches. Small work items completed in a single session may commit directly to main.
- The `git` field is only present for work items that have an associated branch.
- Multi-session work items should always have a dedicated branch to maintain clean git history.
- Session-start checks `git.status` to determine whether to create a new branch or continue existing one.
- Session-end updates `git.commits` and `git.status` based on work completion state.

#### 4. `status_update.json` - Session Summary

Updated after each session completion:

```json
{
  "session_id": "session_005",
  "timestamp": "2025-10-09T14:30:00Z",
  "work_items_completed": ["feature_oauth"],
  "work_items_started": ["feature_2fa"],

  "achievements": [
    "Implemented OAuth2 authentication flow",
    "Added token refresh logic",
    "Created 15 unit tests for auth module"
  ],

  "challenges_encountered": [
    "OAuth token refresh more complex than expected",
    "Had to handle edge case for expired tokens"
  ],

  "next_session_priorities": [
    "Complete 2FA implementation",
    "Add integration tests for auth flow",
    "Update API documentation"
  ],

  "documentation_references": [
    "docs/architecture.md - Updated auth flow diagram",
    "docs/prd.md - OAuth implementation marked complete"
  ],

  "metrics": {
    "files_changed": 12,
    "tests_added": 15,
    "lines_added": 450,
    "lines_removed": 120
  }
}
```

#### 5. `stack.txt` - Technology Stack

Auto-generated tech stack documentation:

```
# Technology Stack

## Languages
- Python 3.11 (primary backend)
- TypeScript 5.2 (frontend)

## Backend Framework
- FastAPI 0.104.1
- Pydantic 2.5 (data validation)

## Frontend Framework
- React 18.2
- Next.js 14.0

## Database
- PostgreSQL 15.2 (production)
- Redis 7.2 (caching)

## Testing
- pytest 7.4
- Playwright 1.40 (E2E)

## Infrastructure
- Docker 24.0
- Kubernetes 1.28

## External APIs
- Stripe API (payments)
- SendGrid (email)
- Google OAuth2

Generated: 2025-10-09 14:30:00
Last scanned: session_005
```

#### 6. `stack_updates.json` - Technology Change Log

```json
{
  "updates": [
    {
      "timestamp": "2025-10-09T14:30:00Z",
      "session": "session_005",
      "change_type": "addition",
      "component": "authentication",
      "technology": "authlib==1.2.1",
      "reasoning": "Needed OAuth2 support for Google/GitHub login",
      "alternatives_considered": [
        "python-social-auth",
        "django-allauth"
      ],
      "selection_rationale": "Best OAuth2/OIDC support, framework-agnostic",
      "breaking_changes": []
    },
    {
      "timestamp": "2025-10-05T10:15:00Z",
      "session": "session_003",
      "change_type": "version_upgrade",
      "component": "core",
      "technology": "fastapi: 0.103.0 → 0.104.1",
      "reasoning": "Security patch for CORS vulnerability",
      "breaking_changes": ["Modified CORS middleware signature"],
      "migration_notes": "Updated CORS config in main.py"
    }
  ]
}
```

#### 7. `learnings.json` - Knowledge Base

Curated project knowledge:

```json
{
  "last_curated": "2025-10-09T14:00:00Z",
  "curator": "session_curator",

  "categories": {
    "architecture_patterns": [
      {
        "pattern": "Repository Pattern for Database Access",
        "description": "All database queries go through repository classes, never direct ORM calls",
        "applies_to": ["database/**/*.py"],
        "learned_in": "session_002",
        "example": "database/repositories/user_repository.py:45-67",
        "rationale": "Enables easier testing and database migration"
      }
    ],

    "gotchas": [
      {
        "issue": "FastAPI async routes require async database connections",
        "context": "Using sync SQLAlchemy in async routes causes blocking",
        "solution": "Use asyncpg and async SQLAlchemy engine",
        "affected_sessions": ["session_001", "session_002"],
        "resolution_session": "session_003"
      }
    ],

    "best_practices": [
      {
        "practice": "Always use dependency injection for database sessions",
        "rationale": "Ensures proper connection handling and enables testing",
        "established_in": "session_001",
        "violations": 0,
        "example": "api/routes/users.py:get_db() dependency"
      }
    ],

    "technical_debt": [
      {
        "debt_item": "Error handling lacks retry logic for external APIs",
        "location": "services/*/api_client.py",
        "severity": "medium",
        "planned_resolution": "session_015",
        "workaround": "Manual retry in calling code",
        "impact": "Occasional failures on transient network issues"
      }
    ],

    "performance_insights": [
      {
        "insight": "Database connection pooling critical for performance",
        "metric": "Response time: 500ms → 50ms after pooling",
        "measured_in": "session_008",
        "action_taken": "Configured SQLAlchemy pool size to 20",
        "configuration": "database/engine.py:pool_size=20"
      }
    ]
  }
}
```

#### 8. `tree_updates.json` - Structure Change Log

```json
{
  "updates": [
    {
      "timestamp": "2025-10-09T14:30:00Z",
      "session": "session_005",
      "change_type": "directory_added",
      "path": "auth/providers/",
      "reasoning": "Separated OAuth providers into dedicated directory",
      "contains": ["google.py", "github.py", "base.py"],
      "architecture_impact": "Enables easy addition of new OAuth providers"
    },
    {
      "timestamp": "2025-10-09T14:35:00Z",
      "session": "session_005",
      "change_type": "file_moved",
      "from": "utils/db.py",
      "to": "database/connection.py",
      "reasoning": "Consolidated database code under database/ directory",
      "breaking_changes": [
        "Updated imports in 8 files"
      ],
      "migration_commits": ["abc123f"]
    },
    {
      "timestamp": "2025-10-09T14:40:00Z",
      "session": "session_005",
      "change_type": "branch_separation",
      "old_location": "services/email.py (800 lines)",
      "new_structure": "services/email/{sender.py, templates.py, queue.py}",
      "reasoning": "Email service grew too large, split by responsibility",
      "refactoring_approach": "Extracted classes into separate modules",
      "tests_updated": true
    }
  ]
}
```

---

## Part 3: Core Automation Scripts

### Script 1: `session_init.py`

**Purpose**: Initialize a new development session

**What it does:**
1. Validates git repository is clean
2. Loads `work_items.json` and dependency graph
3. Finds next available work item (dependencies satisfied)
4. Validates environment and prerequisites
5. Generates comprehensive session briefing
6. Updates work item status to `in_progress`
7. Outputs briefing file path and next steps

**Usage:**
```bash
# Auto-detect next work item (recommended)
sk start --next

# Specific work item
sk start --item feature_oauth

# Skip git checks (use cautiously)
sk start --next --skip-git-check
```

**Generated Briefing Format:**
```
# Session 5: OAuth2 Authentication Implementation

## Work Item Overview
- **ID**: feature_oauth
- **Type**: Feature
- **Priority**: High
- **Status**: in_progress

## Dependencies
✅ feature_user_model (completed in session_002)
✅ feature_sessions (completed in session_004)

## Objectives
1. Implement OAuth2 authentication flow
2. Add token refresh mechanism
3. Create comprehensive tests

## Specification
[Full spec from specs/auth/oauth.md]

## Previous Session Notes
Session 003: Started basic implementation, authentication flow working

## Implementation Checklist
- [ ] Create OAuth2 provider base class
- [ ] Implement Google OAuth provider
- [ ] Add token refresh logic
- [ ] Create unit tests (target: >80% coverage)
- [ ] Update API documentation

## Success Criteria
- All tests passing
- OAuth flow works end-to-end
- Token refresh handles expiration
- Documentation updated

## Related Files
- auth/oauth.py (to be created)
- tests/test_oauth.py (to be created)
- docs/architecture.md (auth section)

## Learnings to Reference
- "Always use async for external API calls" (session_002)
- "Repository pattern for database access" (established pattern)

---
Generated: 2025-10-09 14:30:00
Run `sk validate` (or `/sk:validate`) to check environment
```

### Script 2: `session_complete.py`

**Purpose**: Complete current session with quality checks

**What it does:**
1. Identifies current in-progress work item
2. Validates implementation files exist
3. Runs test suite
4. Runs linters/formatters
5. Updates project tree
6. Updates work item status to `completed`
7. Generates session summary
8. Creates standardized git commit
9. Updates `status_update.json`
10. Identifies next available work item

**Usage:**
```bash
# Auto-detect current work item
sk end

# Specific work item
sk end --item feature_oauth

# Force completion (skip tests - use cautiously)
sk end --force

# Skip tests
sk end --no-tests
```

**Generated Commit Message Format:**
```
Session 5: Implement OAuth2 Authentication

- Add OAuth2 authentication flow
- Implement token refresh mechanism
- Create 15 unit tests for auth module
- Update architecture documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Quality Gates Implementation:**

The script runs comprehensive quality checks before completion:

```python
def run_quality_gates(self, work_item: Dict, config: Dict) -> bool:
    """Execute all configured quality gates in order"""

    gates = []
    results = {}

    # Gate 1: Tests
    if config.post_session.tests_pass:
        print("🧪 Running tests...")
        test_result = self.run_tests(work_item)
        results['tests'] = test_result
        if not test_result and config.fail_on_error.tests:
            print("❌ Tests failed (blocking)")
            return False

    # Gate 2: Linting
    if config.runtime_standards.linting.enabled:
        print("🔍 Running linter...")
        lint_result = self.run_linter(config.runtime_standards.linting)
        results['linting'] = lint_result
        if not lint_result and config.runtime_standards.linting.fail_on_error:
            print("❌ Linting failed (blocking)")
            self.show_lint_errors()
            return False

    # Gate 3: Formatting
    if config.runtime_standards.formatting.enabled:
        print("✨ Checking formatting...")
        format_result = self.check_formatting(config.runtime_standards.formatting)
        results['formatting'] = format_result
        if not format_result:
            if config.runtime_standards.formatting.auto_fix:
                print("🔧 Auto-fixing formatting...")
                self.auto_format()
            else:
                print("❌ Formatting check failed")
                return False

    # Gate 4: Type Checking (optional)
    if config.runtime_standards.type_checking.enabled:
        print("🔎 Running type checker...")
        type_result = self.run_type_checker(config.runtime_standards.type_checking)
        results['type_checking'] = type_result
        if not type_result and config.runtime_standards.type_checking.fail_on_error:
            print("❌ Type checking failed (blocking)")
            return False
        elif not type_result:
            print("⚠️  Type checking failed (warning only)")

    # Gate 5: Documentation
    if config.post_session.documentation_updated:
        print("📝 Checking documentation...")
        docs_result = self.check_docs_updated()
        results['documentation'] = docs_result
        if not docs_result:
            print("⚠️  Documentation may need updates")

    # Gate 6: Library Documentation Verification
    if config.runtime_standards.mcp_tools.context7.required:
        print("📚 Verifying library documentation...")
        lib_docs_result = self.verify_library_docs(work_item)
        results['library_docs'] = lib_docs_result
        if not lib_docs_result:
            print("⚠️  Some libraries not verified via Context7")

    # Summary
    print("\n" + "="*50)
    print("Quality Gates Summary:")
    for gate, result in results.items():
        icon = "✅" if result else "❌"
        print(f"  {icon} {gate}")
    print("="*50 + "\n")

    return all(results.values())

def run_linter(self, linting_config: Dict) -> bool:
    """Run configured linter on changed files"""
    changed_files = get_changed_files()

    # Group by language
    files_by_lang = group_files_by_language(changed_files)

    all_passed = True
    for lang, files in files_by_lang.items():
        if lang not in linting_config.tools:
            continue

        tool_config = linting_config.tools[lang]
        cmd = tool_config['command']

        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode != 0:
                if tool_config.get('auto_fix'):
                    print(f"  🔧 Auto-fixing {lang} issues...")
                    fix_cmd = cmd + " --fix"
                    subprocess.run(fix_cmd.split(), cwd=self.project_root)
                else:
                    all_passed = False
                    print(f"  ❌ {lang} linting failed:")
                    print(f"     {result.stdout}")
        except Exception as e:
            print(f"  ⚠️  Error running {lang} linter: {e}")
            all_passed = False

    return all_passed

def verify_library_docs(self, work_item: Dict) -> bool:
    """Verify all used libraries were checked via Context7"""
    # Check session notes for Context7 usage
    session_notes = work_item.get('session_notes', {})
    current_session = max(work_item.get('sessions', [0]))

    # Look for library imports in implementation files
    impl_files = work_item.get('implementation_paths', [])
    libraries_used = extract_libraries_from_files(impl_files)

    # Check if libraries were verified
    important_libraries = config.runtime_standards.mcp_tools.context7.libraries_to_always_check

    unverified = []
    for lib in libraries_used:
        if lib in important_libraries:
            # Check if Context7 was used for this library
            notes = session_notes.get(f'session_{current_session:03d}', '')
            if f'context7_{lib}' not in notes.lower():
                unverified.append(lib)

    if unverified:
        print(f"  ⚠️  Libraries not verified via Context7: {', '.join(unverified)}")
        print(f"     Consider checking documentation for accuracy")
        return False

    return True
```

**Override Flags:**
```bash
# Skip specific gates
sk end --no-tests --no-lint

# Force completion despite failures
sk end --force

# Skip only specific check
sk end --skip-gate linting
```

### Script 3: `session_validate.py`

**Purpose**: Comprehensive pre/post-session validation

**What it does:**
1. Git repository validation
2. File structure validation
3. Work item data integrity checks
4. Dependency validation
5. Environment validation (Python version, packages)
6. Test infrastructure validation
7. Custom validation rules from `.sessionrc.json`

**Usage:**
```bash
# Full validation
sk validate

# Validate specific work item
sk validate --item feature_oauth

# Fix common issues automatically
sk validate --fix-issues
```

**Validation Checks:**
- ✅ Git repository clean or on appropriate branch
- ✅ Required directories exist
- ✅ work_items.json is valid and consistent
- ✅ Dependencies are satisfied for current work item
- ✅ Implementation files have valid syntax
- ✅ Test files exist
- ✅ Python environment matches requirements.txt
- ✅ Custom validation rules pass

### Script 4: `work_item_update.py`

**Purpose**: Safe atomic updates to work_items.json

**What it does:**
1. Loads work_items.json with validation
2. Updates specified fields
3. Validates state transitions (e.g., can't go from `not_started` to `completed`)
4. Updates metadata counts
5. Creates backup before saving
6. Saves atomically (temp file + rename)

**Usage:**
```bash
# Update status
sk work-update feature_oauth --status completed

# Update paths
sk work-update feature_oauth \
  --implementation-path auth/oauth.py \
  --test-path tests/test_oauth.py

# List all work items
sk work-update --list

# Show specific work item
sk work-update feature_oauth --show

# Restore from backup
sk work-update --restore-backup
```

**Valid Status Transitions:**
- `not_started` → `in_progress`, `blocked`
- `in_progress` → `completed`, `blocked`, `not_started`
- `completed` → `in_progress` (re-opening)
- `blocked` → `in_progress`, `not_started`

### Script 5: `generate_stack.py`

**Purpose**: Auto-detect and document technology stack

**What it does:**
1. Scans project for language files (*.py, *.ts, *.js, etc.)
2. Parses package files (requirements.txt, package.json, Cargo.toml, etc.)
3. Detects frameworks from imports and config files
4. Identifies databases from connection strings
5. Detects external APIs from code
6. Generates formatted stack.txt
7. Compares with previous version
8. Reports changes

**Usage:**
```bash
# Generate and save
solokit generate-stack

# Show changes from last scan
solokit generate-stack --show-changes

# Output only (don't save)
solokit generate-stack --output-only
```

**Detection Strategy:**
- **Languages**: File extensions (.py, .ts, .js, .go, .rs, etc.)
- **Backend Frameworks**: Import analysis (FastAPI, Django, Express, etc.)
- **Frontend Frameworks**: package.json dependencies (React, Vue, Svelte)
- **Databases**: Connection strings, ORM imports (SQLAlchemy, Prisma)
- **Testing**: pytest, jest, vitest in dependencies
- **Infrastructure**: Dockerfile, docker-compose.yml, kubernetes/*.yaml

### Script 6: `generate_tree.py`

**Purpose**: Deterministic project structure documentation

**What it does:**
1. Runs `tree` command with consistent filtering
2. Ignores common noise (.git, __pycache__, node_modules, etc.)
3. Compares with previous tree
4. Shows additions and removals
5. Updates project_tree.txt
6. Provides statistics

**Usage:**
```bash
# Generate and save
solokit generate-tree

# Show changes
solokit generate-tree --show-changes

# Include hidden files
solokit generate-tree --include-hidden

# Display current tree
solokit generate-tree --display-current
```

**Filtered Items:**
```
.git, __pycache__, *.pyc, .pytest_cache, .venv, venv,
node_modules, .DS_Store, *.egg-info, .mypy_cache,
.ruff_cache, *.log, *.tmp, *.backup
```

### Script 7: `curate_learnings.py`

**Purpose**: Intelligent learning curation and organization

**What it does:**
1. Loads raw learnings from session summaries
2. Categorizes learnings (patterns, gotchas, best practices, etc.)
3. Merges similar/duplicate learnings
4. Archives obsolete learnings
5. Generates learning summary reports
6. Updates learnings.json

**Usage:**
```bash
# Run curation
sk learn-curate

# Dry run (show what would change)
sk learn-curate --dry-run

# Force recategorization of all learnings
sk learn-curate --recategorize-all

# Generate summary report
sk learn-curate --report
```

**Curation Rules:**
- Run every 5-10 sessions
- Merge learnings with >80% similarity
- Archive learnings older than 50 sessions if not referenced
- Promote frequently-referenced gotchas to best practices
- Suggest technical debt items for learnings with "TODO" or "workaround"

---

## Part 4: Session Workflow

### Starting a New Session

**User initiates session:**
```
User: /start
```

**Claude's workflow:**
1. Read CLAUDE.md (automatic)
2. Sees `/start` trigger in protocol
3. Runs: `sk start --next`
4. Validates git status (clean working directory)
5. Creates or resumes branch for work item
6. Reads generated briefing file
7. Confirms understanding:
   ```
   Session 5 initialized: OAuth2 Authentication

   I'll be implementing:
   - OAuth2 authentication flow
   - Token refresh mechanism
   - Comprehensive tests

   Dependencies satisfied:
   ✅ User model (session_002)
   ✅ Session management (session_004)

   Ready to begin. Shall I start with the OAuth2 base class?
   ```

### During Session

**Claude follows briefing:**
- Implements features per specification
- Writes tests alongside code (TDD)
- Updates documentation as changes are made
- References learnings when relevant
- Asks clarifying questions when needed

**User can check status:**
```
User: @status
Claude: [runs work_item_update.py --list]
Currently working on: feature_oauth (in_progress)
Completed today:
- Created OAuth2 base class (auth/providers/base.py)
- Implemented Google provider (auth/providers/google.py)
- Added 8 unit tests (tests/test_oauth.py)

Next: Token refresh mechanism
```

### Ending Session

**User signals completion:**
```
User: /end
```

**Claude's workflow:**
1. Runs: `sk end`
2. Executes:
   - Runs test suite
   - Validates code quality
   - Updates project tree
   - Updates work item status
   - Creates git commit
   - Generates session summary
3. Reports results:
   ```
   Session 5 completed successfully!

   ✅ All tests passing (18 tests, 85% coverage)
   ✅ Code quality checks passed
   ✅ Documentation updated
   ✅ Committed: "Session 5: Implement OAuth2 Authentication"

   Achievements:
   - OAuth2 authentication flow working
   - Token refresh mechanism implemented
   - 15 unit tests added

   Next session suggestion:
   - feature_2fa: Two-Factor Authentication
   - Dependencies satisfied, ready to start

   Session summary: .session/history/session_005_summary.md
   ```
4. Git operations:
   - Commits changes with standardized message
   - Pushes branch to remote
   - Optionally merges if work item complete

---

## Part 5: Advanced Features

### Dependency-Driven Workflow

**The `--next` Flag:**

Instead of rigid sequences, work items are selected by dependency satisfaction:

```json
{
  "feature_profile": {
    "dependencies": ["feature_oauth", "feature_user_model"],
    "status": "not_started"
  },
  "feature_oauth": {
    "dependencies": ["feature_user_model"],
    "status": "completed"
  },
  "feature_user_model": {
    "dependencies": [],
    "status": "completed"
  }
}
```

`session_init.py --next` finds `feature_profile` because all dependencies are completed.

**Benefits:**
- No artificial ordering constraints
- Parallel work paths possible
- Adapts to complexity changes
- Blocks work that isn't ready

### Milestone Organization

Work items grouped into milestones for planning:

```json
{
  "milestones": {
    "mvp_auth": {
      "name": "MVP Authentication System",
      "work_items": [
        "feature_oauth",
        "feature_sessions",
        "feature_2fa",
        "feature_password_reset"
      ],
      "target_date": "2025-10-15",
      "completed": 2,
      "total": 4
    },
    "mvp_payments": {
      "name": "Payment Integration",
      "work_items": [
        "feature_stripe_integration",
        "feature_subscription_management",
        "feature_invoicing"
      ],
      "dependencies": ["mvp_auth"],
      "target_date": "2025-10-30"
    }
  }
}
```

### Learning Accumulation System

**Raw Learning Capture:**

During sessions, Claude adds learnings to session summaries:

```json
{
  "session_005": {
    "learnings": [
      {
        "type": "gotcha",
        "content": "OAuth state parameter must be cryptographically random",
        "context": "Using simple random numbers led to security vulnerability"
      },
      {
        "type": "pattern",
        "content": "Provider classes should inherit from BaseOAuthProvider",
        "rationale": "Ensures consistent interface and shared token refresh logic"
      }
    ]
  }
}
```

**Curation Process:**

Every 5-10 sessions, `curate_learnings.py` processes raw learnings:

1. **Categorization**: Assigns to architecture_patterns, gotchas, best_practices, etc.
2. **Deduplication**: Merges similar learnings
3. **Promotion**: Frequently-referenced gotchas → best practices
4. **Archival**: Old, unreferenced learnings → archive
5. **Technical Debt Detection**: Learnings with "TODO" → technical_debt category

**Result**: Clean, organized knowledge base that grows with the project.

### Stack Change Tracking

**Automatic Detection:**

`generate_stack.py` runs at session completion and detects:
- New dependencies added
- Version upgrades
- Removed dependencies
- Configuration changes

**Change Logging:**

Prompts Claude to provide reasoning:

```
Detected new dependency: authlib==1.2.1

Please provide:
1. Reasoning for addition
2. Alternatives considered
3. Selection rationale
```

Claude responds, and `stack_updates.json` is updated with full context.

### Project Structure Evolution

**Tree Diffing:**

`generate_tree.py --show-changes` shows:

```
Added (5):
  auth/providers/
  auth/providers/google.py
  auth/providers/github.py
  auth/providers/base.py
  tests/auth/test_oauth.py

Removed (1):
  utils/auth_helpers.py

Modified structure:
  auth/ directory now organized by OAuth providers
```

**Change Reasoning:**

Prompts Claude to log reasoning in `tree_updates.json`:

```json
{
  "change_type": "directory_added",
  "path": "auth/providers/",
  "reasoning": "Separated OAuth providers for better organization",
  "architecture_impact": "Enables easy addition of new providers"
}
```

---

## Part 6: Integration with AI-Augmented Solo Development Framework

### Framework Alignment

The AI-Augmented Solo Development Framework defines **8 phases** of software development:

1. Discovery & Requirements
2. Architecture & Design
3. Environment Setup & Foundation
4. Iterative Development
5. Integration & System Testing
6. Deployment & Launch
7. Operations & Maintenance
8. Evolution & Continuous Improvement

**Solokit provides the execution layer** for these phases, particularly Phase 4 (Iterative Development).

### Phase Mapping

#### Phase 1-2: Planning & Architecture
- Create initial documentation (vision.md, prd.md, architecture.md)
- Initialize Solokit in project: `plugin initialization`
- Define work items for implementation
- Set up milestones aligned with architecture

#### Phase 3: Foundation
- **Work Item Type**: `setup`
- Tasks: CI/CD pipeline, project structure, test framework
- Solokit tracks foundation setup through work items

#### Phase 4: Iterative Development
- **Core Solokit Phase**
- Work items: features, bugs, refactors
- Session-by-session implementation
- Continuous quality enforcement
- Learning accumulation

#### Phase 5-6: Testing & Deployment
- **Work Item Type**: `integration`, `deployment`
- Solokit tracks testing and deployment tasks
- Validation gates ensure production readiness

#### Phase 7-8: Operations & Evolution
- **Work Item Type**: `maintenance`, `enhancement`
- Solokit continues tracking improvements
- Learnings guide optimization

### AI Role Integration

The framework defines AI as specialist roles:
- Product Manager
- Senior Architect
- Development Expert
- QA Specialist
- DevOps Expert
- Security Specialist
- UX/UI Expert

**Solokit enhances these roles** by providing context:

```markdown
## Session Briefing: feature_security_audit

Your Role: Security Specialist

Context from learnings.json:
- "Always sanitize user input" (best practice, established session_002)
- "Use parameterized queries for SQL" (security pattern)
- "JWT tokens need short expiration" (security requirement)

Previous security work:
- session_003: Implemented OAuth2 security
- session_007: Added CSRF protection

Apply security expertise with project context.
```

### Documentation Standards

Framework emphasizes comprehensive documentation:
- Architecture Decision Records (ADRs)
- API Documentation
- Operational Documentation
- Code Documentation

**Solokit automates documentation tracking:**
- `tree_updates.json` logs structural decisions (ADR-like)
- `stack_updates.json` logs technology decisions
- `learnings.json` captures implementation insights
- Session summaries provide operational context

---

## Part 7: Implementation Guide

### Installing Solokit in a Project

**Prerequisites:**
- Git repository
- Python 3.11+
- Project documentation (vision.md, architecture.md recommended)

**Installation:**

1. Install the Session plugin in Claude Code
2. Navigate to your project
3. Run `/sk:start` to initialize the `.session/` directory

The plugin will automatically create the necessary directory structure when you start your first session.
```

**Initialization Prompts:**

```
Session-Driven Development Initialization

Project name: my-awesome-app
Project type: (web_app/library/data_pipeline/cli_tool): web_app
Work item model: (feature_based/sprint_based/kanban): feature_based

Validation rules:
  Require clean git before sessions? (y/n): y
  Run tests before session completion? (y/n): y
  Require linting pass? (y/n): y

Creating directory structure...
✅ .session/ created
✅ .session/tracking/ created
✅ Solokit installed (solokit command available)
✅ .sessionrc.json created
✅ CLAUDE.md generated

Next steps:
1. Review .sessionrc.json configuration
2. Create docs/vision.md with project goals
3. Define initial work items: /work-item create
4. Start first session: /start
```

### Creating Work Items

**Interactive Creation:**

```bash
/work-item create
```

Prompts:
```
Work item type: (feature/bug/refactor/setup): feature
Title: OAuth2 Authentication
Priority: (low/medium/high/critical): high
Dependencies (comma-separated IDs, or none): feature_user_model

Milestone: (optional): mvp_auth

Specification file: (path or skip): specs/auth/oauth.md

Estimated sessions: 2-4

Created: feature_oauth
Specification template created at: specs/auth/oauth.md
```

**Bulk Creation from File:**

```bash
# Create work_items.yaml
/work-item import work_items.yaml
```

Example `work_items.yaml`:
```yaml
milestones:
  - id: mvp_auth
    name: MVP Authentication System
    target_date: 2025-10-15

work_items:
  - id: feature_user_model
    type: feature
    title: User Model and Database Schema
    priority: high
    milestone: mvp_auth
    sessions: 1-2

  - id: feature_oauth
    type: feature
    title: OAuth2 Authentication
    priority: high
    milestone: mvp_auth
    dependencies: [feature_user_model]
    sessions: 2-4
```

### Configuring Validation Rules

Edit `.sessionrc.json`:

```json
{
  "validation_rules": {
    "pre_session": {
      "git_clean": true,
      "dependencies_met": true,
      "environment_valid": true,
      "custom_checks": [
        "scripts/check_api_keys.py",
        "scripts/validate_db_connection.py"
      ]
    },
    "post_session": {
      "tests_pass": true,
      "test_coverage_min": 80,
      "linting_pass": true,
      "type_check_pass": false,
      "documentation_updated": true,
      "custom_checks": [
        "scripts/check_security_scan.py"
      ]
    }
  }
}
```

**Custom Check Script Example:**

```python
# scripts/check_api_keys.py
import os
import sys

required_keys = ['STRIPE_API_KEY', 'SENDGRID_API_KEY']

missing = [key for key in required_keys if not os.getenv(key)]

if missing:
    print(f"❌ Missing API keys: {', '.join(missing)}")
    sys.exit(1)

print("✅ All required API keys present")
sys.exit(0)
```

### Customizing CLAUDE.md

Template is auto-generated but can be customized:

```markdown
# Project Instructions for Claude Code

## Session Protocol
[Auto-generated standard protocol]

## Project-Specific Guidelines

### Coding Standards
- Use async/await for all database operations
- Repository pattern for database access
- Pydantic models for all API request/response schemas
- Type hints required for all functions

### Testing Requirements
- Minimum 80% coverage
- Test files must mirror source structure
- Use pytest fixtures for test data
- No mocking of database (use test database)

### Security Requirements
- Never log sensitive data (passwords, tokens, API keys)
- Always use parameterized queries
- Validate all user input with Pydantic
- Include security consideration in all API endpoints

### Documentation
- Update API docs with every endpoint change
- Add ADR for significant architectural decisions
- Document all external API integrations

## Key Architecture Decisions

### Decision: Use FastAPI instead of Django
**Rationale**: Need async support and OpenAPI auto-generation
**Trade-offs**: Less built-in admin, more manual auth
**Session**: session_001

### Decision: PostgreSQL over MongoDB
**Rationale**: Relational data model, ACID guarantees
**Trade-offs**: Less flexible schema
**Session**: session_002

[Auto-generated sections follow...]
```

---

## Part 8: Advanced Configuration

### Work Item Types

Define custom work item types in `.sessionrc.json`:

```json
{
  "work_item_types": {
    "feature": {
      "template": "templates/feature_spec.md",
      "typical_sessions": "2-4",
      "validation": {
        "tests_required": true,
        "coverage_min": 80,
        "documentation_required": true
      }
    },
    "bug": {
      "template": "templates/bug_report.md",
      "typical_sessions": "1-2",
      "validation": {
        "tests_required": true,
        "regression_test_required": true
      }
    },
    "refactor": {
      "template": "templates/refactor_plan.md",
      "typical_sessions": "1-3",
      "validation": {
        "tests_required": true,
        "no_functionality_change": true,
        "performance_test": true
      }
    },
    "security": {
      "template": "templates/security_task.md",
      "typical_sessions": "1-2",
      "validation": {
        "security_scan_required": true,
        "penetration_test": true,
        "security_review": true
      },
      "priority": "critical"
    }
  }
}
```

### Project Type Presets

Solokit comes with preset configurations:

#### Web Application Preset
```json
{
  "preset": "web_application",
  "typical_structure": {
    "frontend": "frontend/",
    "backend": "backend/",
    "tests": "tests/",
    "docs": "docs/"
  },
  "validation_rules": {
    "e2e_tests_required": true,
    "api_documentation": true
  }
}
```

#### Python Library Preset
```json
{
  "preset": "python_library",
  "typical_structure": {
    "source": "src/",
    "tests": "tests/",
    "docs": "docs/"
  },
  "validation_rules": {
    "docstrings_required": true,
    "type_hints_required": true,
    "changelog_updated": true
  }
}
```

#### Data Pipeline Preset
```json
{
  "preset": "data_pipeline",
  "typical_structure": {
    "stages": "pipeline/stages/",
    "transforms": "pipeline/transforms/",
    "tests": "tests/"
  },
  "validation_rules": {
    "data_validation_required": true,
    "idempotency_required": true
  }
}
```

#### Microservices Preset
```json
{
  "preset": "microservices",
  "typical_structure": {
    "services": "services/",
    "shared": "shared/",
    "tests": "tests/"
  },
  "validation_rules": {
    "service_isolation": true,
    "api_versioning": true,
    "health_checks": true
  }
}
```

### Curation Configuration

Control learning curation behavior:

```json
{
  "curation": {
    "frequency": 5,
    "auto_categorize": true,
    "similarity_threshold": 0.8,
    "archive_after_sessions": 50,
    "promote_gotchas_threshold": 3,
    "technical_debt_keywords": [
      "TODO",
      "FIXME",
      "workaround",
      "temporary",
      "hack"
    ]
  }
}
```

### Multi-Language Support

Solokit can handle polyglot projects:

```json
{
  "languages": {
    "python": {
      "test_command": "pytest",
      "lint_command": "ruff check",
      "format_command": "black ."
    },
    "typescript": {
      "test_command": "npm test",
      "lint_command": "eslint .",
      "format_command": "prettier --write ."
    },
    "rust": {
      "test_command": "cargo test",
      "lint_command": "cargo clippy",
      "format_command": "cargo fmt"
    }
  }
}
```

Session completion runs appropriate commands based on changed files.

---

## Part 9: Best Practices

### Work Item Granularity

**Good Work Item Size:**
- 1-4 sessions of focused work
- Single, clear objective
- Testable completion criteria
- Well-defined scope

**Too Large (Split It):**
```
❌ "Build authentication system"
✅ "Implement OAuth2 flow"
✅ "Add session management"
✅ "Implement 2FA"
✅ "Add password reset"
```

**Too Small (Combine It):**
```
❌ "Add import statement"
❌ "Create empty class file"
✅ "Implement user repository pattern"
```

### Session Duration

**Optimal Session Length: 30-90 minutes**

**Too Short (<30 min):**
- High overhead from session init/complete
- Not enough time for meaningful progress

**Too Long (>2 hours):**
- Context becomes overwhelming
- Quality may degrade
- Harder to maintain focus

**Sweet Spot: 60 minutes**
- Focused work block
- Time for implementation + testing
- Manageable context size

### Dependency Management

**Define Dependencies Upfront:**

```json
{
  "feature_profile_picture": {
    "dependencies": [
      "feature_file_upload",
      "feature_image_processing",
      "feature_user_model"
    ]
  }
}
```

**Don't Start Until Dependencies Done:**
- Solokit will prevent starting `feature_profile_picture` if dependencies incomplete
- Ensures stable foundation
- Prevents rework

**Use Dependency Graph for Planning:**

```bash
/work-item graph --output dependency_graph.png
```

Visualizes work item relationships and critical path.

### Learning Capture

**Capture Learnings Immediately:**

During session, when you discover something:
```
Claude: I've discovered that FastAPI requires async database connections.
This is important - should I add this to learnings?

User: Yes

Claude: Added to session_005 learnings:
- Type: gotcha
- Content: "FastAPI async routes require async database connections"
- Context: "Using sync SQLAlchemy in async routes causes blocking"
```

**Be Specific:**

❌ "Database was slow"
✅ "Database queries slow without connection pooling (500ms → 50ms after pooling)"

❌ "Security is important"
✅ "OAuth state parameter must be cryptographically random to prevent CSRF"

### Documentation Strategy

**Living Documentation:**
- Update docs as code changes (not after)
- Use doc generation where possible (API docs from code)
- Keep ADRs updated when decisions change

**Documentation Types:**

1. **Vision** (docs/vision.md): Why the project exists
2. **Architecture** (docs/architecture.md): System design
3. **Development Plan** (docs/development_plan.md): Roadmap
4. **API Docs** (auto-generated): Interface contracts
5. **Operational Docs** (docs/operations/): How to deploy/monitor
6. **Learning Docs** (learnings.json): Institutional knowledge

### Git Workflow

**Branching Strategy:**

```bash
# Option 1: Session branches
git checkout -b session-005-oauth
# Complete session
git checkout main
git merge session-005-oauth

# Option 2: Feature branches
git checkout -b feature/oauth
# Multiple sessions on same branch
git checkout main
git merge feature/oauth

# Option 3: Direct to main (if solo)
# Work directly on main with session commits
```

**Commit Messages:**

Solokit auto-generates standardized commits:
```
Session 5: Implement OAuth2 Authentication

- Add OAuth2 authentication flow
- Implement token refresh mechanism
- Create 15 unit tests for auth module
- Update architecture documentation

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Testing Philosophy

**Test Pyramid:**
- 60% Unit tests (fast, isolated)
- 25% Integration tests (components together)
- 10% E2E tests (full user flows)
- 5% Manual exploratory

**TDD Approach:**
1. Write test first
2. Implement to pass test
3. Refactor
4. Repeat

**Coverage Targets:**
- Minimum: 80% overall
- Critical paths: 100% (auth, payments, security)
- Utilities: 90%+

---

## Part 10: Troubleshooting

### Common Issues

#### Issue: "Working directory not clean"

**Cause:** Git has uncommitted changes

**Solution:**
```bash
# Option 1: Commit changes
git add .
git commit -m "WIP: Save progress"

# Option 2: Stash changes
git stash

# Option 3: Skip check (use cautiously)
sk start --next --skip-git-check
```

#### Issue: "Dependency not completed"

**Cause:** Trying to start work item before dependencies done

**Solution:**
```bash
# Check which dependencies are incomplete
/work-item show feature_oauth

# Complete dependencies first
/work-item update feature_user_model --status completed
```

#### Issue: "Agent status file corrupted"

**Cause:** work_items.json has invalid JSON or inconsistent data

**Solution:**
```bash
# Validate file
sk work-update --validate

# Restore from backup
sk work-update --restore-backup

# Fix issues automatically
sk validate --fix-issues
```

#### Issue: "Tests failing at session completion"

**Cause:** Implementation has bugs or incomplete

**Solution:**
```bash
# Fix tests first
pytest -v

# Or force completion (skip tests) - use cautiously
sk end --no-tests

# Or complete with failures for WIP commits
sk end --force
```

#### Issue: "Session briefing unclear"

**Cause:** Work item specification insufficient

**Solution:**
```bash
# Update specification
vim .session/specs/feature_oauth.md

# Regenerate briefing
solokit generate-briefing --item feature_oauth --regenerate
```

### Debugging Solokit Scripts

**Enable verbose output:**
```bash
sk start --next --verbose
```

**Check script logs:**
```bash
tail -f .session/logs/session_init.log
```

**Validate environment:**
```bash
sk validate --verbose
```

---

## Part 11: Extending Solokit

### Custom Validation Rules

Create custom validation script:

```python
# scripts/validate_api_versioning.py
"""
Custom validation: Ensure all API routes have version prefix
"""
import sys
from pathlib import Path

def check_api_versioning():
    api_files = Path("api/routes").glob("*.py")

    violations = []
    for file in api_files:
        content = file.read_text()
        if '@router.get("/' in content:
            if not '@router.get("/v1/' in content:
                violations.append(f"{file}: Missing /v1 prefix")

    if violations:
        print("❌ API versioning violations:")
        for v in violations:
            print(f"   {v}")
        return False

    print("✅ All API routes properly versioned")
    return True

if __name__ == "__main__":
    sys.exit(0 if check_api_versioning() else 1)
```

Add to `.sessionrc.json`:
```json
{
  "validation_rules": {
    "post_session": {
      "custom_checks": [
        "scripts/validate_api_versioning.py"
      ]
    }
  }
}
```

### Custom Work Item Types

Define specialized work item types:

```json
{
  "work_item_types": {
    "spike": {
      "template": "templates/spike_template.md",
      "description": "Time-boxed research or proof-of-concept",
      "typical_sessions": "1",
      "validation": {
        "tests_required": false,
        "documentation_required": true,
        "findings_report_required": true
      }
    },
    "performance_optimization": {
      "template": "templates/performance_template.md",
      "typical_sessions": "1-2",
      "validation": {
        "before_after_benchmarks": true,
        "tests_required": true,
        "no_functionality_change": true
      }
    },
    "database_migration": {
      "template": "templates/migration_template.md",
      "typical_sessions": "1",
      "validation": {
        "rollback_script": true,
        "data_backup": true,
        "staging_test": true
      }
    }
  }
}
```

### Integration with CI/CD

**GitHub Actions Integration:**

```yaml
# .github/workflows/session-checks.yml
name: Session Quality Checks

on:
  push:
    branches: [main, 'session-*']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Solokit
        run: plugin installation

      - name: Validate work items
        run: sk work-update --validate

      - name: Check session completeness
        run: sk validate

      - name: Verify documentation
        run: |
          if git diff --name-only HEAD~1 | grep -q '.py$'; then
            python scripts/check_docs_updated.py
          fi
```

### Plugin System (Future)

Solokit will support plugins:

```python
# .session/plugins/notion_sync.py
from session_dev.plugin import Plugin

class NotionSyncPlugin(Plugin):
    """Sync work items to Notion database"""

    def on_work_item_created(self, work_item):
        """Called when new work item created"""
        notion_api.create_page(work_item)

    def on_session_complete(self, session_summary):
        """Called when session completes"""
        notion_api.update_page(session_summary)
```

Enable in `.sessionrc.json`:
```json
{
  "plugins": [
    ".session/plugins/notion_sync.py",
    ".session/plugins/slack_notifications.py"
  ]
}
```

---

## Part 12: Real-World Example

### Scenario: Building a SaaS Application

**Project**: Task management SaaS with team collaboration

**Phase 1: Setup**

```bash
# Create project
mkdir taskmaster && cd taskmaster
git init

# Initialize Solokit
plugin initialization

# Select: web_application preset
# Enable: tests, linting, documentation

# Create docs
vim docs/vision.md
vim docs/architecture.md
vim docs/development_plan.md
```

**Phase 2: Define Work Items**

```yaml
# work_items.yaml
milestones:
  - id: mvp_auth
    name: Authentication & User Management
    target_date: 2025-11-01

  - id: mvp_tasks
    name: Core Task Management
    target_date: 2025-11-15

  - id: mvp_teams
    name: Team Collaboration
    target_date: 2025-12-01

work_items:
  # Milestone 1: Auth
  - id: setup_project_structure
    type: setup
    title: Project Structure & CI/CD
    milestone: mvp_auth
    sessions: 2

  - id: feature_user_model
    type: feature
    title: User Model & Database
    milestone: mvp_auth
    dependencies: [setup_project_structure]
    sessions: 1-2

  - id: feature_oauth
    type: feature
    title: OAuth2 Authentication
    milestone: mvp_auth
    dependencies: [feature_user_model]
    sessions: 2-3

  # Milestone 2: Tasks
  - id: feature_task_model
    type: feature
    title: Task Model & CRUD
    milestone: mvp_tasks
    dependencies: [feature_user_model]
    sessions: 2

  - id: feature_task_api
    type: feature
    title: Task Management API
    milestone: mvp_tasks
    dependencies: [feature_task_model]
    sessions: 2-3

  # Milestone 3: Teams
  - id: feature_team_model
    type: feature
    title: Team & Membership
    milestone: mvp_teams
    dependencies: [feature_user_model]
    sessions: 2
```

```bash
/work-item import work_items.yaml
```

**Phase 3: Development Sessions**

**Session 1: Project Setup**

```
User: /start

Claude:
Session 1 initialized: Project Structure & CI/CD

I'll be setting up:
- FastAPI project structure
- PostgreSQL database configuration
- pytest test framework
- GitHub Actions CI/CD
- Docker configuration

Ready to begin. Shall I start with the FastAPI project structure?

User: Yes, let's use Python 3.11, FastAPI, and PostgreSQL

[Claude implements project structure...]

User: /end

Claude:
Session 1 completed successfully!

✅ Project structure created
✅ CI/CD pipeline working
✅ Docker configuration complete
✅ 5 tests passing

Next session: feature_user_model
Dependencies satisfied, ready to start.
```

**Session 2: User Model**

```
User: /start

Claude:
Session 2 initialized: User Model & Database

Context from previous session:
- Database: PostgreSQL with SQLAlchemy async
- Project structure: Standard FastAPI layout
- Testing: pytest with async support

I'll implement:
- User model with email, password hash
- Database migrations with Alembic
- User repository pattern
- Comprehensive tests

[Implementation proceeds...]

Learning captured: "Use async SQLAlchemy for database operations"

User: /end

Claude:
Session 2 completed successfully!

✅ User model implemented
✅ Database migrations working
✅ Repository pattern established
✅ 12 tests passing (88% coverage)

Learnings captured:
- Repository pattern for database access (architecture pattern)
- Async SQLAlchemy required for FastAPI (gotcha)

Next session: feature_oauth
Dependencies satisfied, ready to start.
```

**Session 3-4: OAuth Implementation**

Similar pattern continues...

**Session 10: Discovering Technical Debt**

```
User: /start

Claude:
Session 10 initialized: Task Management API

Context from learnings:
- Repository pattern established (session_002)
- Always validate input with Pydantic (session_005)

Previous technical debt noted:
- Error handling lacks retry logic (medium priority)

[During implementation...]

Claude:
I notice the OAuth token refresh doesn't have retry logic for network failures.
This is the same technical debt pattern from session_005.

Should I:
1. Add retry logic now (increases session scope)
2. Create separate work item for retry logic refactor
3. Add workaround and document technical debt

User: Option 2

Claude: Created work item: refactor_retry_logic
Added to technical debt in learnings.json
Continuing with current implementation...
```

**Session 15: Learning Curation**

```bash
# Automatic curation runs
sk learn-curate

Curation Report:
✅ Categorized 8 new learnings
✅ Merged 3 duplicate gotchas
✅ Promoted "Repository pattern" to best practice (referenced 6 times)
✅ Identified 2 new technical debt items
✅ Archived 1 obsolete learning

Updated learnings.json
```

**Session 20: Milestone 1 Complete**

```
Status:
Milestone: mvp_auth (100% complete)
- setup_project_structure: ✅
- feature_user_model: ✅
- feature_oauth: ✅

Total sessions: 8
Estimated: 5-7
Actual: 8 (OAuth was more complex than expected)

Learnings captured: 15
Best practices established: 4
Technical debt items: 2

Next milestone: mvp_tasks
Ready to start: feature_task_model
```

**Result After 40 Sessions:**

```
Project: taskmaster
Total sessions: 40
Duration: 8 weeks
Milestones completed: 3/3

Work items: 24
- Completed: 24
- Quality: 85% avg test coverage
- Documentation: 100% up-to-date

Learnings accumulated: 47
- Architecture patterns: 12
- Best practices: 8
- Gotchas documented: 15
- Technical debt: 7 (4 resolved, 3 planned)

Stack changes: 15
- Dependencies added: 12
- Upgrades: 3
- All changes documented with reasoning

Outcome: Functional MVP shipped on schedule
```

---

## Part 13: Package Distribution

### Installation

The Session plugin is installed through Claude Code's plugin system. Refer to PLUGIN_IMPLEMENTATION_PLAN_PHASES_0-4.md and PLUGIN_IMPLEMENTATION_PLAN_PHASES_5+.md for installation instructions.

### Plugin Commands

```bash
# Initialize Solokit in project
/sk:start

# Work item management
/work-item create
/work-item list [--status in_progress]
/work-item show <id>
/work-item update <id> --status completed
/work-item graph [--output graph.png]
/work-item import <file.yaml>

# Session management
/sk:start [--next|--item <id>]
/sk:end
/sk:validate
/sk:status

# Documentation
/docs update
/docs generate-briefing <item-id>
/docs stack-scan

# Learning management
/learning curate
/learning show [--category patterns]
/learning search <query>

# Configuration
/config show
/config set <key> <value>
/config validate

# Utilities
/tree update
/tree diff
/backup create
/backup restore <timestamp>
```

### API (Python)

```python
from session_dev import SessionManager, WorkItem, LearningsCurator

# Session management
manager = SessionManager("/path/to/project")

# Start session
work_item = manager.start_session(auto_next=True)
print(f"Working on: {work_item.title}")

# Complete session
summary = manager.complete_session()
print(f"Completed: {summary.achievements}")

# Work item queries
wip = manager.get_work_items(status="in_progress")
ready = manager.get_ready_work_items()  # Dependencies satisfied

# Learnings
curator = LearningsCurator(manager)
patterns = curator.get_learnings(category="architecture_patterns")
curator.curate()
```

### GitHub Action

```yaml
# .github/workflows/session.yml
name: Session-Dev Quality Gates

on:
  push:
    branches: [main]
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: validate-action@v1
        with:
          check-work-items: true
          check-documentation: true
          check-learnings: true
```

---

## Part 14: Success Metrics

### Project-Level Metrics

**Quality Metrics:**
- Test coverage: Target >85%
- Documentation currency: 100% files documented
- Learning capture rate: >5 learnings per 10 sessions
- Technical debt: <10% of work items

**Velocity Metrics:**
- Sessions per week: 5-10 (1-2 hours each)
- Work items per month: 15-25
- Milestone completion: Within 20% of estimates

**Knowledge Metrics:**
- Best practices established: 1-2 per milestone
- Patterns documented: 3-5 per milestone
- Gotchas captured: Prevents >50% issue recurrence

### Session-Level Metrics

**Effectiveness:**
- Sessions with clear deliverables: >90%
- Sessions requiring rework: <10%
- Validation gate failures: <5%

**Efficiency:**
- Time to session start: <5 minutes
- Time to session complete: <10 minutes
- Briefing read time: <5 minutes

### Long-Term Metrics

**Sustainability:**
- Context continuity: >95% sessions start with full context
- Onboarding time: New developer productive in 1 day
- Knowledge retention: >80% institutional knowledge captured

**Maintenance:**
- Bug introduction rate: <3% sessions introduce bugs
- Regression prevention: >90% bugs prevented by tests
- Refactoring cadence: 1 refactor work item per 10 features

---

## Part 15: Conclusion

### What Solokit Provides

1. **Stateful AI Development**: Perfect context handoffs between sessions
2. **Enforced Quality**: Validation gates prevent quality degradation
3. **Knowledge Accumulation**: Institutional memory grows with project
4. **Dependency Management**: Logical work ordering, not arbitrary sequences
5. **Deterministic Process**: Reliable, repeatable session management
6. **Living Documentation**: Always current, never stale

### When to Use Solokit

**Ideal For:**
- Solo developers building complex products
- Long-running projects (weeks to months)
- Projects requiring team-level quality
- AI-augmented development workflows
- Projects with evolving requirements

**Not Necessary For:**
- Simple scripts or one-off tools
- Projects <5 sessions
- Exploratory prototypes
- Throwaway code

### The Solokit Promise

**Without Solokit:**
- Context lost between sessions
- Quality degrades over time
- Knowledge fragmented
- Inconsistent decisions

**With Solokit:**
- Perfect context continuity
- Quality maintained/improved
- Knowledge accumulated
- Consistent, informed decisions

### Getting Started

1. Install Solokit: `plugin installation`
2. Initialize: `plugin initialization`
3. Create docs: vision.md, architecture.md
4. Define work items: `/work-item create`
5. Start first session: `/start`

### Resources

- Documentation available in the `docs/` directory
- Implementation guides:
  - PLUGIN_IMPLEMENTATION_PLAN_PHASES_0-4.md (Foundation - Complete)
  - PLUGIN_IMPLEMENTATION_PLAN_PHASES_5+.md (Quality & Operations - In Progress)
- Roadmap in ROADMAP.md

---

## Part 16: Development Tool Integration

### Overview

Solokit integrates runtime development tools to enforce quality standards and ensure accurate library usage during every session. This section details how linters, formatters, type checkers, and MCP tools work together to maintain code quality.

### Context7 MCP Integration

**Purpose**: Ensure all library usage is based on current, accurate documentation

#### When to Use Context7

**MANDATORY usage scenarios:**
- **New library**: Before first import of any external library
- **Version upgrade**: When upgrading library versions
- **Unfamiliar API**: Implementing complex library features
- **Unexpected behavior**: Debugging library-related issues
- **Best practices**: Verifying current patterns and conventions

**Recommended usage frequency:**
- Check documentation at start of session if using libraries
- Re-verify after encountering API errors
- Confirm patterns before implementing complex features

#### Workflow Integration

**1. Pre-Implementation Check**

When starting work that involves external libraries:

```
Session briefing includes:
---
Libraries Used in This Work Item:
- FastAPI (last verified: session_003, version: 0.109.0)
- SQLAlchemy (last verified: session_005, version: 2.0.25)

Action required:
- Verify FastAPI documentation (6 days since last check)
- SQLAlchemy documentation current (1 day old)
---

Claude workflow:
1. Read briefing, note library usage
2. Check Context7 for FastAPI updates:
   mcp__context7__resolve-library-id "fastapi"
   mcp__context7__get-library-docs "/tiangolo/fastapi" --topic "routing"
3. Review current patterns
4. Proceed with implementation using verified APIs
```

**2. During Implementation**

When encountering new library functionality:

```
Claude: I need to implement OAuth2 with FastAPI. Let me check the
        current recommended approach...

[Runs: mcp__context7__get-library-docs "/tiangolo/fastapi" --topic "security"]

Based on FastAPI 0.109 documentation:
- Use OAuth2PasswordBearer for token authentication
- Dependency injection pattern for auth
- Current example from docs...

[Implements using current patterns]

Added to session notes:
- Verified FastAPI OAuth2 patterns (Context7, 2025-10-09)
- Using OAuth2PasswordBearer (current recommended approach)
```

**3. Learning Capture**

Library information automatically captured in learnings:

```json
{
  "learnings": [{
    "session": "session_005",
    "type": "architecture_pattern",
    "content": "FastAPI OAuth2 using dependency injection",
    "library": "fastapi",
    "library_version": "0.109.0",
    "verified_via": "context7",
    "verified_date": "2025-10-09",
    "documentation_url": "/tiangolo/fastapi",
    "example": "auth/oauth.py:45-67"
  }]
}
```

#### Configuration

```json
{
  "runtime_standards": {
    "mcp_tools": {
      "context7": {
        "required": true,
        "check_on_new_import": true,
        "prompt_for_verification": true,
        "cache_duration": "24h",
        "libraries_to_always_check": [
          "fastapi", "sqlalchemy", "pydantic",
          "react", "vue", "nextjs"
        ],
        "auto_capture_version": true,
        "add_to_learnings": true
      }
    }
  }
}
```

#### Benefits

✅ **Accuracy**: Always use current API patterns
✅ **Confidence**: Know patterns are up-to-date
✅ **Learning**: Library versions captured in knowledge base
✅ **Debugging**: Easier to identify version-specific issues
✅ **Maintenance**: Quick identification of deprecated patterns

### Linter Integration

**Purpose**: Enforce code quality standards automatically

#### Configuration by Language

**Python (Ruff):**
```json
{
  "python": {
    "command": "ruff check .",
    "auto_fix": true,
    "config": "pyproject.toml",
    "rules": [
      "E",   // pycodestyle errors
      "F",   // pyflakes
      "I",   // isort (import sorting)
      "N",   // pep8-naming
      "UP"   // pyupgrade (modern syntax)
    ]
  }
}
```

**TypeScript/JavaScript (ESLint):**
```json
{
  "typescript": {
    "command": "eslint .",
    "auto_fix": true,
    "config": ".eslintrc.json"
  }
}
```

**Rust (Clippy):**
```json
{
  "rust": {
    "command": "cargo clippy",
    "auto_fix": false,
    "fail_on_warnings": false
  }
}
```

#### Session Integration

**During Session:**
```
Session in progress...

[Every 15 minutes, or on manual check:]
Running linter check...
⚠️  2 issues found in auth/oauth.py:
   - Line 45: E501 Line too long (95 > 88)
   - Line 78: F401 Unused import 'datetime'

Auto-fixing issues...
✅ Fixed 2 issues automatically
```

**Session Completion:**
```
Running quality gates...

🔍 Running linter...
  Python files: ✅ No issues (auto-fixed 2 during session)
  TypeScript files: ✅ Passed

Quality gate: linting ✅ PASSED
```

**Failure Handling:**
```
🔍 Running linter...
❌ 5 issues found that cannot be auto-fixed:

auth/oauth.py:
  Line 45: E501 Line too long (requires manual fix)
  Line 67: E722 Bare except (add exception type)

Fix issues manually or use:
  sk end --no-lint

Session completion blocked.
```

#### Override Options

```bash
# Skip linting for this session (use cautiously)
sk end --no-lint

# Skip auto-fix, show issues only
sk end --lint-no-fix

# Force completion despite lint failures
sk end --force
```

### Formatter Integration

**Purpose**: Maintain consistent code style across all sessions

#### Configuration

**Python (Black):**
```json
{
  "python": {
    "command": "black .",
    "line_length": 88,
    "target_version": ["py39", "py310", "py311"]
  }
}
```

**TypeScript/JavaScript (Prettier):**
```json
{
  "typescript": {
    "command": "prettier --write .",
    "config": ".prettierrc"
  }
}
```

#### Integration Points

**1. On-Save (IDE Integration)**

If working in an environment that supports it:
- Format file on save
- Immediate feedback
- No manual formatting needed

**2. Pre-Commit Hook**

Generated by Solokit during initialization:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Formatting code..."
black .
prettier --write .

echo "Running linter..."
ruff check .

if [ $? -ne 0 ]; then
  echo "❌ Linting failed. Fix issues or use git commit --no-verify"
  exit 1
fi

echo "✅ Pre-commit checks passed"
```

**3. Session Completion**

```
✨ Checking formatting...
  Found 3 files needing formatting

Auto-formatting:
  - auth/oauth.py
  - api/routes/users.py
  - database/models.py

✅ All files formatted

Quality gate: formatting ✅ PASSED
```

### Type Checker Integration

**Purpose**: Catch type-related errors early (optional)

#### Configuration

```json
{
  "type_checking": {
    "enabled": false,  // Optional by default
    "on_commit": true,
    "fail_on_error": false,  // Warning only by default
    "tools": {
      "python": {
        "command": "mypy .",
        "config": "mypy.ini",
        "strict": false
      },
      "typescript": {
        "command": "tsc --noEmit",
        "config": "tsconfig.json"
      }
    }
  }
}
```

#### Session Integration

```
🔎 Running type checker...
  Found 3 type issues:

auth/oauth.py:45: error: Argument 1 to "get_user" has incompatible type "str"; expected "int"
auth/oauth.py:67: error: Incompatible return value type (got "None", expected "User")

⚠️  Type checking failed (warning only)

Quality gate: type_checking ⚠️  WARNED (non-blocking)

Continue with session completion? (y/n): y
```

**Strict Mode** (fail_on_error: true):
```
🔎 Running type checker...
❌ Type checking failed (blocking)

Fix type errors or:
  sk end --no-type-check

Session completion blocked.
```

### Complete Quality Gate Workflow

**Full Session Completion with All Gates:**

```
User: /end

Claude: Running session completion...

============================================================
QUALITY GATES EXECUTION
============================================================

1. 🧪 Running tests...
   Running: pytest tests/auth/
   ✅ 18 tests passed in 2.3s
   Coverage: 87% (target: 80%)
   Quality gate: tests ✅ PASSED

2. 🔍 Running linter...
   Python: ruff check .
   Auto-fixed 2 issues
   ✅ No remaining issues
   Quality gate: linting ✅ PASSED

3. ✨ Checking formatting...
   Black: Found 1 file to format
   Auto-formatted: auth/oauth.py
   ✅ All files formatted
   Quality gate: formatting ✅ PASSED

4. 🔎 Running type checker...
   mypy: No issues found
   ✅ Type checking passed
   Quality gate: type_checking ✅ PASSED

5. 📝 Checking documentation...
   Modified files: 3
   Documentation files updated: 2
   ✅ Documentation current
   Quality gate: documentation ✅ PASSED

6. 📚 Verifying library documentation...
   Libraries used: fastapi, sqlalchemy
   fastapi: ✅ Verified via Context7 (session_005)
   sqlalchemy: ✅ Verified via Context7 (session_003)
   Quality gate: library_docs ✅ PASSED

============================================================
QUALITY GATES SUMMARY
============================================================
  ✅ tests
  ✅ linting
  ✅ formatting
  ✅ type_checking
  ✅ documentation
  ✅ library_docs

All quality gates passed!
============================================================

Updating project tree...
✅ Project tree updated

Updating work item status...
✅ feature_oauth marked as completed

Creating git commit...
✅ Committed: "Session 5: Implement OAuth2 Authentication"

Generating session summary...
✅ Summary saved: .session/history/session_005_summary.md

============================================================
SESSION 5 COMPLETED SUCCESSFULLY
============================================================

Achievements:
- OAuth2 authentication flow implemented
- Token refresh mechanism added
- 18 tests added (87% coverage)
- Documentation updated

Next session available:
- feature_2fa: Two-Factor Authentication
  Dependencies: ✅ All satisfied
  Ready to start

Session summary: .session/history/session_005_summary.md
```

### Tool-Specific Workflows

#### Workflow 1: New Library Discovery

```
User: Let's add Stripe payment integration

Claude:
I'll implement Stripe integration. First, let me get the current
Stripe API documentation...

[Runs: mcp__context7__resolve-library-id "stripe"]
Found: /stripe/stripe-python

[Runs: mcp__context7__get-library-docs "/stripe/stripe-python" --topic "payments"]

Current Stripe Python library (v7.4.0):
- Payment Intents API (recommended over Charges)
- Webhook handling with construct_event()
- Async support available

I'll implement using the current Payment Intents pattern...

[Implementation proceeds with verified patterns]

Added to learnings:
- Stripe v7.4 uses Payment Intents (not Charges API)
- Webhook signature verification required for security
- Verified via Context7 on 2025-10-09
```

#### Workflow 2: Lint Failure During Session

```
[15 minutes into session]

Auto-running linter check...

⚠️  3 issues found:
  payments/stripe_client.py:23: E501 Line too long
  payments/stripe_client.py:45: F401 Unused import

Attempting auto-fix...
✅ Fixed 2 issues
⚠️  1 issue remains (manual fix needed)

payments/stripe_client.py:23: E501 Line too long (requires refactoring)

Claude: I'll refactor that line to fix the length issue...
[Fixes the long line by splitting into multiple lines]

Running linter again...
✅ All issues resolved
```

#### Workflow 3: Documentation Freshness Check

```
Session briefing shows:

Libraries to verify:
- react: Last checked 8 days ago (may be outdated)
- axios: Last checked 2 days ago (current)

Claude:
React was last checked 8 days ago. Let me verify the documentation
is still current...

[Runs: mcp__context7__get-library-docs "/facebook/react" --topic "hooks"]

React 18.2 documentation current.
Note: React 18.3 released 5 days ago, but no breaking changes to hooks.

Proceeding with React 18.2 patterns (upgrade not required for this work).

Updated session notes:
- React 18.2 verified current (2025-10-09)
- React 18.3 available but no breaking changes
```

---

## Appendix A: Complete File Templates

### A.1: .sessionrc.json Template

```json
{
  "framework_version": "1.0.0",
  "project": {
    "name": "project-name",
    "type": "web_application",
    "work_item_model": "feature_based",
    "description": "Brief project description"
  },

  "session_protocol": {
    "start_trigger": "/start",
    "end_trigger": "/end",
    "auto_briefing": true,
    "briefing_template": "default"
  },

  "paths": {
    "tracking": ".session/tracking",
    "briefings": ".session/briefings",
    "specs": ".session/specs",
    "scripts": ".session/scripts",
    "history": ".session/history"
  },

  "validation_rules": {
    "pre_session": {
      "git_clean": true,
      "dependencies_met": true,
      "environment_valid": true,
      "previous_session_closed": true,
      "custom_checks": []
    },
    "post_session": {
      "tests_pass": true,
      "test_coverage_min": 80,
      "linting_pass": true,
      "type_check_pass": false,
      "documentation_updated": true,
      "git_committed": true,
      "custom_checks": []
    }
  },

  "work_item_types": {
    "feature": {
      "template": "feature_spec.md",
      "typical_sessions": "2-4",
      "validation": {
        "tests_required": true,
        "coverage_min": 80,
        "documentation_required": true
      }
    },
    "bug": {
      "template": "bug_report.md",
      "typical_sessions": "1-2",
      "validation": {
        "tests_required": true,
        "regression_test": true
      }
    },
    "refactor": {
      "template": "refactor_plan.md",
      "typical_sessions": "1-3",
      "validation": {
        "tests_required": true,
        "no_functionality_change": true
      }
    },
    "setup": {
      "template": "setup_task.md",
      "typical_sessions": "1-2",
      "validation": {
        "documentation_required": true
      }
    }
  },

  "testing": {
    "framework": "pytest",
    "command": "pytest",
    "coverage_command": "pytest --cov",
    "coverage_min": 80
  },

  "runtime_standards": {
    "linting": {
      "enabled": true,
      "on_save": false,
      "on_commit": true,
      "fail_on_error": true,
      "tools": {
        "python": {
          "command": "ruff check .",
          "auto_fix": true,
          "config": "pyproject.toml",
          "rules": ["E", "F", "I", "N", "UP"]
        },
        "typescript": {
          "command": "eslint .",
          "auto_fix": true,
          "config": ".eslintrc.json"
        },
        "javascript": {
          "command": "eslint .",
          "auto_fix": true,
          "config": ".eslintrc.json"
        },
        "rust": {
          "command": "cargo clippy",
          "auto_fix": false,
          "fail_on_warnings": false
        },
        "go": {
          "command": "golangci-lint run",
          "auto_fix": false
        }
      }
    },
    "formatting": {
      "enabled": true,
      "on_save": true,
      "on_commit": true,
      "check_only_changed": true,
      "tools": {
        "python": {
          "command": "black .",
          "line_length": 88,
          "target_version": ["py39", "py310", "py311"]
        },
        "typescript": {
          "command": "prettier --write .",
          "config": ".prettierrc"
        },
        "javascript": {
          "command": "prettier --write .",
          "config": ".prettierrc"
        },
        "rust": {
          "command": "cargo fmt"
        },
        "go": {
          "command": "gofmt -w ."
        }
      }
    },
    "type_checking": {
      "enabled": false,
      "on_commit": true,
      "fail_on_error": false,
      "tools": {
        "python": {
          "command": "mypy .",
          "config": "mypy.ini",
          "strict": false
        },
        "typescript": {
          "command": "tsc --noEmit",
          "config": "tsconfig.json"
        }
      }
    },
    "mcp_tools": {
      "context7": {
        "required": true,
        "check_on_new_import": true,
        "prompt_for_verification": true,
        "cache_duration": "24h",
        "libraries_to_always_check": [
          "fastapi",
          "sqlalchemy",
          "pydantic",
          "django",
          "flask",
          "react",
          "vue",
          "nextjs",
          "express",
          "nestjs"
        ],
        "auto_capture_version": true,
        "add_to_learnings": true
      }
    }
  },

  "documentation": {
    "required_files": [
      "docs/vision.md",
      "docs/architecture.md",
      "docs/development_plan.md"
    ],
    "auto_update": true
  },

  "curation": {
    "frequency": 5,
    "auto_categorize": true,
    "similarity_threshold": 0.8,
    "archive_after_sessions": 50
  },

  "git": {
    "auto_commit": true,
    "commit_template": "session_commit.txt",
    "require_clean": true
  }
}
```

### A.2: Feature Specification Template

```markdown
# Feature: [Feature Name]

## Overview
Brief description of what this feature does and why it's needed.

## User Story
As a [user type], I want [goal] so that [benefit].

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Specification

### API Endpoints

POST /api/v1/resource
GET /api/v1/resource/:id
PUT /api/v1/resource/:id
DELETE /api/v1/resource/:id

### Data Model
```
python
class Resource:
    id: UUID
    name: str
    created_at: datetime
```

### Dependencies
- feature_dependency_1
- feature_dependency_2

## Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E test for critical user flow

## Documentation Updates
- API documentation
- Architecture diagram
- User guide section

## Estimated Complexity
Sessions: 2-3
Complexity: Medium

## Notes
Additional context, constraints, or considerations.
```

### A.3: Session Briefing Template

```markdown
# Session {session_number}: {work_item_title}

Generated: {timestamp}

## Quick Overview
- **Work Item**: {work_item_id}
- **Type**: {type}
- **Priority**: {priority}
- **Status**: {status}
- **Estimated Sessions**: {estimate}

## Dependencies
{dependency_list}

## Objectives
{objectives_list}

## Specification
{full_specification}

## Previous Session Notes
{previous_notes}

## Implementation Checklist
{checklist}

## Success Criteria
{success_criteria}

## Related Files
{file_list}

## Relevant Learnings
{learnings_to_reference}

## Architecture Context
{architecture_notes}

## Next Steps
1. Review this briefing
2. Run validation: `sk validate`
3. Begin implementation
4. Update documentation as you go
5. Run tests frequently
6. Complete session: `sk end`

---
**Commands:**
- Status: `/sk:status`
- Validate: `/sk:validate`
- Complete: `/sk:end`
```

---

## Appendix B: Integration with Existing Projects

### Adding Solokit to Existing Codebase

**Step 1: Assessment**
```bash
cd existing-project

# Analyze current state and initialize
/sk:start
```

The plugin will analyze:
- Language: Python
- Framework: FastAPI
- Database: PostgreSQL
- Tests: pytest (65% coverage)
- Docs: Partial (missing architecture.md)

Recommendations:
1. Add architecture documentation
2. Increase test coverage to 80%
3. Define work items for remaining features
4. Set up validation rules

Proceed with initialization? (y/n)
```

**Step 2: Initialization**
```bash
plugin initialization --existing

# Prompts:
# - Preserve existing git history? yes
# - Import existing issues as work items? yes
# - Scan codebase for patterns? yes
```

**Step 3: Import Existing Work**
```bash
# From GitHub issues
/work-item import-github --repo owner/repo

# From Jira
/work-item import-jira --project KEY

# From linear
/work-item import-linear --team team-id

# Manual entry
/work-item create-from-codebase
```

**Step 4: Establish Baseline**
```bash
# Document current architecture
/docs generate-architecture

# Capture current patterns
/learning extract-from-code

# Document current stack
/docs stack-scan

# Create initial project tree
/tree update
```

**Step 5: First Session**
```bash
# Define first improvement work item
/work-item create

# Start session
User: /start
```

---

## Appendix C: Comparison with Other Methodologies

### Solokit vs Traditional Agile

| Aspect | Traditional Agile | Session-Driven Development |
|--------|------------------|---------------------------|
| **Team Size** | 5-9 developers | Solo or small team with AI |
| **Sprint Length** | 1-2 weeks | N/A (continuous sessions) |
| **Planning** | Sprint planning meetings | Work item dependency graph |
| **Standup** | Daily team sync | Session briefings |
| **Retrospective** | End of sprint | Continuous learning capture |
| **Documentation** | Often minimal | Comprehensive, automated |
| **Context** | Tribal knowledge | Explicit, documented |

### Solokit vs Kanban

| Aspect | Kanban | Session-Driven Development |
|--------|--------|---------------------------|
| **Work Units** | User stories | Work items |
| **Flow** | Pull-based | Dependency-driven |
| **WIP Limits** | Explicit column limits | 1 work item per session |
| **Quality Gates** | Definition of Done | Automated validation |
| **Visualization** | Kanban board | work_items.json + dependency graph |
| **Metrics** | Lead time, cycle time | Sessions per work item, learning rate |

### Solokit vs Traditional Solo Development

| Aspect | Solo Ad-Hoc | Session-Driven Development |
|--------|-------------|---------------------------|
| **Context Continuity** | Memory/notes | Automated briefings |
| **Quality Enforcement** | Manual discipline | Automated gates |
| **Knowledge Capture** | None/minimal | Systematic learning accumulation |
| **Documentation** | Outdated quickly | Always current |
| **Onboarding** | Weeks/months | Days |
| **Technical Debt** | Hidden, accumulates | Visible, tracked, prioritized |

---

## Appendix D: Future Roadmap

### Version 1.0 (Launch)
- Core automation through slash commands
- work_items.json management
- Session init/complete workflows
- Basic validation gates
- Learning capture
- Stack tracking
- Claude Code plugin integration

### Version 1.1
- Learning curation automation
- Dependency graph visualization
- Multiple project preset templates
- Custom work item types
- Plugin system foundation

### Version 1.2
- IDE integrations (VS Code extension)
- GitHub Actions integration
- Slack/Discord notifications
- Notion/Linear sync plugins
- Advanced metrics dashboard

### Version 1.3
- AI-powered briefing enhancement
- Predictive session estimation
- Auto-detection of technical debt
- Pattern recognition from code
- Intelligent work item recommendations

### Version 2.0
- Multi-developer support
- Real-time collaboration features
- Advanced analytics and insights
- Integration with Claude Team plans
- Enterprise features (SSO, audit logs)

---

**End of Framework Documentation**

*Session-Driven Development: Enabling AI-augmented software development with team-level quality and continuity.*

*Version: 1.0.0-draft*
*Last Updated: 2025-10-09*
*License: MIT (planned)*
*Author: Session-Dev Project*
