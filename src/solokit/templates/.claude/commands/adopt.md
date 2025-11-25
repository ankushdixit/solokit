---
description: Adopt Solokit into an existing project with code
---

# Adopt Solokit into Existing Project

Add Solokit session management to an existing project without modifying your code.

## When to Use This Command

Use `/adopt` when you have an existing project with code and want to add:

- Session tracking and briefings
- Work item management
- Learning capture system
- Quality gates
- Claude Code slash commands

**Note:** For new/blank projects, use `/init` instead.

---

## Interactive Configuration (3 Questions)

Use the **AskUserQuestion tool** to collect configuration:

### Question 1: Confirm Adoption

**Question**: "This will add Solokit session management to your existing project. Existing configs may be overwritten. Continue?"
**Header**: "Confirm"
**Multi-Select**: false

**Options**:

1. **Label**: "Yes, adopt Solokit"
   **Description**: "Add session management, quality gates, and slash commands to this project"

2. **Label**: "No, cancel"
   **Description**: "Exit without making changes"

If the user selects "No, cancel", stop and inform them that adoption was cancelled.

---

### Question 2: Quality Gates Tier

**Question**: "What level of quality gates do you want?"
**Header**: "Quality Tier"
**Multi-Select**: false

**Options**:

1. **Label**: "Essential"
   **Description**: "Linting, formatting, type-check, basic tests (fastest setup)"

2. **Label**: "Standard"
   **Description**: "+ Git hooks, security scanning (recommended for most projects)"

3. **Label**: "Comprehensive"
   **Description**: "+ Coverage reports, integration tests, mutation testing (production-ready)"

4. **Label**: "Production-Ready"
   **Description**: "+ Performance monitoring, error tracking, deployment safety (enterprise-grade)"

---

### Question 3: Testing Coverage Target

**Question**: "What testing coverage level do you want to enforce?"
**Header**: "Coverage"
**Multi-Select**: false

**Options**:

1. **Label**: "Basic (60%)"
   **Description**: "Minimal coverage for prototypes and MVPs"

2. **Label**: "Standard (80%)"
   **Description**: "Industry standard for production code (recommended)"

3. **Label**: "Strict (90%)"
   **Description**: "High-reliability applications and mission-critical systems"

---

## Run Adoption

After collecting all answers via AskUserQuestion, run the Python CLI:

```bash
sk adopt --tier=<tier> --coverage=<coverage> --yes
```

**Mapping user selections to CLI arguments:**

**Tier mapping:**

- "Essential" → `--tier=tier-1-essential`
- "Standard" → `--tier=tier-2-standard`
- "Comprehensive" → `--tier=tier-3-comprehensive`
- "Production-Ready" → `--tier=tier-4-production`

**Coverage mapping:**

- "Basic (60%)" → `--coverage=60`
- "Standard (80%)" → `--coverage=80`
- "Strict (90%)" → `--coverage=90`

The `--yes` flag skips the confirmation prompt since we already confirmed via AskUserQuestion.

**Important:** The Python command handles ALL work deterministically:

- Project type detection (Python, Node.js, TypeScript, Fullstack)
- Creating .session/ directory structure
- Installing Claude Code slash commands
- Updating README.md and CLAUDE.md
- Updating .gitignore
- Installing git hooks
- Creating adoption commit

---

## What Gets Added

Tell the user what Solokit adds to their project:

**New directories:**
- `.session/` - Session tracking, work items, learnings
- `.claude/commands/` - Slash commands for Claude Code

**Updated files:**
- `README.md` - Appended with Session-Driven Development section
- `CLAUDE.md` - Appended with Solokit guidance (or created if missing)
- `.gitignore` - Appended with Solokit entries

**NOT modified:**
- Your existing source code
- Your existing configuration files (linters, formatters, etc.)
- Your existing documentation content

---

## After Successful Adoption

Show the user the success output from the script, then explain:

"Solokit has been added to your project!

**Next steps:**

1. Review the updated `README.md` and `CLAUDE.md`
2. Create your first work item: `/work-new`
3. Start a session: `/start`

**Available commands:**
- `/start` - Begin a session with comprehensive briefing
- `/end` - Complete session with quality gates
- `/work-new` - Create new work items
- `/work-list` - View all work items
- `/status` - Check current session status"

---

## Error Handling

If the `sk adopt` command fails, show the error message from the CLI output.

Common issues:
- Already has `.session/` directory (Solokit may already be installed)
- Permission errors
- Git repository issues

Do not retry automatically - let the user address the issue and run `/adopt` again.
