# Dependency Installation Gaps Report

**Date:** 2025-11-21
**Author:** Claude Code Analysis
**Status:** Ready for Implementation

## Executive Summary

This report documents critical gaps in how dependencies are installed across different solokit usage scenarios. The primary issue is that **Playwright browsers are not installed during `sk init`**, causing E2E tests to fail for new users until they manually install browsers.

---

## Scenarios Analyzed

| Scenario | Description | Status |
|----------|-------------|--------|
| Local test runs | `python analysis-docs/test_all_templates.py` | Works (browsers cached) |
| CI smoke tests | `.github/workflows/test-pr.yml` | Works (E2E skipped) |
| New user experience | `pip install solokit` → `sk init` | **BROKEN** for E2E |
| User's project CI | Template workflows on GitHub | Works (browsers installed) |

---

## Gap 1: Playwright Browsers Not Installed by `sk init`

### Severity: HIGH

### Problem

When a user runs `sk init --template saas_t3 --tier tier-3-comprehensive`, the `playwright` npm package is installed, but the actual browser binaries (chromium, firefox, webkit) are NOT installed.

### Current Behavior

```bash
sk init --template saas_t3 --tier tier-3-comprehensive
# ✓ Playwright npm package installed
# ✗ Playwright browsers NOT installed

npm run test:e2e
# Error: browserType.launch: Executable doesn't exist at /path/to/chromium
# Run "npx playwright install" to download browsers
```

### Expected Behavior

```bash
sk init --template saas_t3 --tier tier-3-comprehensive
# ✓ Playwright npm package installed
# ✓ Playwright browsers installed (for tier-3+)

npm run test:e2e
# ✓ Tests run successfully
```

### Affected Files

| File | Line | Current Code |
|------|------|--------------|
| `src/solokit/init/dependency_installer.py` | 166 | Missing browser install after npm packages |

### Root Cause

The `install_npm_dependencies()` function installs npm packages but does not run `npx playwright install --with-deps` for tier-3+ projects.

### Impact

- **New users:** First E2E test attempt fails with confusing error
- **Developer experience:** Broken out-of-box experience for tier-3+ projects
- **Documentation:** No mention of manual browser installation requirement

### Recommended Fix

**Option A: Auto-install browsers (Recommended)**

Add to `dependency_installer.py` after line 166:

```python
# Install Playwright browsers for tier-3+
if tier in ["tier-3-comprehensive", "tier-4-production"]:
    logger.info("Installing Playwright browsers...")
    browser_result = runner.run(
        ["npx", "playwright", "install", "--with-deps"],
        cwd=project_root,
        timeout=300  # 5 minutes for browser download
    )
    if browser_result.success:
        logger.info("✓ Playwright browsers installed")
    else:
        logger.warning(f"Playwright browser installation failed: {browser_result.stderr}")
        logger.warning("Run 'npx playwright install --with-deps' manually")
```

**Option B: Document manual step**

Add to generated README.md for tier-3+ projects:

```markdown
## E2E Testing Setup

Before running E2E tests, install Playwright browsers:

```bash
npx playwright install --with-deps
```

Then run tests:
```bash
npm run test:e2e
```
```

### Estimated Effort

- Option A: 30 minutes (code change + testing)
- Option B: 15 minutes (template update)

---

## Gap 2: Test Script Skips Playwright Browser Installation

### Severity: MEDIUM

### Problem

The test script `test_all_templates.py` explicitly skips the "Install Playwright browsers" CI step when simulating CI checks, meaning browser-related failures are never caught locally.

### Current Behavior

```python
# analysis-docs/test_all_templates.py line 903
skip_keywords = [
    'checkout', 'setup', 'install dependencies', 'install playwright',  # <-- SKIPPED
    'upload', 'show mutation results',
    'prisma migrate', 'set up python', 'check if'
]
```

### Impact

- **Local testing:** E2E tests appear to pass but actually aren't running with browsers
- **CI failures:** Issues only discovered after pushing to GitHub
- **GCP tests:** The `run-gcp-tests.sh` failures you're seeing are likely related

### Recommended Fix

Remove `'install playwright'` from skip_keywords OR add explicit browser installation:

```python
# Option 1: Don't skip browser installation
skip_keywords = [
    'checkout', 'setup', 'install dependencies',  # Removed 'install playwright'
    'upload', 'show mutation results',
    'prisma migrate', 'set up python', 'check if'
]

# Option 2: Add explicit browser installation before CI checks
def _run_ci_checks(self, project_path: Path, stack: str, tier: str) -> tuple[bool, List[str]]:
    # Install Playwright browsers first for Next.js stacks
    if stack != "ml_ai_fastapi" and tier in ["tier-3-comprehensive", "tier-4-production"]:
        self._run_command(["npx", "playwright", "install", "--with-deps"], project_path)
    # ... rest of CI check logic
```

### Estimated Effort

- 15-30 minutes

---

## Gap 3: GCP Test Script Browser Installation Issues

### Severity: MEDIUM

### Problem

The `scripts/run-gcp-tests.sh` installs Playwright browsers globally, but individual test projects may not find them due to path issues.

### Current Behavior

```bash
# run-gcp-tests.sh line 555-559
npx -y playwright@latest install chromium
```

This installs to `~/.cache/ms-playwright/` but test projects look in their own `node_modules`.

