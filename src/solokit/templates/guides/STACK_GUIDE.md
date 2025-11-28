# Solokit Stack Selection Guide

This guide helps you choose the right technology stack for your project. Each stack is optimized for specific use cases and enforces architectural patterns that work well for those scenarios.

---

## Quick Decision Tree

```
What are you building?

├── A SaaS product with user accounts and complex data?
│   └── Do you want maximum TypeScript type safety?
│       ├── Yes → saas_t3 (T3 Stack)
│       └── No, I prefer flexibility → fullstack_nextjs
│
├── An ML/AI backend or Python-heavy API?
│   └── ml_ai_fastapi
│
├── An admin dashboard or internal CRUD tool?
│   └── dashboard_refine
│
└── A general web application (marketing, content, e-commerce)?
    └── Do you need complex client-side interactivity?
        ├── Yes → saas_t3 or fullstack_nextjs
        └── No, mostly server-rendered → fullstack_nextjs
```

---

## Stack Overview

| Stack | Best For | Language | Key Technology |
|-------|----------|----------|----------------|
| **saas_t3** | SaaS, complex apps | TypeScript | tRPC + Prisma + Next.js |
| **ml_ai_fastapi** | ML/AI backends, APIs | Python | FastAPI + SQLModel |
| **dashboard_refine** | Admin dashboards | TypeScript | Refine + shadcn/ui |
| **fullstack_nextjs** | General web apps | TypeScript | Next.js + Prisma |

---

## Detailed Stack Profiles

### 1. SaaS T3 Stack (`saas_t3`)

**Technology Versions:**
- Next.js 16.0.1 + React 19.2.0
- tRPC 11.7.1
- Prisma 6.19.0
- TypeScript 5.9.3
- Tailwind CSS 4.1.17

**Best For:**
- SaaS products with user authentication
- Applications requiring end-to-end type safety
- Teams that are TypeScript-focused
- Internal tools where you control all clients
- Rapid development with minimal API boilerplate

**Not Ideal For:**
- APIs consumed by third-party clients (mobile apps, external services)
- Polyglot backends (Python ML services, Go microservices)
- Teams unfamiliar with TypeScript
- Simple static websites

**Key Architectural Patterns:**

1. **tRPC for All Internal APIs**
   - No REST endpoints for internal data fetching
   - Type safety flows from database → API → UI automatically
   - Queries and mutations are type-checked at compile time

2. **Server/Client Separation**
   - Database access only in `server/` directory
   - Clear boundaries prevent accidental client-side DB imports

3. **Environment Validation**
   - All environment variables validated with Zod at startup
   - Fail fast if configuration is missing

**File Organization (target structure you will build):**

Note: The template provides minimal scaffolding. The structure below shows what your project will look like as you build features.

```
server/
├── api/
│   ├── trpc.ts       # tRPC initialization (provided)
│   ├── root.ts       # Router composition (provided, add routers)
│   └── routers/      # CREATE: Feature routers
└── db.ts             # Prisma client (provided)

lib/
├── api.tsx           # tRPC React provider (provided)
└── env.ts            # Environment validation (provided)

app/                  # CREATE: Next.js pages
components/           # CREATE: React components
prisma/
└── schema.prisma     # Database schema (provided, add models)
```

**What This Stack Enforces:**
- All API communication through tRPC (not REST)
- TypeScript strict mode
- Prisma for database access
- Server components for data fetching

---

### 2. ML/AI FastAPI (`ml_ai_fastapi`)

**Technology Versions:**
- FastAPI 0.121.3
- Python 3.11+
- SQLModel 0.0.25 + SQLAlchemy 2.0.37
- Pydantic 2.12.4
- PostgreSQL with Alembic migrations

**Best For:**
- Machine learning model serving
- Data pipelines and processing APIs
- Python-heavy backends
- APIs with multiple consumers (web, mobile, third-party)
- Projects requiring automatic OpenAPI documentation

**Not Ideal For:**
- Frontend-heavy applications
- Teams without Python experience
- Simple CRUD with minimal business logic
- Projects requiring tight frontend integration

**Key Architectural Patterns:**

1. **Async-First Design**
   - All route handlers are async
   - Non-blocking I/O for database and external calls
   - Efficient handling of concurrent requests

2. **Service Layer Pattern**
   - Routes → Services → Database
   - Business logic isolated in services
   - Easy to test with dependency injection

