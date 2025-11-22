# Init Command

**Usage:** `sk init [OPTIONS]`

**Description:** Initialize a new Session-Driven Development project with template-based structure.

## Overview

The `init` command creates a complete project structure from production-ready templates with tier-based quality gates. It handles:

- Template file installation
- Dependency installation
- Git repository setup
- Session tracking initialization
- Documentation structure creation
- Initial project scans

## Quick Start

### Interactive Mode

Run without arguments for guided setup:

```bash
cd your-project-directory
sk init
```

You'll be prompted to select:
1. **Template** - Project type (saas_t3, fullstack_nextjs, dashboard_refine, ml_ai_fastapi)
2. **Tier** - Quality level (tier-1-essential through tier-4-production)
3. **Coverage** - Test coverage target (60%, 70%, 80%, 90%)
4. **Options** - Additional features (ci_cd, docker, env_templates)

### Command Line Mode

Specify all options at once:

```bash
sk init \
  --template=saas_t3 \
  --tier=tier-4-production \
  --coverage=80 \
  --options=ci_cd,docker,env_templates
```

## Options

### --template

Select the project template to use.

**Available templates:**

| Template ID | Description | Tech Stack |
|------------|-------------|------------|
| `saas_t3` | SaaS Application with T3 Stack | Next.js + tRPC + Prisma |
| `fullstack_nextjs` | Full-Stack Product | Next.js + REST API |
| `dashboard_refine` | Admin Dashboard | Next.js + Refine + Ant Design |
| `ml_ai_fastapi` | ML/AI Backend | FastAPI + Python + SQLModel |

See [Templates Guide](../templates/TEMPLATES_GUIDE.md) for detailed comparison.

### --tier

Select the quality tier for your project.

**Available tiers:**

| Tier | Level | Coverage | Best For |
|------|-------|----------|----------|
| `tier-1-essential` | Minimum | 60% | Prototypes, POCs |
| `tier-2-standard` | Team | 70% | Small teams, MVPs |
| `tier-3-comprehensive` | Production | 80% | Client projects |
| `tier-4-production` | Enterprise | 80% | Critical systems |

**Tier capabilities:**

- **Tier 1**: Unit tests, linting, type checking
- **Tier 2**: + Formatting, security scanning, git hooks (Husky)
- **Tier 3**: + E2E tests, performance monitoring, code quality
- **Tier 4**: + Error tracking, analytics, production monitoring

### --coverage

Set test coverage target percentage (60, 70, 80, or 90).

```bash
sk init --coverage=80  # Require 80% code coverage
```

This configures:
- Test runner coverage thresholds
- Quality gate requirements
- CI/CD pipeline checks

### --options

Comma-separated list of additional features to include.

**Available options:**

- `ci_cd` - GitHub Actions workflows for CI/CD
- `docker` - Docker and docker-compose configuration
- `env_templates` - Environment variable templates for all environments

```bash
sk init --options=ci_cd,docker
```

## Installation Process

The init command performs these steps:

### 1. Pre-flight Validation
- Checks directory is empty or suitable for initialization
- Validates environment (Node.js/Python version)
- Verifies template exists

### 2. Git Initialization
- Initializes git repository
- Sets default branch to 'main'
- Creates initial .gitignore

### 3. Template Installation
- Copies base template files
- Installs tier 1 files
- Installs tier 2 files (if tier ≥ 2)
- Installs tier 3 files (if tier ≥ 3)
- Installs tier 4 files (if tier = 4)
- Installs optional features (CI/CD, Docker, etc.)
- Processes template placeholders ({project_name}, etc.)

### 4. Dependency Installation
- Creates virtual environment (Python) or uses npm/yarn
- Installs base dependencies
- Installs tier dependencies incrementally
- Applies security fixes

### 5. Project Structure Setup
- Creates documentation directories (docs/)
- Creates session tracking directories (.session/)
- Generates README.md
- Creates environment file templates

### 6. Initial Scans
- Generates stack.txt (technology inventory)
- Generates tree.txt (file structure)
- Creates project context

### 7. Git Configuration
- Installs git hooks
- Updates .gitignore
- Creates initial commit

## Examples

### SaaS Application (Full Setup)

```bash
cd my-saas-app
sk init \
  --template=saas_t3 \
  --tier=tier-4-production \
  --coverage=80 \
  --options=ci_cd,docker,env_templates
```

**Result:**
- Complete T3 Stack setup (Next.js + tRPC + Prisma)
- All quality tools (testing, linting, formatting, security)
- E2E tests with Playwright
- Production monitoring (Sentry, analytics)
- GitHub Actions CI/CD
- Docker configuration
- Pre-commit hooks
- Environment templates

**Time:** ~25 minutes

### Quick Prototype (Minimal Setup)

```bash
cd my-prototype
sk init \
  --template=fullstack_nextjs \
  --tier=tier-1-essential \
  --coverage=60
```

**Result:**
- Basic Next.js application
- Unit testing with Jest
- TypeScript and ESLint
- Dev server with hot reload

**Time:** ~5 minutes

### Admin Dashboard

