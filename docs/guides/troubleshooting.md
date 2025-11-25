# Troubleshooting Guide

## First Step: Run Diagnostics

**Before diving into specific issues, run the diagnostic command:**

```bash
sk doctor
```

This command performs a comprehensive system check and identifies common problems:
- ✓ Python version compatibility (>= 3.11.0)
- ✓ Git installation and availability
- ✓ Project structure (`.session/` directory and config.json)
- ✓ Configuration file validity
- ✓ Work items file integrity
- ✓ Quality tools availability (pytest, ruff, etc.)

**Example output:**
```
Running system diagnostics...

✓ Python 3.11.7 (>= 3.11.0 required)
✓ git version 2.45.2 installed
✓ .session/ directory exists with config.json
✓ config.json is valid
✓ work_items.json will be created when needed
✓ All quality tools available: pytest, ruff

✓ All 6 checks passed
```

If any checks fail, `sk doctor` provides actionable suggestions for fixing the issue.

## Common Issues and Solutions

### Undoing a Failed `/sk:start` Command

If you run `/sk:start` and it fails (e.g., spec file not found, wrong work item), you can undo the changes by reverting the session state:

#### What `/sk:start` Changes:

1. **Work Item Status** - Sets status to "in_progress" in `.session/tracking/work_items.json`
2. **Session Tracking** - Adds a session entry to the work item
3. **Git Branch** - Creates/checks out a feature branch
4. **Status File** - Creates/updates `.session/tracking/status_update.json`
5. **Briefing File** - Creates `.session/briefings/session_XXX_briefing.md`

#### Manual Undo Steps:

**Option 1: Quick Reset (Recommended)**

```bash
# 1. Switch back to main branch
git checkout main

# 2. Delete the feature branch (if it was created)
git branch -D session-XXX-US-X-X  # Replace with actual branch name

# 3. Edit .session/tracking/work_items.json
# Change the work item status back to "not_started"
# Remove the "sessions" array entry
# Update the "updated_at" timestamp

# 4. Delete the status file
rm .session/tracking/status_update.json

# 5. Delete the briefing file (optional, for cleanup)
rm .session/briefings/session_XXX_briefing.md
```

**Option 2: Using Git to Reset Work Items**

```bash
# If you have work_items.json committed, you can restore it
git checkout HEAD -- .session/tracking/work_items.json

# Then manually handle git branch and status file as above
```

#### Automated Undo Script (Future Enhancement)

A `/sk:undo` or `/sk:reset` command could be added to automate this process.

---

### Spec File Not Found in Briefing

**Symptom:** Running `/sk:start` generates a briefing, but the work item specification section shows "Specification file not found"

**Cause:** The spec file path in `work_items.json` doesn't match the actual file location.

**Solution:**

1. Check your work item definition in `.session/tracking/work_items.json`:
   ```json
   "spec_file": ".session/specs/US-0-1-project-initialization.md"
   ```

2. Verify the file exists at that path:
   ```bash
   ls -la .session/specs/US-0-1-project-initialization.md
   ```

3. If the filename is different, either:
   - **Option A:** Rename the spec file to match the `spec_file` field
   - **Option B:** Update the `spec_file` field in work_items.json to match the actual filename

**Note:** As of version 0.5.9+, the briefing generator uses the `spec_file` field from work_items.json, so you have flexibility in naming your spec files.

---

### Work Item Already In Progress

**Symptom:** When running `/sk:start`, you get a work item that's already marked "in_progress"

**Cause:** A previous session was started but not completed with `/sk:end`

**Solution:**

**Option 1: Resume the Session**
```bash
# Continue working on the in-progress item
/sk:start
# This will resume the existing work item
```

**Option 2: Force Reset**
```bash
# Manually edit .session/tracking/work_items.json
# Change the status from "in_progress" to "not_started"
# Then run /sk:start again
```

**Option 3: Complete the Session**
```bash
# If you're actually done with the work
/sk:end
# This will mark it complete and move to the next item
```

---

### No Available Work Items

**Symptom:** `/sk:start` says "No available work items. All dependencies must be satisfied first."

**Cause:** All remaining work items have unsatisfied dependencies.

**Solution:**

1. Check work item dependencies:
   ```bash
   /sk:work-list --status not_started
   ```

2. Look at the dependency graph:
   ```bash
   /sk:work-graph --bottlenecks
   ```

3. Either:
   - Complete the blocking work items first
   - Remove/modify dependencies if they're incorrect
   - Create a new work item without dependencies

---

### Git Branch Already Exists

**Symptom:** `/sk:start` fails because the git branch already exists

**Cause:** A previous session created the branch but wasn't cleaned up

**Solution:**

```bash
# Option 1: Resume on existing branch
git checkout session-XXX-US-X-X
/sk:start

# Option 2: Delete and recreate
git checkout main
git branch -D session-XXX-US-X-X
/sk:start

# Option 3: Rename the old branch for archival
git branch -m session-XXX-US-X-X session-XXX-US-X-X-old
/sk:start
```

---

### Briefing Shows Wrong Work Item

**Symptom:** The briefing shows a different work item than you expected

**Cause:** The system automatically selects the next available work item based on:
1. In-progress items (resumes these first)
2. Not-started items with satisfied dependencies
3. Priority ordering (critical > high > medium > low)

**Solution:**

```bash
# Specify which work item you want to start
/sk:start --item US-X-X

# Or check what the next item will be
/sk:work-next
```

---

### Environment Validation Fails

**Symptom:** Briefing shows environment checks failing (Git not found, Python wrong version, etc.)

**Cause:** Required development tools aren't installed or configured

