# Solokit Workflow Enhancements

This document tracks identified workflow improvements to make Solokit more user-friendly and automated.

## Status Legend
- 🔵 IDENTIFIED - Enhancement identified, not yet implemented
- 🟡 IN_PROGRESS - Currently being worked on
- ✅ IMPLEMENTED - Completed and merged

---

## Completed Enhancements

All core workflow enhancements have been implemented:

- **Enhancement #1**: Auto Git Initialization in `sk init` → ✅ IMPLEMENTED
- **Enhancement #2**: CHANGELOG Update Workflow → ✅ IMPLEMENTED
- **Enhancement #3**: Pre-flight Commit Check in `/sk:end` → ✅ IMPLEMENTED
- **Enhancement #4**: Add OS-Specific Files to Initial .gitignore → ✅ IMPLEMENTED
- **Enhancement #5**: Create Initial Commit on Main During sk init → ✅ IMPLEMENTED
- **Enhancement #6**: Work Item Completion Status Control → ✅ IMPLEMENTED (Session 11)
- **Enhancement #7**: Phase 1 - Documentation Reorganization & Project Files → ✅ IMPLEMENTED (Session 8)
- **Enhancement #8**: Phase 2 - Test Suite Reorganization → ✅ IMPLEMENTED (Session 9, 1,401 tests, 85% coverage)
- **Enhancement #9**: Phase 3 - Complete Phase 5.9 (src/ Layout Transition) → ✅ IMPLEMENTED (Session 12)
- **Enhancement #10**: Add Work Item Deletion Command → ✅ IMPLEMENTED (Session 13, PR #90)
- **Enhancement #11**: Enhanced Session Briefings with Context Continuity → ✅ IMPLEMENTED (Session 14)
- **Enhancement #12**: Change `/sk:end` Default to Complete → ✅ IMPLEMENTED (Session 30)
- **Enhancement #13**: Interactive UI Integration → ✅ IMPLEMENTED (Session 31)
- **Enhancement #14**: Template-Based Project Initialization → ✅ IMPLEMENTED (Session 32)

---

### Enhancement #15: Session Briefing Optimization

**Status:** 🔵 IDENTIFIED

**Problem:**

Session briefings currently consume significant context window space and may not provide the most useful information for AI-assisted development. Potential issues include:

1. **Excessive context usage**: Briefings may include redundant or less relevant information
2. **Missing critical context**: Important architectural constraints or patterns might be omitted
3. **Inefficient information structure**: Data not organized for optimal AI consumption
4. **Lack of progressive disclosure**: All information presented upfront rather than contextually

**Proposed Solution:**

Research and optimize session briefing content and structure to:

1. **Maximize information value**: Include only the most relevant and actionable information
2. **Minimize context usage**: Compress or restructure data for efficiency
3. **Improve AI effectiveness**: Format information in ways that improve AI understanding
4. **Context-aware loading**: Load additional detail on-demand rather than upfront

**Implementation:**

To be researched and determined during implementation. May include:
- Analysis of current briefing content and usage patterns
- Identification of high-value vs low-value information
- Experimentation with different information structures
- Compression techniques for historical data
- Dynamic context loading strategies

**Files Affected:**

**Modified:**
- `src/solokit/session/briefing.py` - Session briefing generation
- `src/solokit/session/briefing/` - Briefing module components
- `.claude/commands/start.md` - Start command documentation
- Briefing templates and data structures

**Benefits:**

1. **More context available**: Reduced briefing size leaves more room for code and docs
2. **Better AI assistance**: Higher quality information improves AI effectiveness
3. **Faster sessions**: Less time loading and processing briefing data
4. **Improved focus**: Only relevant information presented

**Priority:** High - Impacts every session and all future work

**Notes:**
- Details to be researched and refined during implementation
- May involve experimentation and iteration to find optimal approach
- Should measure context usage before and after optimization

---

### Enhancement #16: Pre-Merge Security Gates

**Status:** 🔵 IDENTIFIED

**Problem:**

Currently, security scans run at `/sk:end`, but if they fail, code might already be committed to the branch. There's no enforcement mechanism to prevent merging insecure code to main. Critical security issues include:

1. **Secret exposure**: API keys, passwords, tokens accidentally committed
2. **Known vulnerabilities**: Dependencies with CVEs in production
3. **Code vulnerabilities**: SQL injection, XSS, insecure authentication patterns
4. **Supply chain attacks**: Malicious packages in dependencies
5. **License compliance**: Incompatible licenses that create legal risk

**Current Workflow Gap:**
```
Code written → /sk:end → Security scan (may fail) → Commit to branch → Merge to main
                                                      ❌ No gate here
```

**Proposed Solution:**

Implement **mandatory pre-merge security gates** that prevent merging to main if critical security issues exist:

1. **Secret Scanning**
   - Scan for API keys, tokens, passwords, private keys
   - Tools: GitGuardian, TruffleHog, detect-secrets
   - Block merge if secrets detected

2. **Static Application Security Testing (SAST)**
   - Analyze code for security vulnerabilities
   - Check for SQL injection, XSS, insecure crypto, etc.
   - Tools: Bandit (Python), ESLint security plugins (JS/TS), Semgrep
   - Block merge if critical/high vulnerabilities found

3. **Dependency Vulnerability Scanning**
   - Check for known CVEs in dependencies
   - Tools: Safety (Python), npm audit (JS/TS), Snyk
   - Block merge if critical CVEs exist

4. **Supply Chain Security**
   - Detect malicious or compromised packages
   - Verify package signatures and checksums
   - Tools: Sigstore, Socket Security

5. **License Compliance**
   - Ensure dependencies use compatible licenses
   - Flag GPL in proprietary projects, etc.
   - Tools: license-checker, FOSSA

**Implementation:**

**Pre-merge hook (Git or CI/CD):**
```bash
# .git/hooks/pre-push or CI workflow
solokit security-scan --pre-merge
→ Runs all security checks
→ Exits with code 1 if critical issues found
→ Blocks push/merge
```

**Quality gate integration:**
```python
# Note: This file will be created during implementation
# src/solokit/quality/security_gates.py
def run_pre_merge_security_gates():
    results = {
        "secret_scan": run_secret_scanning(),
        "sast": run_static_analysis(),
        "dependencies": scan_dependencies(),
        "supply_chain": check_supply_chain(),
        "licenses": check_license_compliance()
    }
    return all_passed, results
```

**Files Affected:**

**New:**
- `src/solokit/security/secret_scanner.py` - Secret detection (will be created)
- `src/solokit/security/sast_scanner.py` - Static analysis (will be created)
- `src/solokit/security/dependency_scanner.py` - CVE checking (will be created)
- `src/solokit/security/supply_chain_checker.py` - Package verification (will be created)
- `src/solokit/security/license_checker.py` - License compliance (will be created)
- `src/solokit/quality/security_gates.py` - Pre-merge gate orchestration (will be created)
- `.git/hooks/pre-push` - Git hook for local enforcement
- Tests for all security modules

**Modified:**
- `src/solokit/session/complete.py` - Integrate pre-merge security gates
- `.session/config.json` - Add security gate configuration
- CI/CD workflows - Add security gate job

**Benefits:**

1. **Prevents secret leaks**: Catches credentials before they reach remote
2. **Blocks vulnerable code**: No critical security issues in production
3. **Supply chain protection**: Detects malicious dependencies
4. **Compliance assurance**: Legal risks from licenses caught early
5. **Developer awareness**: Immediate feedback on security issues
6. **Audit trail**: All security decisions documented

**Priority:** Critical - Security is foundational, must be enforced before anything reaches production

---

### Enhancement #17: Continuous Security Monitoring

**Status:** 🔵 IDENTIFIED

**Problem:**

Security is currently checked only during development sessions. Between sessions, new vulnerabilities may be discovered (CVEs published), and the codebase remains unmonitored. This creates a security gap:

1. **Zero-day vulnerabilities**: New CVEs published for existing dependencies
2. **Unmaintained dependencies**: Libraries deprecated or abandoned
3. **Drift from security best practices**: New security advisories not applied
4. **No proactive alerting**: Developer only finds issues when starting next session

**Current Gap:**
```
Session 1: Security scan ✓ → Time passes (days/weeks) → New CVE published! ❌ No alert
                                                       → Session 2: User unaware
```

**Proposed Solution:**

Implement **continuous security monitoring** that runs scheduled scans and alerts developers of new security issues:

1. **Scheduled CVE Scanning**
   - Daily/weekly scans for new CVEs in dependencies
   - Compare against CVE databases (NVD, GitHub Advisory)
   - Generate alerts for critical/high severity issues

2. **Dependency Update Monitoring**
   - Track security patches for dependencies
   - Automatically create work items for critical updates
   - Suggest safe update paths (minor vs major version changes)

3. **Security Advisory Notifications**
   - Subscribe to security advisories for frameworks used
   - Alert on new attack vectors or best practice changes
   - Generate remediation work items

4. **License Compliance Monitoring**
   - Track dependency license changes
   - Alert on new incompatible licenses
   - Monitor for license violations

**Implementation:**

**Scheduled monitoring (GitHub Actions, cron):**
```yaml
# .github/workflows/security-monitoring.yml
name: Security Monitoring
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security monitoring
        run: solokit security-monitor --create-work-items
```

**Monitoring system:**
```python
# Note: This file will be created during implementation
# src/solokit/security/monitor.py
class SecurityMonitor:
    def scan_for_new_cves(self):
        # Check dependencies against CVE databases

    def check_for_updates(self):
        # Find security updates for dependencies

    def create_security_work_items(self, findings):
        # Auto-create work items for critical issues

    def notify_developer(self, critical_issues):
        # Email/Slack notification
```

**Files Affected:**

**New:**
- `src/solokit/security/monitor.py` - Continuous monitoring system (will be created)
- `src/solokit/security/cve_database.py` - CVE lookup and caching (will be created)
- `src/solokit/security/advisory_tracker.py` - Security advisory tracking (will be created)
- `.github/workflows/security-monitoring.yml` - Scheduled workflow (will be created)
- Tests for monitoring system

**Modified:**
- `src/solokit/work_items/creator.py` - Auto-create security work items
- `.session/config.json` - Add monitoring configuration
- `src/solokit/notifications/` - Alert mechanisms (email, Slack) (will be created)

**Benefits:**

1. **Proactive security**: Find vulnerabilities before attackers
2. **Zero-day protection**: Immediate alerts for new CVEs
3. **Reduced exposure window**: Faster response to security issues
4. **Automated remediation**: Work items auto-created
5. **Compliance**: Continuous license monitoring
6. **Peace of mind**: Always know security status

**Priority:** High - Continuous protection is essential for production systems

---

### Enhancement #18: Test Quality Gates

**Status:** 🔵 IDENTIFIED

**Problem:**

Currently, tests are required but there's no validation of test quality. This allows:

1. **Weak tests**: Tests that always pass regardless of code correctness
2. **Insufficient coverage**: Critical paths untested
3. **Missing test types**: No integration or E2E tests
4. **Performance regressions**: No performance test baseline
5. **Flaky tests**: Unreliable tests that randomly fail

**Example of weak tests:**
```python
def test_user_authentication():
    result = authenticate_user("user", "pass")
    assert result is not None  # ❌ Always passes even if auth is broken
```

**Current Gap:**
```
Tests written → All tests pass ✓ → Merge
                ❌ But tests might be weak or incomplete
```

**Proposed Solution:**

Implement **test quality gates** that enforce test effectiveness:

1. **Critical Path Coverage**
   - Identify critical paths (authentication, payment, data loss scenarios)
   - Require >90% coverage for critical paths
   - Tools: coverage.py with path analysis, Istanbul

2. **Mutation Testing**
   - Inject bugs into code, ensure tests catch them
   - Mutation score must meet threshold (e.g., >75%)
   - Tools: Stryker (JS/TS), mutmut (Python)

3. **Integration Test Requirements**
   - Require integration tests for multi-component features
   - Validate data flow across components
   - Minimum number of integration tests per work item type

4. **E2E Test Requirements** (for web apps)
   - Require E2E tests for user-facing features
   - Validate complete user workflows
   - Tools: Playwright, Cypress, Selenium

5. **Performance Regression Tests**
   - Establish performance baselines
   - Fail if performance degrades beyond threshold (e.g., >10% slower)
   - Track response times, throughput, resource usage

6. **Test Reliability (Flakiness Detection)**
   - Detect flaky tests (inconsistent pass/fail)
   - Quarantine flaky tests
   - Require fixing before merge

**Implementation:**

**Test quality gate:**
```python
# Note: This file will be created during implementation
# src/solokit/quality/test_quality_gates.py
class TestQualityGates:
    def check_critical_path_coverage(self, work_item):
        # Verify critical paths have >90% coverage

    def run_mutation_testing(self):
        # Run mutation tests, check score

    def validate_integration_tests(self, work_item):
        # Ensure integration tests exist

    def check_e2e_tests(self, work_item):
        # For UI work items, verify E2E tests

    def check_performance_regression(self):
        # Compare against baseline
```

**Work item spec integration:**
```markdown
## Testing Requirements

**Critical Paths:** (auto-detected or specified)
- User authentication flow
- Payment processing
- Data backup/restore

**Required Test Types:**
- [x] Unit tests (>85% coverage)
- [x] Integration tests (≥3 scenarios)
- [x] E2E tests (main user workflow)
- [x] Performance tests (baseline established)

**Mutation Score Target:** 75%
```

**Files Affected:**

**New:**
- `src/solokit/quality/test_quality_gates.py` - Test quality validation (will be created)
- `src/solokit/testing/mutation_runner.py` - Mutation testing integration (will be created)
- `src/solokit/testing/critical_path_analyzer.py` - Critical path identification (will be created)
- `src/solokit/testing/flakiness_detector.py` - Flaky test detection (will be created)
- `src/solokit/testing/performance_baseline.py` - Performance tracking (will be created)
- Tests for all test quality modules

**Modified:**
- `src/solokit/session/complete.py` - Add test quality gates
- `src/solokit/session/validate.py` - Add validation checks
- `src/solokit/work_items/spec_parser.py` - Parse testing requirements
- `.session/config.json` - Test quality thresholds

**Benefits:**

1. **Confidence in tests**: Know tests actually catch bugs
2. **Prevents regressions**: Performance baselines protect against degradation
3. **Complete coverage**: All test types required
4. **Reliable builds**: No flaky tests breaking CI
5. **Quality assurance**: Tests verified to be effective

**Priority:** High - Quality tests are essential for reliable software

---

### Enhancement #19: Advanced Code Quality Gates

**Status:** 🔵 IDENTIFIED

**Problem:**

Current linting only catches basic style issues. Complex code quality problems go undetected:

1. **High complexity**: Functions with cyclomatic complexity >10 are hard to maintain
2. **Code duplication**: Copy-pasted code creates maintenance burden
3. **Dead code**: Unused functions and imports waste space and create confusion
4. **Weak typing**: TypeScript without strict mode allows bugs

**Example:**
```python
def process_order(order):  # Complexity: 23 ❌ Too complex
    if order.status == "pending":
        if order.payment_method == "card":
            if order.card_valid:
                if order.inventory_available:
                    # ... 50 more lines of nested ifs
```

**Current Gap:**
```
Linting passes ✓ → Merge
❌ Complex, duplicated, dead code still merges
```

**Proposed Solution:**

Implement **advanced code quality gates** that enforce maintainability:

1. **Cyclomatic Complexity Enforcement**
   - Fail if function complexity >10
   - Suggest breaking down complex functions
   - Tools: radon (Python), complexity-report (JS/TS)

2. **Code Duplication Detection**
   - Detect copy-pasted code blocks
   - Fail if duplication >5% of codebase
   - Tools: jscpd, pylint duplicate-code

3. **Dead Code Detection**
   - Find unused functions, classes, imports
   - Require removal before merge
   - Tools: vulture (Python), ts-prune (TypeScript)

4. **Type Coverage Enforcement** (TypeScript)
   - Require strict mode in tsconfig.json
   - Fail if `any` types used without justification
   - Measure type coverage percentage

5. **Cognitive Complexity**
   - Measure how hard code is to understand
   - Complement cyclomatic complexity
   - Tools: SonarQube, CodeClimate

6. **Code Documentation Standards**
   - Enforce documentation for public APIs, classes, and functions
   - Validate docstring/JSDoc completeness and quality
   - Require parameter and return type documentation
   - Check for outdated documentation (code changes without doc updates)
   - Generate missing documentation warnings
   - Tools: pydocstyle, JSDoc validation, custom documentation linters

**Implementation:**

**Code quality gate:**
```python
# Note: This file will be created during implementation
# src/solokit/quality/code_quality_gates.py
class CodeQualityGates:
    def check_complexity(self, file_changes):
        # Analyze cyclomatic complexity
        # Fail if any function >10

    def detect_duplication(self):
        # Scan for code duplication
        # Fail if >5% duplicated

    def find_dead_code(self):
        # Detect unused code
        # Report for removal

    def check_type_coverage(self):
        # For TypeScript: verify strict mode
        # Check for excessive `any` usage

    def validate_documentation(self, file_changes):
        # Check for missing docstrings/JSDoc
        # Validate documentation completeness
        # Detect outdated documentation
        # Generate documentation warnings
```

**Configuration:**
```json
// .session/config.json
"code_quality_gates": {
  "complexity": {
    "enabled": true,
    "max_complexity": 10,
    "max_cognitive_complexity": 15
  },
  "duplication": {
    "enabled": true,
    "max_percentage": 5,
    "min_tokens": 50
  },
  "dead_code": {
    "enabled": true,
    "fail_on_unused": true
  },
  "type_coverage": {
    "enabled": true,
    "require_strict_mode": true,
    "max_any_percentage": 2
  },
  "documentation": {
    "enabled": true,
    "require_public_api_docs": true,
    "require_param_docs": true,
    "require_return_docs": true,
    "min_docstring_length": 20,
    "check_outdated_docs": true
  }
}
```

**Files Affected:**

**New:**
- `src/solokit/quality/code_quality_gates.py` - Code quality validation (will be created)
- `src/solokit/analysis/complexity_analyzer.py` - Complexity calculation (will be created)
- `src/solokit/analysis/duplication_detector.py` - Duplication detection (will be created)
- `src/solokit/analysis/dead_code_finder.py` - Dead code detection (will be created)
- `src/solokit/analysis/type_coverage.py` - TypeScript type coverage (will be created)
- `src/solokit/analysis/documentation_validator.py` - Code documentation validation (will be created)
- Tests for all analysis modules

**Modified:**
- `src/solokit/session/complete.py` - Add code quality gates
- `src/solokit/session/validate.py` - Add validation checks
- `.session/config.json` - Code quality thresholds

**Benefits:**

1. **Maintainable code**: Low complexity = easy to understand
2. **DRY principle**: No code duplication
3. **Clean codebase**: No dead code clutter
4. **Type safety**: Strong typing prevents bugs
5. **Technical debt prevention**: Quality enforced continuously
6. **Better documentation**: Code is self-documenting and easier to understand
7. **Onboarding efficiency**: New developers can understand code faster with proper documentation

**Priority:** Medium-High - Prevents technical debt accumulation

---

### Enhancement #20: Production Readiness Gates

**Status:** 🔵 IDENTIFIED

**Problem:**

Code may pass all tests but still not be ready for production. Production-specific requirements are not validated:

1. **No health checks**: Can't monitor service health
2. **No observability**: Can't debug production issues
3. **No error tracking**: Errors silently fail
4. **Inconsistent logging**: Can't trace requests
5. **Unsafe migrations**: Database changes cause downtime

**Example of production failure:**
```
All tests pass ✓ → Deploy to production → Service starts
                                        → Health check missing ❌
                                        → Load balancer can't detect failures
                                        → Site down, no alerts
```

**Proposed Solution:**

Implement **production readiness gates** that validate operational requirements:

1. **Health Check Endpoints**
   - Require `/health` and `/ready` endpoints
   - Validate they return proper status codes
   - Test health check logic actually works

2. **Metrics and Observability**
   - Require `/metrics` endpoint (Prometheus format)
   - Validate metrics exported (request count, latency, errors)
   - Ensure distributed tracing configured (OpenTelemetry)

3. **Error Tracking Integration**
   - Require error tracking setup (Sentry, Rollbar, etc.)
   - Validate errors are captured and reported
   - Test error grouping and notification

4. **Structured Logging**
   - Enforce structured logging (JSON format)
   - Require correlation IDs for request tracing
   - Validate log levels appropriate

5. **Database Migration Safety**
   - Require reversible migrations
   - Test migrations on staging data
   - Validate migration doesn't cause downtime

6. **Configuration Management**
   - All config via environment variables
   - No secrets in code or version control
   - Validate required env vars documented

**Implementation:**

**Production readiness gate:**
```python
# src/solokit/quality/production_gates.py
class ProductionReadinessGates:
    def validate_health_endpoints(self):
        # Check /health and /ready exist
        # Test they return 200

    def validate_metrics(self):
        # Check /metrics endpoint
        # Validate metrics format

    def validate_error_tracking(self):
        # Verify error tracking configured
        # Test error capture works

    def validate_logging(self):
        # Check structured logging
        # Verify correlation IDs

    def validate_migrations(self):
        # Test migrations reversible
        # Validate no downtime
```

**Work item checklist for deployment:**
```markdown
## Production Readiness

- [x] Health check endpoints implemented and tested
- [x] Metrics exported (Prometheus format)
- [x] Error tracking configured and tested
- [x] Structured logging with correlation IDs
- [x] Database migrations tested and reversible
- [x] Required environment variables documented
- [x] Secrets managed via secrets manager (not in code)
```

**Files Affected:**

**New:**
- `src/solokit/quality/production_gates.py` - Production readiness validation (will be created)
- `src/solokit/production/health_check_validator.py` - Health check testing (will be created)
- `src/solokit/production/metrics_validator.py` - Metrics validation (will be created)
- `src/solokit/production/migration_validator.py` - Migration safety checks (will be created)
- Tests for production validation

**Modified:**
- `src/solokit/session/complete.py` - Add production gates for deployment work items
- `src/solokit/templates/deployment.md` - Add production checklist
- `.session/config.json` - Production requirements configuration

**Benefits:**

1. **Operational visibility**: Always know service health
2. **Faster debugging**: Logs and traces available
3. **Proactive alerting**: Errors tracked and reported
4. **Safe deployments**: Migrations tested and reversible
5. **Production confidence**: All operational needs met

**Priority:** High - Essential for production deployments

---

### Enhancement #21: Deployment Safety Gates

**Status:** 🔵 IDENTIFIED

**Problem:**

Deployments can fail or cause outages even with good code:

1. **Untested deployments**: Deployment procedure never practiced
2. **Breaking changes**: API changes break clients
3. **No rollback plan**: Can't revert if deployment fails
4. **Risky releases**: All changes deployed at once

**Example of deployment failure:**
```
Code ready → Deploy to production → API change breaks mobile app
                                  → No rollback procedure ❌
                                  → Site down for hours
```

**Proposed Solution:**

Implement **deployment safety gates** that validate deployment readiness:

1. **Deployment Dry-Run**
   - Test deployment procedure in staging
   - Validate all deployment steps work
   - Ensure no manual steps required

2. **Breaking Change Detection**
   - Detect API changes (endpoints removed, fields changed)
   - Validate backward compatibility
   - Require versioning for breaking changes
   - Tools: OpenAPI diff, GraphQL schema comparison

3. **Rollback Testing**
   - Test rollback procedure before deployment
   - Validate rollback completes successfully
   - Document rollback steps

4. **Canary Deployment Support**
   - Gradual rollout to small percentage of users
   - Monitor metrics during rollout
   - Automatic rollback if errors spike

5. **Smoke Tests**
   - Run smoke tests after deployment
   - Validate critical paths work
   - Automatic rollback if smoke tests fail

**Implementation:**

**Deployment safety gate:**
```python
# src/solokit/deployment/safety_gates.py
class DeploymentSafetyGates:
    def run_dry_run(self, deployment_config):
        # Test deployment in staging

    def detect_breaking_changes(self):
        # Compare API schemas
        # Detect breaking changes

    def test_rollback(self):
        # Execute rollback procedure
        # Validate success

    def setup_canary(self, percentage):
        # Configure canary deployment
        # Set up monitoring

    def run_smoke_tests(self):
        # Execute smoke tests
        # Return results
```