### Recommended Fix

Either:

1. **Set `PLAYWRIGHT_BROWSERS_PATH` environment variable:**
```bash
export PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright
```

2. **Install browsers per-project:**
```bash
cd $project_path && npx playwright install --with-deps
```

3. **Use `--with-deps` flag** to ensure system dependencies are available:
```bash
npx playwright install chromium --with-deps
```

### Estimated Effort

- 15 minutes

---

## Gap 4: Missing requirements-dev.txt Validation for Python Stack

### Severity: LOW

### Problem

The ML/AI FastAPI template's CI expects `requirements-dev.txt` to contain all tier-specific tools, but there's no validation that this file is correctly generated.

### Current Behavior

The test script handles this by installing missing packages on-the-fly:

```python
# test_all_templates.py lines 1068-1076
# Installs packages found in workflow files that aren't in requirements
```

### Impact

- **Inconsistency:** Local dev may have different packages than CI
- **Debugging difficulty:** "Works on my machine" issues

### Recommended Fix

Add validation in `dependency_installer.py` to verify `requirements-dev.txt` contains expected packages for the tier level.

### Estimated Effort

- 1 hour

---

## Gap 5: No Documentation for Manual Steps

### Severity: LOW

### Problem

Generated README.md doesn't mention:
- Playwright browser installation for tier-3+
- Database setup for Prisma (already in CI but not documented)
- Environment variable requirements

### Recommended Fix

Update `src/solokit/init/readme_generator.py` to include tier-specific setup instructions.

### Estimated Effort

- 30 minutes

---

## Summary Table

| Gap | Severity | Impact | Fix Complexity | Priority |
|-----|----------|--------|----------------|----------|
| Gap 1: Playwright browsers not in `sk init` | HIGH | New user E2E broken | Low | P0 |
| Gap 2: Test script skips browser install | MEDIUM | CI issues not caught locally | Low | P1 |
| Gap 3: GCP script browser path issues | MEDIUM | GCP tests failing | Low | P1 |
| Gap 4: requirements-dev.txt validation | LOW | Inconsistent environments | Medium | P2 |
| Gap 5: Missing setup documentation | LOW | User confusion | Low | P2 |

---

## Recommended Implementation Order

### Phase 1: Critical Fix (Gap 1)
1. Add Playwright browser installation to `dependency_installer.py` for tier-3+
2. Test locally with all 4 stacks
3. Verify new user flow works end-to-end

### Phase 2: Test Infrastructure (Gaps 2, 3)
1. Update `test_all_templates.py` to not skip browser installation
2. Fix `run-gcp-tests.sh` browser path issues
3. Run full Phase 4 tests to verify

### Phase 3: Polish (Gaps 4, 5)
1. Add requirements-dev.txt validation
2. Update README generator with setup instructions
3. Document all manual steps

---

## Testing Verification

After implementing fixes, verify with:

```bash
# Test 1: New user flow
rm -rf /tmp/test-project
cd /tmp
sk init --template saas_t3 --tier tier-3-comprehensive test-project
cd test-project
npm run test:e2e  # Should pass without manual browser install

# Test 2: All stacks
python analysis-docs/test_all_templates.py --phase 1 --ci-checks --workers 4

# Test 3: GCP full suite
./scripts/run-gcp-tests.sh
```

---

## Related Files

| File | Purpose |
|------|---------|
| `src/solokit/init/dependency_installer.py` | Main dependency installation logic |
| `src/solokit/init/orchestrator.py` | Init flow orchestration |
| `src/solokit/templates/stack-versions.yaml` | Package versions and install commands |
| `analysis-docs/test_all_templates.py` | Test script for template validation |
| `scripts/run-gcp-tests.sh` | GCP remote test execution |
| `src/solokit/templates/*/ci-cd/.github/workflows/test.yml` | Template CI workflows |

---

## Appendix: Dependency Flow Diagrams

### Current Flow (Broken for E2E)

```
pip install solokit
        │
        ▼
sk init --tier tier-3-comprehensive
        │
        ├── Templates copied
        ├── package.json created
        ├── npm install (packages only)
        │       │
        │       └── playwright package ✓
        │           playwright browsers ✗
        │
        ▼
npm run test:e2e
        │
        ▼
    ❌ FAILS
"Browsers not installed"
```

### Fixed Flow

```
pip install solokit
        │
        ▼
sk init --tier tier-3-comprehensive
        │
        ├── Templates copied
        ├── package.json created
        ├── npm install (packages)
        │       │
        │       └── playwright package ✓
        │
        ├── npx playwright install --with-deps  ← NEW STEP
        │       │
        │       └── playwright browsers ✓
        │
        ▼
npm run test:e2e
        │
        ▼
    ✅ PASSES
```

---

## Work Item Suggestion

```yaml
id: feature_fix_dependency_installation_gaps
type: feature
title: Fix Playwright browser installation gaps in sk init
priority: high
estimated_sessions: 2
description: |
  Implement automatic Playwright browser installation for tier-3+
  Next.js projects during sk init, update test scripts, and fix
  GCP test infrastructure.

acceptance_criteria:
  - New user can run E2E tests immediately after sk init (tier-3+)
  - Test script catches browser-related issues locally
  - GCP tests pass for all stacks
  - README includes setup instructions for manual steps

dependencies: []
```