```bash
cd admin-panel
sk init \
  --template=dashboard_refine \
  --tier=tier-3-comprehensive \
  --coverage=80 \
  --options=ci_cd,env_templates
```

**Result:**
- Refine dashboard with CRUD operations
- Comprehensive testing (unit + E2E)
- Code quality tools
- Performance monitoring
- CI/CD pipeline
- Environment configurations

**Time:** ~20 minutes

### Python ML API

```bash
cd ml-api
sk init \
  --template=ml_ai_fastapi \
  --tier=tier-2-standard \
  --coverage=70 \
  --options=docker,env_templates
```

**Result:**
- FastAPI with async PostgreSQL
- Testing with pytest
- Security scanning (bandit, pip-audit)
- Docker setup for deployment
- Environment templates

**Time:** ~20 minutes

## After Initialization

Once initialization completes, you'll see:

```
✅ Solokit Template Initialization Complete!

📦 Template: SaaS Application (T3 Stack)
🎯 Quality Tier: tier-4-production
📊 Coverage Target: 80%

✓ Project structure created
✓ Dependencies installed
✓ Quality gates configured
✓ Documentation structure created
✓ Session tracking initialized
✓ Git repository configured

🚀 Next Steps:
   1. Review README.md for getting started guide
   2. Create your first work item: /sk:work-new
   3. Start working: /sk:start
```

### Next Steps

1. **Read the README:**
   ```bash
   cat README.md
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your values
   ```

3. **Run the project:**

   **Next.js templates:**
   ```bash
   npm run dev
   ```

   **FastAPI template:**
   ```bash
   source venv/bin/activate
   uvicorn src.main:app --reload
   ```

4. **Run tests:**

   **Next.js templates:**
   ```bash
   npm test
   ```

   **FastAPI template:**
   ```bash
   pytest
   ```

5. **Create work items:**
   ```bash
   /sk:work-new
   ```

6. **Start session:**
   ```bash
   /sk:start
   ```

## Troubleshooting

### "Project directory not empty"

The directory must be empty or only contain:
- `.git/`
- `.gitignore`
- `README.md`

**Solution:** Clean the directory or use a new one.

### "Node.js version too old"

Next.js 16 requires Node.js 18+.

**Solution:**
```bash
node --version  # Check version
nvm install 18  # Install if needed
nvm use 18
```

### "Python version too old"

FastAPI template requires Python 3.11+.

**Solution:**
```bash
python3 --version  # Check version
brew install python@3.11  # macOS
apt install python3.11     # Ubuntu
```

### Installation hangs or fails

**Network issues:**
```bash
# Check npm registry
npm ping

# Try different registry
npm config set registry https://registry.npmjs.org/

# For Python
pip install --upgrade pip
```

**Disk space:**
```bash
df -h .  # Check available space
# Node.js projects need ~500MB
# Python projects need ~300MB
```

### Tests fail after init

Some templates require additional setup:

**Database templates (saas_t3, ml_ai_fastapi):**
```bash
# Start PostgreSQL
brew services start postgresql  # macOS
sudo service postgresql start   # Ubuntu

# Run migrations
npx prisma migrate dev          # T3 Stack
alembic upgrade head            # FastAPI
```

**Environment variables:**
```bash
cp .env.example .env.local
# Edit .env.local with your database URL
```

## Advanced Usage

### Custom project name

By default, the project name is the directory name:

```bash
mkdir my-awesome-app
cd my-awesome-app
sk init  # Project name will be "my-awesome-app"
```

### Reinitializing

To change tier or add options:

1. **Commit your current work:**
   ```bash
   git add .
   git commit -m "Save before reinit"
   ```

2. **Reinitialize with new settings:**
   ```bash
   sk init --template=saas_t3 --tier=tier-3-comprehensive
   ```

3. **Review changes:**
   ```bash
   git diff
   ```

**Warning:** This overwrites configuration files. Custom code changes are preserved.

### Skipping options

To initialize without optional features:

```bash
sk init --template=saas_t3 --tier=tier-2-standard --coverage=70
# No --options specified = no optional features
```

## Configuration Files

Init creates these key configuration files:

**JavaScript/TypeScript templates:**
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `eslint.config.js` - Linting rules
- `jest.config.js` or `vitest.config.ts` - Test configuration
- `playwright.config.ts` - E2E test configuration (tier 3+)
- `next.config.js` - Next.js configuration

**Python templates:**
- `pyproject.toml` - Project configuration and dependencies
- `pytest.ini` - Test configuration
- `ruff.toml` - Linting and formatting rules
- `.banditrc` - Security scanning configuration (tier 2+)
- `alembic.ini` - Database migrations

**All templates:**
- `.gitignore` - Git ignore rules
- `.editorconfig` - Editor configuration
- `.env.example` - Environment variable template
- `README.md` - Project documentation
- `.session/config.json` - Solokit configuration

## See Also

- [Templates Guide](../templates/TEMPLATES_GUIDE.md) - Choose the right template
- [Creating Templates](../templates/CREATING_TEMPLATES.md) - Build custom templates
- [Work New Command](work-new.md) - Create work items
- [Start Command](start.md) - Begin development session