**Solution:**

1. **Install missing tools:**
   ```bash
   # Git
   brew install git  # macOS
   sudo apt install git  # Linux

   # Python (use appropriate version)
   brew install python@3.11  # macOS
   ```

2. **Check installations:**
   ```bash
   git --version
   python --version
   ```

3. **Update PATH if needed:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="/usr/local/bin:$PATH"
   ```

---

### Next.js Initialization Conflicts with `.session/` Directory

**Symptom:** When trying to initialize a Next.js project with `create-next-app`, you get an error:
```
Error: The directory contains files that could conflict:
  .session/
Either try using a new directory name, or remove the files listed above.
```

**Cause:** The Solokit framework creates a `.session/` directory for tracking work items, learnings, and session state. Tools like `create-next-app` detect this as a conflict because they expect an empty directory.

**Solutions:**

**Option 1: Initialize in Parent Directory (Recommended)**
```bash
# If you're in the Solokit project directory, initialize Next.js in the current directory
# using the --force flag (use with caution)
npx create-next-app@latest . --typescript --tailwind --app --use-npm
# When prompted about conflicts, confirm to proceed
```

**Option 2: Manual Setup**
```bash
# Instead of using create-next-app, manually set up Next.js
npm install next@latest react@latest react-dom@latest
npm install --save-dev typescript @types/react @types/node
npm install --save-dev tailwindcss postcss autoprefixer

# Create necessary config files manually
npx tailwindcss init -p

# Create directory structure
mkdir -p app
```

**Option 3: Temporary Workaround**
```bash
# Temporarily rename .session directory
mv .session .session.tmp

# Run create-next-app
npx create-next-app@latest . --typescript --tailwind --app --use-npm

# Restore .session directory
mv .session.tmp .session
```

**Note:** The `.session/` directory is essential for Solokit to function. Do not delete it or add it to `.gitignore` if you're using Session-Driven Development workflow.

---

### `work-update` Command Fails with EOFError

**Symptom:** Running `sk work-update US-0-1 --status in_progress` fails with:
```
EOFError: EOF when reading a line
```

**Cause:** Prior to version 0.5.10, the `work-update` command always used interactive mode, even when flags were provided. This caused it to prompt for user input, which fails when Claude runs it non-interactively.

**Solution:**

**For Solokit v0.5.10+:** This is fixed! The `work-update` command now supports both interactive and non-interactive modes:

```bash
# Non-interactive mode (with flags)
sk work-update US-0-1 --status completed
sk work-update US-0-1 --priority high
sk work-update US-0-1 --milestone "MVP"
sk work-update US-0-1 --add-dependency US-0-2
sk work-update US-0-1 --remove-dependency US-0-3

# Interactive mode (no flags)
sk work-update US-0-1
# Prompts: What would you like to update?
```

**For older versions:** Upgrade to the latest version or avoid using `work-update` in non-interactive contexts.

**Important for Claude Code Users:**
- The `/sk:start` command automatically updates the work item status to `in_progress`
- You do NOT need to manually run `sk work-update US-0-1 --status in_progress` after starting a session
- The briefing will show: `✓ Work item status updated: US-0-1 → in_progress`

---

### Running Out of Context with Failing Quality Gates

**Symptom:** You're near the end of your Claude Code context window, quality gates are failing, but you want to save your work and end the session.

**Cause:** Quality gates require fixes but you don't have enough context remaining to debug and fix the issues.

**Solution: Use `--incomplete` mode to checkpoint your work**

The `/sk:end` command supports two modes:

**Complete mode (`--complete`):**
- Quality gates are enforced/blocking
- All gates must pass to end session
- Use when work is truly complete

**Incomplete mode (`--incomplete`):**
- Quality gates run but are non-blocking
- Shows warnings but doesn't prevent session end
- Allows checkpointing work-in-progress
- Perfect for running out of context

**Example workflow:**

```bash
# You're running out of context...
/sk:end

# Interactive prompt appears:
# "Is this work item complete?"
# → Select: "No - Keep as in-progress"

# Quality gates run (non-blocking):
Running quality gates (non-blocking)...
⚠️  Tests: 2/15 tests failed (WARNING - not blocking)
⚠️  Coverage: 72.3% (threshold: 80%) (WARNING - not blocking)
✓ Linting passed
✓ All changes committed (2 commits)

Session ended with warnings. Work item remains in-progress.

Quality gate warnings (fix in next session):
  - 2 failing tests need attention
  - Coverage needs 7.7% increase

# Next session - resume with full context
/sk:start  # Auto-resumes the in-progress work item
# ... fix the failing tests and coverage ...
/sk:validate  # Verify all gates pass
/sk:end  # Select "Yes - Mark as completed"
```

**Key Benefits:**
1. **No Data Loss**: All commits, learnings, and context are saved
2. **Flexible Workflow**: Don't need to fix everything immediately
3. **Context Preservation**: Resume exactly where you left off
4. **Quality Visibility**: Still see what needs fixing
5. **Progress Tracking**: Work item stays "in_progress" for auto-resume

---

## Getting Help

If you encounter issues not covered here:

1. Check the [Session-Driven Development docs](./solokit-methodology.md)
2. Review the [Configuration guide](./configuration.md)
3. Open an issue on the [Solokit GitHub repository](https://github.com/anthropics/solokit)
4. Check the command-specific docs in `docs/commands/`

---

## Debug Mode

For more verbose output during troubleshooting:

```bash
# Enable debug logging (if implemented)
export SDD_DEBUG=1

# Run commands
/sk:start

# Check logs
tail -f .session/debug.log
```