3. **Dependency Injection**
   - Database sessions via `Depends(get_db)`
   - Clean separation of concerns
   - Testable by overriding dependencies

4. **Schema Separation**
   - Database models (SQLModel) separate from API schemas (Pydantic)
   - Clear input/output contracts

**File Organization (target structure you will build):**

Note: The template provides minimal scaffolding. The structure below shows what your project will look like as you build features.

```
src/
├── api/
│   ├── dependencies.py   # Database dependencies (provided)
│   └── routes/           # CREATE: API endpoints
├── models/               # CREATE: SQLModel database models
├── services/             # CREATE: Business logic
└── core/
    ├── config.py         # Pydantic Settings (provided)
    └── database.py       # Engine and session (provided)

alembic/
├── env.py                # Alembic config (provided)
└── versions/             # CREATE: Migration files
```

**What This Stack Enforces:**
- Async route handlers
- Alembic for all schema changes (no manual SQL)
- Virtual environment isolation
- Service layer for business logic

---

### 3. Dashboard Refine (`dashboard_refine`)

**Technology Versions:**
- Refine (latest) + Next.js 16.0.1
- React 19.2.0 + shadcn/ui
- React Hook Form 7.66.0 + Zod 4.1.12
- TypeScript 5.9.3
- Tailwind CSS 4.1.17

**Best For:**
- Admin dashboards and back-office tools
- CRUD-heavy applications
- Data management interfaces
- Internal tools with tables, forms, and filters
- Rapid prototyping with mock data

**Not Ideal For:**
- Consumer-facing marketing sites
- Content-heavy blogs or documentation
- Applications with minimal CRUD operations
- Simple landing pages

**Key Architectural Patterns:**

1. **Refine Data Provider Pattern**
   - All CRUD operations through Refine hooks
   - Backend-agnostic (REST, GraphQL, Supabase all supported)
   - Built-in pagination, filtering, sorting

2. **Resource-Based Architecture**
   - URL structure matches resources (`/users`, `/products`)
   - Automatic routing based on resource definitions
   - Consistent patterns across all entities

3. **Route Groups**
   - Dashboard pages in `(dashboard)` group
   - Shared layouts without URL prefix
   - Clear separation from public pages

**File Organization (target structure you will build):**

Note: The template provides minimal scaffolding. The structure below shows what your project will look like as you build features.

```
app/
├── (dashboard)/          # Route group (provided)
│   ├── layout.tsx        # Dashboard layout (provided)
│   └── [resource]/       # CREATE: Resource pages
│       ├── page.tsx      # CREATE: List view
│       ├── create/       # CREATE: Create view
│       ├── edit/         # CREATE: Edit view
│       └── show/         # CREATE: Detail view

components/
├── layout/               # Header, sidebar (provided)
├── forms/                # CREATE: Form components
└── ui/                   # shadcn/ui primitives (provided)

lib/
├── refine.tsx            # Data provider (provided, configure it)
└── validations.ts        # CREATE: Zod schemas
```

**What This Stack Enforces:**
- Refine hooks for all CRUD operations (useList, useTable, useForm, useShow)
- shadcn/ui component library
- Data provider pattern (must implement for production)
- Resource-based URL structure

**Important Note:**
You must implement a data provider to connect to your backend. Refine supports:
- REST APIs (`@refinedev/simple-rest`)
- GraphQL (`@refinedev/graphql`)
- Supabase (`@refinedev/supabase`)
- Custom implementations

---

### 4. Full-Stack Next.js (`fullstack_nextjs`)

**Technology Versions:**
- Next.js 16.0.1
- React 19.2.0
- Prisma 6.19.0
- Zod 4.1.12
- TypeScript 5.9.3
- Tailwind CSS 4.1.17

**Best For:**
- General-purpose web applications
- Content-focused sites with some interactivity
- Projects prioritizing simplicity
- Teams wanting minimal abstraction layers
- SEO-critical applications

**Not Ideal For:**
- Complex real-time applications
- Heavy client-side interactivity
- Projects requiring maximum type safety across API boundaries

**Key Architectural Patterns:**

1. **Server Components First**
   - Default to React Server Components
   - Client Components only when interactivity needed
   - Direct database access in server code

2. **Server Actions for Mutations**
   - Prefer Server Actions over API routes
   - Progressive enhancement support
   - Simpler mental model

