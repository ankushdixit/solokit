---
description: Complete the current development session with quality gates and summary
---

# Session End

Complete the current development session by following these steps in order.

## Step 1: Pre-flight Checks

Before completing the session, ensure all work is properly prepared.

### 1.1 Check CHANGELOG

First, check if CHANGELOG.md was updated in this session:

```bash
git diff --name-only main...HEAD | grep -q CHANGELOG.md && echo "CHANGELOG updated" || echo "CHANGELOG needs update"
```

**If CHANGELOG needs update:**
1. Review commits made this session with `git log --oneline HEAD~10..HEAD`
2. Update CHANGELOG.md under the `## [Unreleased]` section with:
   - Features added under `### Added`
   - Bug fixes under `### Fixed`
   - Changes under `### Changed`
3. Stage the CHANGELOG: `git add CHANGELOG.md`

### 1.2 Check and Commit Uncommitted Changes

Check for uncommitted changes:

```bash
git status --porcelain
```

**If there are uncommitted changes:**
1. Review the changes
2. Stage all changes: `git add -A`
3. Create a commit with this format:

```bash
git commit -m "$(cat <<'EOF'
<type>: <short description>

<detailed description of changes>

LEARNING: <one key insight from this work>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

Where `<type>` is one of: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### 1.3 Generate Learnings

Extract 2-5 key learnings from the session and write them to a file:

```bash
cat > .session/temp_learnings.txt << 'EOF'
<learning 1 - technical insight or pattern discovered>
<learning 2 - gotcha or edge case encountered>
<learning 3 - best practice that worked well>
EOF
```

**What makes a good learning:**
- Technical insights discovered during implementation
- Gotchas or edge cases encountered
- Best practices or patterns that worked well
- Architecture decisions and their rationale
- Performance or security considerations

## Step 2: Ask About Work Item Completion

Ask the user about the work item completion status using `AskUserQuestion`:

**Question: Work Item Completion Status**
- Question: "Is this work item complete? [Include work item title]"
- Header: "Completion"
- Multi-select: false
- Options:
  - Label: "Yes - Mark as completed", Description: "Work item is done. A PR will be created for review."
  - Label: "No - Keep as in-progress", Description: "Work is ongoing. Will auto-resume when you run /start."
  - Label: "Cancel", Description: "Don't end session. Continue working."

## Step 3: Complete Session

Based on the user's selection:

**If "Yes - Mark as completed" selected:**
```bash
sk end --complete --learnings-file .session/temp_learnings.txt
```

**If "No - Keep as in-progress" selected:**
```bash
sk end --incomplete --learnings-file .session/temp_learnings.txt
```

**If "Cancel" selected:**
- Show message: "Session end cancelled. You can continue working."
- Exit without calling command

## Step 4: Create Pull Request (if complete)

**Only if the work item was marked as completed** and the session completed successfully:

Check if a PR already exists for this branch:
```bash
gh pr list --head $(git branch --show-current) --json number --jq '.[0].number'
```

**If no PR exists**, create one:
```bash
gh pr create --title "<work_item_type>: <work_item_title>" --body "$(cat <<'EOF'
## Summary

<Brief description of changes>

## Work Item
- **ID**: <work_item_id>
- **Type**: <work_item_type>
- **Session**: <session_number>

## Changes
<List of key changes from commits>

## Testing
- [ ] Tests pass locally
- [ ] Manual testing completed

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Step 5: Show Results

Display the session completion summary to the user:

1. **Quality Gate Results**
   - Tests: PASSED/FAILED
   - Linting: PASSED/FAILED
   - Security: PASSED/FAILED
   - Documentation: PASSED/FAILED

2. **Session Summary**
   - Work item status (completed or in-progress)
   - Commits made this session
   - Files changed

3. **Learnings Captured**
   - List the learnings that were saved

4. **PR Status** (if applicable)
   - PR URL if created
   - "PR ready for review at: <url>"

5. **Next Steps**
   - For completed work: "PR created. Review and merge when ready."
   - For in-progress work: "Run /start to resume this work item."

---

## Quality Gate Behavior

**--complete mode:** All gates must pass. If any fail, the session cannot be completed. Fix issues and retry.

**--incomplete mode:** Gates run and show warnings but don't block. Useful when running out of context or needing to checkpoint work-in-progress.
