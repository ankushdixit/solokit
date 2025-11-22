---
description: Initialize a new Session-Driven Development project with template-based setup
---

# Template-Based Project Initialization

Initialize a new Solokit project with guided template selection for production-ready setup.

## Interactive Template Selection (4 Questions)

Use the **AskUserQuestion tool** to collect all configuration:

### Question 1: Project Category

**Question**: "What type of project are you building?"
**Header**: "Category"
**Multi-Select**: false

**Options**:

1. **Label**: "SaaS Application"
   **Description**: "T3 stack with Next.js, Prisma, tRPC - Full-featured web apps with auth, payments, multi-tenancy"

2. **Label**: "ML/AI Tooling"
   **Description**: "FastAPI with Python ML libraries - Machine learning APIs, data pipelines, model serving"

3. **Label**: "Internal Dashboard"
   **Description**: "Refine with React admin framework - Admin panels, analytics dashboards, internal tools"

4. **Label**: "Full-Stack Product"
   **Description**: "Next.js with full-stack capabilities - General purpose web applications"

---

### Question 2: Quality Gates Tier

**Question**: "What level of quality gates do you want?"
**Header**: "Quality Tier"
**Multi-Select**: false

**Options**:

1. **Label**: "Essential"
   **Description**: "Linting, formatting, type-check, basic tests (fastest setup)"

2. **Label**: "Standard"
   **Description**: "+ Git hooks (Husky), security scanning (recommended for most projects)"

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

### Question 4: Additional Options

**Question**: "Select additional features to include:"
**Header**: "Add-ons"
**Multi-Select**: true

**Options** (all optional, user can select multiple):

1. **Label**: "GitHub Actions CI/CD"
   **Description**: "Automated testing and deployment workflows"

2. **Label**: "Docker Support"
   **Description**: "Containerization with docker-compose"

3. **Label**: "Environment Templates"
   **Description**: ".env files and .editorconfig for all editors"

---

## Run Initialization

After collecting all answers via AskUserQuestion, run the Python CLI with the appropriate arguments:

```bash
sk init --template=<category> --tier=<tier> --coverage=<coverage> --options=<options>
```

**Mapping user selections to CLI arguments:**

**Category mapping:**

- "SaaS Application" → `--template=saas_t3`
- "ML/AI Tooling" → `--template=ml_ai_fastapi`
- "Internal Dashboard" → `--template=dashboard_refine`
- "Full-Stack Product" → `--template=fullstack_nextjs`

**Tier mapping:**

- "Essential" → `--tier=tier-1-essential`
- "Standard" → `--tier=tier-2-standard`
- "Comprehensive" → `--tier=tier-3-comprehensive`
- "Production-Ready" → `--tier=tier-4-production`

**Coverage mapping:**

- "Basic (60%)" → `--coverage=60`
- "Standard (80%)" → `--coverage=80`
- "Strict (90%)" → `--coverage=90`
- Custom value from "Type something" → `--coverage=<value>`

**Options mapping:**

- "GitHub Actions CI/CD" → `ci_cd`
- "Docker Support" → `docker`
- "Environment Templates" → `env_templates`

Combine multiple options with commas: `--options=ci_cd,docker,env_templates`

**Important:** The Python command handles ALL validation and setup deterministically:

- Pre-flight checks (blank project, git init, environment validation)
- Template installation
- Dependency installation
- All file generation

---

## After Successful Init

Show the user the success output from the script, then explain:

"Your project is now set up with production-ready tooling!

**Next steps:**

1. Review `README.md` for stack-specific getting started guide
2. Create your first work item: `/sk:work-new`
3. Start working: `/sk:start`"

---

## Error Handling

If the `sk init` command fails, show the error message from the CLI output. The Python script provides clear error messages for common issues:

- Already initialized
- Not a blank project
- Missing environment requirements
- etc.

Do not retry automatically - let the user address the issue and run `/sk:init` again.