3. **Minimal Abstraction**
   - No tRPC or complex API layer
   - Direct Prisma queries in server code
   - API routes only for webhooks and external APIs

**File Organization (target structure you will build):**

Note: The template provides minimal scaffolding. The structure below shows what your project will look like as you build features.

```
app/
├── api/              # API routes (health check provided)
├── actions/          # CREATE: Server Actions
└── [resource]/       # CREATE: Resource pages

lib/
├── prisma.ts         # Prisma singleton (provided)
├── env.ts            # Environment validation (provided)
└── validations.ts    # CREATE: Zod schemas

components/           # CREATE: React components
prisma/
└── schema.prisma     # Database schema (provided, add models)
```

**What This Stack Enforces:**
- Server Components as default
- Server Actions for most mutations
- Prisma for database access
- Zod for input validation

---

## Comparison Matrix

| Aspect | saas_t3 | ml_ai_fastapi | dashboard_refine | fullstack_nextjs |
|--------|---------|---------------|------------------|------------------|
| **Type Safety** | Maximum | Good | Good | Good |
| **API Style** | tRPC | REST/OpenAPI | Data Provider | Server Actions |
| **Database** | Prisma | SQLModel | External | Prisma |
| **Learning Curve** | Medium | Low-Medium | Medium | Low |
| **Client-Side JS** | Moderate | Minimal | Moderate | Minimal |
| **Third-Party Clients** | No | Yes | Via provider | Via API routes |
| **Monorepo Required** | Effectively yes | No | No | No |
| **Auto API Docs** | No | Yes (OpenAPI) | No | No |
| **Built-in CRUD** | No | No | Yes | No |

---

## When to Switch Stacks

Signs you may have chosen the wrong stack:

### Switch FROM saas_t3 TO ml_ai_fastapi if:
- You need to serve mobile apps or third-party clients
- Your team is more comfortable with Python
- You're building primarily an API without much frontend

### Switch FROM ml_ai_fastapi TO saas_t3 if:
- You're building a frontend-heavy SaaS
- You want tighter frontend-backend integration
- Your team is TypeScript-focused

### Switch FROM dashboard_refine TO fullstack_nextjs if:
- Your app is more content-focused than CRUD-focused
- You need more flexibility than Refine provides
- You're not building a traditional admin dashboard

### Switch FROM fullstack_nextjs TO saas_t3 if:
- You need stronger type safety across API boundaries
- You're building a complex SaaS product
- You want more structure and conventions

---

## Quality Tiers (All Stacks)

Each stack supports 4 quality tiers:

| Tier | Name | Best For | Key Features |
|------|------|----------|--------------|
| **1** | Essential | Prototypes, MVPs | Linting, formatting, basic tests (80% coverage) |
| **2** | Standard | Production apps | + Security scanning, pre-commit hooks |
| **3** | Comprehensive | Mission-critical | + Mutation testing, E2E tests, integration tests |
| **4** | Production-Ready | Enterprise | + Error tracking, observability, performance monitoring |

---

## Making Your Decision

### Step 1: Identify Your Primary Use Case
- SaaS product → `saas_t3` or `fullstack_nextjs`
- ML/AI backend → `ml_ai_fastapi`
- Admin dashboard → `dashboard_refine`
- General web app → `fullstack_nextjs`

### Step 2: Consider Your Team
- TypeScript experts → `saas_t3`
- Python experts → `ml_ai_fastapi`
- Frontend-focused → `dashboard_refine`
- Generalists → `fullstack_nextjs`

### Step 3: Consider Your Constraints
- Need third-party API access → `ml_ai_fastapi` or `fullstack_nextjs`
- Need maximum type safety → `saas_t3`
- Need rapid CRUD development → `dashboard_refine`
- Need simplicity → `fullstack_nextjs`

### Step 4: Start Building
Once you've chosen, run:
```bash
sk init
```

Then read:
- `ARCHITECTURE.md` in your project root for implementation patterns
- `.session/guides/PRD_WRITING_GUIDE.md` for writing your PRD

---

## Further Reading

After choosing your stack:

1. **Write your PRD** using `.session/guides/PRD_WRITING_GUIDE.md`
2. **Review patterns** in your project's `ARCHITECTURE.md`
3. **Create work items** with `/work-new`
4. **Start building** with `/start <work-item-id>`
