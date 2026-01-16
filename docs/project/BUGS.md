# Solokit Bug Tracker

This document tracks bugs discovered during development and testing.

## Status Legend
- 🔴 CRITICAL - Blocks core functionality
- 🟠 HIGH - Significant impact on user experience
- 🟡 MEDIUM - Noticeable but has workarounds
- 🟢 LOW - Minor issue or cosmetic
- ✅ FIXED - Bug has been resolved

---

## Bug #20: Learning Curator Extracts Incomplete and Example Learnings
**Status:** ✅ FIXED (Session 3) - Fixed regex patterns, added file type filtering, and standardized metadata structure.

---

## Bug #21: /start Command Ignores Work Item ID Argument
**Status:** ✅ FIXED (Session 6) - Added argument parsing to briefing_generator.py to respect explicit work item selection.

---

## Bug #22: Git Branch Status Not Finalized When Switching Work Items
**Status:** ✅ FIXED (Session 7) - Implemented automatic git branch status finalization when starting new work items.

---

## Bug #23: Bug Spec Template Missing Acceptance Criteria Section
**Status:** ✅ FIXED (Session 4) - Added Acceptance Criteria section to bug_spec.md and refactor_spec.md templates.

---

## Bug #24: Learning Curator Extracts Test Data Strings as Real Learnings
**Status:** ✅ FIXED (Session 5) - Excluded test directories from learning extraction and improved content validation.

---

## Bug #25: /sk:end Requires Pre-committed Changes, Cannot Commit as Part of Session End
**Status:** ✅ FIXED - The /end skill handles uncommitted changes by committing them before calling sk end, providing a seamless user experience.

---

## Bug Template

Use this template when documenting new bugs. Copy the structure below and fill in all sections with specific details.

```markdown
## Bug #XX: [Bug Title]

**Status:** 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW

**Discovered:** YYYY-MM-DD (During [context: session, testing, production, etc.])

### Description

Clear, concise description of the bug and its impact on users/system.

**Example:**
> User authentication fails intermittently when logging in from mobile devices. Users see a "Session expired" error even though they just created a new session. This affects approximately 15% of mobile login attempts based on error logs.

### Steps to Reproduce

Detailed steps that reliably reproduce the bug:

1. Step 1
2. Step 2
3. Step 3

**Environment:**
- Device/Browser: [e.g., iPhone 14 Pro, Chrome 119]
- OS Version: [e.g., iOS 17.0, Windows 11]
- App/System Version: [e.g., v2.3.1]
- Network: [e.g., WiFi, 5G]

### Expected Behavior

What should happen when the user performs the steps above.

### Actual Behavior

What actually happens, including error messages, logs, screenshots.

**Error Log (if applicable):**
```
[Include relevant error messages or log entries]
```

**Screenshot:** [Attach or describe visual issues]

### Impact

- **Severity:** [Critical/High/Medium/Low] (with justification)
- **Affected Users:** [percentage/number of users affected]
- **Affected Versions:** [which versions have this bug]
- **Business Impact:** [effect on metrics, user experience, revenue]
- **Workaround:** [temporary fix if available, or "None"]

### Root Cause Analysis

#### Investigation

Document what you did to investigate: logs reviewed, code analyzed, experiments run.

**Example:**
1. Reviewed application logs for past 7 days
2. Identified pattern: failures only occur on mobile devices
3. Checked cache metrics: intermittent connection timeouts
4. Analyzed relevant code in [file:line]
5. Reproduced locally with [conditions]

**Key Findings:**
- Finding 1
- Finding 2
- Finding 3

#### Root Cause

The underlying technical cause of the bug.

**Code:**
```python
# Current buggy code in file.py:47-52
def problematic_function():
    # Show the problematic code
    pass
```

#### Why It Happened

Why was this bug introduced? What can we learn?

**Contributing Factors:**
- Factor 1 (e.g., insufficient testing)
- Factor 2 (e.g., missing monitoring)
- Factor 3 (e.g., incorrect assumptions)

### Fix Approach

How will this bug be fixed? Include code changes if relevant.

**Code Changes:**
```python
# Fixed code in file.py:47-58
def fixed_function():
    # Show the corrected code
    pass
```

**Files Modified:**
- `path/to/file1.py` - Description of changes
- `path/to/file2.py` - Description of changes

### Acceptance Criteria

- [ ] Root cause is identified and addressed (not just symptoms)
- [ ] All reproduction steps no longer trigger the bug
- [ ] Comprehensive tests added to prevent regression
- [ ] No new bugs or regressions introduced by the fix
- [ ] Edge cases identified in investigation are handled
- [ ] All tests pass (unit, integration, and manual)

### Testing Strategy

#### Regression Tests
- [ ] Add unit test for [specific scenario]
- [ ] Add integration test for [workflow]
- [ ] Add test to verify [edge case]

#### Manual Verification
- [ ] Test on [environment/device]
- [ ] Test with [specific conditions]
- [ ] Verify [expected outcome]

#### Edge Cases
- [ ] Test with [edge case 1]
- [ ] Test with [edge case 2]

### Prevention

How can we prevent similar bugs in the future?

- Add tests for [scenario]
- Set up monitoring/alerting for [metric]
- Code review checklist: [specific check]
- Documentation: [what to document]

### Workaround

Temporary fix available to users while bug is being fixed, or "None" if no workaround exists.

### Related Issues

- Bug #XX: [related bug]
- Enhancement #XX: [related enhancement]
- External issue: [link]

### Files Affected

- `path/to/file1.py:line` - Description
- `path/to/file2.py:line` - Description
```
