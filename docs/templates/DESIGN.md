# Template-Based Project Initialization - Complete Design

## 1. Overview

Transform `/sk:init` into a guided template-based initialization system that sets up production-ready projects in <1 minute with complete tooling, quality gates, and CI/CD from day one.

**Stack Selection**: Four carefully chosen stacks cover the most common development scenarios: SaaS applications (T3 Stack for type-safe APIs), ML/AI tooling (FastAPI for Python's ML ecosystem), internal dashboards (Refine for rapid CRUD), and general full-stack products (Next.js for maximum flexibility). Each stack provides strong typing for AI assistant effectiveness and proven production-readiness.

## 2. Interactive Flow Design

### 2.1 Pre-Flight Validation

**Performed BEFORE showing any interactive UI to user**:

1. **Check if already initialized**
   - Verify `.session/` directory does NOT exist
   - If exists: Error message "Project already initialized with Solokit" and exit

2. **Check if project is blank**
   - Verify no configuration files exist (package.json, tsconfig.json, pyproject.toml, etc.)
   - Verify no source directories exist (src/, app/, components/, etc.)
   - Allowed files: .git, .gitignore, README.md, LICENSE, .gitattributes, docs/
   - If not blank: Error message with list of blocking files and exit

3. **Initialize/verify git repository**
   - Check if .git directory exists
   - If not: Initialize git with `git init`
   - Verify git is functional

4. **Validate AND auto-update environment**
   - **Node.js check** (for Next.js stacks):
     - Check Node.js version >= 18.0.0
     - If not available: Attempt auto-install using nvm (if available)
     - If auto-install fails: Error message with installation instructions and exit

   - **Python check** (for ML/AI stack):
     - Check Python version >= 3.11.0
     - If system Python < 3.11: Check for python3.11 binary
     - If python3.11 found: Use it for virtual environment creation
     - If not found: Attempt auto-install using pyenv (if available)
     - If auto-install fails: Error message with installation instructions and exit

**Error Messages** should be helpful and actionable:
```
ERROR: Project already initialized
Found existing .session/ directory.

This project has already been initialized with Solokit.

Solutions:
  1. Use existing .session/ structure
  2. Remove .session/ to reinitialize (CAUTION: loses all session data)
```

```
ERROR: Project directory is not blank
Found existing project files:
  - package.json (Node.js project detected)
  - src/ directory

Solokit initialization must be run in a blank project directory.

Solutions:
  1. Create a new directory: mkdir my-project && cd my-project
  2. Clone an empty repo: git clone <repo-url> && cd <repo>
```

```
ERROR: Python 3.11+ required for ML/AI stack
Found: Python 3.9.7

The ML/AI FastAPI stack requires Python 3.11 or higher.

Installation:
  macOS:    brew install python@3.11
  Ubuntu:   sudo apt install python3.11 python3.11-venv

After installation, python3.11 binary will be auto-detected.
```

### 2.2 Four-Question Interactive Flow

**All questions use AskUserQuestion tool** (consistent with /start, /work-new, /end commands):

#### Step 1: Project Category (Single-Select)

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

**Note**: "Type something" automatically added by AskUserQuestion for custom input (though not expected for this question)

---

#### Step 2: Quality Gates Tier (Single-Select)

**Question**: "What level of quality gates do you want?"
**Header**: "Quality Tier"
**Multi-Select**: false

**Options**:
1. **Label**: "Essential"
   **Description**: "Linting, formatting, type-check, basic tests (fastest setup)"

2. **Label**: "Standard"
   **Description**: "+ Type checking, git hooks (Husky) (recommended for most projects)"

3. **Label**: "Comprehensive"
   **Description**: "+ Coverage reports, integration tests (production-ready)"

4. **Label**: "Production-Ready"
   **Description**: "+ Security scanning, performance monitoring (enterprise-grade)"

**Tier Details** - Based on all planned enhancements, here are the 4 tiers:

#### Tier 1: Essential (Current + Minimal)
**Best for**: Prototypes, MVPs, small internal tools

**Includes**:
- ✓ Linting (ESLint for JS/TS, Ruff for Python)
- ✓ Formatting (Prettier for JS/TS, Ruff for Python)
- ✓ Type checking (TypeScript strict mode, Pyright/mypy)
- ✓ Basic unit tests (Jest/Vitest for JS/TS, pytest for Python)
- ✓ Test coverage minimum (80%)

**Related Enhancements**: Current implementation

---

#### Tier 2: Standard (Essential + Security Foundation)
**Best for**: Production applications, funded startups, small teams

**Includes All Essential Plus**:
- ✓ **Security** (Enhancement #16 - Pre-Merge Security Gates)
  - Secret scanning (git-secrets, detect-secrets)
  - Dependency vulnerability scanning (npm audit, safety/pip-audit)
  - Basic SAST (ESLint security rules, bandit)
  - License compliance checking
  
- ✓ **Git Hooks** (Husky + lint-staged + security checks)
- ✓ **Git Workflow Integration**
  - Automatic branch naming
  - Commit message validation
  - Co-authored-by Claude in commits

**Related Enhancements**: #16 (Pre-Merge Security Gates - partial)

---

#### Tier 3: Comprehensive (Standard + Advanced Quality + Testing)
**Best for**: Production SaaS, growing teams, mission-critical apps

**Includes All Standard Plus**:
- ✓ **Advanced Code Quality** (Enhancement #19)
  - Cyclomatic complexity enforcement (max 10)
  - Code duplication detection (jscpd for JS/TS, radon for Python)
  - Dead code detection (ts-prune, vulture)
  - Type coverage enforcement (typescript-coverage-report, type-coverage for Python)
  - Cognitive complexity limits
  
- ✓ **Test Quality Gates** (Enhancement #18)
  - Critical path coverage >90%
  - Mutation testing (Stryker for JS/TS, mutmut for Python) >75% score
  - Integration tests required
  - E2E tests for user-facing features (Playwright)
  - Performance regression tests (benchmarking)
  - Flakiness detection
  
- ✓ **Full Security Suite** (Complete Enhancement #16)
  - Supply chain security (Snyk, Socket.dev)
  - Full SAST (SonarQube/SonarCloud, semgrep)
  - Container scanning (if Docker included)
  
- ✓ **Frontend Quality** (Enhancement #29 - for applicable stacks)
  - Accessibility testing (axe-core, pa11y)
  - Visual regression (Chromatic, Percy)
  - Bundle size budgets
  - Lighthouse CI for performance

**Related Enhancements**: #16 (complete), #18, #19, #29

---

#### Tier 4: Production-Ready (Comprehensive + Operations + Deployment)
**Best for**: Enterprise applications, regulated industries, high-scale production

**Includes All Comprehensive Plus**:
- ✓ **Production Readiness** (Enhancement #20)
  - Health check endpoints
  - Metrics and observability (Prometheus, OpenTelemetry)
  - Error tracking integration (Sentry)
  - Structured logging (winston, pino for JS/TS, structlog for Python)
  - Database migration safety checks
  - Configuration management validation
  
- ✓ **Deployment Safety** (Enhancement #21)
  - Deployment dry-run
  - Breaking change detection (OpenAPI diff, API versioning checks)
  - Rollback testing
  - Canary deployment support
  - Smoke tests after deployment
  
- ✓ **Performance Testing** (Enhancement #33)
  - Performance benchmarks in specs
  - Automated load testing (k6, Artillery)
  - Performance regression detection
  - Bottleneck identification
  - Baseline tracking
  
- ✓ **Continuous Security Monitoring** (Enhancement #17)
  - Scheduled CVE scanning
  - Dependency update monitoring
  - Security advisory notifications
  - Automatic security work item creation
  
- ✓ **Compliance Framework** (Enhancement #36 - if applicable)
  - GDPR compliance tooling
  - HIPAA compliance checks
  - SOC 2 controls monitoring
  - Audit trail generation

**Related Enhancements**: #16, #17, #18, #19, #20, #21, #29, #33, #36

---

#### Step 3: Testing Coverage Target (Single-Select)

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

**Note**: "Type something" automatically added by AskUserQuestion for custom percentages (e.g., user can type "75")

**Coverage applies to**:
- Line coverage
- Branch coverage
- Function coverage
- Statement coverage

---

#### Step 4: Additional Options (Multi-Select)

**Question**: "Select additional features to include:"
**Header**: "Add-ons"
**Multi-Select**: true

**Options** (all optional, multi-select):
1. **Label**: "GitHub Actions CI/CD"
   **Description**: "Automated testing and deployment workflows"

2. **Label**: "Docker Support"
   **Description**: "Containerization with docker-compose"

3. **Label**: "Environment Templates"
   **Description**: ".env files and .editorconfig for all editors"

**Note**: "Type something" automatically added by AskUserQuestion for custom input

**What "Environment Templates" includes**:
- `.editorconfig` - Generic editor configuration (works with all editors)
- `.env.example` - Stack-specific environment variables template
- `.env.local.example` - Local development environment template
- **NO IDE-specific configs** - .editorconfig is universal

---

## 3. Blank Project Detection

### 3.1 Current Behavior
Currently, init can be run on any project and will:
- Detect existing project type
- Add/update package files
- Create .session structure

### 3.2 New Required Behavior
Init should **ONLY work in completely blank projects** to avoid conflicts and ensure clean setup.

### 3.3 Detection Logic

```python
def is_blank_project() -> bool:
    """
    Check if the current directory is blank enough for initialization.
    
    Returns:
        True if blank/safe to initialize, False otherwise
    """
    project_root = Path.cwd()
    
    # Check for existing project files that indicate non-blank project
    blocking_files = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
        "tsconfig.json",
        ".eslintrc.js",
        ".eslintrc.json",
        ".prettierrc",
        "jest.config.js",
        "vitest.config.ts",
        ".session"
    ]
    
    # Check for blocking files
    for file in blocking_files:
        if (project_root / file).exists():
            return False
    
    # Check for source directories (strong signal of existing project)
    blocking_dirs = [
        "src",
        "app",
        "pages",
        "components",
        "lib",
        "utils",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__"
    ]
    
    for dir_name in blocking_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            # Check if directory has actual content (not just .gitkeep)
            contents = list(dir_path.iterdir())
            if contents and not (len(contents) == 1 and contents[0].name == ".gitkeep"):
                return False
    
    # Allowed files that don't block initialization
    allowed_files = [
        ".git",
        ".gitignore",
        "README.md",
        "LICENSE",
        ".gitattributes"
    ]
    
    # Project is blank if only allowed files exist
    return True


def check_blank_project_or_exit() -> None:
    """
    Check if project is blank, exit with error message if not.
    
    Raises:
        ValidationError: If project is not blank with helpful error message
    """
    if not is_blank_project():
        existing_files = []
        
        # Build helpful list of what was found
        project_root = Path.cwd()
        if (project_root / "package.json").exists():
            existing_files.append("package.json (Node.js project detected)")
        if (project_root / "pyproject.toml").exists():
            existing_files.append("pyproject.toml (Python project detected)")
        if (project_root / ".session").exists():
            existing_files.append(".session (Solokit already initialized)")
        if (project_root / "src").exists():
            existing_files.append("src/ directory")
        
        error_msg = (
            "Cannot initialize: Project directory is not blank.\n\n"
            "Found existing project files:\n"
            + "\n".join(f"  - {f}" for f in existing_files)
            + "\n\n"
            "Solokit initialization must be run in a blank project directory to avoid conflicts.\n\n"
            "Solutions:\n"
            "  1. Create a new directory: mkdir my-project && cd my-project\n"
            "  2. Clone an empty repo: git clone <repo-url> && cd <repo>\n"
            "  3. Clear existing project (CAUTION): rm -rf * .* (except .git if you want to keep it)\n"
        )
        
        raise ValidationError(
            message=error_msg,
            code=ErrorCode.PROJECT_NOT_BLANK,
            context={"existing_files": existing_files},
            remediation="Use a blank directory for initialization"
        )
```

---

## 4. Installation Process

### 4.1 Deterministic Installation with Python Scripts

All installation steps are executed via deterministic Python scripts located in `src/solokit/init/`:

| Script | Purpose | Responsibilities |
|--------|---------|------------------|
| `git_setup.py` | Git initialization | Check/init repo, verify clean state |
| `environment_validator.py` | Environment validation & update | Check versions, attempt pyenv/nvm install |
| `template_installer.py` | Template installation | Copy files from templates/, apply selections |
| `readme_generator.py` | README generation | Create README with project info |
| `config_generator.py` | Config file generation | Create .eslintrc, .prettierrc, jest.config, etc. |
| `dependency_installer.py` | Dependency installation | Run npm/pip install with exact versions |
| `docs_structure.py` | Docs directory creation | Create docs/ structure |
| `code_generator.py` | Minimal code generation | Create basic source files |
| `test_generator.py` | Smoke test generation | Create initial test files |
| `env_generator.py` | Environment file generation | Create .env.example, .env.local.example |
| `session_structure.py` | Session initialization | Create .session/ directory |
| `initial_scans.py` | Initial scans | Generate stack.txt, tree.txt |
| `git_hooks.py` | Git hooks installation | Install pre-commit, commit-msg |
| `gitignore_updater.py` | .gitignore updates | Add stack-specific entries |
| `initial_commit.py` | Initial commit creation | Commit all files |

**Master Orchestrator**: `src/solokit/project/init.py` (updated to use AskUserQuestion and call all scripts)

### 4.2 Installation Commands (Exact Commands from Fresh Build Testing)

**All commands tested and validated on 2025-11-07**. See `src/solokit/templates/stack-versions.yaml` for exact versions.

#### SaaS T3 Stack Installation

**Pre-Installation**:
```bash
# Auto-answer create-next-app prompts (No to React Compiler and Turbopack)
(yes "n" | npx create-next-app@latest <project-name> --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*")
```

**Tier 1: Base + Essential**:
```bash
npm install next@16.0.7 react@19.2.1 react-dom@19.2.1 \
  @trpc/server@11.7.1 @trpc/client@11.7.1 @trpc/react-query@11.7.1 @trpc/next@11.7.1 \
  @tanstack/react-query@5.90.7 \
  prisma@6.19.0 @prisma/client@6.19.0 \
  zod@4.1.12 \
  tailwindcss@4.1.17 @tailwindcss/postcss@4.1.17 postcss@8.4.49 autoprefixer@10.4.20

npm install --save-dev eslint@9.39.1 eslint-config-next@16.0.7 \
  @typescript-eslint/parser@8.46.3 @typescript-eslint/eslint-plugin@8.46.3 \
  prettier@3.6.2 \
  jest@30.2.0 @types/jest@30.0.0 ts-jest@29.4.5 jest-environment-jsdom@30.2.0 \
  @testing-library/react@16.3.0 @testing-library/jest-dom@6.9.1
```

**Tier 2: Standard**:
```bash
npm install --save-dev husky@9.1.7 lint-staged@16.2.6
```

**Tier 3: Comprehensive**:
```bash
npm install --save-dev jscpd@4.0.5 ts-prune@0.10.3 type-coverage@2.29.7 \
  @stryker-mutator/core@9.3.0 @stryker-mutator/jest-runner@9.3.0 \
  playwright@1.56.1 @axe-core/playwright@4.11.0 \
  eslint-plugin-jest-dom@5.5.0 eslint-plugin-testing-library@7.13.3
```

**Tier 4: Production-Ready** (CRITICAL: patch-package MUST be installed FIRST):
```bash
# Step 1: Install patch-package and other dev dependencies FIRST
npm install --save-dev patch-package @next/bundle-analyzer@latest @lhci/cli@latest dotenv-cli@latest

# Step 2: Install Sentry and analytics (requires patch-package)
npm install @sentry/nextjs@latest @vercel/analytics@latest
```

**Validation**: `npm run build` (should complete in ~1.2 seconds with 0 errors)

#### ML/AI FastAPI Stack Installation

**Pre-Installation** (CRITICAL):
```bash
# Check Python version (MUST be 3.11+)
python3 --version

# If < 3.11, locate Python 3.11
which python3.11

# Create virtual environment with Python 3.11+
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

**Tier 1: Base + Essential**:
```bash
pip install fastapi==0.115.6 "uvicorn[standard]==0.34.0" pydantic==2.12.4 \
  sqlmodel==0.0.25 sqlalchemy==2.0.37 psycopg2-binary==2.9.10 alembic==1.14.0 \
  pytest==8.3.4 pytest-cov==6.0.0 pytest-asyncio==0.25.2 httpx==0.28.1 \
  ruff==0.9.2 pyright==1.1.407
```

**Tier 2: Standard**:
```bash
pip install detect-secrets==1.5.0 pip-audit==2.7.3 "bandit[toml]==1.8.0" pre-commit==4.0.1
```

**Tier 3: Comprehensive**:
```bash
pip install radon==6.0.1 vulture==2.14 mutmut==3.3.1 locust==2.42.2 semgrep==1.142.1 "coverage[toml]==7.11.1"
```

**Tier 4: Production-Ready**:
```bash
pip install prometheus-client statsd structlog python-json-logger fastapi-health \
  pydantic-settings python-dotenv opentelemetry-instrumentation-fastapi
```

**Security Fixes**:
```bash
pip install --upgrade setuptools starlette
```

**Validation**: `pytest` and `pip-audit` (should show 0 vulnerabilities)

#### Dashboard Refine Stack Installation

**Pre-Installation**:
```bash
(yes "n" | npx create-next-app@latest <project-name> --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*")
```

**Tier 1: Base + Essential**:
```bash
npm install next@16.0.7 react@19.2.1 react-dom@19.2.1 \
  @refinedev/cli@latest @refinedev/core@latest @refinedev/nextjs-router@latest \
  @refinedev/react-table@latest @refinedev/react-hook-form@latest \
  recharts@latest react-hook-form@latest zod@4.1.12 @hookform/resolvers@latest \
  lucide-react@latest class-variance-authority@latest clsx@latest tailwind-merge@latest \
  tailwindcss@4.1.17 @tailwindcss/postcss@4.1.17

npm install --save-dev eslint@9.39.1 eslint-config-next@16.0.7 \
  @typescript-eslint/parser@8.46.3 @typescript-eslint/eslint-plugin@8.46.3 \
  prettier@3.6.2 \
  jest@30.2.0 @types/jest@30.0.0 ts-jest@29.4.5 jest-environment-jsdom@30.2.0 \
  @testing-library/react@16.3.0 @testing-library/jest-dom@6.9.1
```

**Tier 2: Standard**:
```bash
npm install --save-dev husky@9.1.7 lint-staged@16.2.6
```

**Tier 3: Comprehensive**:
```bash
npm install --save-dev jscpd@4.0.5 ts-prune@0.10.3 type-coverage@2.29.7 \
  @stryker-mutator/core@9.3.0 @stryker-mutator/jest-runner@9.3.0 \
  playwright@1.56.1 @axe-core/playwright@4.11.0 \
  eslint-plugin-jest-dom@5.5.0 eslint-plugin-testing-library@7.13.3
```

**Tier 4: Production-Ready** (CRITICAL: patch-package MUST be installed FIRST):
```bash
# Step 1: Install patch-package and other dev dependencies FIRST
npm install --save-dev patch-package @next/bundle-analyzer@latest @lhci/cli@latest dotenv-cli@latest

# Step 2: Install Sentry and analytics (requires patch-package)
npm install @sentry/nextjs@latest @vercel/analytics@latest
```

**Validation**: `npm run build` (should complete in ~3.0 seconds)

#### Full-Stack Next.js Installation

**Pre-Installation**:
```bash
(yes "n" | npx create-next-app@latest <project-name> --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*")
```

**Tier 1: Base + Essential**:
```bash
npm install next@16.0.7 react@19.2.1 react-dom@19.2.1 \
  prisma@6.19.0 @prisma/client@6.19.0 zod@4.1.12 \
  tailwindcss@4.1.17 @tailwindcss/postcss@4.1.17

npm install --save-dev eslint@9.39.1 eslint-config-next@16.0.7 \
  prettier@3.6.2 \
  jest@30.2.0 @types/jest@30.0.0 ts-jest@29.4.5 jest-environment-jsdom@30.2.0 \
  @testing-library/react@16.3.0 @testing-library/jest-dom@6.9.1
```

**Tier 2: Standard**:
```bash
npm install --save-dev husky@9.1.7 lint-staged@16.2.6
```

**Tier 3: Comprehensive**:
```bash
npm install --save-dev jscpd@4.0.5 ts-prune@0.10.3 type-coverage@2.29.7 \
  @stryker-mutator/core@9.3.0 @stryker-mutator/jest-runner@9.3.0 \
  playwright@1.56.1 @axe-core/playwright@4.11.0 \
  eslint-plugin-jest-dom@5.5.0 eslint-plugin-testing-library@7.13.3
```

**Tier 4: Production-Ready** (CRITICAL: patch-package MUST be installed FIRST):
```bash
# Step 1: Install patch-package and other dev dependencies FIRST
npm install --save-dev patch-package @next/bundle-analyzer@latest @lhci/cli@latest dotenv-cli@latest

# Step 2: Install Sentry and analytics (requires patch-package)
npm install @sentry/nextjs@latest @vercel/analytics@latest
```

**Validation**: `npm run build` (should complete in ~3.2 seconds)

---

## 5. Template Structure

### 5.1 Directory Layout

```
src/solokit/templates/
├── template-registry.json          # Master registry of all templates
│
├── saas-t3/                        # T3 Stack Template
│   ├── template.json               # Template metadata
│   ├── base/                       # Base files (always included)
│   │   ├── package.json.template
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── postcss.config.mjs
│   │   ├── .env.example
│   │   └── .gitignore
│   ├── tier-1-essential/           # Essential quality gates
│   │   ├── .eslintrc.json
│   │   ├── .prettierrc
│   │   ├── jest.config.ts
│   │   └── package.json.tier1.template
│   ├── tier-2-standard/            # Standard quality gates
│   │   ├── .git-secrets
│   │   ├── .pre-commit-config.yaml
│   │   └── package.json.tier2.template
│   ├── tier-3-comprehensive/       # Comprehensive gates
│   │   ├── .jscpd.json             # Duplication detection
│   │   ├── stryker.conf.json       # Mutation testing
│   │   ├── playwright.config.ts    # E2E testing
│   │   └── package.json.tier3.template
│   ├── tier-4-production/          # Production-ready gates
│   │   ├── k6-load-test.js         # Performance testing
│   │   ├── sentry.config.js        # Error tracking
│   │   └── package.json.tier4.template
│   ├── ci-cd/                      # GitHub Actions workflows
│   │   └── .github/
│   │       └── workflows/
│   │           ├── quality-check.yml
│   │           ├── test.yml
│   │           ├── security.yml
│   │           ├── build.yml
│   │           └── deploy.yml
│   ├── docker/                     # Docker support
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   └── docker-compose.yml
│   ├── vscode/                     # VS Code configuration
│   │   └── .vscode/
│   │       ├── settings.json
│   │       ├── extensions.json
│   │       └── launch.json
│   ├── starter/                    # Starter code (optional)
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── layout.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── server/
│   │   │   │   ├── api/
│   │   │   │   │   └── routers/
│   │   │   │   └── db.ts
│   │   │   └── styles/
│   │   │       └── globals.css
│   │   └── prisma/
│   │       └── schema.prisma
│   └── tests/                      # Test templates
│       ├── unit/
│       │   └── example.test.ts
│       ├── integration/
│       │   └── api.test.ts
│       └── e2e/
│           └── home.spec.ts
│
├── ml-ai-fastapi/                  # FastAPI ML/AI Template
│   ├── template.json
│   ├── base/
│   │   ├── pyproject.toml.template
│   │   ├── requirements.txt.template
│   │   ├── .env.example
│   │   └── .gitignore
│   ├── tier-1-essential/
│   │   ├── pyproject.toml.tier1.template
│   │   ├── .ruff.toml
│   │   ├── pyrightconfig.json
│   │   └── pytest.ini
│   ├── tier-2-standard/
│   │   ├── .pre-commit-config.yaml
│   │   ├── .bandit
│   │   └── pyproject.toml.tier2.template
│   ├── tier-3-comprehensive/
│   │   ├── .radon.cfg
│   │   ├── .vulture
│   │   ├── mutmut_config.py
│   │   └── pyproject.toml.tier3.template
│   ├── tier-4-production/
│   │   ├── locustfile.py           # Load testing
│   │   ├── sentry_config.py
│   │   └── pyproject.toml.tier4.template
│   ├── ci-cd/
│   │   └── .github/
│   │       └── workflows/
│   │           ├── quality-check.yml
│   │           ├── test.yml
│   │           ├── security.yml
│   │           └── deploy.yml
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   └── docker-compose.yml
│   ├── vscode/
│   │   └── .vscode/
│   │       ├── settings.json
│   │       ├── extensions.json
│   │       └── launch.json
│   ├── starter/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   │   └── routes/
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── config.py
│   │   └── alembic/
│   │       └── env.py
│   └── tests/
│       ├── unit/
│       │   └── test_example.py
│       ├── integration/
│       │   └── test_api.py
│       └── load/
│           └── locustfile.py
│
├── dashboard-refine/               # Refine Dashboard Template
│   ├── template.json
│   ├── base/
│   │   ├── package.json.template
│   │   ├── tsconfig.json
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── components.json         # shadcn/ui config
│   │   ├── .env.example
│   │   └── .gitignore
│   ├── tier-1-essential/
│   │   ├── .eslintrc.json
│   │   ├── .prettierrc
│   │   ├── vitest.config.ts
│   │   └── package.json.tier1.template
│   ├── tier-2-standard/
│   │   ├── .git-secrets
│   │   ├── .pre-commit-config.yaml
│   │   └── package.json.tier2.template
│   ├── tier-3-comprehensive/
│   │   ├── .jscpd.json
│   │   ├── stryker.conf.json
│   │   ├── playwright.config.ts
│   │   ├── .axe-config.json        # Accessibility testing
│   │   └── package.json.tier3.template
│   ├── tier-4-production/
│   │   ├── k6-load-test.js
│   │   ├── sentry.config.js
│   │   └── package.json.tier4.template
│   ├── ci-cd/
│   │   └── .github/
│   │       └── workflows/
│   │           ├── quality-check.yml
│   │           ├── test.yml
│   │           ├── security.yml
│   │           └── deploy.yml
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── .dockerignore
│   │   └── docker-compose.yml
│   ├── vscode/
│   │   └── .vscode/
│   │       ├── settings.json
│   │       ├── extensions.json
│   │       └── launch.json
│   ├── starter/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── (dashboard)/
│   │   │   ├── components/
│   │   │   │   └── ui/             # shadcn/ui components
│   │   │   ├── lib/
│   │   │   └── styles/
│   │   │       └── globals.css
│   │   └── public/
│   └── tests/
│       ├── unit/
│       │   └── component.test.tsx
│       ├── integration/
│       │   └── dashboard.test.tsx
│       └── e2e/
│           └── user-flow.spec.ts
│
└── fullstack-nextjs/               # Full-Stack Next.js Template
    ├── template.json
    ├── base/
    │   ├── package.json.template
    │   ├── tsconfig.json
    │   ├── next.config.ts
    │   ├── tailwind.config.ts
    │   ├── .env.example
    │   └── .gitignore
    ├── tier-1-essential/
    │   ├── .eslintrc.json
    │   ├── .prettierrc
    │   ├── vitest.config.ts
    │   └── package.json.tier1.template
    ├── tier-2-standard/
    │   ├── .git-secrets
    │   ├── .pre-commit-config.yaml
    │   └── package.json.tier2.template
    ├── tier-3-comprehensive/
    │   ├── .jscpd.json
    │   ├── stryker.conf.json
    │   ├── playwright.config.ts
    │   └── package.json.tier3.template
    ├── tier-4-production/
    │   ├── k6-load-test.js
    │   ├── sentry.config.js
    │   └── package.json.tier4.template
    ├── ci-cd/
    │   └── .github/
    │       └── workflows/
    │           ├── quality-check.yml
    │           ├── test.yml
    │           ├── security.yml
    │           └── deploy.yml
    ├── docker/
    │   ├── Dockerfile
    │   ├── .dockerignore
    │   └── docker-compose.yml
    ├── vscode/
    │   └── .vscode/
    │       ├── settings.json
    │       ├── extensions.json
    │       └── launch.json
    ├── starter/
    │   ├── src/
    │   │   ├── app/
    │   │   │   ├── layout.tsx
    │   │   │   ├── page.tsx
    │   │   │   └── api/
    │   │   ├── components/
    │   │   ├── lib/
    │   │   └── styles/
    │   │       └── globals.css
    │   └── prisma/
    │       └── schema.prisma
    └── tests/
        ├── unit/
        │   └── example.test.ts
        ├── integration/
        │   └── api.test.ts
        └── e2e/
            └── flow.spec.ts
```

---

## 6. Template Registry Format

### 6.1 Registry Structure

**Example structure** (showing saas-t3 template, other templates follow same pattern).

**Note**: The version numbers shown below are for illustrative purposes only. All actual version details are stored in `src/solokit/templates/stack-versions.yaml` as the single source of truth.

```json
{
  "version": "1.0.0",
  "templates": {
    "saas-t3": {
      "id": "saas-t3",
      "display_name": "SaaS Application (T3 Stack)",
      "description": "Full-featured SaaS with Next.js 16, React 19, tRPC, Prisma, and Tailwind",
      "category": "saas",
      "stack": {
        "frontend": "Next.js 16.0.7 + React 19.2.1",
        "language": "TypeScript 5.7.3",
        "api": "tRPC 11.7.1",
        "database": "PostgreSQL 16+ with Prisma 6.1.0",
        "styling": "Tailwind CSS 4.1.17"
      },
      "known_issues": [
        {
          "issue": "Sentry Requires patch-package",
          "severity": "LOW",
          "description": "@sentry/nextjs installation fails if patch-package is not installed first",
          "resolution": "Include patch-package in Tier 4 dev dependencies, install before Sentry",
          "status": "RESOLVED"
        }
      ],
      "quality_gates": {
        "tier-1": {
          "lint": "next lint",
          "format": "prettier --check .",
          "type-check": "tsc --noEmit",
          "test": "jest"
        },
        "tier-2": {
          "extends": "tier-1",
          "secret-scan": "git-secrets --scan",
          "audit": "npm audit --audit-level=moderate"
        }
      },
      "package_manager": "npm",
      "supports_docker": true,
      "supports_ci_cd": true
    }
    // ... ml-ai-fastapi, dashboard-refine, fullstack-nextjs follow same structure
  }
}
```

---

## 7. Implementation Changes to init.py

### 7.1 New init_project() Flow

```python
def init_project() -> int:
    """
    Initialize Session-Driven Development with template-based setup.
    
    New flow:
    1. Check if project is blank (new requirement)
    2. Interactive template selection (4 steps)
    3. Template installation
    4. Dependency installation
    5. .session structure creation
    6. Initial commit
    """
    logger.info("🚀 Initializing Session-Driven Development...\n")

    # 1. CHECK IF PROJECT IS BLANK (NEW)
    check_blank_project_or_exit()

    # 2. CHECK OR INITIALIZE GIT
    check_or_init_git()

    # 3. INTERACTIVE TEMPLATE SELECTION (NEW - 4 STEPS)
    template_config = interactive_template_selection()
    # Returns: {
    #     "template_id": "saas-t3",
    #     "quality_tier": "tier-2",
    #     "coverage_target": 80,
    #     "additional_options": ["ci-cd", "docker", "env-templates"]
    # }

    # 4. INSTALL TEMPLATE (NEW)
    install_template(template_config)
    
    # 5. INSTALL DEPENDENCIES
    install_dependencies_from_template(template_config)

    # 6. CREATE .SESSION STRUCTURE
    create_session_structure()

    # 7. INITIALIZE TRACKING FILES
    initialize_tracking_files()

    # 8. RUN INITIAL SCANS
    run_initial_scans()

    # 9. INSTALL GIT HOOKS
    install_git_hooks()

    # 10. UPDATE .GITIGNORE
    ensure_gitignore_entries()

    # 11. CREATE INITIAL COMMIT
    create_initial_commit(template_config)

    # SUCCESS SUMMARY
    print_success_summary(template_config)

    return 0
```

### 7.2 Key Functions to Implement

**Template Selection**:
```python
def interactive_template_selection() -> dict:
    """Guide user through 4-step AskUserQuestion flow. Returns template config."""

def select_project_category() -> str:
    """Step 1: Use AskUserQuestion for category selection."""

def select_quality_tier() -> str:
    """Step 2: Use AskUserQuestion for tier selection."""

def select_coverage_target() -> int:
    """Step 3: Use AskUserQuestion for coverage target."""

def select_additional_options() -> list[str]:
    """Step 4: Use AskUserQuestion (multi-select) for add-ons."""
```

**Template Installation**:
```python
def install_template(config: dict) -> None:
    """
    Install template files:
    1. Copy base files from templates/{stack}/base/
    2. Copy tier-specific files from templates/{stack}/{tier}/
    3. Copy additional options (ci-cd, docker, etc.)
    4. Merge package.json/pyproject.toml files
    5. Replace placeholders (project name, coverage, etc.)
    """
```

**Detailed implementations** will use the patterns from `/start`, `/work-new`, `/end` for AskUserQuestion integration.

---

## 8. Version Pinning Strategy

### 8.1 Approach: Exact Version Pinning

For deterministic, reproducible builds, all dependencies will use **exact version pinning**:

**JavaScript/TypeScript (package.json)**:
```json
{
  "dependencies": {
    "next": "15.1.3",
    "react": "19.0.0",
    "react-dom": "19.0.0"
  }
}
```
- No `^` or `~` prefixes
- Exact versions only
- Updates require explicit template version bump

**Python (requirements.txt)**:
```
fastapi==0.115.6
pydantic==2.10.6
sqlmodel==0.0.25
```
- Use `==` for exact versions
- No `>=` or `~=` operators
- Lock file (requirements.lock) for additional safety

**Benefits**:
- **Reproducible**: Same versions every time
- **Predictable**: No surprise breaking changes
- **Debuggable**: Easier to diagnose issues
- **Compatible**: Guaranteed compatible combinations

**Maintenance**:
- Template versions updated quarterly
- Security patches trigger immediate updates
- Version compatibility tested in CI
- Migration guides for major version bumps

---

## 9. Future: Compatibility Checking Script

### 9.1 Vision

A future enhancement (#14 extension) will add a command to check library compatibility before adding new dependencies:

```bash
/sk:add-package react-query

# Checks:
# 1. Is react-query compatible with current React version?
# 2. Does it conflict with existing dependencies?
# 3. What's the recommended version for this stack?
# 4. Are there known issues in the community?

# Output:
✓ react-query is compatible
ℹ Recommended version: 5.62.8 (matches @tanstack/react-query)
⚠ Note: react-query is deprecated, use @tanstack/react-query
  
Would you like to install @tanstack/react-query@5.62.8? (Y/n)
```

### 9.2 Implementation Approach

```python
def check_package_compatibility(package_name: str, version: str = None):
    """
    Check if package is compatible with current stack.
    
    Checks:
    1. Peer dependency requirements
    2. Known conflicts with current packages
    3. Version compatibility with framework
    4. Community-reported issues
    5. Deprecation status
    """
    # Load current stack info
    stack = load_stack_info()
    
    # Check peer dependencies via npm/pip APIs
    peer_deps = get_peer_dependencies(package_name, version)
    
    # Validate against current packages
    conflicts = check_for_conflicts(peer_deps, stack)
    
    # Check for deprecation
    deprecation = check_deprecation_status(package_name)
    
    # Check community issues
    issues = check_github_issues(package_name, stack)
    
    return {
        "compatible": len(conflicts) == 0,
        "recommended_version": get_recommended_version(package_name, stack),
        "conflicts": conflicts,
        "deprecation": deprecation,
        "issues": issues,
        "alternatives": get_alternatives(package_name) if deprecation else None
    }
```

This would integrate with:
- npm registry API for JS/TS packages
- PyPI API for Python packages
- GitHub API for issue tracking
- Community databases (npms.io, libraries.io)

---

## 10. Stack Compatibility Validation

### 10.1 Validation Status

**Date**: 2025-11-07
**Status**: ✅ COMPLETE (4 of 4 validated)

All four stacks have been validated through fresh installation testing. Exact versions and installation commands are documented in `src/solokit/templates/stack-versions.yaml`.

### 10.2 Validation Results Summary

| Stack | Status | Build | Key Versions |
|-------|--------|-------|--------------|
| SaaS T3 | ✅ VALIDATED | PASSING | Next 16.0.7, React 19.2.1, tRPC 11.7.1, Zod 4.1.12, Jest 30 |
| ML/AI FastAPI | ✅ VALIDATED | PASSING | FastAPI 0.115.6, Pydantic 2.12.4, Python 3.11+ required |
| Dashboard Refine | ✅ VALIDATED | PASSING | Next 16.0.7, React 19.2.1, Refine 5.0.5, Zod 4.1.12, Jest 30 |
| Full-Stack Next.js | ✅ VALIDATED | PASSING | Next 16.0.7, React 19.2.1, Prisma 6.19.0, Zod 4.1.12, Jest 30 |

**🎉 VERSION CONVERGENCE**: All three Next.js-based stacks use identical versions for shared dependencies (Next.js 16.0.7, React 19.2.1, Zod 4.1.12, Jest 30, Tailwind 4.1.17).

### 10.3 Key Validation Findings

**Critical Requirements**:
- **ML/AI Stack**: Python 3.11+ REQUIRED (locust dependency in Tier 3)
- **Next.js Stacks**: patch-package must be installed before @sentry/nextjs (Tier 4)
- **All Stacks**: Build and test successfully with 0 vulnerabilities (except accepted @lhci/cli dev-only issues)

**Version Updates from Initial Design**:
- **Zod**: Upgraded to v4.1.12 (backward compatible, zero breaking changes)
- **Jest**: Upgraded to v30.2.0 (seamless upgrade)
- **React**: 19.2.1 (latest stable, CVE-2025-55182 fix)
- **Next.js**: 16.0.7 (latest stable, CVE-2025-66478 fix)

All validated versions and installation commands are stored in `src/solokit/templates/stack-versions.yaml`.

---

## 11. Success Metrics

### 11.1 Time to First Work Item
- **Current**: 10-20 minutes of manual setup
- **Target**: <1 minute with template initialization
- **Measurement**: Time from `sk init` to `/sk:work-new`

### 11.2 Quality Gate Failures
- **Current**: 40-60% of new projects have initial quality gate failures
- **Target**: <5% quality gate failures after init
- **Measurement**: `/sk:validate` success rate on first run

### 11.3 Developer Satisfaction
- **Current**: N/A (no templates)
- **Target**: 90%+ satisfaction with template setup
- **Measurement**: Post-init survey

### 11.4 Template Adoption
- **Target**: 80%+ of new projects use templates
- **Measurement**: Track template vs custom init ratio

---

## 12. Implementation Phases

### 12.1 Phase 1: Core Template System (Week 1-2)
- [ ] Blank project detection
- [ ] Interactive selection UI (4 steps)
- [ ] Template registry and metadata
- [ ] Base template installation engine
- [ ] Create 1 complete template (SaaS T3) with all tiers
- [ ] Update init.py flow
- [ ] Unit tests for new functions

### 12.2 Phase 2: Complete Template Library (Week 3-4)
- [ ] ML/AI FastAPI template (all tiers)
- [ ] Dashboard Refine template (all tiers)
- [ ] Full-Stack Next.js template (all tiers)
- [ ] Test all templates end-to-end
- [ ] Documentation updates

### 12.3 Phase 3: Additional Options (Week 5)
- [ ] CI/CD workflow generation
- [ ] Docker support files
- [ ] VS Code configurations
- [ ] Environment templates
- [ ] API documentation setup
- [ ] Integration tests

### 12.4 Phase 4: Polish & Launch (Week 6)
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Migration guide from old init
- [ ] Example projects for each template
- [ ] Launch preparation

---

## 13. Migration Path

### 13.1 For Existing Projects

Existing projects already initialized with old `/sk:init` will continue working. No breaking changes to .session structure or workflow.

### 13.2 For New Projects

All new projects must use template-based init. Old init path will be deprecated but available via flag:

```bash
# New default (template-based)
sk init

# Old behavior (deprecated, requires flag)
sk init --legacy
```

Deprecation timeline:
- **v1.0**: Template init is default, legacy available with flag
- **v1.1**: Warning added to legacy init
- **v1.2**: Legacy init removed

---

## 14. Documentation Updates

### 14.1 Files to Update
- [ ] `.claude/commands/init.md` - New interactive flow
- [ ] `docs/commands/init.md` - Complete documentation
- [ ] `README.md` - Updated getting started section
- [ ] `CHANGELOG.md` - Version 1.0 entry
- [ ] New: `docs/templates/README.md` - Template documentation
- [ ] New: `docs/templates/creating-templates.md` - Template creation guide
- [ ] New: `docs/templates/available-templates.md` - Template catalog

---

## 15. Testing Strategy

### 15.1 Unit Tests
- [ ] Blank project detection (various scenarios)
- [ ] Each selection function (all options)
- [ ] Template installation (file copying, merging)
- [ ] Version extraction and validation
- [ ] Placeholder replacement

### 15.2 Integration Tests
- [ ] Complete init flow for each template
- [ ] Quality gate execution after init
- [ ] Dependency installation verification
- [ ] .session structure creation

### 15.3 End-to-End Tests
- [ ] Full SaaS T3 project initialization + first work item
- [ ] Full ML/AI FastAPI project initialization + first work item
- [ ] Full Dashboard Refine project initialization + first work item
- [ ] Full Full-Stack Next.js project initialization + first work item
- [ ] Verify all quality gates pass on each template

### 15.4 Manual Testing Checklist
- [ ] Test each template with each tier
- [ ] Test all combinations of additional options
- [ ] Test custom coverage values
- [ ] Test terminal fallback (non-Claude Code environment)
- [ ] Test blank project detection edge cases
- [ ] Verify generated projects build successfully
- [ ] Verify all quality gates execute correctly

---

## 16. Post-Installation

### 16.1 Generated Files

After template installation, the following files are auto-generated:

#### 16.1.1 README.md
**Location**: Project root
**Content**:
- Project name and category (from template selection)
- Tech stack summary (framework versions from stack-versions.yaml)
- Getting started instructions (stack-specific)
- Available scripts (npm run dev, test, build, etc.)
- Quality gates tier and coverage target
- Testing commands
- Known issues section (if applicable)
- Links to documentation

**Example structure**:
```markdown
# My SaaS Project

A SaaS Application built with the T3 stack.

## Tech Stack

- **Framework**: Next.js 16.0.7 + React 19.2.1
- **API Layer**: tRPC 11.7.1
- **Database**: Prisma 6.19.0
- **Styling**: Tailwind CSS 4.1.17
- **Validation**: Zod 4.1.12

## Quality Gates: Standard Tier

- ✓ Linting and formatting
- ✓ Type checking
- ✓ Unit tests with 80% coverage
- ✓ Git hooks (Husky) for code quality
- ✓ Security scanning

## Getting Started

\`\`\`bash
npm install
npm run dev
\`\`\`

Visit http://localhost:3000

## Testing

\`\`\`bash
npm test              # Run tests
npm run test:coverage # Coverage report
\`\`\`

## Known Issues

[Auto-populated if applicable]
```

#### 16.1.2 .editorconfig
**Location**: Project root
**Purpose**: Universal editor configuration (works with all editors)

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[*.py]
indent_size = 4
```

#### 16.1.3 .env.example
**Location**: Project root (if Environment Templates selected)
**Content**: Stack-specific environment variables with descriptions

**Next.js stacks**:
```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Next.js
NEXTAUTH_SECRET=""
NEXTAUTH_URL="http://localhost:3000"

# API
API_BASE_URL="http://localhost:3000/api"

# Optional: Error Tracking (Tier 4)
SENTRY_DSN=""

# Optional: Analytics (Tier 4)
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=""
```

**Python stack**:
```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# API
API_HOST="0.0.0.0"
API_PORT=8000
API_RELOAD=true

# Security
SECRET_KEY="your-secret-key-here"
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"

# Optional: Monitoring (Tier 4)
SENTRY_DSN=""
PROMETHEUS_PORT=9090
```

#### 16.1.4 docs/ Directory Structure
**Location**: Project root
**Structure**:
```
docs/
├── architecture/
│   ├── README.md          # Architecture overview
│   └── decisions/         # Architecture decision records (ADRs)
├── api/
│   └── README.md          # API documentation
├── guides/
│   ├── development.md     # Development setup guide
│   └── deployment.md      # Deployment guide
└── SECURITY.md            # Security policy
```

### 16.2 Session Structure

The `.session/` directory is created with the following structure:

```
.session/
├── config.json              # Project configuration (quality gates, git workflow, etc.)
├── config.schema.json       # JSON schema for configuration validation
├── briefings/               # Session briefings (one per session)
│   └── session_XXX_briefing.md
├── history/                 # Session summaries (one per session)
│   └── session_XXX_summary.md
├── specs/                   # Work item specifications
│   └── <work_item_spec>.md
└── tracking/                # All tracking data
    ├── learnings.json       # Captured learnings
    ├── work_items.json      # Work items tracking
    ├── stack.txt            # Technology stack information
    ├── stack_updates.json   # Stack update history
    ├── tree.txt             # Project structure snapshot
    ├── tree_updates.json    # Tree update history
    └── status_update.json   # Status updates
```

**tracking/stack.txt** - Auto-generated technology stack information:
```
# Technology Stack

## Languages
- Python 3.11+
- TypeScript 5.7.3

## Frameworks
- Next.js 16.0.7
- React 19.2.1

## Key Libraries
- tRPC 11.7.1
- Prisma 6.19.0
- Zod 4.1.12
- Tailwind CSS 4.1.17

## Testing
- Jest 30.2.0
- Playwright 1.56.1

Generated: 2025-11-07 18:45:00
```

**tracking/tree.txt** - Initial project structure snapshot:
```
.
├── .env.example
├── .eslintrc.json
├── .gitignore
├── .prettierrc
├── README.md
├── next.config.ts
├── package.json
├── tailwind.config.ts
├── tsconfig.json
├── app/
│   ├── layout.tsx
│   └── page.tsx
├── docs/
│   ├── architecture/
│   ├── api/
│   └── guides/
└── tests/
    └── unit/
        └── example.test.ts
```

**config.json** - Project configuration (includes quality gates tier and coverage target):
```json
{
  "quality_gates": {
    "tier": "standard",
    "coverage_threshold": 80,
    "test_execution": {
      "enabled": true,
      "required": true,
      "commands": {
        "python": "pytest --cov=src --cov-report=json",
        "javascript": "npm test -- --coverage",
        "typescript": "npm test -- --coverage"
      }
    },
    "linting": { "enabled": true, "required": true },
    "formatting": { "enabled": true, "required": true },
    "security": { "enabled": true, "required": true }
  },
  "git_workflow": {
    "mode": "pr",
    "auto_push": true,
    "auto_create_pr": true
  }
}
```

### 16.3 Initial Commit

After all files are generated, an initial commit is created automatically:

**Commit Message Template**:
```
chore: Initialize project with Solokit template system

Template: [category] ([template_id])
Quality Tier: [tier]
Coverage Target: [coverage]%
Additional Options: [options]

Stack:
- [Framework]: [version]
- [Language]: [version]
- [Additional stack details]

Generated files:
- Project configuration ([count] files)
- Quality gate configs ([tier] tier)
- [Additional options if selected]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example**:
```
chore: Initialize project with Solokit template system

Template: SaaS Application (saas-t3)
Quality Tier: Standard
Coverage Target: 80%
Additional Options: GitHub Actions CI/CD, Environment Templates

Stack:
- Next.js: 16.0.7
- React: 19.2.1
- TypeScript: 5.7.3
- tRPC: 11.7.1
- Prisma: 6.19.0
- Tailwind CSS: 4.1.17

Generated files:
- Project configuration (15 files)
- Quality gate configs (Standard tier)
- CI/CD workflows (4 workflows)
- Git hooks (Husky) configured
- Environment templates created

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 17. Versions Management

### 17.1 stack-versions.yaml Structure

**Location**: `src/solokit/templates/stack-versions.yaml`

This file serves as the single source of truth for all validated dependency versions across all stacks.

**Purpose**:
- Define exact versions for all dependencies (all tiers)
- Document installation commands tested during validation
- Track known issues and their resolutions
- Enable automated version compatibility checking (future)
- Support scheduled version updates (future)

**Structure Overview**:
```yaml
metadata:
  validation_date: "2025-11-07"
  python_min_version: "3.11"
  node_min_version: "18.0.0"

stacks:
  saas_t3:
    name: "Next.js T3 Stack"
    base_framework:
      next: "16.0.7"
      react: "19.2.1"
      # ... all versions
    tier1_essential:
      # ... tier-specific versions
    installation:
      commands:
        # ... exact installation commands
    known_issues:
      # ... documented issues

  ml_ai_fastapi:
    # ... similar structure
```

**Key Features**:
1. **Exact Version Pinning**: All versions use exact format (no ^ or ~)
2. **Tier Organization**: Dependencies organized by quality tier
3. **Installation Commands**: Tested commands for each tier
4. **Known Issues**: Documented with severity and resolution
5. **Metadata**: Validation date, minimum versions, success metrics

**Usage by Init Command**:
```python
import yaml
from pathlib import Path

def load_stack_versions():
    """Load validated versions from stack-versions.yaml"""
    versions_file = Path(__file__).parent / "templates" / "stack-versions.yaml"
    with open(versions_file) as f:
        return yaml.safe_load(f)

def get_stack_version(stack_id: str, tier: str, package: str) -> str:
    """Get exact version for a package in a specific stack/tier"""
    versions = load_stack_versions()
    return versions["stacks"][stack_id][tier][package]
```

### 17.2 Version Update Process (Future Enhancement)

**NOT part of current work item** - Documented for future implementation.

**Vision**: Automated script to check for version updates and test compatibility.

**Proposed Process**:
1. **Scheduled Check** (weekly/monthly via CI/CD):
   ```bash
   python scripts/check_version_updates.py
   ```

2. **Version Discovery**:
   - Query npm registry for latest versions
   - Query PyPI for latest Python packages
   - Compare with current stack-versions.yaml

3. **Compatibility Testing**:
   - Create temporary test project
   - Install new versions
   - Run build, tests, quality gates
   - Check for breaking changes

4. **Update Decision**:
   - Patch updates: Auto-apply if tests pass
   - Minor updates: Create PR for review
   - Major updates: Flag for manual review
   - Security patches: Prioritize immediately

5. **Update stack-versions.yaml**:
   - Update version numbers
   - Update validation_date
   - Add notes about changes
   - Create git commit

**Example Script Structure**:
```python
def check_package_updates(stack_id: str):
    """Check for updates to packages in a stack"""
    versions = load_stack_versions()
    stack = versions["stacks"][stack_id]

    updates = []
    for tier in ["base_framework", "tier1_essential", ...]:
        for package, current_version in stack[tier].items():
            latest = get_latest_version(package)
            if latest != current_version:
                updates.append({
                    "package": package,
                    "current": current_version,
                    "latest": latest,
                    "type": classify_update(current_version, latest)
                })

    return updates
```

**Benefits**:
- Keep templates up-to-date with latest stable versions
- Catch security vulnerabilities early
- Reduce manual maintenance burden
- Ensure compatibility before recommending updates

---

## Finalized Decisions

All design decisions have been finalized through stakeholder input and technical validation:

### Core Architecture Decisions

1. **Package Manager**: npm only
   - **Rationale**: Simplifies implementation, covers 70%+ of users
   - **Future**: pnpm/yarn support as enhancement

2. **Starter Code**: Always include
   - **Rationale**: Helps onboarding, demonstrates best practices
   - **Includes**: Minimal working code for each template

3. **README Generation**: Auto-generate
   - **Rationale**: Better UX, provides next steps
   - **Includes**: Template-specific setup and usage

4. **Template Updates**: Not applicable
   - **Rationale**: No existing projects yet (dogfooding phase)
   - **Future**: Manual migration guides when needed

### User Experience Decisions

5. **Pre-selected Options**: Yes
   - **Default selections**: GitHub Actions CI/CD, Environment Templates
   - **Rationale**: Encourages best practices, user can uncheck

6. **Default Coverage**: 80% (Standard)
   - **Rationale**: Good balance of quality and pragmatism
   - **Options**: 60% (Basic), 80% (Standard), 90% (Strict), Custom

7. **Terminal Support**: Claude Code only
   - **Rationale**: Aligns with Solokit vision, simpler implementation
   - **No fallback**: Requires Claude Code environment

### Additional Template Files

8. **Developer Experience Files** (included in base):
   - Makefile (tier-specific versions)
   - .editorconfig (universal)
   - .gitmessage + prepare-commit-msg hook

9. **Documentation Files** (included in base):
   - README.md skeleton
   - CHANGELOG.md structure
   - docs/ directory with SECURITY.md

10. **Testing Approach**: Tier 3 validation
    - **Thoroughness**: Full validation (install, build, dev, quality gates, tests)

---

*Last Updated: 2025-11-07 18:45*
*Enhancement: #14 - Template-Based Project Initialization*
*Status: Design Finalized - ✅ ALL STACKS VALIDATED (4/4 complete)*