**Deployment workflow:**
```yaml
# .github/workflows/deploy.yml
jobs:
  pre-deployment:
    - Dry-run in staging
    - Detect breaking changes
    - Test rollback procedure

  deploy:
    - Canary to 5% of users
    - Monitor for 10 minutes
    - If metrics good, continue
    - If errors spike, rollback
    - Gradually increase to 100%

  post-deployment:
    - Run smoke tests
    - Verify health checks
    - Monitor for issues
```

**Files Affected:**

**New:**
- `src/solokit/deployment/safety_gates.py` - Deployment validation (will be created)
- `src/solokit/deployment/dry_run.py` - Dry-run execution (will be created)
- `src/solokit/deployment/breaking_change_detector.py` - API diff analysis (will be created)
- `src/solokit/deployment/rollback_tester.py` - Rollback validation (will be created)
- `src/solokit/deployment/canary.py` - Canary deployment orchestration (will be created)
- `src/solokit/deployment/smoke_tests.py` - Smoke test runner (will be created)
- Tests for deployment safety

**Modified:**
- CI/CD workflows - Add deployment gates
- `src/solokit/templates/deployment.md` - Add safety checklist
- `.session/config.json` - Deployment safety configuration

**Benefits:**

1. **Safe deployments**: Tested before production
2. **No breaking changes**: Backward compatibility validated
3. **Quick recovery**: Rollback always available
4. **Gradual rollouts**: Canary reduces risk
5. **Confidence**: Deploy without fear

**Priority:** High - Essential for production stability

---

### Enhancement #22: Disaster Recovery & Backup Automation

**Status:** 🔵 IDENTIFIED

**Problem:**

Production systems lack comprehensive disaster recovery and backup automation:

1. **No automated backups**: Critical data loss risk if manual backups forgotten
2. **Untested recovery procedures**: Backups may be corrupt or incomplete
3. **No disaster recovery plan**: No documented procedure for system restoration
4. **No data retention policies**: Old backups accumulate or critical data deleted too soon
5. **Single point of failure**: No geographic redundancy or failover capability

**Example of failure:**

```
Production running → Database corruption ❌
                   → No recent backup
                   → Or backup exists but restore untested
                   → Or backup incomplete (missing files/secrets)
                   → Hours/days of data loss
                   → Extended downtime
```

**Proposed Solution:**

Implement **comprehensive disaster recovery and backup automation system**:

1. **Automated Backup Strategy**
   - Automated database backups (full, incremental, differential)
   - Automated file system backups
   - Automated configuration and secrets backup (encrypted)
   - Automated infrastructure state backup (IaC state files)
   - Customizable backup schedules (hourly, daily, weekly)

2. **Backup Verification & Testing**
   - Automated backup integrity checks (checksum validation)
   - Automated restore testing in isolated environment
   - Backup completeness validation (all critical data included)
   - Corruption detection and alerting
   - Test restore performance benchmarks

3. **Disaster Recovery Planning**
   - Automated DR plan generation based on system architecture
   - Recovery Time Objective (RTO) and Recovery Point Objective (RPO) tracking
   - Step-by-step recovery procedures (runbooks)
   - Automated failover procedures for critical services
   - Business continuity documentation

4. **Data Retention & Lifecycle Management**
   - Configurable retention policies (7 days, 30 days, 1 year, etc.)
   - Automated old backup cleanup
   - Compliance with data retention regulations
   - Backup versioning and point-in-time recovery
   - Archive to cold storage for long-term retention

5. **Geographic Redundancy**
   - Multi-region backup replication
   - Automated cross-region failover testing
   - Geo-distributed backup storage
   - Regional disaster scenario testing

6. **Recovery Procedures**
   - One-command full system restore
   - Selective data recovery (specific tables, files, configs)
   - Point-in-time recovery (restore to specific timestamp)
   - Dry-run recovery testing (test without affecting production)
   - Recovery progress monitoring and ETA

**Implementation:**

**Backup orchestrator:**
```python
# src/solokit/disaster_recovery/backup_manager.py
class BackupManager:
    def schedule_backups(self, config):
        # Schedule automated backups based on config
        # - Database backups
        # - File system backups
        # - Configuration backups
        # - Infrastructure state backups

    def verify_backup(self, backup_id):
        # Verify backup integrity
        # - Checksum validation
        # - Completeness check
        # - Size validation

    def test_restore(self, backup_id, test_env):
        # Test restore in isolated environment
        # - Spin up test environment
        # - Restore backup
        # - Validate data integrity
        # - Measure restore time
        # - Cleanup test environment
```

**Disaster recovery planner:**
```python
# src/solokit/disaster_recovery/dr_planner.py
class DisasterRecoveryPlanner:
    def generate_dr_plan(self, architecture):
        # Analyze system architecture
        # Generate disaster recovery plan
        # - Identify critical components
        # - Define recovery priorities
        # - Create recovery procedures
        # - Calculate RTO/RPO

    def validate_dr_plan(self):
        # Test disaster recovery plan
        # - Simulate disaster scenarios
        # - Execute recovery procedures
        # - Measure recovery time
        # - Identify gaps and improvements
```

**Recovery executor:**
```python
# src/solokit/disaster_recovery/recovery_executor.py
class RecoveryExecutor:
    def full_system_restore(self, backup_id, target_env):
        # Restore entire system from backup
        # - Restore infrastructure
        # - Restore database
        # - Restore file system
        # - Restore configurations
        # - Verify system health

    def selective_restore(self, backup_id, resources):
        # Restore specific resources
        # - Specific database tables
        # - Specific files
        # - Specific configurations

    def point_in_time_restore(self, timestamp, target_env):
        # Restore system to specific point in time
        # - Find appropriate backups
        # - Restore and replay logs
        # - Verify data consistency
```

**Backup configuration:**
```yaml
# .session/config.json or .solokit/backup_config.yml
backup_config:
  schedule:
    database:
      full: "0 2 * * 0"  # Weekly full backup (Sunday 2 AM)
      incremental: "0 2 * * 1-6"  # Daily incremental
      continuous: true  # Continuous log shipping
    filesystem:
      frequency: "0 3 * * *"  # Daily at 3 AM
      exclude_patterns:
        - "node_modules/"
        - "*.log"
        - ".git/"
    infrastructure:
      frequency: "0 4 * * *"  # Daily at 4 AM
      include:
        - terraform_state
        - kubernetes_manifests
        - ci_cd_configs

  retention:
    short_term: 7  # 7 days
    medium_term: 30  # 30 days
    long_term: 365  # 1 year
    archive_after: 90  # Move to cold storage after 90 days

  verification:
    integrity_check: true  # Always verify checksums
    test_restore_frequency: "0 5 * * 0"  # Weekly restore test
    test_environment: "dr-test"

  storage:
    primary_region: "us-east-1"
    replica_regions:
      - "us-west-2"
      - "eu-west-1"
    encryption: "AES-256"

  recovery_objectives:
    rto: "1h"  # Recovery Time Objective
    rpo: "15m"  # Recovery Point Objective (max data loss)

  notifications:
    backup_failures: ["email", "slack"]
    verification_failures: ["email", "pagerduty"]
    recovery_tests: ["email"]
```

**DR plan template:**
```markdown
# Disaster Recovery Plan

## Recovery Objectives
- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 15 minutes

## Critical Components (Priority Order)
1. Database (PostgreSQL)
2. Application servers
3. File storage
4. Cache layer
5. Background workers

## Disaster Scenarios

### Scenario 1: Database Corruption
**Detection**: Health checks fail, query errors
**Recovery Procedure**:
1. Stop application servers (prevent further corruption)
2. Identify last known good backup
3. Restore database from backup: `solokit dr restore-database --backup-id <id>`
4. Replay transaction logs from backup point to current
5. Verify data integrity: `solokit dr verify-database`
6. Restart application servers
7. Monitor for errors
**Estimated Recovery Time**: 30 minutes

### Scenario 2: Complete Infrastructure Loss
**Detection**: All services unreachable
**Recovery Procedure**:
1. Activate secondary region: `solokit dr activate-failover --region us-west-2`
2. Restore infrastructure: `solokit dr restore-infrastructure --backup-id <id>`
3. Restore database: `solokit dr restore-database --backup-id <id> --region us-west-2`
4. Update DNS to point to new region
5. Verify all services operational
6. Notify stakeholders
**Estimated Recovery Time**: 1 hour

### Scenario 3: Data Deletion (Human Error)
**Detection**: Reports of missing data
**Recovery Procedure**:
1. Identify deletion timestamp
2. Point-in-time restore: `solokit dr restore-point-in-time --timestamp "2025-10-29T10:30:00Z"`
3. Extract affected data
4. Merge recovered data into production
5. Verify data integrity
**Estimated Recovery Time**: 20 minutes
```

**Commands:**
```bash
# Configure backup system
/sk:dr-init

# View backup status
/sk:dr-status

# Test disaster recovery plan
/sk:dr-test [--scenario SCENARIO]

# Restore from backup
/sk:dr-restore [--backup-id ID] [--point-in-time TIMESTAMP]

# Verify backups
/sk:dr-verify-backups

# Generate DR plan
/sk:dr-plan-generate
```

**Files Affected:**

**New:**
- `src/solokit/disaster_recovery/backup_manager.py` - Backup orchestration (will be created)
- `src/solokit/disaster_recovery/dr_planner.py` - DR plan generation (will be created)
- `src/solokit/disaster_recovery/recovery_executor.py` - Recovery execution (will be created)
- `src/solokit/disaster_recovery/backup_verifier.py` - Backup verification (will be created)
- `src/solokit/disaster_recovery/retention_manager.py` - Data lifecycle management (will be created)
- `.claude/commands/dr-init.md` - DR initialization command (will be created)
- `.claude/commands/dr-status.md` - DR status command (will be created)
- `.claude/commands/dr-test.md` - DR testing command (will be created)
- `.claude/commands/dr-restore.md` - Recovery command (will be created)
- `docs/disaster_recovery_plan.md` - Generated DR plan (will be created)
- `.solokit/backup_config.yml` - Backup configuration (will be created)
- Tests for DR system

**Modified:**
- `src/solokit/project/init.py` - Add DR setup to project initialization
- `.session/config.json` - Add DR configuration section
- CI/CD workflows - Add backup verification jobs

**Benefits:**

1. **Data protection**: Automated backups prevent data loss
2. **Business continuity**: Quick recovery from disasters
3. **Tested recovery**: Regular restore testing ensures backups work
4. **Compliance**: Meet data retention and backup requirements
5. **Peace of mind**: Know you can recover from any disaster
6. **Geographic redundancy**: Protected against regional failures
7. **Documented procedures**: Clear recovery steps for any scenario
8. **Minimal downtime**: Fast recovery meets RTO/RPO objectives

**Priority:** Critical - Data loss and prolonged outages can be catastrophic

**Notes:**
- Backup storage costs should be factored into project budget
- Recovery testing should be scheduled during low-traffic periods
- DR plan should be reviewed and updated quarterly
- Encryption keys and secrets must be backed up separately and securely
- Team should be trained on recovery procedures

---

### Enhancement #23: JSON Schema Spec Validation

**Status:** 🔵 IDENTIFIED

**Problem:**

Current spec validation only checks for section presence (completeness checking). This creates issues:

1. **No structure validation**: Sections may be present but empty or malformed
2. **No type checking**: Cannot enforce that "Priority" is one of [critical, high, medium, low]
3. **Late error detection**: Structural issues found during `/start` or `/end`
4. **Poor error messages**: "Section missing" but not "Section has wrong format"
5. **No schema evolution**: Cannot version spec formats or migrate old specs

**Example of current validation gap:**

```markdown
# Current spec file - PASSES current validation
## Acceptance Criteria
(empty section)

## Implementation Details
not a list, just a paragraph

## Priority
Super Urgent!!!  ← Not a valid priority value

Current validator: ✓ All sections present, validation passes
Desired validator: ✗ Multiple schema violations detected
```

**Proposed Solution:**

Implement **JSON Schema-based spec validation** for rigorous spec structure checking:

1. **Schema Definitions**
   - Define JSON Schema for each work item type
   - Validate section structure, content types, enums
   - Support required vs optional fields
   - Version schemas for backward compatibility

2. **Markdown-to-Structure Parser**
   - Parse markdown specs into structured data
   - Extract sections, lists, metadata
   - Convert to JSON for schema validation
   - Preserve original markdown for human readability

3. **Comprehensive Validation**
   - Schema validation (structure, types, enums)
   - Cross-field validation (dependencies must exist)
   - Custom business rules (time box reasonable for spike)
   - Reference validation (links, file paths)

4. **Better Error Messages**
   - Precise error location (line number, section)
   - Explain what's wrong and how to fix
   - Suggest corrections
   - Examples of correct format

5. **Schema Migration**
   - Detect spec version
   - Migrate old specs to new schema
   - Preserve content during migration
   - Log migration actions

**Implementation:**

**JSON Schema definitions:**
```json
// src/solokit/templates/schemas/feature_spec_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://solokit.dev/schemas/feature_spec.json",
  "title": "Feature Spec",
  "description": "Schema for feature work item specifications",
  "type": "object",
  "required": ["title", "type", "overview", "rationale", "acceptance_criteria"],
  "properties": {
    "title": {
      "type": "string",
      "minLength": 5,
      "maxLength": 200,
      "description": "Feature title"
    },
    "type": {
      "type": "string",
      "enum": ["feature"],
      "description": "Work item type"
    },
    "priority": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "default": "medium",
      "description": "Feature priority"
    },
    "overview": {
      "type": "string",
      "minLength": 20,
      "description": "Feature overview (what, why, for whom)"
    },
    "rationale": {
      "type": "string",
      "minLength": 20,
      "description": "Why this feature is needed"
    },
    "acceptance_criteria": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "minLength": 5
      },
      "description": "List of acceptance criteria"
    },
    "implementation_details": {
      "type": "object",
      "properties": {
        "approach": {"type": "string"},
        "files_to_modify": {
          "type": "array",
          "items": {"type": "string"}
        },
        "new_files": {
          "type": "array",
          "items": {"type": "string"}
        },
        "dependencies": {
          "type": "array",
          "items": {"type": "string", "pattern": "^[a-z_]+$"}
        }
      }
    },
    "testing_strategy": {
      "type": "object",
      "properties": {
        "unit_tests": {"type": "array", "items": {"type": "string"}},
        "integration_tests": {"type": "array", "items": {"type": "string"}},
        "test_coverage_target": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100,
          "default": 80
        }
      }
    },
    "dependencies": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^(feature|bug|refactor|security|integration_test|deployment)_[a-z0-9_]+$"
      },
      "description": "Work item dependencies (must exist)"
    }
  }
}
```

**Spec parser:**
```python
# src/solokit/work_items/spec_parser.py (enhanced)
import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, List

class SpecParser:
    """Parse and validate markdown specs against JSON schemas"""

    def __init__(self):
        self.schema_dir = Path("src/solokit/templates/schemas")
        self.schemas = self.load_schemas()

    def load_schemas(self) -> Dict[str, Dict]:
        """Load all JSON schemas"""
        schemas = {}
        for schema_file in self.schema_dir.glob("*_schema.json"):
            work_item_type = schema_file.stem.replace("_spec_schema", "")
            with open(schema_file) as f:
                schemas[work_item_type] = json.load(f)
        return schemas

    def parse_spec_to_structure(self, spec_path: Path) -> Dict[str, Any]:
        """Parse markdown spec into structured data"""
        content = spec_path.read_text()

        # Extract frontmatter (YAML)
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                content = parts[2]

        # Parse markdown sections
        sections = self.parse_markdown_sections(content)

        # Combine frontmatter and sections
        structure = {**frontmatter, **sections}

        return structure

    def parse_markdown_sections(self, content: str) -> Dict[str, Any]:
        """Parse markdown sections into structured data"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            # Detect section headers
            if line.startswith("##"):
                # Save previous section
                if current_section:
                    sections[current_section] = self.parse_section_content(
                        current_section, "\n".join(current_content)
                    )

                # Start new section
                current_section = line.replace("##", "").strip().lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = self.parse_section_content(
                current_section, "\n".join(current_content)
            )

        return sections

    def parse_section_content(self, section_name: str, content: str) -> Any:
        """Parse section content based on expected type"""
        content = content.strip()

        # List sections (bullet points)
        if section_name in ["acceptance_criteria", "implementation_steps", "test_cases"]:
            items = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    items.append(line[1:].strip())
                elif line.startswith("- [ ]") or line.startswith("- [x]"):
                    items.append(line[5:].strip())
            return items if items else content

        # Object sections (key-value pairs)
        elif section_name in ["implementation_details", "testing_strategy"]:
            # Try to parse as structured data
            try:
                return self.parse_structured_section(content)
            except:
                return {"raw": content}

        # String sections
        else:
            return content

    def parse_structured_section(self, content: str) -> Dict[str, Any]:
        """Parse structured section content (key: value format)"""
        result = {}
        current_key = None
        current_value = []

        for line in content.split("\n"):
            if ":" in line and not line.startswith(" "):
                # Save previous key-value
                if current_key:
                    result[current_key] = "\n".join(current_value).strip()

                # Start new key
                key, value = line.split(":", 1)
                current_key = key.strip().lower().replace(" ", "_")
                current_value = [value.strip()] if value.strip() else []
            else:
                current_value.append(line)

        # Save last key-value
        if current_key:
            result[current_key] = "\n".join(current_value).strip()

        return result

    def validate_spec_structure(
        self,
        spec_path: Path,
        work_item_type: str
    ) -> tuple[bool, List[str]]:
        """Validate spec against JSON schema"""

        # Get schema
        if work_item_type not in self.schemas:
            return False, [f"No schema found for type: {work_item_type}"]

        schema = self.schemas[work_item_type]

        # Parse spec to structure
        try:
            structure = self.parse_spec_to_structure(spec_path)
        except Exception as e:
            return False, [f"Failed to parse spec: {str(e)}"]

        # Validate against schema
        errors = []
        try:
            jsonschema.validate(instance=structure, schema=schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(self.format_validation_error(e))
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {str(e)}")

        return False, errors

    def format_validation_error(self, error: jsonschema.ValidationError) -> str:
        """Format validation error with helpful message"""
        path = " → ".join(str(p) for p in error.path) if error.path else "root"

        message = f"Validation error at '{path}':\n"
        message += f"  Issue: {error.message}\n"

        # Add helpful suggestions
        if error.validator == "required":
            message += f"  Fix: Add the required field '{error.validator_value}'\n"
        elif error.validator == "enum":
            message += f"  Fix: Use one of: {', '.join(error.validator_value)}\n"
        elif error.validator == "minLength":
            message += f"  Fix: Provide at least {error.validator_value} characters\n"
        elif error.validator == "minItems":
            message += f"  Fix: Provide at least {error.validator_value} items\n"

        return message

    def validate_cross_references(
        self,
        spec_path: Path,
        work_item_id: str
    ) -> tuple[bool, List[str]]:
        """Validate cross-references (dependencies exist, files exist, etc.)"""
        from solokit.work_items.repository import WorkItemRepository

        structure = self.parse_spec_to_structure(spec_path)
        errors = []

        # Validate dependencies exist
        dependencies = structure.get("dependencies", [])
        if dependencies:
            repository = WorkItemRepository()
            existing_work_items = {wi["id"] for wi in repository.list_work_items()}

            for dep in dependencies:
                if dep not in existing_work_items:
                    errors.append(f"Dependency '{dep}' does not exist")
                elif dep == work_item_id:
                    errors.append(f"Work item cannot depend on itself")

        # Validate file references (if mentioned)
        files_to_modify = structure.get("implementation_details", {}).get("files_to_modify", [])
        for file_path in files_to_modify:
            if not Path(file_path).exists():
                errors.append(f"File to modify does not exist: {file_path}")

        return len(errors) == 0, errors
```

**Enhanced spec validator:**
```python
# src/solokit/work_items/spec_validator.py (enhanced)
class SpecValidator:
    def __init__(self):
        self.parser = SpecParser()

    def validate_spec(
        self,
        spec_path: Path,
        work_item_type: str,
        work_item_id: str
    ) -> tuple[bool, List[str]]:
        """Comprehensive spec validation"""
        all_errors = []

        # 1. Schema validation
        schema_valid, schema_errors = self.parser.validate_spec_structure(
            spec_path, work_item_type
        )
        all_errors.extend(schema_errors)

        # 2. Cross-reference validation
        refs_valid, ref_errors = self.parser.validate_cross_references(
            spec_path, work_item_id
        )
        all_errors.extend(ref_errors)

        # 3. Custom business rules
        rules_valid, rule_errors = self.validate_business_rules(
            spec_path, work_item_type
        )
        all_errors.extend(rule_errors)

        return len(all_errors) == 0, all_errors

    def validate_business_rules(
        self,
        spec_path: Path,
        work_item_type: str
    ) -> tuple[bool, List[str]]:
        """Validate custom business rules"""
        structure = self.parser.parse_spec_to_structure(spec_path)
        errors = []

        # Spike-specific rules
        if work_item_type == "spike":
            time_box = structure.get("time_box", "")
            if not time_box:
                errors.append("Spike must have a time box defined")
            elif self.parse_time_box_hours(time_box) > 40:
                errors.append(f"Spike time box too long: {time_box} (max 40 hours)")

        # Security work item rules
        if work_item_type == "security":
            threat_model = structure.get("threat_model", "")
            if not threat_model or len(threat_model) < 50:
                errors.append("Security work item must have detailed threat model")

        return len(errors) == 0, errors
```

**Files Affected:**

**New:**
- `src/solokit/templates/schemas/feature_spec_schema.json` - Feature spec schema (will be created)
- `src/solokit/templates/schemas/bug_spec_schema.json` - Bug spec schema (will be created)
- `src/solokit/templates/schemas/refactor_spec_schema.json` - Refactor spec schema (will be created)
- `src/solokit/templates/schemas/security_spec_schema.json` - Security spec schema (will be created)
- `src/solokit/templates/schemas/integration_test_spec_schema.json` - Integration test schema (will be created)
- `src/solokit/templates/schemas/deployment_spec_schema.json` - Deployment spec schema (will be created)
- `tests/unit/test_spec_parser_schema.py` - Schema validation tests (will be created)
- `tests/fixtures/specs/` - Test spec fixtures (will be created)

**Modified:**
- `src/solokit/work_items/spec_parser.py` - Enhanced with schema validation
- `src/solokit/work_items/spec_validator.py` - Use schema validation
- `src/solokit/work_items/creator.py` - Validate on work item creation
- `pyproject.toml` - Add jsonschema dependency

**Benefits:**

1. **Earlier error detection**: Catch spec issues during creation, not during session
2. **Better error messages**: Precise location and suggested fixes
3. **Type safety**: Ensure fields have correct types and formats
4. **Consistency**: All specs follow standard structure
5. **Extensibility**: Easy to add new validation rules
6. **Migration support**: Can evolve spec format over time
7. **Documentation**: Schema serves as spec documentation
8. **IDE support**: Schemas enable autocomplete in IDEs

**Priority:** Medium-High - Quality improvement, prevents errors

