# Solokit Templates Guide

Solokit provides production-ready project templates with tier-based quality gates. This guide helps you choose the right template and tier for your project.

## Available Templates

### 1. SaaS Application (T3 Stack)
**Template ID:** `saas_t3`

A full-stack SaaS application template built with the T3 Stack.

**Tech Stack:**
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4
- **Backend**: tRPC 11, Prisma ORM, PostgreSQL
- **State Management**: TanStack Query
- **Type Safety**: TypeScript, Zod validation

**Best for:**
- SaaS products
- B2B applications
- Internal tools with complex data models
- Projects requiring type-safe API

**Key Features:**
- End-to-end type safety (frontend to database)
- Optimistic updates with React Query
- Server-side rendering
- API routes with tRPC

**Time to initialize:** 25 minutes (tier-4)

---

### 2. Full-Stack Product (Next.js)
**Template ID:** `fullstack_nextjs`

A flexible full-stack application template with REST APIs.

**Tech Stack:**
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4
- **Backend**: Next.js API Routes
- **Styling**: Tailwind CSS 4 with Lightning CSS
- **Type Safety**: TypeScript

**Best for:**
- Marketing websites with dynamic features
- Content platforms
- E-commerce sites
- Projects that need REST APIs

**Key Features:**
- Server and client components
- REST API endpoints
- Static and dynamic rendering
- Edge runtime support

**Time to initialize:** 10 minutes (tier-4)

---

### 3. Internal Dashboard (Refine)
**Template ID:** `dashboard_refine`

A data-driven admin dashboard built with Refine framework.

**Tech Stack:**
- **Frontend**: Next.js 16, React 19, Refine 4
- **Backend**: Backend-agnostic (works with any REST/GraphQL API)
- **UI**: Tailwind CSS 4, Ant Design components
- **Type Safety**: TypeScript

**Best for:**
- Admin panels
- Internal dashboards
- CRUD applications
- Data management tools

**Key Features:**
- Out-of-the-box CRUD operations
- Built-in authentication
- Table views with filtering/sorting
- Form generation
- Backend-agnostic architecture

**Time to initialize:** 20 minutes (tier-4)

---

### 4. ML/AI Tooling (FastAPI)
**Template ID:** `ml_ai_fastapi`

A Python backend template for ML/AI applications with async support.

**Tech Stack:**
- **Backend**: FastAPI 0.115, Python 3.11+
- **Database**: PostgreSQL with SQLModel ORM
- **Async**: asyncpg, aiosqlite
- **Validation**: Pydantic 2
- **Migrations**: Alembic

**Best for:**
- ML model serving APIs
- Data processing pipelines
- Python microservices
- AI/ML tooling backends

**Key Features:**
- Async request handling
- Automatic API documentation (OpenAPI)
- Type validation with Pydantic
- Database migrations with Alembic
- Health check endpoints

**Time to initialize:** 35 minutes (tier-4)

---

## Quality Tiers

Each template supports 4 quality tiers. Choose based on your project phase and requirements:

### Tier 1: Essential (Minimum Viable Quality)
**Best for:** Prototypes, proof of concepts, learning projects

**Includes:**
- Unit testing framework
- Code linter
- Type checker
- Hot reload/dev server
- Basic test examples

**Coverage requirement:** 60%
**Installation time:** +5-15 minutes

### Tier 2: Standard (Team Collaboration)
**Best for:** Small team projects, internal tools, MVPs

**Includes:** Everything in Tier 1, plus:
- Code formatter
- Security vulnerability scanning
- Git pre-commit hooks
- Commit message linting
- License checking

**Coverage requirement:** 70%
**Installation time:** +3-5 minutes

### Tier 3: Comprehensive (Quality Assurance)
**Best for:** Production projects, client projects, open source

**Includes:** Everything in Tier 2, plus:
- End-to-end testing (Playwright/Locust)
- Performance monitoring (Lighthouse)
- Code quality analysis (SonarQube/Radon)
- Mutation testing
- Load testing

**Coverage requirement:** 80%
**Installation time:** +5-13 minutes

**Note:** Requires one-time browser setup for E2E tests: `npm run setup` (see Next Steps below)

### Tier 4: Production (Enterprise Ready)
**Best for:** Enterprise applications, high-traffic sites, critical systems

**Includes:** Everything in Tier 3, plus:
- Error tracking (Sentry)
- Analytics and monitoring
- Performance observability (OpenTelemetry/Prometheus)
- Health check endpoints
- Production deployment configs
- Bundle analysis and optimization

**Coverage requirement:** 80%
**Installation time:** +3-5 minutes

**Note:** Requires one-time browser setup for E2E tests: `npm run setup` (see Next Steps below)

---

## Additional Options

All templates support these optional features:

### CI/CD Integration
**Option:** `ci_cd`

GitHub Actions workflows for:
- Running tests on PR
- Type checking
- Linting and formatting
- Building production bundles
- Automated deployments