**Notes:**
- Backward compatible: Existing specs validated, warnings shown but not blocked
- Migration tool can convert old specs to new schema
- Schemas can evolve with version numbers
- Custom types (Enhancement #32) can define their own schemas

---

### Enhancement #24: Custom Work Item Types

**Status:** 🔵 IDENTIFIED

**Problem:**

Solokit currently supports only 6 fixed work item types (feature, bug, refactor, security, integration_test, deployment). This creates limitations:

1. **No project-specific types**: Different projects need different work item types (spike, research, documentation-task, data-migration, experiment, etc.)
2. **No extensibility**: Users cannot define custom types for their workflow
3. **Rigid structure**: Solo developers may want simpler or more specialized types
4. **Missing common types**: Common software development activities like "spike" (time-boxed investigation) or "research" have no dedicated type

**Example use cases:**

```
Solo developer working on data-intensive project:
- Needs: data-migration, data-validation, schema-evolution work item types
- Current: Must use "feature" or "refactor" which don't fit semantically

Solo developer doing R&D:
- Needs: spike, research, experiment, proof-of-concept types
- Current: No appropriate type, forced to use "feature"

Solo developer maintaining docs:
- Needs: documentation-task, tutorial, guide types
- Current: No dedicated documentation type
```

**Proposed Solution:**

Implement **custom work item type system** allowing users to define their own work item types with:

1. **User-Defined Type Schema**
   - Define custom type name and metadata
   - Specify required and optional spec sections
   - Set default priority and milestone behavior
   - Configure type-specific quality gates

2. **Custom Spec Templates**
   - Create custom spec templates for each type
   - Define type-specific validation rules
   - Include type-specific guidance and examples
   - Template variables for dynamic content

3. **Type-Specific Quality Gates**
   - Different quality gate requirements per type
   - Example: "spike" type may not require tests
   - Example: "documentation-task" may only require linting and grammar checks
   - Configurable gate strictness per type

4. **Type Lifecycle Configuration**
   - Define valid status transitions per type
   - Set default session behavior (single-session vs multi-session)
   - Configure completion criteria
   - Set up type-specific git branch naming patterns

**Implementation:**

**Custom type definition:**
```yaml
# .session/config.json - custom_work_item_types section
{
  "custom_work_item_types": {
    "spike": {
      "display_name": "Spike",
      "description": "Time-boxed investigation or research task",
      "template_file": "spike_spec.md",
      "required_sections": [
        "Goal",
        "Time Box",
        "Questions to Answer",
        "Findings",
        "Recommendations"
      ],
      "optional_sections": [
        "References",
        "Experiments Conducted"
      ],
      "quality_gates": {
        "tests": {"enabled": false, "required": false},
        "linting": {"enabled": false, "required": false},
        "documentation": {"enabled": true, "required": true}
      },
      "default_priority": "medium",
      "typical_duration_days": 2,
      "multi_session_allowed": false,
      "branch_prefix": "spike"
    },
    "data_migration": {
      "display_name": "Data Migration",
      "description": "Database schema or data migration task",
      "template_file": "data_migration_spec.md",
      "required_sections": [
        "Migration Goal",
        "Current Schema",
        "Target Schema",
        "Data Transformation",
        "Rollback Plan",
        "Testing Strategy"
      ],
      "quality_gates": {
        "tests": {"enabled": true, "required": true, "coverage_threshold": 95},
        "integration_tests": {"enabled": true, "required": true},
        "rollback_test": {"enabled": true, "required": true},
        "backup_verification": {"enabled": true, "required": true}
      },
      "default_priority": "high",
      "multi_session_allowed": true,
      "branch_prefix": "migration"
    },
    "documentation_task": {
      "display_name": "Documentation Task",
      "description": "Documentation writing or updating",
      "template_file": "documentation_task_spec.md",
      "required_sections": [
        "Documentation Goal",
        "Target Audience",
        "Content Outline",
        "Examples Required"
      ],
      "quality_gates": {
        "tests": {"enabled": false, "required": false},
        "linting": {"enabled": true, "required": true},
        "grammar_check": {"enabled": true, "required": true},
        "link_validation": {"enabled": true, "required": true},
        "documentation": {"enabled": false, "required": false}
      },
      "default_priority": "low",
      "multi_session_allowed": false,
      "branch_prefix": "docs"
    },
    "experiment": {
      "display_name": "Experiment",
      "description": "Experimental feature or proof of concept",
      "template_file": "experiment_spec.md",
      "required_sections": [
        "Hypothesis",
        "Success Criteria",
        "Experiment Design",
        "Results",
        "Conclusion"
      ],
      "quality_gates": {
        "tests": {"enabled": false, "required": false},
        "documentation": {"enabled": true, "required": true}
      },
      "default_priority": "low",
      "typical_duration_days": 3,
      "multi_session_allowed": false,
      "branch_prefix": "experiment"
    }
  }
}
```

**Custom spec template example:**
```markdown
# src/solokit/templates/spike_spec.md
---
type: spike
---

# [Spike Title]

**Type:** Spike
**Time Box:** [e.g., 2 days, 8 hours]
**Created:** [Auto-generated]

## Goal

What question are you trying to answer? What are you investigating?

## Questions to Answer

1. [Question 1]
2. [Question 2]
3. [Question 3]

## Approach

How will you conduct this investigation?

- [ ] Research approach 1
- [ ] Experiment 2
- [ ] Prototype 3

## Findings

*(To be filled during/after spike)*

### What We Learned

- Finding 1
- Finding 2

### What We Don't Know Yet

- Unknown 1
- Unknown 2

## Recommendations

Based on findings, what should we do next?

- [ ] Recommendation 1: [Create feature work item / Continue research / Abandon approach]
- [ ] Recommendation 2

## References

- [External resources, articles, documentation]

## Time Tracking

- Time spent: [e.g., 6 hours out of 8 hour time box]
- Time box respected: [Yes/No]
```

**Type manager:**
```python
# src/solokit/work_items/type_manager.py
class WorkItemTypeManager:
    def __init__(self, config_path=".session/config.json"):
        self.config = self.load_config(config_path)
        self.built_in_types = self.load_built_in_types()
        self.custom_types = self.load_custom_types()

    def get_all_types(self):
        """Return all available work item types (built-in + custom)"""
        return {**self.built_in_types, **self.custom_types}

    def get_type_config(self, type_name):
        """Get configuration for a specific work item type"""
        all_types = self.get_all_types()
        if type_name not in all_types:
            raise ValueError(f"Unknown work item type: {type_name}")
        return all_types[type_name]

    def validate_type_definition(self, type_config):
        """Validate custom type configuration"""
        required_fields = ["display_name", "description", "template_file",
                          "required_sections", "quality_gates"]
        for field in required_fields:
            if field not in type_config:
                raise ValueError(f"Custom type missing required field: {field}")

        # Validate template file exists
        template_path = Path("src/solokit/templates") / type_config["template_file"]
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        return True

    def create_custom_type(self, type_name, type_config):
        """Create a new custom work item type"""
        self.validate_type_definition(type_config)

        # Add to config
        if "custom_work_item_types" not in self.config:
            self.config["custom_work_item_types"] = {}

        self.config["custom_work_item_types"][type_name] = type_config
        self.save_config()

        return type_name

    def get_quality_gates_for_type(self, type_name):
        """Get quality gate configuration for work item type"""
        type_config = self.get_type_config(type_name)
        return type_config.get("quality_gates", {})

    def get_required_sections_for_type(self, type_name):
        """Get required spec sections for work item type"""
        type_config = self.get_type_config(type_name)
        return type_config.get("required_sections", [])
```

**Enhanced work item creation:**
```python
# src/solokit/work_items/creator.py (modified)
def create_work_item(self, work_item_id, work_item_type, **kwargs):
    """Create work item with support for custom types"""
    type_manager = WorkItemTypeManager()

    # Validate type exists (built-in or custom)
    if work_item_type not in type_manager.get_all_types():
        available_types = ", ".join(type_manager.get_all_types().keys())
        raise ValueError(f"Unknown type '{work_item_type}'. Available: {available_types}")

    # Get type configuration
    type_config = type_manager.get_type_config(work_item_type)

    # Create work item with type-specific defaults
    work_item = {
        "id": work_item_id,
        "type": work_item_type,
        "priority": kwargs.get("priority", type_config.get("default_priority", "medium")),
        "status": "not_started",
        # ... rest of work item creation
    }

    # Generate spec from type-specific template
    spec_content = self.generate_spec_from_template(
        template=type_config["template_file"],
        work_item=work_item
    )

    # Save spec file
    spec_path = Path(f".session/specs/{work_item_id}.md")
    spec_path.write_text(spec_content)

    return work_item
```

**Quality gates integration:**
```python
# src/solokit/quality/gates.py (modified)
def get_gates_for_work_item(self, work_item):
    """Get quality gates based on work item type"""
    type_manager = WorkItemTypeManager()
    type_config = type_manager.get_type_config(work_item["type"])

    # Get type-specific quality gate configuration
    type_gates = type_config.get("quality_gates", {})

    # Merge with default gates, type-specific takes precedence
    gates = self.default_gates.copy()
    gates.update(type_gates)

    return gates
```

**Commands:**
```bash
# List all available work item types (built-in + custom)
/sk:work-types

# Create custom work item type interactively
/sk:work-type-create

# Create custom work item type from file
/sk:work-type-create --from-file .solokit/custom_types/spike.yml

# Validate custom type definition
/sk:work-type-validate --type spike

# Show details of a work item type
/sk:work-type-show spike
```

**Files Affected:**

**New:**
- `src/solokit/work_items/type_manager.py` - Custom type management (will be created)
- `src/solokit/templates/spike_spec.md` - Spike spec template (will be created)
- `src/solokit/templates/data_migration_spec.md` - Data migration template (will be created)
- `src/solokit/templates/documentation_task_spec.md` - Documentation task template (will be created)
- `src/solokit/templates/experiment_spec.md` - Experiment template (will be created)
- `.claude/commands/work-types.md` - List types command (will be created)
- `.claude/commands/work-type-create.md` - Create custom type command (will be created)
- `.claude/commands/work-type-show.md` - Show type details command (will be created)
- `tests/unit/test_type_manager.py` - Type manager tests (will be created)
- `tests/e2e/test_custom_work_item_types.py` - Custom type E2E tests (will be created)

**Modified:**
- `src/solokit/work_items/creator.py` - Support custom types in creation
- `src/solokit/work_items/spec_validator.py` - Validate against type-specific requirements
- `src/solokit/quality/gates.py` - Type-specific quality gates
- `.session/config.json` - Add custom_work_item_types section
- `.claude/commands/work-new.md` - Document custom type support

**Benefits:**

1. **Project flexibility**: Adapt Solokit to any project's workflow and terminology
2. **Better semantics**: Use work item types that match the actual work being done
3. **Workflow optimization**: Different quality gates for different work types
4. **Common patterns**: Support common types like spike, research, experiment
5. **Solo developer friendly**: Simpler types for simple projects, complex for complex
6. **Extensibility**: Framework grows with user needs
7. **Type safety**: Validation ensures custom types are well-formed
8. **Documentation**: Custom templates guide users through unfamiliar work types

**Priority:** High - Extensibility is foundational for framework adoption

**Notes:**
- Custom types stored in `.session/config.json` for project-specific customization
- Built-in types cannot be modified (ensures backward compatibility)
- Template variables allow dynamic content generation
- Type-specific quality gates prevent inappropriate requirements (e.g., no tests for documentation)
- Community could share custom type definitions

---

### Enhancement #25: MCP Server Integration

**Status:** 🔵 IDENTIFIED

**Problem:**

Current Solokit-Claude Code integration is via slash commands that execute CLI commands and return text output. This creates limitations:

1. **Text-only output**: All Solokit data must be formatted as text for stdout/stderr
2. **No programmatic access**: Claude cannot query Solokit state directly
3. **Parsing overhead**: Claude must parse text output to understand Solokit data
4. **Limited interactivity**: Cannot have rich, interactive conversations about Solokit state
5. **No structured data**: JSON/structured data must be formatted as text then parsed
6. **Foundation missing**: Cannot build advanced features like inline annotations without programmatic access

**Example of current limitation:**

```
User: "What learnings are relevant to authentication?"

Current flow:
1. User must use /learn-search authentication
2. CLI returns text output
3. Claude reads and interprets text
4. Claude formats response to user

Desired flow with MCP:
1. Claude directly queries: solokit://learnings/search?query=authentication&limit=10
2. Receives structured JSON response
3. Claude analyzes and presents insights
4. Can follow up with related queries programmatically
```

**Proposed Solution:**

Implement **MCP (Model Context Protocol) server for Solokit** that exposes Solokit operations as structured tools:

1. **MCP Server Implementation**
   - Standalone MCP server process
   - Exposes Solokit operations as MCP tools
   - Returns structured data (JSON) instead of text
   - Handles concurrent requests
   - Maintains session state

2. **MCP Tools for Solokit Operations**
   - Work item operations (list, get, create, update, delete)
   - Learning operations (search, get, create, curate)
   - Session operations (status, start, end, validate)
   - Quality gate operations (run, get results)
   - Visualization operations (dependency graph)
   - Project operations (status, metrics)

3. **Rich Data Structures**
   - Typed responses (not string parsing)
   - Nested objects for complex data
   - Metadata and context in responses
   - Error handling with structured error objects

4. **Real-Time State Access**
   - Query Solokit state anytime
   - No need to run CLI commands
   - Efficient data access
   - Caching for performance

**Implementation:**

**MCP Server:**
```python
# src/solokit/mcp/server.py
import asyncio
from typing import Any, Dict, List
from mcp import Server, Tool

class SDDMCPServer:
    def __init__(self):
        self.server = Server("solokit")
        self.register_tools()

    def register_tools(self):
        """Register all Solokit tools with MCP server"""

        # Work item tools
        self.server.add_tool(Tool(
            name="sdd_work_items_list",
            description="List all work items with optional filters",
            parameters={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["not_started", "in_progress", "blocked", "completed"]},
                    "type": {"type": "string"},
                    "milestone": {"type": "string"}
                }
            },
            handler=self.list_work_items
        ))

        self.server.add_tool(Tool(
            name="sdd_work_item_get",
            description="Get detailed information about a specific work item",
            parameters={
                "type": "object",
                "properties": {
                    "work_item_id": {"type": "string", "required": True}
                },
                "required": ["work_item_id"]
            },
            handler=self.get_work_item
        ))

        # Learning tools
        self.server.add_tool(Tool(
            name="sdd_learnings_search",
            description="Search learnings by keyword or semantic query",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 10},
                    "category": {"type": "string"},
                    "semantic": {"type": "boolean", "default": False}
                },
                "required": ["query"]
            },
            handler=self.search_learnings
        ))

        self.server.add_tool(Tool(
            name="sdd_learnings_relevant",
            description="Get learnings relevant to a work item or topic",
            parameters={
                "type": "object",
                "properties": {
                    "work_item_id": {"type": "string"},
                    "topic": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                }
            },
            handler=self.get_relevant_learnings
        ))

        # Session tools
        self.server.add_tool(Tool(
            name="sdd_session_status",
            description="Get current session status and progress",
            parameters={"type": "object", "properties": {}},
            handler=self.get_session_status
        ))

        self.server.add_tool(Tool(
            name="sdd_quality_gates_results",
            description="Get quality gate results for current or past sessions",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "work_item_id": {"type": "string"}
                }
            },
            handler=self.get_quality_gate_results
        ))

        # Visualization tools
        self.server.add_tool(Tool(
            name="sdd_dependency_graph",
            description="Get work item dependency graph data",
            parameters={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "enum": ["json", "ascii", "dot"], "default": "json"},
                    "focus": {"type": "string"},
                    "include_completed": {"type": "boolean", "default": False}
                }
            },
            handler=self.get_dependency_graph
        ))

        # Project metrics tools
        self.server.add_tool(Tool(
            name="sdd_project_metrics",
            description="Get project-level metrics and statistics",
            parameters={
                "type": "object",
                "properties": {
                    "metric_type": {"type": "string", "enum": ["velocity", "quality", "learnings", "all"], "default": "all"}
                }
            },
            handler=self.get_project_metrics
        ))

    async def list_work_items(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List work items with filters"""
        from solokit.work_items.repository import WorkItemRepository

        repository = WorkItemRepository()
        work_items = repository.list_work_items(
            status=params.get("status"),
            work_type=params.get("type"),
            milestone=params.get("milestone")
        )

        return {
            "work_items": work_items,
            "total": len(work_items),
            "filters_applied": {k: v for k, v in params.items() if v is not None}
        }

    async def get_work_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed work item information"""
        from solokit.work_items.repository import WorkItemRepository

        repository = WorkItemRepository()
        work_item_id = params["work_item_id"]

        # Get work item metadata
        work_item = repository.get_work_item(work_item_id)

        # Get spec content
        spec_path = Path(f".session/specs/{work_item_id}.md")
        spec_content = spec_path.read_text() if spec_path.exists() else None

        # Get session history
        sessions = repository.get_work_item_sessions(work_item_id)

        return {
            "work_item": work_item,
            "spec_content": spec_content,
            "sessions": sessions,
            "dependency_info": repository.get_dependency_info(work_item_id)
        }

    async def search_learnings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search learnings"""
        from solokit.learning.repository import LearningRepository

        repository = LearningRepository()
        query = params["query"]
        limit = params.get("limit", 10)
        category = params.get("category")
        semantic = params.get("semantic", False)

        if semantic:
            # Use AI-powered semantic search (Enhancement #37)
            results = repository.semantic_search(query, limit=limit, category=category)
        else:
            # Use keyword search
            results = repository.search(query, limit=limit, category=category)

        return {
            "learnings": results,
            "total": len(results),
            "query": query,
            "search_type": "semantic" if semantic else "keyword"
        }

    async def get_relevant_learnings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get learnings relevant to work item or topic"""
        from solokit.session.briefing.learning_loader import get_relevant_learnings

        work_item_id = params.get("work_item_id")
        topic = params.get("topic")
        limit = params.get("limit", 10)

        if work_item_id:
            # Get learnings for work item
            learnings = get_relevant_learnings(work_item_id, limit=limit)
            context = f"work item: {work_item_id}"
        elif topic:
            # Get learnings for topic
            learnings = get_relevant_learnings(topic, limit=limit)
            context = f"topic: {topic}"
        else:
            return {"error": "Must provide work_item_id or topic"}

        return {
            "learnings": learnings,
            "total": len(learnings),
            "context": context
        }

    async def get_session_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current session status"""
        from solokit.session.status import get_session_status

        status = get_session_status()

        return status

    async def get_quality_gate_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get quality gate results"""
        from solokit.quality.gates import QualityGateRunner

        runner = QualityGateRunner()
        session_id = params.get("session_id")
        work_item_id = params.get("work_item_id")

        results = runner.get_results(session_id=session_id, work_item_id=work_item_id)

        return {
            "quality_gate_results": results,
            "session_id": session_id,
            "work_item_id": work_item_id
        }

    async def get_dependency_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get dependency graph"""
        from solokit.visualization.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        format_type = params.get("format", "json")
        focus = params.get("focus")
        include_completed = params.get("include_completed", False)

        graph_data = graph.generate(
            format=format_type,
            focus=focus,
            include_completed=include_completed
        )

        return {
            "graph": graph_data,
            "format": format_type,
            "metadata": graph.get_metadata()
        }

    async def get_project_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project metrics"""
        from solokit.improvement.dora_metrics import DORAMetrics
        from solokit.improvement.velocity_tracker import VelocityTracker

        metric_type = params.get("metric_type", "all")

        metrics = {}

        if metric_type in ["velocity", "all"]:
            velocity = VelocityTracker()
            metrics["velocity"] = velocity.get_metrics()

        if metric_type in ["quality", "all"]:
            dora = DORAMetrics()
            metrics["dora"] = dora.get_metrics()

        if metric_type in ["learnings", "all"]:
            from solokit.learning.curator import LearningCurator
            curator = LearningCurator()
            metrics["learnings"] = curator.get_statistics()

        return {
            "metrics": metrics,
            "metric_type": metric_type
        }

    async def start(self):
        """Start MCP server"""
        await self.server.start()

# Entry point
async def main():
    server = SDDMCPServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**Claude Code MCP Configuration:**
```json
// ~/.claude/config.json or project-specific config
{
  "mcpServers": {
    "solokit": {
      "command": "solokit",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

**CLI command to start MCP server:**
```bash
# Start MCP server
solokit mcp serve

# Or via Claude Code (auto-started)
```

**Example usage in Claude Code:**
```
User: "What learnings do we have about authentication?"

Claude (internal):
→ Calls sdd_learnings_search(query="authentication", limit=10, semantic=True)
→ Receives structured JSON with learnings
→ Analyzes and presents to user

Claude (to user): "We have 7 learnings about authentication:

1. Always use bcrypt for password hashing (Security - Session 5)
2. Implement JWT token refresh mechanism (Best Practices - Session 8)
..."
```

**Files Affected:**

**New:**
- `src/solokit/mcp/server.py` (will be created) - MCP server implementation
- `src/solokit/mcp/tools.py` (will be created) - MCP tool definitions
- `src/solokit/mcp/__init__.py` (will be created) - MCP module initialization
- `docs/mcp/README.md` (will be created) - MCP integration documentation
- `docs/mcp/tools.md` (will be created) - MCP tools reference
- `tests/unit/test_mcp_server.py` (will be created) - MCP server tests
- `tests/integration/test_mcp_integration.py` (will be created) - Integration tests

**Modified:**
- `src/solokit/cli.py` - Add MCP server command
- `README.md` - Document MCP integration
- `.claude/config.json` - MCP server configuration example

**Benefits:**

1. **Programmatic access**: Claude can query Solokit state directly
2. **Structured data**: No text parsing, clean JSON responses
3. **Rich interactions**: Contextual follow-up queries
4. **Foundation for features**: Enables inline annotations, real-time updates
5. **Better UX**: Faster, more accurate responses
6. **Extensibility**: Easy to add new MCP tools
7. **Standard protocol**: MCP is Claude Code's official integration method
8. **Stateful**: Server maintains context across queries

**Priority:** High - Foundation for better Claude Code integration (required for Enhancement #35)

**Notes:**
- Requires Claude Code with MCP support
- MCP server runs as separate process
- Server lifecycle managed by Claude Code
- Backward compatible (slash commands still work)
- Performance: MCP calls faster than CLI commands

---

### Enhancement #26: Context-Aware MCP Server Management

**Status:** 🔵 IDENTIFIED

**Problem:**

MCP (Model Context Protocol) servers provide valuable capabilities like accessing documentation (context7), visual testing (playwright), database querying, and more. However, they have significant limitations:

1. **Token Consumption**:
   - MCP servers consume context tokens even when idle
   - Not all servers are relevant to every work item
   - Context window fills up with unused server definitions
   - Reduces space available for code and briefing content

2. **Manual Management**:
   - Developers must manually configure MCP servers per project
   - Must remember which servers are useful for which tasks
   - No systematic way to enable/disable servers per session
   - Server selection is reactive, not proactive

3. **No Context Awareness**:
   - Same servers enabled for frontend and backend work
   - Playwright enabled during database optimization work (irrelevant)
   - Documentation servers for wrong tech stack
   - No intelligent server selection based on work context

4. **Setup Friction**:
   - Setting up MCP servers requires manual configuration
   - No project templates include MCP server setup
   - Developers may not know which servers are useful
   - Configuration is project-specific but not automated

**Proposed Solution:**

Implement **context-aware MCP server management** that automatically enables relevant servers based on work item context:

1. **Project-Level Server Registry**
   - Define available MCP servers during `sk init`
   - Servers registered but not enabled by default (zero token cost)
   - Server metadata: name, purpose, tech stack, use cases
   - Template-based server recommendations

2. **Context-Aware Enablement**
   - `sk start` analyzes work item and enables relevant servers
   - Smart matching based on work item type, tags, tech stack, dependencies
   - Token budgeting: enable servers within context budget
   - Priority-based selection when budget is limited

3. **Intelligent Server Selection**
   - Frontend work → Enable playwright, context7 (frontend frameworks)
   - Backend work → Enable database tools, API testing tools
   - Security work → Enable security scanning tools
   - Documentation work → Enable context7 for all relevant frameworks

4. **Manual Override**
   - Explicit enable/disable via flags
   - Session-specific server configuration
   - Persistent preferences for specific work item types

**Implementation:**

**MCP server registry schema:**
```json
// .session/mcp_servers.json
{
  "servers": [
    {
      "id": "context7",
      "name": "Context7",
      "description": "Access up-to-date documentation for any framework or library",
      "command": "npx",
      "args": ["-y", "@context7/mcp"],
      "enabled_by_default": false,
      "relevance_rules": {
        "work_item_types": ["feature", "bug", "refactor"],
        "tech_stack": ["*"],  // All tech stacks
        "tags": ["documentation", "learning", "new-technology"],
        "priority": "high"
      },
      "token_cost_estimate": 500,
      "env": {}
    },
    {
      "id": "playwright",
      "name": "Playwright MCP",
      "description": "Visual testing and screenshot capture for frontend work",
      "command": "npx",
      "args": ["-y", "@playwright/mcp-server"],
      "enabled_by_default": false,
      "relevance_rules": {
        "work_item_types": ["feature", "bug"],
        "tech_stack": ["react", "vue", "svelte", "angular", "next.js", "nuxt"],
        "tags": ["frontend", "ui", "visual", "responsive"],
        "keywords": ["layout", "design", "visual", "ui", "component", "page"],
        "priority": "high"
      },
      "token_cost_estimate": 800,
      "env": {}
    },
    {
      "id": "postgres",
      "name": "PostgreSQL MCP",
      "description": "Query and inspect PostgreSQL databases",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "enabled_by_default": false,
      "relevance_rules": {
        "work_item_types": ["feature", "bug", "refactor", "performance"],
        "tech_stack": ["postgresql", "postgres"],
        "tags": ["database", "backend", "data", "migration"],
        "keywords": ["query", "database", "sql", "migration", "schema"],
        "priority": "medium"
      },
      "token_cost_estimate": 600,
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/db"
      }
    },
    {
      "id": "filesystem",
      "name": "Filesystem MCP",
      "description": "Read and manipulate files across the project",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "enabled_by_default": false,
      "relevance_rules": {
        "work_item_types": ["feature", "bug", "refactor"],
        "tech_stack": ["*"],
        "tags": ["refactoring", "large-changes"],
        "priority": "low"
      },
      "token_cost_estimate": 400,
      "env": {}
    }
  ],
  "global_config": {
    "max_token_budget": 2000,
    "auto_enable": true,
    "prefer_higher_priority": true
  }
}
```

**Server selection algorithm:**
```python
# src/solokit/mcp/server_manager.py
from typing import List, Dict, Any
from pathlib import Path
import json

class MCPServerManager:
    """Manage MCP server lifecycle and context-aware enablement"""

    def __init__(self, session_dir: Path = Path(".session")):
        self.session_dir = session_dir
        self.registry_path = session_dir / "mcp_servers.json"

    def load_registry(self) -> Dict[str, Any]:
        """Load MCP server registry"""
        if not self.registry_path.exists():
            return {"servers": [], "global_config": {}}
        return json.loads(self.registry_path.read_text())

    def save_registry(self, registry: Dict[str, Any]):
        """Save MCP server registry"""
        self.registry_path.write_text(json.dumps(registry, indent=2))

    def select_servers_for_work_item(
        self,
        work_item: Dict[str, Any],
        work_item_spec: str,
        tech_stack: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Select relevant MCP servers based on work item context.

        Returns list of servers to enable, sorted by priority.
        """
        registry = self.load_registry()
        servers = registry.get("servers", [])
        global_config = registry.get("global_config", {})

        if not global_config.get("auto_enable", True):
            return []

        # Score each server based on relevance
        scored_servers = []
        for server in servers:
            score = self._score_server_relevance(
                server,
                work_item,
                work_item_spec,
                tech_stack
            )
            if score > 0:
                scored_servers.append((server, score))

        # Sort by score (higher = more relevant)
        scored_servers.sort(key=lambda x: x[1], reverse=True)

        # Apply token budget
        max_budget = global_config.get("max_token_budget", 2000)
        selected_servers = []
        total_tokens = 0

        for server, score in scored_servers:
            token_cost = server.get("token_cost_estimate", 500)
            if total_tokens + token_cost <= max_budget:
                selected_servers.append({
                    **server,
                    "relevance_score": score
                })
                total_tokens += token_cost
            elif global_config.get("prefer_higher_priority", True):
                # Skip if over budget
                continue

        return selected_servers

    def _score_server_relevance(
        self,
        server: Dict[str, Any],
        work_item: Dict[str, Any],
        work_item_spec: str,
        tech_stack: List[str]
    ) -> float:
        """
        Score server relevance (0.0-1.0) based on multiple factors.
        """
        rules = server.get("relevance_rules", {})
        score = 0.0

        # Work item type match
        if work_item["type"] in rules.get("work_item_types", []):
            score += 0.3

        # Tech stack match
        server_stack = rules.get("tech_stack", [])
        if "*" in server_stack or any(t in tech_stack for t in server_stack):
            score += 0.3

        # Tags match
        work_item_tags = work_item.get("tags", [])
        server_tags = rules.get("tags", [])
        tag_overlap = len(set(work_item_tags) & set(server_tags))
        if tag_overlap > 0:
            score += 0.2 * min(tag_overlap / len(server_tags), 1.0)

        # Keyword match in title or spec
        keywords = rules.get("keywords", [])
        text = f"{work_item['title']} {work_item_spec}".lower()
        keyword_matches = sum(1 for kw in keywords if kw.lower() in text)
        if keyword_matches > 0:
            score += 0.2 * min(keyword_matches / len(keywords), 1.0)

        # Priority boost
        priority_boost = {
            "critical": 0.3,
            "high": 0.2,
            "medium": 0.1,
            "low": 0.0
        }
        score += priority_boost.get(rules.get("priority", "low"), 0.0)

        return min(score, 1.0)

    def enable_servers(self, server_ids: List[str]) -> Dict[str, Any]:
        """
        Generate MCP configuration for enabled servers.

        Returns Claude Code MCP config dict.
        """
        registry = self.load_registry()
        servers = registry.get("servers", [])

        mcp_config = {"mcpServers": {}}
        for server in servers:
            if server["id"] in server_ids:
                mcp_config["mcpServers"][server["id"]] = {
                    "command": server["command"],
                    "args": server["args"],
                    "env": server.get("env", {})
                }

        return mcp_config

    def initialize_default_servers(self, tech_stack: List[str]):
        """Initialize server registry with recommended servers for tech stack"""
        default_servers = self._get_default_servers_for_stack(tech_stack)
        registry = {
            "servers": default_servers,
            "global_config": {
                "max_token_budget": 2000,
                "auto_enable": True,
                "prefer_higher_priority": True
            }
        }
        self.save_registry(registry)

    def _get_default_servers_for_stack(self, tech_stack: List[str]) -> List[Dict]:
        """Get recommended MCP servers based on tech stack"""
        # Always include context7 (universal documentation)
        servers = [
            {
                "id": "context7",
                "name": "Context7",
                "description": "Access up-to-date documentation",
                "command": "npx",
                "args": ["-y", "@context7/mcp"],
                "enabled_by_default": False,
                "relevance_rules": {
                    "work_item_types": ["feature", "bug", "refactor"],
                    "tech_stack": ["*"],
                    "tags": ["documentation", "learning"],
                    "priority": "high"
                },
                "token_cost_estimate": 500,
                "env": {}
            }
        ]

        # Add playwright for frontend stacks
        frontend_stacks = ["react", "vue", "svelte", "angular", "next.js", "nuxt"]
        if any(stack in tech_stack for stack in frontend_stacks):
            servers.append({
                "id": "playwright",
                "name": "Playwright MCP",
                "description": "Visual testing and screenshots",
                "command": "npx",
                "args": ["-y", "@playwright/mcp-server"],
                "enabled_by_default": False,
                "relevance_rules": {
                    "work_item_types": ["feature", "bug"],
                    "tech_stack": frontend_stacks,
                    "tags": ["frontend", "ui", "visual"],
                    "keywords": ["layout", "design", "ui", "component"],
                    "priority": "high"
                },
                "token_cost_estimate": 800,
                "env": {}
            })

        # Add database servers
        if "postgresql" in tech_stack or "postgres" in tech_stack:
            servers.append({
                "id": "postgres",
                "name": "PostgreSQL MCP",
                "description": "Query PostgreSQL databases",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "enabled_by_default": False,
                "relevance_rules": {
                    "work_item_types": ["feature", "bug", "refactor"],
                    "tech_stack": ["postgresql", "postgres"],
                    "tags": ["database", "backend"],
                    "keywords": ["query", "database", "sql"],
                    "priority": "medium"
                },
                "token_cost_estimate": 600,
                "env": {}
            })

        return servers
```

**Integration with session start:**
```python
# src/solokit/session/briefing/orchestrator.py (enhanced)
def start_session(work_item_id: str, enable_servers: List[str] = None, disable_servers: List[str] = None):
    """Start development session with context-aware MCP server enablement"""
    from solokit.work_items.repository import WorkItemRepository
    from solokit.mcp.server_manager import MCPServerManager
    from solokit.project.stack import detect_tech_stack

    # Get work item
    repository = WorkItemRepository()
    work_item = repository.get_work_item(work_item_id)

    # Get spec
    spec_path = Path(f".session/specs/{work_item_id}.md")
    spec_content = spec_path.read_text() if spec_path.exists() else ""

    # Detect tech stack
    tech_stack = detect_tech_stack()

    # Select relevant MCP servers
    mcp_manager = MCPServerManager()

    if enable_servers:
        # Manual override
        selected_servers = [s for s in mcp_manager.load_registry()["servers"] if s["id"] in enable_servers]
    else:
        # Automatic selection
        selected_servers = mcp_manager.select_servers_for_work_item(
            work_item,
            spec_content,
            tech_stack
        )

    # Apply disable list
    if disable_servers:
        selected_servers = [s for s in selected_servers if s["id"] not in disable_servers]

    # Generate briefing with MCP server info
    briefing = generate_briefing(work_item_id)

    # Add MCP server section
    if selected_servers:
        briefing += "\n\n## Enabled MCP Servers\n\n"
        briefing += "The following MCP servers are enabled for this session:\n\n"
        for server in selected_servers:
            briefing += f"- **{server['name']}**: {server['description']}\n"
            briefing += f"  - Relevance: {server.get('relevance_score', 0.0):.2f}\n"
        briefing += "\nThese servers were automatically selected based on the work item context.\n"

    # Generate MCP config (for potential future auto-configuration)
    mcp_config = mcp_manager.enable_servers([s["id"] for s in selected_servers])

    # Save session state
    save_session_state({
        "work_item_id": work_item_id,
        "enabled_mcp_servers": [s["id"] for s in selected_servers],
        "mcp_config": mcp_config
    })

    return briefing
```

**Integration with sk init:**
```python
# src/solokit/project/init.py (enhanced)
def initialize_project(template: str = None):
    """Initialize Solokit project with MCP server recommendations"""
    from solokit.mcp.server_manager import MCPServerManager
    from solokit.project.stack import detect_tech_stack

    # Create .session directory
    session_dir = Path(".session")
    session_dir.mkdir(exist_ok=True)

    # Detect tech stack
    tech_stack = detect_tech_stack()

    # Initialize MCP server registry with recommendations
    mcp_manager = MCPServerManager(session_dir)
    mcp_manager.initialize_default_servers(tech_stack)

    print("\n✓ MCP Server Registry initialized")
    print(f"  Recommended servers for {', '.join(tech_stack)}:")

    registry = mcp_manager.load_registry()
    for server in registry["servers"]:
        print(f"  - {server['name']}: {server['description']}")

    print("\n  Servers are disabled by default to save context tokens.")
    print("  They will be automatically enabled during 'sk start' based on work item context.")

    # ... rest of initialization
```

**Commands:**
```bash
# Start session with automatic server selection
/sk:start WI-001

# Start with manual server override
/sk:start WI-001 --enable-servers context7,playwright

# Start with specific servers disabled
/sk:start WI-001 --disable-servers postgres

# List available MCP servers
/sk:mcp-list

# Add custom MCP server
/sk:mcp-add --id custom-server --command npx --args "-y,my-mcp-server" --priority high

# Test server relevance for work item
/sk:mcp-test WI-001

# Show currently enabled servers
/sk:status  # (includes MCP server section)
```

**Configuration:**
```json
// .session/config.json (enhanced)
{
  "mcp_server_management": {
    "enabled": true,
    "auto_enable": true,
    "max_token_budget": 2000,
    "prefer_higher_priority": true,
    "manual_overrides": {
      "WI-001": {
        "enabled_servers": ["context7", "playwright"],
        "disabled_servers": []
      }
    }
  }
}
```

**Files Affected:**

**New:**
- `src/solokit/mcp/` (will be created) - New module
- `src/solokit/mcp/__init__.py` (will be created) - Module init
- `src/solokit/mcp/server_manager.py` (will be created) - MCP server management
- `.session/mcp_servers.json` (will be created) - Server registry (created per project)
- `tests/unit/test_mcp_server_manager.py` (will be created) - Unit tests
- `tests/integration/test_mcp_integration.py` (will be created) - Integration tests
- `.claude/commands/mcp-list.md` (will be created) - List servers command
- `.claude/commands/mcp-add.md` (will be created) - Add server command
- `.claude/commands/mcp-test.md` (will be created) - Test relevance command

**Modified:**
- `src/solokit/session/briefing/orchestrator.py` - Add MCP server selection
- `src/solokit/session/briefing/formatter.py` - Include MCP server info in briefing
- `src/solokit/project/init.py` - Initialize MCP server registry
- `src/solokit/templates/config.schema.json` - Add MCP config schema
- `.claude/commands/start.md` - Document server flags
- `.claude/commands/status.md` - Show enabled servers
- `README.md` - Document MCP server management

**Benefits:**

1. **Context Efficiency**: Only enable relevant servers, save thousands of context tokens
2. **Intelligent Selection**: Automatic server selection based on work context
3. **Zero Configuration**: Servers recommended and configured during init
4. **Manual Control**: Override automatic selection when needed
5. **Token Budgeting**: Respect context window limits with smart budgeting
6. **Discoverability**: Developers learn about useful MCP servers through recommendations
7. **Template Integration**: Project templates include optimal MCP server setups
8. **Session Awareness**: Briefings show which servers are available and why
9. **Extensibility**: Easy to add custom project-specific MCP servers
10. **Cost Control**: Reduce API costs from unused MCP server context

**Priority:** High

**Justification:**
- Directly improves context window efficiency (critical for large projects)
- Enhances developer experience with intelligent automation
- Enables better use of MCP ecosystem
- Foundation for advanced MCP integration features
- Aligns with Solokit's philosophy of intelligent automation

**Notes:**
- MCP servers are registered but disabled by default (zero cost)
- Server selection is context-aware but can be overridden
- Token cost estimates should be calibrated based on actual usage
- Server relevance scoring can be enhanced with AI (future: use Enhancement #37's AI capabilities)
- Works with Enhancement #13 (Template-Based Init) - templates include MCP server recommendations
- Complements Enhancement #14 (Session Briefing Optimization) - reduces context usage
- Related to Enhancement #33 (MCP Server Integration) - both use MCP but for different purposes (#33 makes Solokit an MCP server, #38 manages other MCP servers)

---

### Enhancement #27: Inline Editor Annotations (via MCP)

**Status:** 🔵 IDENTIFIED

**Problem:**

When working on a work item, developers have no real-time visibility of Solokit state in their editor:

1. **No work item status visibility**: Can't see if current file relates to an active work item
2. **No learning hints**: Relevant learnings not shown in context
3. **No quality gate indicators**: Must run `/validate` manually to see issues
4. **Context switching**: Must switch to terminal to check Solokit state
5. **Lost context**: May forget which work item is active

**Example scenario:**

```
Developer opens: src/auth/jwt.py

Current experience:
- No indication this relates to work_item_authentication
- No reminder of relevant learnings about JWT
- No warning about quality gate failures
- Must run /status or /validate to see any Solokit info

Desired experience:
Editor shows inline annotations:
┌───────────────────────────────────────────────┐
│ src/auth/jwt.py                               │
│                                               │
│ 📋 Work Item: feature_jwt_authentication      │
│    Status: In Progress (Session 15)           │
│    Priority: High                             │
│                                               │
│ 💡 Relevant Learnings (3):                    │
│    • Always validate JWT signature            │
│    • Use short token expiry (15min)           │
│    • Implement token refresh mechanism        │
│                                               │
│ ⚠️ Quality Gates:                             │
│    ✓ Tests passing (87% coverage)             │
│    ✗ Linting: 2 issues (click to fix)         │
│                                               │
│ def generate_token(user_id):                  │
│     """Generate JWT token"""                  │
│     # ... code ...                            │
└───────────────────────────────────────────────┘
```

**Proposed Solution:**

Implement **inline editor annotations** that display Solokit state contextually in the editor:

1. **Work Item Status Annotations**
   - Show active work item in files being edited
   - Display work item status, priority, progress
   - Link to full work item spec
   - Indicate if file is part of work item scope

2. **Learning Snippets on Hover**
   - Detect relevant learnings based on file/function
   - Show learning snippets on hover
   - Link to full learning details
   - "Learn more" expands learning context

3. **Quality Gate Indicators**
   - Show quality gate status inline
   - Highlight failing tests in test files
   - Show linting errors with quick fixes
   - Display coverage gaps

4. **Dependency Warnings**
   - Warn if editing file that's part of blocked work item
   - Show dependency chain
   - Suggest unblocking actions

5. **Session Context**
   - Show current session info
   - Display session time/progress
   - Link to session briefing
   - Quick access to `/end` or `/validate`

**Implementation:**

**Requires Enhancement #33 (MCP Server) as foundation**

**MCP-based annotation provider:**
```python
# src/solokit/mcp/annotations.py
from pathlib import Path
from typing import List, Dict, Any

class AnnotationProvider:
    """Provide annotations for editor via MCP"""

    def get_annotations_for_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all annotations for a file"""
        annotations = []

        # Work item annotations
        work_item_annotations = self.get_work_item_annotations(file_path)
        annotations.extend(work_item_annotations)

        # Learning annotations
        learning_annotations = self.get_learning_annotations(file_path)
        annotations.extend(learning_annotations)

        # Quality gate annotations
        quality_annotations = self.get_quality_gate_annotations(file_path)
        annotations.extend(quality_annotations)

        return annotations

    def get_work_item_annotations(self, file_path: str) -> List[Dict[str, Any]]:
        """Get work item status annotations"""
        from solokit.session.status import get_session_status
        from solokit.work_items.repository import WorkItemRepository

        # Check if there's an active session
        status = get_session_status()
        if not status.get("active_work_item"):
            return []

        work_item_id = status["active_work_item"]
        repository = WorkItemRepository()
        work_item = repository.get_work_item(work_item_id)

        # Check if file is in work item's git branch commits
        if not self.file_in_work_item_scope(file_path, work_item_id):
            return []

        return [{
            "type": "info",
            "position": {"line": 0, "character": 0},
            "message": f"📋 Work Item: {work_item['title']}",
            "details": {
                "work_item_id": work_item_id,
                "status": work_item["status"],
                "priority": work_item["priority"],
                "session": status.get("session_number")
            },
            "actions": [
                {"label": "View Spec", "command": f"solokit:work-show {work_item_id}"},
                {"label": "End Session", "command": "solokit:end"}
            ]
        }]

    def get_learning_annotations(self, file_path: str) -> List[Dict[str, Any]]:
        """Get relevant learning annotations"""
        from solokit.session.briefing.learning_loader import get_relevant_learnings

        # Analyze file to determine topic
        topic = self.extract_topic_from_file(file_path)
        if not topic:
            return []

        # Get relevant learnings
        learnings = get_relevant_learnings(topic, limit=3)
        if not learnings:
            return []

        # Create annotation
        learning_texts = [
            f"• {learning['content'][:80]}..."
            for learning in learnings[:3]
        ]

        return [{
            "type": "info",
            "position": {"line": 0, "character": 0},
            "message": f"💡 Relevant Learnings ({len(learnings)}):",
            "details": {
                "learnings": learnings,
                "topic": topic
            },
            "hover_content": "\n".join(learning_texts),
            "actions": [
                {"label": "View All", "command": f"solokit:learn-search {topic}"}
            ]
        }]

    def get_quality_gate_annotations(self, file_path: str) -> List[Dict[str, Any]]:
        """Get quality gate status annotations"""
        from solokit.quality.gates import QualityGateRunner

        runner = QualityGateRunner()

        # Get latest quality gate results
        results = runner.get_latest_results()
        if not results:
            return []

        annotations = []

        # Check if file has linting issues
        if "linting" in results and not results["linting"]["passed"]:
            linting_issues = self.get_linting_issues_for_file(file_path, results["linting"])
            for issue in linting_issues:
                annotations.append({
                    "type": "warning",
                    "position": {"line": issue["line"], "character": issue["column"]},
                    "message": f"⚠️ Lint: {issue['message']}",
                    "details": issue,
                    "actions": [
                        {"label": "Fix", "command": f"solokit:validate --fix"}
                    ] if issue.get("fixable") else []
                })

        # Check if file has test coverage gaps
        if "tests" in results:
            coverage_gaps = self.get_coverage_gaps_for_file(file_path, results["tests"])
            if coverage_gaps:
                annotations.append({
                    "type": "info",
                    "position": {"line": 0, "character": 0},
                    "message": f"📊 Coverage: {coverage_gaps['percentage']}% (target: {coverage_gaps['target']}%)",
                    "details": coverage_gaps,
                    "hover_content": f"Uncovered lines: {coverage_gaps['uncovered_lines']}"
                })

        return annotations

    def extract_topic_from_file(self, file_path: str) -> str:
        """Extract main topic/keywords from file"""
        path = Path(file_path)

        # Use file name and path components as topic
        parts = path.stem.split("_")
        parent_parts = path.parent.name.split("_")

        topic = " ".join(parts + parent_parts)
        return topic

    def file_in_work_item_scope(self, file_path: str, work_item_id: str) -> bool:
        """Check if file was modified in work item's branch"""
        # Implementation: check git log for work item's branch
        pass

# MCP tool for annotations
async def get_file_annotations(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool to get annotations for a file"""
    file_path = params["file_path"]

    provider = AnnotationProvider()
    annotations = provider.get_annotations_for_file(file_path)

    return {
        "file_path": file_path,
        "annotations": annotations,
        "count": len(annotations)
    }
```

**Claude Code MCP Tool Registration:**
```python
# Add to src/solokit/mcp/server.py
self.server.add_tool(Tool(
    name="sdd_file_annotations",
    description="Get Solokit annotations for a file (work item status, learnings, quality gates)",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "required": True}
        },
        "required": ["file_path"]
    },
    handler=get_file_annotations
))
```

**Files Affected:**

**New:**
- `src/solokit/mcp/annotations.py` (will be created) - Annotation provider
- `tests/unit/test_annotations.py` (will be created) - Annotation tests

**Modified:**
- `src/solokit/mcp/server.py` (will be created) - Add annotation MCP tool
- `docs/mcp/tools.md` (will be created) - Document annotation tool

**Benefits:**

1. **Context awareness**: See Solokit state without leaving editor
2. **Learning reminders**: Relevant learnings shown in context
3. **Proactive quality**: See issues as you code
4. **Reduced context switching**: Less terminal usage
5. **Better focus**: All info in one place
6. **Discoverability**: Learn about Solokit features through annotations
7. **Productivity**: Faster access to relevant information

**Priority:** Medium - Nice to have, enhances developer experience

**Dependencies:**
- **Requires Enhancement #33 (MCP Server)** - Foundation for annotations
- Requires Claude Code support for displaying annotations (may need API/protocol discussion with Anthropic)

**Notes:**
- Implementation depends on Claude Code's annotation/diagnostic API
- May need custom protocol if Claude Code doesn't have annotation support yet
- Could start with simpler "status bar" annotations before full inline support
- Performance: Annotations should be computed lazily and cached

---

### Enhancement #28: Advanced Testing Types

**Status:** 🔵 IDENTIFIED

**Problem:**

Basic unit and integration tests don't catch all issues:

1. **Mutation testing**: Tests may pass even if they don't catch bugs
2. **Contract testing**: API changes break clients unexpectedly
3. **Accessibility testing**: WCAG compliance not validated
4. **Visual regression**: UI changes undetected

**Example:**
```
API change: Remove field "user.email"
  → Unit tests pass ✓ (don't test this field)
  → Integration tests pass ✓ (don't use this field)
  → Deploy
  → Mobile app breaks ❌ (depends on user.email)
```

**Proposed Solution:**

Implement **advanced testing types** that catch issues traditional tests miss:

1. **Mutation Testing**
   - Inject bugs into code (mutants)
   - Verify tests catch the bugs
   - Mutation score = % mutants killed
   - Tools: Stryker (JS/TS), mutmut (Python)

2. **Contract Testing**
   - Define API contracts
   - Test provider adheres to contract
   - Test consumer expectations met
   - Detect breaking changes early
   - Tools: Pact, Spring Cloud Contract

3. **Accessibility Testing**
   - Validate WCAG 2.1 AA compliance
   - Test keyboard navigation
   - Test screen reader compatibility
   - Check color contrast
   - Tools: axe-core, Pa11y, Lighthouse

4. **Visual Regression Testing**
   - Capture screenshots of UI
   - Compare against baseline
   - Detect unintended visual changes
   - Tools: Percy, Chromatic, BackstopJS

**Implementation:**

**Mutation testing:**
```python
# src/solokit/testing/mutation_tester.py
class MutationTester:
    def run_mutation_tests(self, test_suite):
        # Run Stryker or mutmut
        # Generate mutants
        # Check if tests kill mutants
        # Calculate mutation score

    def check_mutation_score(self, score, threshold):
        # Fail if score < threshold (e.g., 75%)
```

**Contract testing:**
```python
# src/solokit/testing/contract_tester.py
class ContractTester:
    def define_contract(self, api_spec):
        # Create Pact contract from OpenAPI spec

    def test_provider(self, contract):
        # Verify API adheres to contract

    def test_consumer(self, contract):
        # Verify client expectations met

    def detect_breaking_changes(self, old_contract, new_contract):
        # Compare contracts, find breaking changes
```

**Accessibility testing:**
```python
# src/solokit/testing/accessibility_tester.py
class AccessibilityTester:
    def run_axe_audit(self, url):
        # Run axe-core accessibility audit
        # Return violations

    def check_wcag_compliance(self, violations):
        # Verify WCAG 2.1 AA compliance
        # Fail if critical violations
```

**Visual regression:**
```python
# src/solokit/testing/visual_tester.py
class VisualTester:
    def capture_screenshots(self, urls):
        # Capture screenshots of pages

    def compare_with_baseline(self, screenshots):
        # Compare with baseline images
        # Detect differences

    def update_baseline(self, screenshots):
        # Update baseline on approval
```

**Configuration:**
```json
// .session/config.json
"advanced_testing": {
  "mutation_testing": {
    "enabled": true,
    "threshold": 75,
    "framework": "stryker"  // or "mutmut"
  },
  "contract_testing": {
    "enabled": true,
    "format": "pact",
    "break_on_breaking_changes": true
  },
  "accessibility_testing": {
    "enabled": true,
    "standard": "WCAG21AA",
    "fail_on_violations": true
  },
  "visual_regression": {
    "enabled": true,
    "threshold": 0.02  // 2% pixel difference
  }
}
```

**Files Affected:**

**New:**
- `src/solokit/testing/mutation_tester.py` - Mutation testing (will be created)
- `src/solokit/testing/contract_tester.py` - Contract testing (will be created)
- `src/solokit/testing/accessibility_tester.py` - Accessibility testing (will be created)
- `src/solokit/testing/visual_tester.py` - Visual regression testing (will be created)
- `tests/contracts/` - Contract definitions (will be created)
- `tests/visual/baselines/` - Visual baseline images (will be created)
- Tests for advanced testing modules

**Modified:**
- `src/solokit/quality/gates.py` - Add advanced testing gates
- `.session/config.json` - Advanced testing configuration
- CI/CD workflows - Add advanced testing jobs

**Benefits:**

1. **Better test quality**: Mutation testing ensures tests catch bugs
2. **API stability**: Contract testing prevents breaking changes
3. **Accessibility compliance**: Automated WCAG validation
4. **UI stability**: Visual regression catches unintended changes
5. **Comprehensive coverage**: All types of issues caught

**Priority:** Medium - Improves test effectiveness

---

### Enhancement #29: Frontend Quality & Design System Compliance

**Status:** 🔵 IDENTIFIED

**Problem:**

Frontend code has unique quality concerns that general linting and testing don't address. Projects with design systems document standards but lack automated enforcement:

1. **Design System Non-Compliance**:
   - Developers accidentally use hardcoded colors instead of design tokens
   - Inconsistent spacing values (13px, 17px) instead of standard scale (8px, 16px, 24px)
   - Custom font sizes instead of typography scale
   - Direct HTML elements instead of design system components
   - Design debt accumulates silently

2. **Framework-Specific Issues**:
   - React hooks violations (dependencies, conditional usage)
   - Vue composition API anti-patterns
   - Next.js Image component not used (missing optimization)
   - Framework best practices not enforced

3. **Responsive Design Problems**:
   - Non-standard breakpoints used inconsistently
   - Fixed widths without max-width
   - Missing mobile-first CSS
   - Inconsistent responsive patterns

4. **Accessibility Gaps**:
   - Non-semantic HTML (divs instead of buttons, headings)
   - Missing ARIA attributes
   - Poor color contrast
   - Keyboard navigation broken
   - Current testing (#25) only catches regressions, not initial violations

5. **Bundle Size Bloat**:
   - No monitoring of bundle size over time
   - Large dependencies added without review
   - Missing code-splitting for large components
   - Performance budget violations

6. **CSS Quality Issues**:
   - Overuse of !important
   - High CSS specificity causing maintainability issues
   - Duplicate selectors
   - Inconsistent naming conventions

**Proposed Solution:**

Implement **frontend-specific quality gates** that enforce design system compliance, framework best practices, responsive design patterns, accessibility standards, and bundle size limits:

1. **Design Token Compliance**
   - Parse design tokens from CSS/SCSS/JS/Tailwind config
   - Detect hardcoded values in code
   - Validate against approved token values
   - Auto-fix where possible

2. **Component Library Enforcement**
   - Detect direct HTML when component exists
   - Validate component prop usage
   - Detect deprecated components
   - Suggest correct component variants

3. **Framework Best Practices**
   - React: hooks rules, memo usage, key props
   - Vue: composition API patterns, reactivity
   - Next.js: Image, Link, font optimization
   - Svelte: reactive statement patterns

4. **Responsive Design Validation**
   - Enforce standard breakpoints only
   - Validate mobile-first approach
   - Detect problematic fixed widths
   - CSS ordering validation

5. **Accessibility Enforcement**
   - Semantic HTML requirements
   - ARIA attribute validation
   - Color contrast checking (build-time)
   - Keyboard navigation testing
   - Focus management validation

6. **Bundle Size Monitoring**
   - Track bundle size over time
   - Alert on size increases > threshold
   - Identify large dependencies
   - Enforce code-splitting requirements

7. **CSS Quality Standards**
   - !important usage limits
   - Naming convention enforcement
   - Specificity limits
   - Duplicate selector detection

**Implementation:**

**Design token validation:**
```python
# src/solokit/quality/frontend/design_tokens.py
from typing import Dict, List, Any
import re
from pathlib import Path
import json

class DesignTokenValidator:
    """Validate frontend code against design tokens"""

    def __init__(self, tokens_file: Path):
        self.tokens = self._load_tokens(tokens_file)
        self.violations = []

    def _load_tokens(self, tokens_file: Path) -> Dict[str, Any]:
        """Load design tokens from JSON/JS file"""
        if not tokens_file.exists():
            return {}

        content = tokens_file.read_text()

        # Handle both JSON and JS exports
        if tokens_file.suffix == ".json":
            return json.loads(content)
        elif tokens_file.suffix in [".js", ".ts"]:
            # Extract tokens from JS/TS export
            # This is simplified - production would use AST parsing
            match = re.search(r'export\s+(?:default\s+)?({.*})', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))

        return {}

    def validate_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate a single file for design token compliance"""
        content = file_path.read_text()
        violations = []

        # Check for hardcoded colors
        color_pattern = r'(?:color|background|border-color):\s*#([0-9a-fA-F]{3,6}|rgba?\([^)]+\))'
        for match in re.finditer(color_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            violations.append({
                "file": str(file_path),
                "line": line_num,
                "type": "hardcoded_color",
                "value": match.group(0),
                "message": f"Hardcoded color found. Use design token from colors.{self._suggest_color_token(match.group(1))}",
                "severity": "error"
            })

        # Check for hardcoded spacing
        spacing_pattern = r'(?:margin|padding|gap):\s*(\d+)px'
        for match in re.finditer(spacing_pattern, content):
            spacing_value = int(match.group(1))
            if spacing_value not in self.tokens.get("spacing", {}).values():
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "type": "hardcoded_spacing",
                    "value": f"{spacing_value}px",
                    "message": f"Non-standard spacing. Use spacing scale: {list(self.tokens.get('spacing', {}).values())}",
                    "severity": "error"
                })

        # Check for hardcoded font sizes
        font_pattern = r'font-size:\s*(\d+)px'
        for match in re.finditer(font_pattern, content):
            font_size = int(match.group(1))
            if font_size not in self.tokens.get("typography", {}).get("sizes", {}).values():
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "type": "hardcoded_font_size",
                    "value": f"{font_size}px",
                    "message": f"Non-standard font size. Use typography scale: {list(self.tokens.get('typography', {}).get('sizes', {}).values())}",
                    "severity": "error"
                })

        return violations

    def _suggest_color_token(self, color_value: str) -> str:
        """Suggest appropriate color token for a value"""
        # Simplified - production would do color similarity matching
        colors = self.tokens.get("colors", {})
        if color_value.lower() in colors.values():
            return next(k for k, v in colors.items() if v.lower() == color_value.lower())
        return "primary|secondary|error|..."

class ComponentLibraryValidator:
    """Validate component library usage"""

    def __init__(self, component_library: str):
        self.component_library = component_library
        self.violations = []

    def validate_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate component library usage"""
        content = file_path.read_text()
        violations = []

        # Detect raw HTML buttons instead of Button component
        button_pattern = r'<button[^>]*>'
        for match in re.finditer(button_pattern, content):
            # Check if this is inside a custom Button component definition
            if not self._is_in_component_definition(content, match.start(), "Button"):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "type": "raw_html_element",
                    "element": "button",
                    "message": f"Use <Button> from {self.component_library} instead of raw <button>",
                    "severity": "error"
                })

        # Detect raw links instead of Link component
        link_pattern = r'<a\s+href='
        for match in re.finditer(link_pattern, content):
            if not self._is_in_component_definition(content, match.start(), "Link"):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "type": "raw_html_element",
                    "element": "a",
                    "message": f"Use <Link> from {self.component_library} for internal navigation",
                    "severity": "warning"
                })

        return violations

    def _is_in_component_definition(self, content: str, position: int, component_name: str) -> bool:
        """Check if position is inside a component definition"""
        # Simplified - production would use AST
        before = content[:position]
        return f"function {component_name}" in before or f"const {component_name} =" in before
```

**Bundle size monitoring:**
```python
# src/solokit/quality/frontend/bundle_size.py
from typing import Dict, List, Any
from pathlib import Path
import json
import subprocess

class BundleSizeMonitor:
    """Monitor and enforce bundle size limits"""

    def __init__(self, config: Dict[str, Any]):
        self.max_size_mb = config.get("max_size_mb", 0.5)
        self.max_increase_percent = config.get("max_increase_percent", 5)
        self.history_file = Path(".session/bundle_size_history.json")

    def check_bundle_size(self, build_dir: Path) -> Dict[str, Any]:
        """Check current bundle size against limits"""
        current_sizes = self._get_bundle_sizes(build_dir)
        history = self._load_history()

        violations = []

        for bundle_name, current_size in current_sizes.items():
            # Check absolute size
            size_mb = current_size / (1024 * 1024)
            if size_mb > self.max_size_mb:
                violations.append({
                    "bundle": bundle_name,
                    "type": "size_limit_exceeded",
                    "current_size_mb": size_mb,
                    "max_size_mb": self.max_size_mb,
                    "message": f"Bundle size ({size_mb:.2f}MB) exceeds limit ({self.max_size_mb}MB)",
                    "severity": "error"
                })

            # Check size increase
            if bundle_name in history:
                previous_size = history[bundle_name]
                increase_percent = ((current_size - previous_size) / previous_size) * 100

                if increase_percent > self.max_increase_percent:
                    violations.append({
                        "bundle": bundle_name,
                        "type": "size_increase_exceeded",
                        "increase_percent": increase_percent,
                        "max_increase_percent": self.max_increase_percent,
                        "previous_size_mb": previous_size / (1024 * 1024),
                        "current_size_mb": size_mb,
                        "message": f"Bundle size increased by {increase_percent:.1f}% (limit: {self.max_increase_percent}%)",
                        "severity": "warning"
                    })

        # Update history
        self._save_history(current_sizes)

        return {
            "violations": violations,
            "current_sizes": current_sizes,
            "analysis": self._analyze_bundle(build_dir)
        }

    def _get_bundle_sizes(self, build_dir: Path) -> Dict[str, int]:
        """Get sizes of all bundles"""
        sizes = {}

        # Find all JS files in build directory
        for js_file in build_dir.rglob("*.js"):
            if js_file.is_file():
                sizes[js_file.name] = js_file.stat().st_size

        return sizes

    def _analyze_bundle(self, build_dir: Path) -> Dict[str, Any]:
        """Analyze bundle composition"""
        # Run webpack-bundle-analyzer or similar
        # This is simplified - production would integrate with bundler
        return {
            "largest_dependencies": [],
            "duplicate_code": [],
            "recommendations": []
        }

    def _load_history(self) -> Dict[str, int]:
        """Load bundle size history"""
        if not self.history_file.exists():
            return {}
        return json.loads(self.history_file.read_text())

    def _save_history(self, sizes: Dict[str, int]):
        """Save current sizes to history"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(sizes, indent=2))
```

**Accessibility validation:**
```python
# src/solokit/quality/frontend/accessibility.py
from typing import List, Dict, Any
from pathlib import Path
import subprocess

class AccessibilityValidator:
    """Validate accessibility standards"""

    def __init__(self, config: Dict[str, Any]):
        self.wcag_level = config.get("wcag_level", "AA")
        self.check_color_contrast = config.get("check_color_contrast", True)

    def validate_semantic_html(self, file_path: Path) -> List[Dict[str, Any]]:
        """Validate semantic HTML usage"""
        content = file_path.read_text()
        violations = []

        # Check for divs that should be buttons
        div_click_pattern = r'<div[^>]*onClick'
        for match in re.finditer(div_click_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            violations.append({
                "file": str(file_path),
                "line": line_num,
                "type": "non_semantic_html",
                "message": "Use <button> instead of <div onClick>. Divs are not keyboard accessible.",
                "severity": "error",
                "wcag": "WCAG 2.1.1 (Keyboard)"
            })

        # Check for missing alt text on images
        img_pattern = r'<img(?![^>]*alt=)'
        for match in re.finditer(img_pattern, content):
            line_num = content[:match.start()].count('\n') + 1
            violations.append({
                "file": str(file_path),
                "line": line_num,
                "type": "missing_alt_text",
                "message": "Image missing alt attribute",
                "severity": "error",
                "wcag": "WCAG 1.1.1 (Non-text Content)"
            })

        return violations

    def run_axe_core(self, url: str) -> Dict[str, Any]:
        """Run axe-core accessibility tests"""
        # Use playwright or similar to run axe-core
        result = subprocess.run(
            ["npx", "pa11y", "--standard", f"WCAG2{self.wcag_level}", url],
            capture_output=True,
            text=True
        )

        return {
            "passed": result.returncode == 0,
            "violations": self._parse_pa11y_output(result.stdout)
        }

    def _parse_pa11y_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse pa11y output into violations"""
        # Simplified parser
        violations = []
        for line in output.split('\n'):
            if 'Error:' in line:
                violations.append({
                    "message": line.strip(),
                    "severity": "error"
                })
        return violations
```

**Frontend quality gate integration:**
```python
# src/solokit/quality/gates.py (enhanced)
class FrontendQualityGate:
    """Frontend-specific quality gate"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("frontend", {})
        self.design_system_config = self.config.get("design_system", {})
        self.bundle_size_config = self.config.get("bundle_size", {})
        self.accessibility_config = self.config.get("accessibility", {})

    def validate(self) -> Dict[str, Any]:
        """Run all frontend quality checks"""
        results = {
            "passed": True,
            "checks": {}
        }

        # Design token compliance
        if self.design_system_config.get("enabled"):
            token_validator = DesignTokenValidator(
                Path(self.design_system_config["tokens_file"])
            )
            violations = []
            for file in self._get_frontend_files():
                violations.extend(token_validator.validate_file(file))

            results["checks"]["design_tokens"] = {
                "passed": len(violations) == 0,
                "violations": violations
            }
            if violations:
                results["passed"] = False

        # Component library compliance
        if self.design_system_config.get("component_library"):
            component_validator = ComponentLibraryValidator(
                self.design_system_config["component_library"]
            )
            violations = []
            for file in self._get_frontend_files():
                violations.extend(component_validator.validate_file(file))

            results["checks"]["component_library"] = {
                "passed": len(violations) == 0,
                "violations": violations
            }
            if violations:
                results["passed"] = False

        # Bundle size
        if self.bundle_size_config.get("enabled"):
            bundle_monitor = BundleSizeMonitor(self.bundle_size_config)
            build_dir = Path(self.bundle_size_config.get("build_dir", "build"))
            bundle_result = bundle_monitor.check_bundle_size(build_dir)

            results["checks"]["bundle_size"] = bundle_result
            if bundle_result["violations"]:
                results["passed"] = False

        # Accessibility
        if self.accessibility_config.get("enabled"):
            a11y_validator = AccessibilityValidator(self.accessibility_config)
            violations = []
            for file in self._get_frontend_files():
                violations.extend(a11y_validator.validate_semantic_html(file))

            results["checks"]["accessibility"] = {
                "passed": len(violations) == 0,
                "violations": violations
            }
            if violations:
                results["passed"] = False

        # Framework-specific linting (run via ESLint plugins)
        results["checks"]["framework_linting"] = self._run_framework_linting()
        if not results["checks"]["framework_linting"]["passed"]:
            results["passed"] = False

        return results

    def _get_frontend_files(self) -> List[Path]:
        """Get all frontend source files"""
        extensions = [".jsx", ".tsx", ".vue", ".svelte", ".css", ".scss"]
        files = []
        src_dir = Path("src")
        if src_dir.exists():
            for ext in extensions:
                files.extend(src_dir.rglob(f"*{ext}"))
        return files

    def _run_framework_linting(self) -> Dict[str, Any]:
        """Run framework-specific ESLint rules"""
        result = subprocess.run(
            ["npx", "eslint", "src/", "--format", "json"],
            capture_output=True,
            text=True
        )

        try:
            lint_results = json.loads(result.stdout)
            error_count = sum(r["errorCount"] for r in lint_results)
            return {
                "passed": error_count == 0,
                "results": lint_results
            }
        except:
            return {"passed": True, "results": []}
```

**Configuration:**
```json
// .session/config.json (enhanced)
{
  "quality_gates": {
    "frontend": {
      "enabled": true,
      "design_system": {
        "enabled": true,
        "tokens_file": "src/design-tokens.json",
        "strict_mode": true,
        "allowed_exceptions": ["src/legacy/**"],
        "component_library": "@company/design-system"
      },
      "component_library": {
        "enabled": true,
        "library": "@company/design-system",
        "enforce_usage": true
      },
      "bundle_size": {
        "enabled": true,
        "max_size_mb": 0.5,
        "max_increase_percent": 5,
        "build_dir": "build"
      },
      "responsive": {
        "enabled": true,
        "breakpoints": ["640px", "768px", "1024px", "1280px"],
        "mobile_first": true
      },
      "accessibility": {
        "enabled": true,
        "wcag_level": "AA",
        "check_color_contrast": true,
        "semantic_html_required": true
      },
      "framework_linting": {
        "enabled": true,
        "framework": "react",
        "rules": {
          "react-hooks": "error",
          "jsx-a11y": "error"
        }
      }
    }
  }
}
```

**ESLint configuration (.eslintrc.json):**
```json
{
  "extends": [
    "react-app",
    "plugin:jsx-a11y/recommended",
    "plugin:react-hooks/recommended"
  ],
  "plugins": ["jsx-a11y", "react-hooks"],
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/no-static-element-interactions": "error"
  }
}
```

**StyleLint configuration (.stylelintrc.json):**
```json
{
  "extends": ["stylelint-config-standard"],
  "plugins": ["stylelint-use-design-tokens"],
  "rules": {
    "scale-unlimited/declaration-strict-value": [
      ["/color/", "fill", "stroke"],
      {
        "ignoreValues": ["transparent", "inherit", "currentColor"]
      }
    ],
    "declaration-no-important": true,
    "selector-max-specificity": "0,4,0",
    "max-nesting-depth": 3
  }
}
```

**Commands:**
```bash
# Run frontend quality gates
/sk:validate --frontend

# Run specific frontend checks
/sk:frontend-check --design-tokens
/sk:frontend-check --bundle-size
/sk:frontend-check --accessibility

# Analyze bundle size
/sk:bundle-analyze

# Check design token compliance
/sk:design-tokens-check

# Auto-fix design token violations (where possible)
/sk:design-tokens-fix
```

**Files Affected:**

**New:**
- `src/solokit/quality/frontend/` - New module (will be created)
- `src/solokit/quality/frontend/__init__.py` - Module init (will be created)
- `src/solokit/quality/frontend/design_tokens.py` - Design token validation (will be created)
- `src/solokit/quality/frontend/component_library.py` - Component library validation (will be created)
- `src/solokit/quality/frontend/bundle_size.py` - Bundle size monitoring (will be created)
- `src/solokit/quality/frontend/accessibility.py` - Accessibility validation (will be created)
- `src/solokit/quality/frontend/responsive.py` - Responsive design validation (will be created)
- `.session/bundle_size_history.json` - Bundle size tracking (will be created)
- `tests/unit/test_frontend_quality.py` - Unit tests (will be created)
- `tests/integration/test_frontend_gates.py` - Integration tests (will be created)
- `.claude/commands/frontend-check.md` - Frontend check command (will be created)
- `.claude/commands/bundle-analyze.md` - Bundle analysis command (will be created)
- `.claude/commands/design-tokens-check.md` - Design token check command (will be created)

**Modified:**
- `src/solokit/quality/gates.py` - Add frontend quality gate
- `src/solokit/templates/config.schema.json` - Add frontend quality config schema
- `.claude/commands/validate.md` - Document frontend validation
- `README.md` - Document frontend quality gates

**Benefits:**

1. **Automated Design System Enforcement**: No manual reviews needed for design token compliance
2. **Prevents Design Debt**: Catch violations before they accumulate
3. **Framework Best Practices**: Enforce React hooks rules, Next.js optimizations, etc.
4. **Accessibility Built-In**: WCAG compliance validated automatically
5. **Bundle Size Control**: Prevent performance regressions from bloat
6. **Consistent Frontend Code**: Uniform patterns across the codebase
7. **Faster Reviews**: Automated checks reduce manual review time
8. **Learning Tool**: Developers learn design system through validation messages
9. **Responsive Design Consistency**: Standardized breakpoints and patterns
10. **CSS Quality**: Clean, maintainable stylesheets

**Priority:** Medium-High (High for design system projects)

**Justification:**
- Fills significant gap in frontend code quality
- Essential for projects with design systems
- Prevents technical debt accumulation
- Improves accessibility compliance
- Aligns with modern frontend development practices

**Notes:**
- Design token validation requires design tokens to be defined in a parseable format
- Component library validation requires consistent naming conventions
- Bundle size monitoring requires a build step
- Accessibility checks complement but don't replace manual testing
- Framework-specific rules depend on ESLint plugins being installed
- Can be disabled for projects without design systems
- Works well with Enhancement #25 (Advanced Testing Types) - visual regression testing
- Related to Enhancement #18 (Advanced Code Quality Gates) - extends code quality to frontend specifics
- Can integrate with Enhancement #38 (MCP Server Management) - playwright MCP for visual validation
- Template-based init (Enhancement #13) can include framework-specific frontend configurations

---
### Enhancement #30: Documentation-Driven Development

**Status:** 🔵 IDENTIFIED

**Problem:**

The AI-Augmented Solo Framework assumes developers start with Vision, PRD, and Architecture documents, but Solokit currently has no workflow to:

1. **Parse project documentation**: Vision, PRD, Architecture docs exist but aren't used
2. **Generate work items from docs**: Manual work item creation from 100+ page docs is tedious
3. **Maintain doc-code traceability**: No link between code and original requirements
4. **Track architecture decisions**: ADRs not captured or tracked
5. **Validate against architecture**: Work items may violate architecture constraints

**Example workflow gap:**
```
Developer has:
  - Vision.md (product vision)
  - PRD.md (requirements, 50 pages)
  - Architecture.md (system design)

Current process:
  → Manually read all docs
  → Manually create work items
  → Hope work items align with architecture
  → No traceability between code and requirements
```

**Proposed Solution:**

Implement **documentation-driven development workflow** that parses project docs and guides development:

1. **Document Parsing and Analysis**
   - Parse Vision, PRD, Architecture, ADR documents
   - Extract requirements, user stories, architectural constraints
   - Build knowledge graph of project structure

2. **Smart Work Item Generation**
   - Analyze documents and suggest work items
   - Prioritize based on dependencies and business value
   - Map work items to architecture components
   - Estimate complexity from requirements

3. **Architecture Decision Records (ADRs)**
   - Template-based ADR creation
   - Link ADRs to work items
   - Track decision history and rationale
   - Validate work items against ADRs

4. **Document-to-Code Traceability**
   - Link work items to requirements in docs
   - Track which code implements which requirement
   - Generate traceability matrix

5. **Architecture Validation**
   - Validate work items against architecture constraints
   - Detect architecture violations
   - Suggest architecture updates when needed

6. **API-First Documentation System**
   - Automated OpenAPI/Swagger generation from code annotations
   - Interactive API documentation (Swagger UI, Redoc, API Explorer)
   - API versioning and changelog automation
   - SDK generation for multiple languages (Python, TypeScript, Go, etc.)
   - API contract testing integration
   - Breaking change detection between API versions
   - API usage analytics and deprecation management

**Implementation:**

**Document parser:**
```python
# src/solokit/docs/parser.py
class DocumentParser:
    def parse_vision(self, vision_file):
        # Extract business goals, target users

    def parse_prd(self, prd_file):
        # Extract requirements, user stories, acceptance criteria

    def parse_architecture(self, arch_file):
        # Extract components, constraints, patterns

    def parse_adrs(self, adr_dir):
        # Load all ADRs, build decision history
```

**Work item generator:**
```python
# src/solokit/work_items/generator.py
class WorkItemGenerator:
    def suggest_from_documents(self, docs):
        # Analyze docs, extract requirements
        # Generate work item suggestions
        # Prioritize and estimate

    def map_to_architecture(self, work_items, architecture):
        # Map work items to arch components
        # Validate against constraints
```

**API documentation generator:**
```python
# src/solokit/docs/api_doc_generator.py
class APIDocumentationGenerator:
    def generate_openapi_spec(self, codebase):
        # Scan code for API endpoints and annotations
        # Generate OpenAPI 3.0 specification
        # Include schemas, parameters, responses

    def generate_interactive_docs(self, openapi_spec):
        # Generate Swagger UI / Redoc documentation
        # Set up API explorer with try-it-out functionality
        # Deploy to docs site

    def generate_sdk(self, openapi_spec, languages):
        # Generate client SDKs from OpenAPI spec
        # Support Python, TypeScript, Go, Java, etc.
        # Include usage examples and tests

    def detect_breaking_changes(self, old_spec, new_spec):
        # Compare API versions
        # Identify breaking changes (removed endpoints, changed schemas)
        # Generate migration guide

    def track_api_versions(self):
        # Maintain API version history
        # Generate changelogs automatically
        # Mark deprecated endpoints
```

**API documentation example:**
```yaml
# Generated OpenAPI specification
openapi: 3.0.0
info:
  title: User Management API
  version: 2.1.0
  description: API for user authentication and profile management
paths:
  /api/v2/users:
    get:
      summary: List all users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: User created successfully
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        name:
          type: string
```

**Commands:**
```bash
# Parse docs and suggest work items
/sk:work-suggest --from-docs

# Create ADR for architectural decision
/sk:adr-new --title "Use PostgreSQL for primary database"

# Validate work item against architecture
/sk:work-validate <work-item-id> --architecture

# Generate traceability matrix
/sk:trace --requirements docs/PRD.md

# Generate API documentation
/sk:api-docs-generate [--output swagger|redoc|both]

# Generate SDK from API spec
/sk:api-sdk-generate --language [python|typescript|go|java]

# Check for breaking API changes
/sk:api-breaking-changes --compare v1.0.0..v2.0.0
```

**ADR template:**
```markdown
# ADR-NNN: [Decision Title]

**Status:** Proposed | Accepted | Deprecated | Superseded

**Context:**
Why is this decision needed?

**Decision:**
What did we decide?

**Alternatives Considered:**
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Consequences:**
- Positive: [benefits]
- Negative: [trade-offs]

**Related Work Items:**
- feature_xxx
- bug_yyy

**References:**
- [External resources]
```

**Files Affected:**

**New:**
- `src/solokit/docs/parser.py` (will be created) - Document parsing
- `src/solokit/docs/vision_parser.py` (will be created) - Vision document parser
- `src/solokit/docs/prd_parser.py` (will be created) - PRD parser
- `src/solokit/docs/architecture_parser.py` (will be created) - Architecture parser
- `src/solokit/docs/api_doc_generator.py` (will be created) - API documentation generator
- `src/solokit/work_items/generator.py` (will be created) - Work item generator
- `src/solokit/architecture/adr_manager.py` (will be created) - ADR management
- `src/solokit/architecture/validator.py` (will be created) - Architecture validation
- `src/solokit/traceability/tracker.py` (will be created) - Requirement traceability
- `src/solokit/api/openapi_generator.py` (will be created) - OpenAPI specification generator
- `src/solokit/api/sdk_generator.py` (will be created) - Multi-language SDK generator
- `src/solokit/api/breaking_change_detector.py` (will be created) - API version comparator
- `.claude/commands/work-suggest.md` (will be created) - Work suggestion command
- `.claude/commands/adr-new.md` (will be created) - ADR creation command
- `.claude/commands/api-docs-generate.md` (will be created) - API docs generation command
- `.claude/commands/api-sdk-generate.md` (will be created) - SDK generation command
- `.claude/commands/api-breaking-changes.md` (will be created) - Breaking change detection command
- `docs/adr/` (will be created) - ADR directory
- `docs/api/` (will be created) - Generated API documentation
- Tests for document parsing and generation (will be created)

**Modified:**
- `src/solokit/work_items/creator.py` - Support generated work items
- `src/solokit/work_items/spec_parser.py` - Parse architecture constraints
- `.session/tracking/work_items.json` - Add traceability fields

**Benefits:**

1. **Faster planning**: Auto-generate work items from docs
2. **Alignment**: Work items guaranteed to match requirements
3. **Traceability**: Know which code implements which requirement
4. **Architecture compliance**: Work validated against architecture
5. **Decision history**: ADRs track why decisions were made
6. **Knowledge capture**: Documentation drives development
7. **API-first development**: Automated API documentation from code
8. **Multi-language SDKs**: Auto-generated client libraries
9. **API stability**: Breaking change detection prevents client disruption
10. **Developer experience**: Interactive API documentation and examples

**Priority:** High - Bridges gap between planning and implementation

**Notes:**
- Requires project documentation to exist (Vision, PRD, Architecture)
- Parser supports Markdown and common doc formats
- AI can assist with initial document creation if needed

---

### Enhancement #31: AI-Enhanced Learning System

**Status:** 🔵 IDENTIFIED

**Problem:**

Current learning system uses keyword-based algorithms with limitations:

1. **Learning Curation (Deduplication)**:
   - Uses Jaccard similarity for duplicate detection
   - Misses semantically similar learnings with different wording
   - Example: "Use async/await for better performance" vs "Prefer promises over callbacks" are similar but Jaccard doesn't detect

2. **Learning Relevance Scoring**:
   - Uses keyword matching to find relevant learnings
   - Misses semantically related learnings
   - Example: Work item "Implement JWT authentication" → Learning "Always validate tokens on server side" scores low (no "JWT" keyword) but is highly relevant

3. **Learning Categorization**:
   - Keyword-based category assignment
   - May miscategorize learnings with ambiguous keywords
   - Example: "Cache invalidation is hard" → Could be "performance" or "architecture" or "gotchas"

**Proposed Solution:**

Implement **AI-powered learning system** using Claude API for semantic understanding:

1. **AI-Powered Deduplication**
   - Use Claude API to detect semantically similar learnings
   - Understand meaning, not just word overlap
   - Smarter merging of similar learnings
   - Preserve unique insights

2. **Semantic Relevance Scoring**
   - Use Claude API to score learning relevance to work items
   - Understand context and semantic relationships
   - Find relevant learnings even without keyword matches
   - Context-aware recommendations

3. **Intelligent Categorization**
   - Use Claude API to categorize learnings
   - Understand nuance and context
   - Multi-category support (learning can fit multiple categories)
   - Confidence scores for categories

4. **Learning Summarization**
   - Generate summaries of long learnings
   - Extract key insights
   - Create learning digests

5. **Learning Relationships**
   - Detect relationships between learnings
   - Build knowledge graph
   - Suggest related learnings

**Implementation:**

**AI-powered learning curator:**
```python
# src/solokit/learning/ai_curator.py
import anthropic
from typing import List, Dict, Any, Tuple
import json

class AILearningCurator:
    """AI-powered learning curation using Claude API"""

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

    def detect_semantic_similarity(
        self,
        learning1: Dict[str, Any],
        learning2: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Detect if two learnings are semantically similar.

        Returns:
            (is_similar, similarity_score, reasoning)
        """
        prompt = f"""Analyze if these two learnings are semantically similar:

Learning 1: {learning1['content']}
Category 1: {learning1.get('category', 'unknown')}

Learning 2: {learning2['content']}
Category 2: {learning2.get('category', 'unknown')}

Respond in JSON format:
{{
  "similar": true/false,
  "similarity_score": 0.0-1.0,
  "reasoning": "brief explanation",
  "recommendation": "keep_both" | "merge" | "mark_as_related"
}}

Consider:
- Do they convey the same core insight?
- Are they about the same problem/solution?
- Would a developer benefit from seeing both separately?
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)
        return result["similar"], result["similarity_score"], result["reasoning"]

    def score_learning_relevance(
        self,
        learning: Dict[str, Any],
        work_item_title: str,
        work_item_spec: str,
        work_item_type: str
    ) -> Tuple[float, str]:
        """
        Score how relevant a learning is to a work item.

        Returns:
            (relevance_score, reasoning)
        """
        prompt = f"""Rate how relevant this learning is to the work item (0.0-1.0):

Work Item:
- Title: {work_item_title}
- Type: {work_item_type}
- Spec: {work_item_spec[:500]}...

Learning: {learning['content']}
Category: {learning.get('category', 'unknown')}

Respond in JSON format:
{{
  "relevance_score": 0.0-1.0,
  "reasoning": "brief explanation of why/why not relevant",
  "key_connections": ["connection 1", "connection 2"]
}}

Consider:
- Does it help solve the work item's problem?
- Does it prevent common mistakes in this type of work?
- Is it about related technologies/patterns?
- Would a developer benefit from knowing this?
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)
        return result["relevance_score"], result["reasoning"]

    def categorize_learning(
        self,
        learning_content: str
    ) -> List[Tuple[str, float]]:
        """
        Categorize a learning using AI.

        Returns:
            List of (category, confidence) tuples
        """
        categories = [
            "architecture", "gotchas", "best_practices",
            "technical_debt", "performance", "security"
        ]

        prompt = f"""Categorize this learning. It may fit multiple categories.

Learning: {learning_content}

Available categories:
- architecture: Architectural patterns and design decisions
- gotchas: Pitfalls, traps, common mistakes
- best_practices: Conventions, standards, recommendations
- technical_debt: Refactoring needs, workarounds, TODOs
- performance: Optimization insights, benchmarks
- security: Security considerations and hardening

Respond in JSON format:
{{
  "categories": [
    {{"name": "category", "confidence": 0.0-1.0, "reasoning": "brief explanation"}},
    ...
  ],
  "primary_category": "category"
}}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)
        return [
            (cat["name"], cat["confidence"])
            for cat in result["categories"]
        ]

    def summarize_learning(
        self,
        learning_content: str,
        max_length: int = 80
    ) -> str:
        """Generate a concise summary of a learning"""
        prompt = f"""Summarize this learning in {max_length} characters or less:

Learning: {learning_content}

Provide a concise summary that captures the key insight.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = response.content[0].text.strip()
        return summary[:max_length]

    def suggest_merge(
        self,
        learnings: List[Dict[str, Any]]
    ) -> str:
        """Suggest how to merge similar learnings"""
        prompt = f"""These learnings are similar. Suggest how to merge them into one comprehensive learning:

Learnings:
{json.dumps([l['content'] for l in learnings], indent=2)}

Provide a merged learning that:
1. Captures all unique insights
2. Is concise and clear
3. Preserves important details
4. Uses consistent terminology
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def find_related_learnings(
        self,
        learning: Dict[str, Any],
        all_learnings: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Tuple[Dict, float, str]]:
        """Find learnings related to this one"""
        prompt = f"""Find learnings related to this one:

Main Learning: {learning['content']}

Other Learnings:
{json.dumps([{"id": i, "content": l['content']} for i, l in enumerate(all_learnings[:20])], indent=2)}

Respond in JSON format:
{{
  "related": [
    {{
      "id": learning_id,
      "relatedness": 0.0-1.0,
      "relationship": "brief description of how they relate"
    }},
    ...
  ]
}}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)
        related = [
            (all_learnings[r["id"]], r["relatedness"], r["relationship"])
            for r in result["related"]
        ]
        return sorted(related, key=lambda x: x[1], reverse=True)[:limit]
```

**Enhanced learning curator:**
```python
# src/solokit/learning/curator.py (enhanced)
class LearningCurator:
    def __init__(self):
        self.learnings_file = Path(".session/tracking/learnings.json")
        self.ai_curator = AILearningCurator() if self.has_api_key() else None

    def has_api_key(self) -> bool:
        """Check if Anthropic API key is available"""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def curate_learnings(self, use_ai: bool = True):
        """Curate learnings with optional AI enhancement"""
        learnings = self.load_learnings()

        if use_ai and self.ai_curator:
            print("Using AI-powered curation...")
            self.ai_curate_learnings(learnings)
        else:
            print("Using keyword-based curation...")
            self.keyword_curate_learnings(learnings)

    def ai_curate_learnings(self, learnings: List[Dict]):
        """AI-powered curation"""

        # 1. Categorize uncategorized learnings
        for learning in learnings:
            if not learning.get("category"):
                categories = self.ai_curator.categorize_learning(learning["content"])
                learning["category"] = categories[0][0]  # Primary category
                learning["categories_all"] = categories  # All categories with confidence

        # 2. Find and merge similar learnings
        merged_count = 0
        i = 0
        while i < len(learnings):
            j = i + 1
            while j < len(learnings):
                similar, score, reasoning = self.ai_curator.detect_semantic_similarity(
                    learnings[i], learnings[j]
                )

                if similar and score > 0.8:
                    # Merge learnings
                    merged_content = self.ai_curator.suggest_merge([learnings[i], learnings[j]])
                    learnings[i]["content"] = merged_content
                    learnings[i]["merged_from"] = learnings[i].get("merged_from", []) + [learnings[j]["id"]]
                    learnings.pop(j)
                    merged_count += 1
                    print(f"Merged similar learnings: {reasoning}")
                else:
                    j += 1
            i += 1

        print(f"Merged {merged_count} similar learnings")

        # 3. Find learning relationships
        for i, learning in enumerate(learnings):
            related = self.ai_curator.find_related_learnings(
                learning, learnings[:i] + learnings[i+1:], limit=3
            )
            learning["related_learnings"] = [
                {"id": r[0]["id"], "relationship": r[2]}
                for r in related
            ]

        self.save_learnings(learnings)

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        category: str = None
    ) -> List[Dict]:
        """Semantic search using AI"""
        learnings = self.load_learnings()

        if category:
            learnings = [l for l in learnings if l.get("category") == category]

        # Use AI to score relevance
        scored_learnings = []
        for learning in learnings:
            score, reasoning = self.ai_curator.score_learning_relevance(
                learning,
                work_item_title=query,
                work_item_spec=query,
                work_item_type="feature"
            )
            scored_learnings.append((learning, score, reasoning))

        # Sort by relevance
        scored_learnings.sort(key=lambda x: x[1], reverse=True)

        return [
            {**l[0], "relevance_score": l[1], "relevance_reasoning": l[2]}
            for l in scored_learnings[:limit]
        ]
```

**Enhanced session briefing:**
```python
# src/solokit/session/briefing/learning_loader.py (enhanced)
def get_relevant_learnings_ai(work_item_id: str, limit: int = 10) -> List[Dict]:
    """Get relevant learnings using AI-powered scoring"""
    from solokit.work_items.repository import WorkItemRepository
    from solokit.learning.repository import LearningRepository

    # Get work item
    repository = WorkItemRepository()
    work_item = repository.get_work_item(work_item_id)

    # Get spec
    spec_path = Path(f".session/specs/{work_item_id}.md")
    spec_content = spec_path.read_text() if spec_path.exists() else ""

    # Get all learnings
    learning_repo = LearningRepository()
    learnings = learning_repo.load_learnings()

    if learning_repo.ai_curator:
        # Use AI scoring
        scored_learnings = []
        for learning in learnings:
            score, reasoning = learning_repo.ai_curator.score_learning_relevance(
                learning,
                work_item_title=work_item["title"],
                work_item_spec=spec_content,
                work_item_type=work_item["type"]
            )
            scored_learnings.append((learning, score, reasoning))

        # Sort by relevance
        scored_learnings.sort(key=lambda x: x[1], reverse=True)

        return [
            {**l[0], "relevance_score": l[1], "relevance_reasoning": l[2]}
            for l in scored_learnings[:limit]
        ]
    else:
        # Fallback to keyword-based scoring
        return get_relevant_learnings(work_item_id, limit)
```

**Configuration:**
```json
// .session/config.json
{
  "learning_system": {
    "use_ai_curation": true,
    "use_ai_relevance": true,
    "ai_curation_frequency": "weekly",  // or "every_n_sessions": 5
    "semantic_search_enabled": true,
    "min_similarity_threshold": 0.8,
    "api_provider": "anthropic",
    "model": "claude-sonnet-4-5-20250929"
  }
}
```

**Commands:**
```bash
# Use AI curation
/sk:learn-curate --ai

# Semantic search
/sk:learn-search "authentication" --semantic

# Find related learnings
/sk:learn-related <learning_id>
```

**Files Affected:**

**New:**
- `src/solokit/learning/ai_curator.py` (will be created) - AI-powered curation
- `tests/unit/test_ai_curator.py` (will be created) - AI curator tests
- `tests/fixtures/sample_learnings.json` (will be created) - Test learnings

**Modified:**
- `src/solokit/learning/curator.py` - Integrate AI curation
- `src/solokit/learning/repository.py` - Integrate AI search
- `src/solokit/session/briefing/learning_loader.py` - Use AI relevance scoring
- `.session/config.json` - Add AI learning configuration
- `pyproject.toml` - Add anthropic SDK dependency
- `.claude/commands/learn-curate.md` - Document AI curation
- `.claude/commands/learn-search.md` - Document semantic search

**Benefits:**

1. **Better deduplication**: Catches semantically similar learnings
2. **Smarter relevance**: Finds relevant learnings without keyword matches
3. **Improved categorization**: Understands nuance and context
4. **Knowledge graph**: Relationships between learnings
5. **Summarization**: Concise summaries for quick scanning
6. **Higher quality**: Cleaner, more useful knowledge base
7. **Better context loading**: More relevant learnings in session briefings
8. **Learning evolution**: Merge and refine learnings over time

**Priority:** High - Enhances core Solokit feature (learning system)

**Notes:**
- Requires Anthropic API key (set via ANTHROPIC_API_KEY env variable)
- Graceful fallback to keyword-based methods if API key not available
- API costs should be monitored (curation is infrequent, so cost is low)
- Can be disabled per project if API access not desired
- Considers privacy: learnings stay local, only sent to API during curation

---

### Enhancement #32: Continuous Improvement System

**Status:** 🔵 IDENTIFIED

**Problem:**

Development processes don't improve over time. No mechanism to:

1. **Learn from work items**: Patterns and lessons lost
2. **Track technical debt**: Debt accumulates unnoticed
3. **Measure velocity**: Don't know if getting faster or slower
4. **Identify bottlenecks**: Process inefficiencies unknown
5. **Optimize workflows**: No data-driven improvements

**Example:**
```
Work item completed → Next work item started
                    → No reflection on what worked/didn't work
                    → Same issues repeat
                    → No improvement
```

**Proposed Solution:**

Implement **continuous improvement system** that tracks metrics and suggests optimizations:

1. **Automated Retrospectives**
   - After each work item or milestone, generate retrospective
   - Analyze what went well, what didn't
   - Track lessons learned
   - Suggest improvements

2. **Technical Debt Tracking**
   - Identify technical debt during development
   - Track debt accumulation over time
   - Prioritize debt paydown
   - Measure debt ratio

3. **DORA Metrics Dashboard**
   - Deployment frequency: How often deploying
   - Lead time: Time from commit to production
   - Change failure rate: % of deployments that fail
   - Mean time to recovery (MTTR): Time to fix production issues

4. **Velocity and Cycle Time Tracking**
   - Track work item completion time
   - Measure velocity (story points/week)
   - Identify slowdowns
   - Trend analysis

5. **Process Optimization Recommendations**
   - Analyze bottlenecks in workflow
   - Suggest process improvements
   - A/B test process changes
   - Measure impact of improvements

**Implementation:**

**Retrospective generator:**
```python
# src/solokit/improvement/retrospective.py
class RetrospectiveGenerator:
    def generate_retrospective(self, work_item):
        # Analyze work item history
        # Generate retrospective questions
        # Track patterns

    def suggest_improvements(self, retrospectives):
        # Analyze multiple retrospectives
        # Identify recurring issues
        # Suggest improvements
```

**Technical debt tracker:**
```python
# src/solokit/improvement/debt_tracker.py
class TechnicalDebtTracker:
    def identify_debt(self, codebase):
        # Detect code smells
        # Find TODOs and FIXMEs
        # Measure code complexity

    def calculate_debt_ratio(self):
        # Debt ratio = debt / total code
        # Track over time
```

**DORA metrics:**
```python
# src/solokit/improvement/dora_metrics.py
class DORAMetrics:
    def deployment_frequency(self):
        # Count deployments per day/week

    def lead_time(self):
        # Time from commit to production

    def change_failure_rate(self):
        # Failed deployments / total deployments

    def mean_time_to_recovery(self):
        # Average time to fix production issues
```

**Dashboard:**
```markdown
# /sk:status --project

## DORA Metrics
- Deployment Frequency: 3.2/week (↑ from 2.5)
- Lead Time: 2.3 days (↓ from 3.1 days)
- Change Failure Rate: 8% (target: <15%)
- MTTR: 1.2 hours (↓ from 2.5 hours)

## Velocity
- Current: 21 story points/week
- Trend: ↑ 15% over last month
- Average cycle time: 2.1 days

## Technical Debt
- Debt Ratio: 12% (target: <15%)
- High-priority debt items: 3
- Debt added this week: 2 items
- Debt resolved this week: 4 items

## Process Insights
- Bottleneck: Integration testing (avg 45 min)
- Suggestion: Parallelize integration tests
- Improvement opportunity: Automate deployment rollback
```

**Retrospective format:**
```markdown
# Retrospective: feature_user_authentication

**What Went Well:**
- TDD approach caught edge cases early
- Performance testing revealed bottleneck before production
- Documentation was comprehensive

**What Didn't Go Well:**
- Integration tests took 45 minutes (too slow)
- Had to refactor authentication logic twice
- Missing error handling for edge case

**Lessons Learned:**
- Always consider rate limiting from the start
- Test with realistic data volumes

**Action Items:**
- [ ] Speed up integration tests (parallelize)
- [ ] Add rate limiting to API design checklist
- [ ] Create authentication patterns library

**Metrics:**
- Cycle time: 3.2 days
- Test coverage: 92%
- Refactoring events: 2
```

**Files Affected:**

**New:**
- `src/solokit/improvement/retrospective.py` (will be created) - Retrospective generation
- `src/solokit/improvement/debt_tracker.py` (will be created) - Technical debt tracking
- `src/solokit/improvement/dora_metrics.py` (will be created) - DORA metrics calculation
- `src/solokit/improvement/velocity_tracker.py` (will be created) - Velocity tracking
- `src/solokit/improvement/bottleneck_analyzer.py` (will be created) - Bottleneck detection
- `.session/tracking/retrospectives/` (will be created) - Retrospective storage
- `.session/tracking/metrics.json` (will be created) - Metrics history
- Tests for improvement modules (will be created)

**Modified:**
- `src/solokit/session/complete.py` - Generate retrospective on work item completion
- `.claude/commands/status.md` - Add project-level status command
- `.session/tracking/work_items.json` - Add cycle time tracking

**Benefits:**

1. **Continuous learning**: Learn from every work item
2. **Debt management**: Technical debt tracked and managed
3. **Velocity visibility**: Know if improving or slowing down
4. **Data-driven decisions**: Optimize based on metrics
5. **Process improvement**: Systematically improve workflow
6. **Team-level insights**: Solo developer with team-level metrics

**Priority:** Medium - Important for long-term productivity

---

### Enhancement #33: Performance Testing Framework

**Status:** 🔵 IDENTIFIED

**Problem:**

Performance issues are discovered in production, not development:

1. **No performance baselines**: Don't know expected performance
2. **No load testing**: System untested under realistic load
3. **No regression detection**: Performance degradations unnoticed
4. **No bottleneck identification**: Slow endpoints unknown

**Example:**
```
Feature added → All tests pass ✓ → Deploy
                                 → Production: 5s response times ❌
                                 → Users complain
                                 → No baseline to compare
```

**Proposed Solution:**

Implement **comprehensive performance testing framework**:

1. **Performance Benchmarks in Specs**
   - Define performance requirements in work items
   - Example: "API must respond in <200ms at p95"
   - Enforce benchmarks before merge

2. **Automated Load Testing**
   - Run load tests in CI/CD
   - Tools: k6, wrk, Gatling, Locust
   - Test realistic traffic patterns

3. **Performance Regression Detection**
   - Compare results against baseline
   - Fail if performance degrades >10%
   - Track performance over time

4. **Bottleneck Identification**
   - Profile slow endpoints
   - Identify database query issues
   - Find N+1 queries, missing indexes

5. **Performance Baseline Tracking**
   - Store baselines in `.session/tracking/performance_baselines.json`
   - Update baselines when performance improves
   - Historical performance charts

**Implementation:**

**Performance spec in work item:**
```markdown
## Performance Requirements

**Response Time Targets:**
- GET /api/users: <100ms (p50), <200ms (p95)
- POST /api/orders: <500ms (p50), <1s (p95)
- Database queries: <50ms average

**Throughput Targets:**
- 1000 requests/second sustained
- 5000 concurrent users

**Resource Limits:**
- Memory: <512MB
- CPU: <50% average
```

**Load testing:**
```python
# src/solokit/testing/load_tester.py (will be created)
class LoadTester:
    def run_load_test(self, work_item):
        # Extract performance requirements
        # Run k6/wrk load test
        # Compare against baseline
        # Return pass/fail + metrics

    def detect_regression(self, current, baseline):
        # Compare metrics
        # Fail if >10% slower
```

**k6 test generation:**
```javascript
// tests/performance/api_test.js (auto-generated)
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp to 100 users
    { duration: '5m', target: 100 },  // Stay at 100
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<200'],  // 95% requests <200ms
  },
};

export default function() {
  let res = http.get('http://localhost:3000/api/users');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 200,
  });
}
```

**Baseline tracking:**
```json
// .session/tracking/performance_baselines.json
{
  "endpoints": {
    "/api/users": {
      "p50": 85,
      "p95": 180,
      "last_updated": "2025-10-29",
      "session": "session_015"
    }
  }
}
```

**Files Affected:**

**New:**
- `src/solokit/testing/load_tester.py` (will be created) - Load testing orchestration
- `src/solokit/testing/baseline_manager.py` (will be created) - Baseline tracking
- `src/solokit/testing/regression_detector.py` (will be created) - Regression detection
- `src/solokit/testing/profiler.py` (will be created) - Performance profiling
- `tests/performance/` (will be created) - Generated load tests
- `.session/tracking/performance_baselines.json` (will be created) - Baseline storage
- Tests for performance framework (will be created)

**Modified:**
- `src/solokit/quality/gates.py` - Add performance gates
- `src/solokit/work_items/spec_parser.py` - Parse performance requirements
- `.session/config.json` - Performance testing configuration
- CI/CD workflows - Add performance testing job

**Benefits:**

1. **Prevent regressions**: Catch slowdowns before production
2. **Meet SLAs**: Enforce performance requirements
3. **Capacity planning**: Know system limits
4. **Bottleneck identification**: Find and fix slow code
5. **Performance visibility**: Track performance over time

**Priority:** High - Performance issues cause production incidents

---

### Enhancement #34: Operations & Observability

**Status:** 🔵 IDENTIFIED

**Problem:**

After deployment, there's no operational support infrastructure:

1. **No health monitoring**: Can't tell if service is healthy
2. **No incident detection**: Issues discovered by users, not monitoring
3. **No performance dashboards**: Can't see system performance
4. **No capacity planning**: Don't know when to scale
5. **No alert management**: Alerts missing or too noisy

**Example:**
```
Deploy to production ✓ → Service running
                      → Database runs out of connections ❌
                      → No alert
                      → Users report errors
                      → 2 hours to discover issue
```

**Proposed Solution:**

Implement **comprehensive operations and observability infrastructure**:

1. **Health Check Monitoring**
   - Monitor `/health` endpoint continuously
   - Alert on failures
   - Track uptime metrics
   - Integration with UptimeRobot, Pingdom, Datadog

2. **Incident Detection and Response**
   - Automatic incident creation on alerts
   - Incident runbooks linked to alerts
   - PagerDuty/Opsgenie integration
   - Incident timeline and resolution tracking

3. **Performance Metrics Dashboards**
   - Real-time metrics visualization
   - Request rates, latency, error rates
   - Database performance metrics
   - Infrastructure metrics (CPU, memory, disk)
   - Tools: Grafana, Datadog, New Relic

4. **Capacity Planning**
   - Track resource usage trends
   - Predict when scaling needed
   - Cost optimization recommendations
   - Alert on approaching limits

5. **Intelligent Alerting**
   - Reduce alert noise (no alert fatigue)
   - Alert prioritization (critical vs warning)
   - Alert aggregation and correlation
   - Alert routing and escalation

**Implementation:**

**Health monitoring:**
```python
# src/solokit/operations/health_monitor.py
class HealthMonitor:
    def setup_monitoring(self, endpoints):
        # Configure health check monitoring
        # Set up alerts

    def check_health(self):
        # Poll health endpoints
        # Detect failures
        # Create incidents
```

**Incident management:**
```python
# src/solokit/operations/incident_manager.py
class IncidentManager:
    def create_incident(self, alert):
        # Create incident from alert
        # Link to runbook
        # Notify on-call

    def track_incident(self, incident_id):
        # Track resolution steps
        # Update timeline
```

**Dashboards:**
```yaml
# monitoring/dashboards/api_dashboard.yml
dashboard:
  title: "API Performance"
  panels:
    - title: "Request Rate"
      metric: "http_requests_total"
    - title: "Response Time (p95)"
      metric: "http_request_duration_p95"
    - title: "Error Rate"
      metric: "http_errors_total / http_requests_total"
    - title: "Database Connections"
      metric: "db_connections_active"
```

**Alert configuration:**
```yaml
# monitoring/alerts/api_alerts.yml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    severity: "critical"
    notify: ["email", "pagerduty"]

  - name: "Slow Response Time"
    condition: "p95_latency > 1s"
    severity: "warning"
    notify: ["email"]

  - name: "Database Connection Pool Exhausted"
    condition: "db_connections > 90%"
    severity: "critical"
    runbook: "docs/runbooks/db_connections.md"
```

**Files Affected:**

**New:**
- `src/solokit/operations/health_monitor.py` (will be created) - Health monitoring
- `src/solokit/operations/incident_manager.py` (will be created) - Incident management
- `src/solokit/operations/metrics_collector.py` (will be created) - Metrics collection
- `src/solokit/operations/capacity_planner.py` (will be created) - Capacity planning
- `src/solokit/operations/alert_manager.py` (will be created) - Alert management
- `monitoring/dashboards/` (will be created) - Dashboard configurations
- `monitoring/alerts/` (will be created) - Alert configurations
- `docs/runbooks/` (will be created) - Incident runbooks
- Tests for operations modules (will be created)

**Modified:**
- `.session/config.json` - Monitoring configuration
- `src/solokit/quality/gates.py` - Verify monitoring setup
- CI/CD workflows (will be created) - Deploy monitoring configs

**Benefits:**

1. **Proactive issue detection**: Find problems before users
2. **Faster incident response**: Automated incident creation
3. **Performance visibility**: Know system health at all times
4. **Capacity planning**: Scale before running out of resources
5. **Reduced alert fatigue**: Intelligent alerting
6. **Operational confidence**: Always know system status

**Priority:** High - Essential for production operations

---

### Enhancement #35: Project Progress Dashboard

**Status:** 🔵 IDENTIFIED

**Problem:**

No high-level view of project progress:

1. **No progress visibility**: Don't know how much is complete
2. **No milestone tracking**: Can't see milestone progress
3. **No velocity trends**: Don't know if on track

**Proposed Solution:**

Implement **project progress dashboard** showing overall status:

1. **Progress Visualization**
   - Work items by status (pie chart)
   - Completion percentage by milestone
   - Burndown charts

2. **Velocity Tracking**
   - Story points completed per week
   - Velocity trends
   - Projected completion dates

3. **Blocker Identification**
   - Blocked work items highlighted
   - Risk indicators

**Implementation:**

**Dashboard command:**
```bash
/sk:status --project
```

**Dashboard generator:**
```python
# src/solokit/visualization/dashboard.py (will be created)
class ProgressDashboard:
    def generate_dashboard(self):
        # Aggregate work item data from repository
        # Generate charts and metrics
        # Format as markdown
```

**Files Affected:**

**New:**
- `src/solokit/visualization/dashboard.py` (will be created) - Dashboard generation
- Tests for dashboard (will be created)

**Modified:**
- `.claude/commands/status.md` - Add project dashboard
- `src/solokit/work_items/repository.py` - Query work items for dashboard data

**Benefits:**

1. **Progress visibility**: Know project status at glance
2. **Milestone tracking**: See progress toward milestones
3. **Trend analysis**: Know if on track
4. **Risk awareness**: Blockers highlighted

**Priority:** Low - Nice to have, not critical

---

### Enhancement #36: Compliance & Regulatory Framework

**Status:** 🔵 IDENTIFIED

**Problem:**

Projects handling sensitive data must comply with various regulations, but there's no automated compliance tracking:

1. **No compliance validation**: GDPR, HIPAA, SOC2, PCI-DSS requirements not checked
2. **Data privacy gaps**: Personal data handling not tracked or validated
3. **Audit trail missing**: No comprehensive logging for compliance audits
4. **Manual compliance checks**: Time-consuming and error-prone manual verification
5. **Regulation changes**: No monitoring for updates to compliance requirements

**Example of compliance failure:**

```
Collect user data → Store in database → Deploy
                                      → GDPR audit ❌
                                      → Missing: consent tracking, data export, deletion
                                      → Fines and legal issues
                                      → Damage to reputation
```

**Proposed Solution:**

Implement **compliance and regulatory framework** for automated compliance tracking and validation:

1. **GDPR Compliance**
   - Data processing activity tracking
   - User consent management and audit trail
   - Right to access (data export) automation
   - Right to erasure (data deletion) automation
   - Data breach notification procedures
   - Privacy impact assessments

2. **HIPAA Compliance** (Healthcare)
   - PHI (Protected Health Information) identification and tracking
   - Access control and audit logging
   - Encryption at rest and in transit validation
   - Business Associate Agreement (BAA) tracking
   - Breach notification procedures
   - Security risk assessments

3. **SOC 2 Compliance**
   - Security controls validation
   - Availability monitoring
   - Processing integrity checks
   - Confidentiality verification
   - Privacy controls
   - Continuous control monitoring

4. **PCI-DSS Compliance** (Payment Card Industry)
   - Payment data identification and protection
   - Network security requirements
   - Access control validation
   - Regular security testing
   - Security policy enforcement

5. **Compliance Automation**
   - Automated compliance checks in CI/CD
   - Real-time compliance monitoring
   - Compliance dashboard and reporting
   - Evidence collection for audits
   - Automated remediation suggestions

**Implementation:**

**Compliance checker:**
```python
# src/solokit/compliance/compliance_checker.py (will be created)
class ComplianceChecker:
    def check_gdpr_compliance(self, codebase):
        # Verify GDPR requirements
        # - Consent tracking
        # - Data export functionality
        # - Data deletion functionality
        # - Data retention policies
        # - Privacy policy exists

    def check_hipaa_compliance(self, codebase):
        # Verify HIPAA requirements
        # - PHI encryption
        # - Access controls
        # - Audit logging
        # - BAA tracking

    def check_soc2_compliance(self, system):
        # Verify SOC 2 controls
        # - Security controls
        # - Availability metrics
        # - Processing integrity
        # - Confidentiality

    def check_pci_dss_compliance(self, codebase):
        # Verify PCI-DSS requirements
        # - Card data encryption
        # - Network segmentation
        # - Access controls
        # - Regular security testing
```

**GDPR automation:**
```python
# src/solokit/compliance/gdpr_automation.py (will be created)
class GDPRAutomation:
    def track_consent(self, user_id, consent_type):
        # Record user consent with timestamp
        # Track consent version
        # Provide consent audit trail

    def export_user_data(self, user_id):
        # Collect all user data across systems
        # Generate machine-readable export (JSON)
        # Include data processing activities log

    def delete_user_data(self, user_id):
        # Identify all user data locations
        # Delete or anonymize data
        # Maintain deletion audit trail
        # Verify deletion completeness

    def generate_privacy_impact_assessment(self, feature):
        # Identify personal data collected
        # Assess privacy risks
        # Propose mitigation measures
```

**Compliance configuration:**
```yaml
# .session/config.json (extended) or compliance_config.yml (will be created)
compliance:
  regulations:
    - gdpr
    - soc2
    # - hipaa  # Enable for healthcare
    # - pci_dss  # Enable for payment processing

  gdpr:
    enabled: true
    data_retention_days: 365
    consent_tracking: true
    require_privacy_policy: true
    require_data_export: true
    require_data_deletion: true

  soc2:
    enabled: true
    trust_service_criteria:
      - security
      - availability
      - processing_integrity
      - confidentiality
      - privacy
    control_monitoring: true

  hipaa:
    enabled: false
    phi_identification: true
    encryption_required: true
    audit_logging: true
    minimum_necessary_access: true

  pci_dss:
    enabled: false
    cardholder_data_environment: false
    tokenization_required: true
    security_testing_frequency: "quarterly"

  audit:
    evidence_collection: true
    evidence_storage: ".compliance/evidence/"
    audit_log_retention_days: 2555  # 7 years

  alerts:
    compliance_violations: ["email", "slack"]
    regulation_updates: ["email"]
```

**Compliance dashboard:**
```markdown
# /sk:compliance-status

## Compliance Overview
- GDPR: ✅ Compliant (98% - 1 minor issue)
- SOC 2: ⚠️ Partially Compliant (85% - 3 controls need attention)
- HIPAA: N/A (Not enabled)
- PCI-DSS: N/A (Not enabled)

## GDPR Compliance Details
✅ Consent tracking: Implemented
✅ Data export: Implemented (/api/user/export)
✅ Data deletion: Implemented (/api/user/delete)
✅ Privacy policy: Published and versioned
⚠️ Data retention: Policy defined but not enforced in code

## SOC 2 Compliance Details
✅ Security: Multi-factor auth, encryption, access controls
✅ Availability: 99.9% uptime, monitoring, alerting
⚠️ Processing Integrity: Missing transaction logging for audit
⚠️ Confidentiality: Some sensitive data not encrypted at rest
✅ Privacy: GDPR controls cover privacy requirements

## Action Items
1. Implement automated data retention enforcement (GDPR)
2. Add transaction audit logging (SOC 2 - Processing Integrity)
3. Encrypt sensitive configuration data at rest (SOC 2 - Confidentiality)

## Next Audit: 2025-12-01
## Last Audit: 2025-06-15 (Passed with minor findings)
```

**Commands:**
```bash
# Check compliance status
/sk:compliance-status [--regulation gdpr|hipaa|soc2|pci-dss]

# Generate compliance report
/sk:compliance-report --regulation gdpr --output pdf

# Run compliance checks
/sk:compliance-check --fix

# Generate privacy impact assessment
/sk:compliance-pia --feature "user-analytics"

# Export evidence for audit
/sk:compliance-evidence-export --period "2025-01-01..2025-12-31"
```

**Files Affected:**

**New:**
- `src/solokit/compliance/compliance_checker.py` (will be created) - Compliance validation
- `src/solokit/compliance/gdpr_automation.py` (will be created) - GDPR automation
- `src/solokit/compliance/hipaa_checker.py` (will be created) - HIPAA compliance
- `src/solokit/compliance/soc2_monitor.py` (will be created) - SOC 2 monitoring
- `src/solokit/compliance/pci_dss_validator.py` (will be created) - PCI-DSS validation
- `src/solokit/compliance/audit_trail.py` (will be created) - Audit logging
- `src/solokit/compliance/evidence_collector.py` (will be created) - Evidence management
- `.claude/commands/compliance-status.md` (will be created) - Compliance status command
- `.claude/commands/compliance-report.md` (will be created) - Report generation command
- `.claude/commands/compliance-check.md` (will be created) - Compliance validation command
- `.compliance/evidence/` (will be created) - Audit evidence storage
- `compliance_config.yml` (will be created) - Compliance configuration
- Tests for compliance modules (will be created)

**Modified:**
- `src/solokit/project/init.py` - Add compliance setup to project initialization
- `src/solokit/quality/gates.py` - Add compliance gates
- `.session/config.json` - Add compliance configuration
- CI/CD workflows (will be created) - Add compliance check jobs

**Benefits:**

1. **Automated compliance**: Continuous compliance monitoring and validation
2. **Audit readiness**: Evidence automatically collected for audits
3. **Risk mitigation**: Catch compliance issues before they become problems
4. **Regulation tracking**: Stay updated on compliance requirement changes
5. **Cost savings**: Reduce manual compliance effort and potential fines
6. **Customer trust**: Demonstrate commitment to data protection
7. **Legal protection**: Documented compliance procedures and audit trails
8. **Multi-regulation support**: Handle multiple compliance requirements simultaneously

**Priority:** High - Critical for regulated industries (healthcare, finance, e-commerce)

**Notes:**
- Compliance requirements vary by jurisdiction and industry
- Regular compliance audits recommended (quarterly or annually)
- Legal review recommended for compliance implementation
- Some regulations require third-party audits (e.g., SOC 2)
- Compliance is ongoing, not a one-time effort

---

### Enhancement #37: UAT & Stakeholder Workflow

**Status:** 🔵 IDENTIFIED

**Problem:**

No workflow for stakeholder feedback and user acceptance testing:

1. **No stakeholder involvement**: Stakeholders see features only at launch
2. **No UAT process**: No formal user acceptance testing
3. **No demo environments**: Difficult to show work in progress
4. **No approval workflow**: No sign-off before production

**Example:**
```
Feature built → Tests pass ✓ → Deploy to production
              → Stakeholder sees feature for first time
              → "This isn't what I wanted" ❌
              → Rework required
```

**Proposed Solution:**

Implement **UAT and stakeholder workflow** for feedback and approvals:

1. **Stakeholder Feedback Collection**
   - Create shareable demo links
   - Collect structured feedback
   - Track feedback status (addressed/rejected/pending)
   - Link feedback to work items

2. **UAT Test Case Generation**
   - Auto-generate UAT test cases from acceptance criteria
   - Provide test case checklist for stakeholders
   - Track UAT execution and results

3. **Demo/Preview Environments**
   - Auto-create preview environment per work item
   - Shareable URL for stakeholder review
   - Temporary environment (auto-deleted after merge)
   - Tools: Vercel preview deployments, Netlify deploy previews, PR environments

4. **Approval Workflow Before Production**
   - Require stakeholder approval before production deploy
   - Track approval status
   - Block production deployment without approval
   - Document approval decisions

**Implementation:**

**Demo environment:**
```python
# src/solokit/uat/demo_environment.py (will be created)
class DemoEnvironmentManager:
    def create_preview(self, work_item_id, branch):
        # Deploy branch to preview environment
        # Return preview URL

    def share_with_stakeholders(self, preview_url, stakeholders):
        # Send preview link to stakeholders
        # Include UAT test cases
```

**Feedback collection:**
```python
# src/solokit/uat/feedback_collector.py (will be created)
class FeedbackCollector:
    def create_feedback_form(self, work_item):
        # Generate feedback form
        # Include UAT test cases

    def collect_feedback(self, form_id):
        # Retrieve stakeholder feedback
        # Parse and structure feedback

    def link_to_work_item(self, feedback, work_item_id):
        # Associate feedback with work item
        # Create follow-up tasks if needed
```

**UAT test case generator:**
```python
# src/solokit/uat/test_case_generator.py (will be created)
class UATTestCaseGenerator:
    def generate_from_acceptance_criteria(self, work_item):
        # Parse acceptance criteria
        # Generate UAT test cases
        # Format as checklist
```

**Example UAT test cases:**
```markdown
# UAT Test Cases: User Authentication

## Test Case 1: Successful Login
**Given:** User has valid credentials
**When:** User enters email and password
**Then:**
- [ ] User is redirected to dashboard
- [ ] Welcome message displays user's name
- [ ] Session token is stored

## Test Case 2: Failed Login
**Given:** User enters invalid password
**When:** User submits login form
**Then:**
- [ ] Error message "Invalid credentials" displays
- [ ] User remains on login page
- [ ] No session token stored

## Test Case 3: Forgot Password
**Given:** User clicks "Forgot Password"
**When:** User enters email address
**Then:**
- [ ] Email with reset link sent
- [ ] Confirmation message displays
- [ ] Reset link expires in 1 hour
```

**Approval workflow:**
```python
# src/solokit/uat/approval_workflow.py (will be created)
class ApprovalWorkflow:
    def request_approval(self, work_item_id, stakeholders):
        # Send approval request
        # Include demo link and UAT results

    def check_approval_status(self, work_item_id):
        # Check if approved
        # Block deployment if not approved

    def record_approval(self, work_item_id, approver, decision):
        # Record approval decision
        # Document reasoning
```

**Files Affected:**

**New:**
- `src/solokit/uat/demo_environment.py` (will be created) - Demo environment management
- `src/solokit/uat/feedback_collector.py` (will be created) - Feedback collection
- `src/solokit/uat/test_case_generator.py` (will be created) - UAT test case generation
- `src/solokit/uat/approval_workflow.py` (will be created) - Approval management
- `.session/tracking/feedback/` (will be created) - Feedback storage
- `.session/tracking/approvals/` (will be created) - Approval records
- Tests for UAT modules (will be created)

**Modified:**
- `src/solokit/session/complete.py` - Request approval before production deployment
- `src/solokit/quality/gates.py` - Block deployment without approval
- `.session/config.json` - UAT and approval configuration

**Benefits:**

1. **Early feedback**: Stakeholders see features before production
2. **Reduce rework**: Catch misalignments before deployment
3. **Formal UAT**: Structured testing process
4. **Approval tracking**: Know what's approved for production
5. **Demo environments**: Easy to share work in progress
6. **Stakeholder confidence**: Involved throughout development

**Priority:** Medium - Important for stakeholder collaboration

---

### Enhancement #38: Cost & Resource Optimization

**Status:** 🔵 IDENTIFIED

**Problem:**

Cloud costs can spiral out of control without monitoring and optimization:

1. **No cost visibility**: Don't know where money is being spent
2. **Resource waste**: Over-provisioned or unused resources
3. **No budget alerts**: Costs exceed budget without warning
4. **Inefficient architecture**: Expensive architectures when cheaper alternatives exist
5. **No optimization recommendations**: Manual cost optimization is time-consuming

**Example of cost waste:**

```
Deploy application → Runs for 6 months
                   → Database over-provisioned (90% idle)
                   → Load balancer for single instance
                   → Storage full of old logs
                   → Monthly cost: $1,200
                   → Optimized cost could be: $300
                   → Wasted: $900/month = $10,800/year
```

**Proposed Solution:**

Implement **cost and resource optimization framework** for monitoring and reducing cloud costs:

1. **Cost Monitoring & Visibility**
   - Real-time cost tracking per service
   - Cost allocation by project/environment/feature
   - Cost trend analysis and forecasting
   - Budget tracking and alerts
   - Multi-cloud cost aggregation (AWS, GCP, Azure)

2. **Resource Utilization Analysis**
   - Identify under-utilized resources
   - Track resource usage patterns
   - Detect idle or unused resources
   - Analyze peak vs average utilization
   - Right-sizing recommendations

3. **Automated Cost Optimization**
   - Auto-scaling based on actual usage
   - Spot instance recommendations
   - Reserved instance analysis
   - Storage tier optimization (hot/warm/cold)
   - Automated cleanup of unused resources

4. **Cost Optimization Recommendations**
   - Alternative architecture suggestions
   - Service tier optimization
   - Region cost comparisons
   - Commitment discount opportunities
   - Open-source alternative suggestions

5. **Budget Management**
   - Set budget limits per environment
   - Automated alerts on threshold breach
   - Spending forecasts
   - Cost anomaly detection
   - Automated resource shutdown on budget exceeded

**Implementation:**

**Cost monitor:**
```python
# src/solokit/cost/cost_monitor.py (will be created)
class CostMonitor:
    def track_current_costs(self):
        # Query cloud provider billing APIs
        # Aggregate costs by service, region, project
        # Calculate daily/weekly/monthly costs

    def analyze_cost_trends(self):
        # Historical cost analysis
        # Identify cost spikes
        # Forecast future costs

    def alert_on_budget_breach(self, threshold):
        # Check if costs exceed budget
        # Send alerts to configured channels
        # Trigger automated actions if needed
```

**Resource optimizer:**
```python
# src/solokit/cost/resource_optimizer.py (will be created)
class ResourceOptimizer:
    def identify_underutilized_resources(self):
        # Analyze CPU, memory, disk usage
        # Identify resources with <30% utilization
        # Calculate potential savings

    def recommend_rightsizing(self, resource):
        # Analyze historical usage patterns
        # Recommend appropriate instance types
        # Calculate cost savings

    def find_idle_resources(self):
        # Identify stopped instances still incurring costs
        # Find unused load balancers, IPs, volumes
        # Estimate monthly waste

    def optimize_storage_tiers(self):
        # Analyze storage access patterns
        # Recommend tier migrations (hot → cold)
        # Calculate storage cost savings
```

**Cost optimization engine:**
```python
# src/solokit/cost/optimization_engine.py (will be created)
class CostOptimizationEngine:
    def recommend_spot_instances(self):
        # Identify workloads suitable for spot instances
        # Calculate potential savings (60-90% off)
        # Provide migration guide

    def analyze_reserved_instances(self):
        # Compare on-demand vs reserved pricing
        # Recommend reservation commitments
        # Calculate breakeven point

    def suggest_architectural_changes(self):
        # Identify expensive patterns
        # Suggest cheaper alternatives
        # Estimate implementation effort vs savings

    def recommend_service_alternatives(self):
        # Identify overpriced managed services
        # Suggest open-source alternatives
        # Calculate TCO comparison
```

**Cost configuration:**
```yaml
# .session/config.json (extended) or cost_config.yml (will be created)
cost_optimization:
  monitoring:
    enabled: true
    cloud_providers:
      - aws
      - gcp
      # - azure
    update_frequency: "hourly"

  budgets:
    development:
      monthly_limit: 500
      alert_thresholds: [50, 75, 90, 100]
    staging:
      monthly_limit: 200
      alert_thresholds: [75, 90, 100]
    production:
      monthly_limit: 2000
      alert_thresholds: [75, 90, 100]
      auto_shutdown: false  # Don't auto-shutdown production

  optimization:
    auto_rightsizing: false  # Recommend only, don't auto-apply
    auto_cleanup_idle: true  # Clean up stopped resources after 7 days
    storage_tier_optimization: true
    reserved_instance_analysis: true

  alerts:
    cost_alerts: ["email", "slack"]
    optimization_opportunities: ["email"]
    budget_breach: ["email", "pagerduty"]

  reporting:
    weekly_cost_report: true
    monthly_optimization_report: true
    savings_tracking: true
```

**Cost dashboard:**
```markdown
# /sk:cost-status

## Monthly Cost Summary
- **Current Month**: $1,247 / $2,000 budget (62%)
- **Last Month**: $1,189
- **Forecast**: $1,650 (18% under budget)
- **YoY Growth**: +12%

## Cost Breakdown by Service
- Compute (EC2/VMs): $687 (55%)
- Database (RDS/Cloud SQL): $312 (25%)
- Storage (S3/GCS): $127 (10%)
- Networking: $89 (7%)
- Other: $32 (3%)

## Cost by Environment
- Production: $987 (79%)
- Staging: $172 (14%)
- Development: $88 (7%)

## Optimization Opportunities
1. **Right-size database** - Current: db.m5.2xlarge ($562/mo), Recommended: db.m5.xlarge ($281/mo)
   - Savings: $281/month ($3,372/year)
   - Utilization: 28% average CPU

2. **Move logs to cold storage** - 500GB in hot storage ($115/mo), 450GB not accessed in 90 days
   - Savings: $90/month ($1,080/year)
   - Move 450GB to Glacier

3. **Use spot instances for batch jobs** - 5 instances running 24/7 ($365/mo)
   - Savings: $255/month ($3,060/year)
   - 70% cost reduction with spot

4. **Remove unused load balancer** - 1 ALB with no traffic ($23/mo)
   - Savings: $23/month ($276/year)

## Total Potential Savings: $649/month ($7,788/year)
## Current Optimization Score: 72/100
```

**Commands:**
```bash
# View cost status
/sk:cost-status [--environment prod|staging|dev]

# Analyze optimization opportunities
/sk:cost-optimize --analyze

# Generate cost report
/sk:cost-report --period "2025-01-01..2025-12-31" --output pdf

# Set budget alert
/sk:cost-budget-set --environment prod --limit 2000 --currency USD

# Forecast costs
/sk:cost-forecast --months 6
```

**Files Affected:**

**New:**
- `src/solokit/cost/cost_monitor.py` (will be created) - Cost tracking and monitoring
- `src/solokit/cost/resource_optimizer.py` (will be created) - Resource utilization analysis
- `src/solokit/cost/optimization_engine.py` (will be created) - Cost optimization recommendations
- `src/solokit/cost/budget_manager.py` (will be created) - Budget tracking and alerts
- `src/solokit/cost/cloud_provider_integrations/` (will be created) - AWS, GCP, Azure integrations
- `.claude/commands/cost-status.md` (will be created) - Cost status command
- `.claude/commands/cost-optimize.md` (will be created) - Optimization command
- `.claude/commands/cost-report.md` (will be created) - Cost reporting command
- `.claude/commands/cost-budget-set.md` (will be created) - Budget management command
- `cost_config.yml` (will be created) - Cost optimization configuration
- Tests for cost monitoring modules (will be created)

**Modified:**
- `src/solokit/project/init.py` - Add cost monitoring setup
- `.session/config.json` - Add cost optimization configuration
- CI/CD workflows (will be created) - Add cost check jobs

**Benefits:**

1. **Cost visibility**: Always know where money is spent
2. **Budget control**: Prevent cost overruns with alerts and limits
3. **Resource efficiency**: Eliminate waste from idle or over-provisioned resources
4. **Predictable costs**: Accurate forecasting for budget planning
5. **Automated savings**: Continuous optimization without manual effort
6. **Multi-cloud support**: Track costs across multiple cloud providers
7. **ROI tracking**: Measure savings from optimization efforts
8. **Financial accountability**: Cost allocation per project/team

**Priority:** Medium-High - Important for budget-conscious solo developers and startups

**Notes:**
- Requires cloud provider API credentials with billing access
- Cost data typically has 24-hour delay
- Aggressive optimization can impact performance (monitor carefully)
- Reserved instances require commitment (1-3 years)
- Consider business criticality before automated resource shutdown

---

### Enhancement #39: Automated Code Review

**Status:** 🔵 IDENTIFIED

**Problem:**

Code reviews are manual and time-consuming. Common issues missed:

1. **No automated review**: Every line requires human review
2. **Inconsistent feedback**: Review quality varies
3. **Common patterns missed**: Same issues repeat
4. **Security vulnerabilities**: May be overlooked in review

**Proposed Solution:**

Implement **AI-powered automated code review** that provides suggestions:

1. **Code Analysis**
   - Analyze code changes for common issues
   - Detect anti-patterns and code smells
   - Identify performance issues

2. **Best Practice Recommendations**
   - Suggest better patterns and approaches
   - Recommend idiomatic code
   - Link to documentation and examples

3. **Security Vulnerability Detection**
   - Identify security issues in code
   - Suggest secure alternatives
   - Link to security best practices

4. **Improvement Suggestions**
   - Suggest refactoring opportunities
   - Identify complexity issues
   - Recommend simplifications

**Implementation:**

**Code reviewer:**
```python
# src/solokit/review/code_reviewer.py (will be created)
class AutomatedCodeReviewer:
    def review_changes(self, file_changes):
        # Analyze code changes
        # Generate review comments

    def detect_issues(self, code):
        # Find anti-patterns, code smells

    def suggest_improvements(self, code):
        # Recommend better approaches
```

**Files Affected:**

**New:**
- `src/solokit/review/code_reviewer.py` (will be created) - Automated review
- `src/solokit/review/pattern_detector.py` (will be created) - Anti-pattern detection
- `src/solokit/review/security_analyzer.py` (will be created) - Security vulnerability detection
- Tests for code review modules (will be created)

**Modified:**
- `src/solokit/session/complete.py` - Run automated review before completion
- `src/solokit/quality/gates.py` - Add code review quality gate
- `.session/config.json` - Add code review configuration

**Benefits:**

1. **Faster reviews**: Automated feedback
2. **Consistent quality**: Every change reviewed
3. **Learning opportunity**: Suggestions improve skills
4. **Catch issues early**: Problems found before merge

**Priority:** Low - Nice to have, not critical

---

### Enhancement #40: React Performance Best Practices Integration

**Status:** 🔵 IDENTIFIED

**Problem:**

AI assistants writing React code often produce functional but suboptimal code with common performance anti-patterns:

1. **Async waterfalls**: Sequential data fetching when parallel is possible (e.g., awaiting data before early returns)
2. **Bundle size bloat**: Heavy client-side imports, missing code splitting, unnecessary dependencies
3. **Re-render storms**: Missing memoization, improper useEffect dependencies, cascading state updates
4. **Server/client misalignment**: Work done on client that should be server-side, or vice versa
5. **Framework anti-patterns**: Not leveraging Next.js App Router optimizations, RSC patterns

These issues are particularly problematic for solo developers who may not have the expertise to catch them in code review.

**Context:**

Vercel released `react-best-practices` (January 2026) - a structured knowledge base of **40+ rules across 8 priority categories**, specifically designed for AI agent consumption:

| Category | Prefix | Focus | Impact Level |
|----------|--------|-------|--------------|
| Eliminating Waterfalls | `async-*` | Sequential → parallel data fetching | CRITICAL |
| Bundle Size | `bundle-*` | Code splitting, tree shaking, lazy loading | CRITICAL |
| Server-Side Performance | `server-*` | RSC, streaming, edge runtime | HIGH |
| Client-Side Data Fetching | `client-*` | SWR, React Query, caching | HIGH |
| Re-render Optimization | `rerender-*` | Memoization, state management | MEDIUM-HIGH |
| Rendering Performance | `rendering-*` | Virtual DOM, reconciliation | MEDIUM |
| Advanced Patterns | `advanced-*` | Suspense, transitions, concurrent | LOW-MEDIUM |
| JavaScript Performance | `js-*` | Micro-optimizations | LOW |

Each rule includes:
- Impact level classification
- Problematic code example (what NOT to do)
- Correct code example (what TO do)
- Explanation of why it matters
- References to documentation

Source: https://vercel.com/blog/introducing-react-best-practices
Repository: https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices

**Applicable Solokit Stacks:**

Three of four Solokit stacks use React:
- **saas_t3** - Next.js 16 + React 19 + tRPC + Prisma
- **dashboard_refine** - Next.js 16 + Refine 5 + shadcn/ui
- **fullstack_nextjs** - Next.js 16 + React 19 + Prisma

Only **ml_ai_fastapi** (Python/FastAPI) is out of scope.

**Proposed Solution:**

Integrate React performance best practices into Solokit's quality and guidance system for React-based stacks:

**1. React Performance Guide Generation**

Generate a `REACT_PERFORMANCE_GUIDE.md` in `.session/guides/` during `sk init` for React stacks:

```python
# src/solokit/init/react_performance_guide.py (will be created)
class ReactPerformanceGuideGenerator:
    def __init__(self, quality_tier: int, stack: str):
        self.quality_tier = quality_tier
        self.stack = stack

    def generate(self) -> str:
        """Generate tier-appropriate React performance guide."""
        rules = self._get_rules_for_tier()
        return self._render_guide(rules)

    def _get_rules_for_tier(self) -> list[dict]:
        """Return rules appropriate for quality tier."""
        # Tier 1-2: CRITICAL + HIGH only
        # Tier 3: Add MEDIUM-HIGH, MEDIUM
        # Tier 4: Full coverage including advanced patterns
```

**2. Rule Curation by Quality Tier**

Map Vercel's impact levels to Solokit's quality tiers:

| Quality Tier | Included Rules | Rationale |
|--------------|----------------|-----------|
| Tier 1: Essential | CRITICAL only (async waterfalls, bundle size) | Focus on highest-impact issues |
| Tier 2: Standard | CRITICAL + HIGH (+ server, client) | Add server/client optimization |
| Tier 3: Comprehensive | All except LOW | Full performance coverage |
| Tier 4: Production-Ready | All 40+ rules | Complete best practices |

**3. Session Briefing Integration**

Include relevant React performance reminders in session briefings when working on React components:

```python
# src/solokit/session/briefing.py (modified)
def _get_react_performance_context(self, work_item: WorkItem) -> str:
    """Include React performance guidance for component work."""
    if self._is_react_component_work(work_item):
        return self._load_relevant_rules(work_item)
    return ""
```

**4. Anti-Pattern Detection Quality Gate (Optional)**

Add a quality gate checker that scans for known anti-patterns:

```python
# src/solokit/quality/checkers/react_performance_checker.py (will be created)
class ReactPerformanceChecker(BaseChecker):
    """Detect common React performance anti-patterns."""

    PATTERNS = {
        "cascading_useeffect": r"useEffect\([^)]+\)[\s\S]*?useEffect\(",
        "heavy_client_import": r"'use client'[\s\S]*?import.*from\s+['\"](?:lodash|moment)['\"]",
        "missing_suspense": r"async function.*Component",
        # ... more patterns
    }

    def check(self, files: list[str]) -> CheckResult:
        """Scan React files for anti-patterns."""
```

**5. Claude Code Integration**

Add React-specific guidance to `.claude/` for React stacks:

```markdown
# .claude/REACT_PERFORMANCE.md (will be created for React stacks)

## React Performance Guidelines

When writing React code in this project, follow these priority-ordered practices:

### CRITICAL: Eliminate Async Waterfalls
- Parallelize independent data fetches with Promise.all()
- Move awaits inside conditionals when early returns exist
- Use React Server Components for data fetching when possible

### CRITICAL: Minimize Bundle Size
- Use dynamic imports for heavy components: `const Chart = dynamic(() => import('./Chart'))`
- Prefer server components (no 'use client' unless needed)
- Tree-shake imports: `import { specific } from 'lib'` not `import * from 'lib'`

[... more rules based on quality tier ...]
```

**6. Stack-Specific Adaptations**

Different React stacks have different patterns:

| Stack | Special Considerations |
|-------|----------------------|
| saas_t3 | tRPC batching, Prisma query optimization |
| dashboard_refine | Refine data provider caching, table virtualization |
| fullstack_nextjs | Server Actions, streaming, Partial Prerendering |

**Implementation:**

**Phase 1: Guide Generation**
```python
# src/solokit/init/react_performance_guide.py
class ReactPerformanceGuideGenerator:
    RULES_BY_IMPACT = {
        "CRITICAL": [
            {
                "id": "async-parallel-fetching",
                "title": "Parallelize Independent Data Fetches",
                "problem": "Sequential awaits for independent data",
                "solution": "Use Promise.all() for parallel fetching",
                "example_bad": "const a = await fetchA(); const b = await fetchB();",
                "example_good": "const [a, b] = await Promise.all([fetchA(), fetchB()]);",
            },
            {
                "id": "async-conditional-await",
                "title": "Move Awaits Inside Conditionals",
                "problem": "Awaiting data before early return checks",
                "solution": "Check conditions before awaiting when possible",
            },
            {
                "id": "bundle-dynamic-imports",
                "title": "Use Dynamic Imports for Heavy Components",
                "problem": "Large components in initial bundle",
                "solution": "Use next/dynamic or React.lazy for code splitting",
            },
            # ... more CRITICAL rules
        ],
        "HIGH": [
            {
                "id": "server-rsc-data-fetching",
                "title": "Fetch Data in Server Components",
                "problem": "Client-side data fetching with useEffect",
                "solution": "Use async Server Components for initial data",
            },
            # ... more HIGH rules
        ],
        # ... MEDIUM-HIGH, MEDIUM, LOW-MEDIUM, LOW
    }

    def generate_for_tier(self, tier: int) -> str:
        """Generate guide content for specified quality tier."""
        included_impacts = self._get_impacts_for_tier(tier)
        rules = []
        for impact in included_impacts:
            rules.extend(self.RULES_BY_IMPACT.get(impact, []))
        return self._render_markdown(rules)

    def _get_impacts_for_tier(self, tier: int) -> list[str]:
        if tier == 1:
            return ["CRITICAL"]
        elif tier == 2:
            return ["CRITICAL", "HIGH"]
        elif tier == 3:
            return ["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM"]
        else:  # tier 4
            return ["CRITICAL", "HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW-MEDIUM", "LOW"]
```

**Phase 2: Init Integration**
```python
# src/solokit/init/orchestrator.py (modified)
def _setup_guides(self, stack: str, tier: int):
    """Generate development guides for the project."""
    # Existing guide generation...

    # Add React performance guide for React stacks
    if stack in ["saas_t3", "dashboard_refine", "fullstack_nextjs"]:
        react_guide = ReactPerformanceGuideGenerator(tier, stack)
        guide_content = react_guide.generate()
        self._write_guide(".session/guides/REACT_PERFORMANCE_GUIDE.md", guide_content)
```

**Phase 3: Briefing Integration**
```python
# src/solokit/session/briefing.py (modified)
def _build_briefing(self, work_item: WorkItem) -> str:
    briefing_parts = [
        self._get_header(work_item),
        self._get_spec_summary(work_item),
        self._get_relevant_learnings(work_item),
        self._get_relevant_guides(work_item),  # NEW: includes React perf guide
        self._get_git_context(),
    ]
    return "\n\n".join(briefing_parts)

def _get_relevant_guides(self, work_item: WorkItem) -> str:
    """Include relevant guide excerpts based on work item context."""
    guides = []

    # Include React performance tips for component work
    if self._involves_react_components(work_item):
        react_guide = self._load_guide("REACT_PERFORMANCE_GUIDE.md")
        if react_guide:
            # Include top 5 most relevant rules based on work item
            guides.append(self._extract_relevant_rules(react_guide, work_item))

    return "\n".join(guides)
```

**Phase 4: Quality Gate (Optional)**
```python
# src/solokit/quality/checkers/react_performance_checker.py
from solokit.quality.checkers.base import BaseChecker, CheckResult

class ReactPerformanceChecker(BaseChecker):
    """Check for common React performance anti-patterns."""

    name = "react-performance"
    description = "React performance anti-pattern detection"

    # Regex patterns for common anti-patterns
    ANTI_PATTERNS = {
        "sequential-await": {
            "pattern": r"const\s+\w+\s*=\s*await\s+\w+\([^)]*\);\s*\n\s*const\s+\w+\s*=\s*await",
            "message": "Consider using Promise.all() for parallel data fetching",
            "severity": "warning",
            "impact": "CRITICAL",
        },
        "use-client-with-heavy-import": {
            "pattern": r"['\"]use client['\"][\s\S]{0,500}import.*from\s+['\"](?:lodash|moment|date-fns)['\"]",
            "message": "Heavy library imported in client component - consider server component or dynamic import",
            "severity": "warning",
            "impact": "CRITICAL",
        },
        "cascading-useeffect": {
            "pattern": r"useEffect\(\s*\(\)\s*=>\s*\{[^}]+set\w+\([^)]+\)[^}]+\}\s*,\s*\[[^\]]+\]\s*\)[\s\S]{0,200}useEffect",
            "message": "Cascading useEffect calls detected - consider combining or using derived state",
            "severity": "info",
            "impact": "MEDIUM-HIGH",
        },
    }

    def check(self, context: CheckContext) -> CheckResult:
        """Scan React/TSX files for anti-patterns."""
        issues = []
        react_files = self._find_react_files(context.project_root)

        for file_path in react_files:
            content = self._read_file(file_path)
            for pattern_name, pattern_info in self.ANTI_PATTERNS.items():
                if re.search(pattern_info["pattern"], content):
                    issues.append({
                        "file": file_path,
                        "pattern": pattern_name,
                        "message": pattern_info["message"],
                        "severity": pattern_info["severity"],
                    })

        return CheckResult(
            passed=len([i for i in issues if i["severity"] == "error"]) == 0,
            issues=issues,
            summary=f"Found {len(issues)} potential React performance issues",
        )
```

**Files Affected:**

**New:**
- `src/solokit/init/react_performance_guide.py` - Guide generator with curated rules
- `src/solokit/quality/checkers/react_performance_checker.py` - Anti-pattern detector
- `src/solokit/templates/saas_t3/base/.claude/REACT_PERFORMANCE.md` - Claude guidance
- `src/solokit/templates/dashboard_refine/base/.claude/REACT_PERFORMANCE.md` - Claude guidance
- `src/solokit/templates/fullstack_nextjs/base/.claude/REACT_PERFORMANCE.md` - Claude guidance
- `src/solokit/data/react_performance_rules.py` - Curated rule definitions
- Tests for React performance modules

**Modified:**
- `src/solokit/init/orchestrator.py` - Add React guide generation for React stacks
- `src/solokit/session/briefing.py` - Include React performance context in briefings
- `src/solokit/quality/gates.py` - Register React performance checker
- `.session/config.json` schema - Add react_performance checker config
- Template `package.json` files - No changes (no runtime dependencies)

**Testing Requirements:**

1. **Unit Tests:**
   - Guide generator produces correct rules for each tier
   - Anti-pattern regex patterns detect known bad patterns
   - Stack detection correctly identifies React stacks

2. **Integration Tests:**
   - `sk init` generates REACT_PERFORMANCE_GUIDE.md for React stacks
   - `sk init` does NOT generate guide for ml_ai_fastapi
   - Session briefings include React guidance when appropriate
   - Quality gate reports anti-patterns correctly

3. **E2E Tests:**
   - Full init → start → develop → end cycle with React performance guidance
   - Verify guide content matches quality tier selection

**Benefits:**

1. **Proactive quality**: AI writes better React code from the start
2. **Prioritized guidance**: Focus on highest-impact issues first (waterfalls, bundle size)
3. **Tier-appropriate**: Don't overwhelm beginners with advanced patterns
4. **Self-contained**: No external dependencies, rules bundled with Solokit
5. **Stack-aware**: Guidance tailored to specific React stack (T3, Refine, Next.js)
6. **Continuous improvement**: Rules can be updated with Solokit releases
7. **Learning capture**: Developers learn best practices through usage

**Priority:** Medium-High - Significant quality improvement for React stacks (75% of templates)

**Notes:**
- Rules should be curated from Vercel's repository, not copied verbatim (licensing)
- Consider periodic updates as React/Next.js evolves
- Anti-pattern checker should be non-blocking by default (warnings, not errors)
- May want to add `/sk:react-audit` command in future for on-demand review
- Integration with Enhancement #29 (Frontend Quality & Design System Compliance)

**References:**
- Vercel Blog: https://vercel.com/blog/introducing-react-best-practices
- Agent Skills Repo: https://github.com/vercel-labs/agent-skills
- React Performance Docs: https://react.dev/learn/render-and-commit

---