### Docker Support
**Option:** `docker`

Production-ready Docker configuration:
- Multi-stage Dockerfile
- Docker Compose for local development
- Optimized image layers
- Health checks

### Environment Templates
**Option:** `env_templates`

Environment variable templates:
- `.env.local.example` - Local development
- `.env.development.example` - Dev environment
- `.env.staging.example` - Staging environment
- `.env.production.example` - Production environment

---

## Quick Start

### Interactive Mode
```bash
cd your-project-directory
sk init
```

Follow the prompts to select:
1. Template type
2. Quality tier
3. Coverage target
4. Additional options

### Command Line Mode
```bash
sk init \
  --template=saas_t3 \
  --tier=tier-4-production \
  --coverage=80 \
  --options=ci_cd,docker,env_templates
```

---

## Decision Guide

### Choose by Project Type

**Building a SaaS product?**
→ Use `saas_t3` for type-safe APIs and complex data models

**Need a marketing website with some dynamic features?**
→ Use `fullstack_nextjs` for flexibility and simplicity

**Creating an admin panel or dashboard?**
→ Use `dashboard_refine` for built-in CRUD and data management

**Building ML/AI APIs or Python microservices?**
→ Use `ml_ai_fastapi` for async Python backend

### Choose by Team Size

**Solo developer or learning:**
→ Start with Tier 1 or 2

**Small team (2-5 developers):**
→ Use Tier 2 or 3

**Medium to large team (5+ developers):**
→ Use Tier 3 or 4

**Enterprise or critical systems:**
→ Always use Tier 4

### Choose by Project Phase

**Early prototype/POC:**
→ Tier 1 (Essential)

**MVP or alpha:**
→ Tier 2 (Standard)

**Beta or pre-launch:**
→ Tier 3 (Comprehensive)

**Production/launched:**
→ Tier 4 (Production)

---

## Upgrading Tiers

You can upgrade to a higher tier later by re-running initialization:

```bash
sk init --template=saas_t3 --tier=tier-3-comprehensive
```

**Note:** This will overwrite your configuration files. Commit your changes first!

---

## Template Comparison

| Feature | SaaS T3 | Full-Stack Next.js | Dashboard Refine | ML/AI FastAPI |
|---------|---------|-------------------|------------------|---------------|
| **Type Safety** | End-to-end | Frontend + API | Frontend + API | Backend |
| **API Style** | tRPC | REST | REST/GraphQL | REST |
| **Database** | Prisma + PG | Optional | Optional | SQLModel + PG |
| **Best Use Case** | SaaS apps | General web apps | Admin panels | ML/AI APIs |
| **Learning Curve** | Medium | Low | Low | Medium |
| **Setup Time** | 25 min | 10 min | 20 min | 35 min |

---

## Package Versions

All templates use the latest stable versions:

**JavaScript/TypeScript:**
- Next.js 16.0.1
- React 19.2.0
- TypeScript 5.9.3
- Tailwind CSS 4.1.17

**Python:**
- FastAPI 0.115.6
- Python 3.11.7+
- Pydantic 2.12.4
- SQLModel 0.0.25

For complete version information, see [stack-versions.yaml](../../src/solokit/templates/stack-versions.yaml).

---

## Next Steps

After initialization:

1. **Review the README.md** in your project for specific getting started instructions
2. **Set up environment variables** from `.env.example`
3. **For Tier-3 & Tier-4 only:** Install Playwright browsers for E2E tests
   ```bash
   npm run setup  # Installs browsers (~400MB, one-time setup)
   ```
   This is required before running `npm run test:e2e` or `npm run test:all`
4. **Create your first work item:** `/sk:work-new`
5. **Start a development session:** `/sk:start`

---

## Troubleshooting

### Installation fails

**Check Node.js version:**
```bash
node --version  # Should be 18+ for Next.js templates
```

**Check Python version:**
```bash
python3 --version  # Should be 3.11+ for FastAPI template
```

### Tests fail after initialization

Most templates require environment setup:

1. Copy `.env.example` to `.env.local`
2. Fill in required values
3. For database templates, ensure PostgreSQL is running
4. Run `npm install` or `pip install -e .` again

**For Tier-3 & Tier-4 E2E test failures:**

If you see `Error: browserType.launch: Executable doesn't exist`, run:
```bash
npm run setup  # Installs Playwright browsers
```

This is a one-time setup required for E2E tests with Playwright.

### Build fails

Clear caches and reinstall:

**Next.js:**
```bash
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

**Python:**
```bash
rm -rf venv __pycache__ .pytest_cache
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

---

## Further Reading

- [Creating Custom Templates](CREATING_TEMPLATES.md)
- [Stack Versions Reference](../../src/solokit/templates/stack-versions.yaml)
- [Template Registry](../../src/solokit/templates/template-registry.json)
- [Init Command Reference](../commands/init.md)
