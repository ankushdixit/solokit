# T3 Stack Architecture Guide

This document describes the architecture, patterns, and conventions used in this T3 Stack application.

## Overview

The T3 Stack is a full-stack TypeScript framework optimized for type safety and developer experience:

| Component          | Purpose                         |
| ------------------ | ------------------------------- |
| **Next.js 16**     | React framework with App Router |
| **tRPC**           | End-to-end typesafe APIs        |
| **Prisma**         | Type-safe database ORM          |
| **PostgreSQL**     | Production database             |
| **TanStack Query** | Data fetching and caching       |
| **Zod**            | Runtime validation              |
| **Tailwind CSS**   | Utility-first styling           |

## Building From Scratch

This is a minimal scaffolding project. You'll create files from scratch following the patterns below.

### Adding a New Feature

1. **Database Model**: Add model to `prisma/schema.prisma`
2. **Generate Client**: Run `npx prisma generate`
3. **Migration**: Run `npx prisma migrate dev --name add_[feature]`
4. **tRPC Router**: Create `server/api/routers/[feature].ts`
5. **Register Router**: Add to `server/api/root.ts`
6. **Component**: Create `components/[feature]/` (use `"use client"` for interactivity)
7. **Page**: Create `app/[feature]/page.tsx`
8. **Tests**: Create tests in `__tests__/` directories

### Example: Adding a "Posts" Feature

These are files you will CREATE (not existing template files):

```
prisma/schema.prisma            # ADD: Post model to existing file
server/api/routers/posts.ts     # CREATE: tRPC router with getAll, create, etc.
server/api/root.ts              # UPDATE: Register postsRouter
components/posts/               # CREATE: Post-specific components
app/posts/page.tsx              # CREATE: Posts list page
app/posts/__tests__/            # CREATE: Tests for posts pages
```

### Type Safety Flow

The T3 Stack provides end-to-end type safety:

```
Prisma Schema → Prisma Client → tRPC Router → tRPC Client → React Component
     ↓              ↓              ↓              ↓              ↓
   model Post    db.post       postsRouter   api.posts     useQuery()
```

Changes to your Prisma schema automatically flow through to your React components with full TypeScript inference.

## Architecture Decisions

### Decision 1: tRPC for API Layer

**What**: All API communication uses tRPC instead of REST or GraphQL.

**Why**:

- Full stack type safety without code generation
- Automatic TypeScript inference from server to client
- Excellent DX with autocomplete everywhere
- No need to maintain API documentation
- Automatic request batching

**Trade-offs**:

- TypeScript only (no other language clients)
- Requires shared code (monorepo or fullstack repo)
- Not suitable for public APIs

**Implication**: Never create REST endpoints in `/app/api/` for internal data fetching. All server communication goes through tRPC routers.

### Decision 2: Prisma Client as `db`

**What**: The Prisma client is exported as `db` from `@/server/db`.

**Why**:

- T3 Stack community convention
- Shorter, cleaner imports
- Consistent with create-t3-app

**Usage**:

```typescript
import { db } from "@/server/db";
const users = await db.user.findMany();
```

**Implication**: Always import from `@/server/db`, never instantiate Prisma client elsewhere.

### Decision 3: Server/Client Separation

**What**: All server-side code lives in `server/` directory.

**Why**:

- Clear boundary between server and client code
- Prevents accidental client-side imports of server code
- Makes security audits easier

**Implication**:

- Never import from `server/` in client components
- Database access only happens in `server/`

### Decision 4: Environment Validation

**What**: All environment variables are validated at startup using Zod in `lib/env.ts`.

**Why**:

- Fail fast on misconfiguration
- Type-safe env vars throughout the app
- Clear error messages for missing/invalid vars

**Usage**:

```typescript
import { env } from "@/lib/env";
// NOT process.env.DATABASE_URL
const url = env.DATABASE_URL;
```

**Implication**: Always add new env vars to the schema before using them.

### Decision 5: SuperJSON Serialization

**What**: tRPC uses SuperJSON for data serialization.

**Why**:

- Automatic handling of Date, Map, Set, BigInt
- No manual serialization needed
- Preserves JavaScript types across the wire

**Implication**: You can return Dates and other complex types from procedures without transformation.

## Project Structure

```
.
├── app/                          # Next.js App Router
│   ├── api/
│   │   ├── health/              # Health check endpoint
│   │   └── trpc/[trpc]/         # tRPC HTTP handler (DO NOT ADD REST ROUTES)
│   ├── globals.css               # Global styles & Tailwind
│   ├── layout.tsx                # Root layout with tRPC provider
│   ├── page.tsx                  # Home page
│   ├── error.tsx                 # Error boundary
│   └── loading.tsx               # Loading UI
│
├── components/                   # React components (add yours here)
│
├── lib/                          # Client utilities
│   ├── api.tsx                   # tRPC React provider and hooks
│   ├── utils.ts                  # Utility functions (cn helper)
│   └── env.ts                    # Environment validation
│
├── server/                       # Server-only code (NEVER import in client)
│   ├── api/
│   │   ├── root.ts              # Root router (combines all routers)
│   │   ├── trpc.ts              # tRPC initialization and context
│   │   └── routers/             # Add your routers here
│   └── db.ts                     # Prisma client singleton
│
├── prisma/
│   └── schema.prisma             # Database schema (add your models)
│
└── components.json               # shadcn/ui configuration
```

## Key Files Reference

| File                      | Purpose                                  | When to Modify                |
| ------------------------- | ---------------------------------------- | ----------------------------- |
| `server/api/trpc.ts`      | tRPC initialization, context, procedures | Adding auth, changing context |
| `server/api/root.ts`      | Root router combining all routers        | Adding new routers            |
| `server/api/routers/*.ts` | Individual feature routers               | Adding new API endpoints      |
| `server/db.ts`            | Prisma client singleton                  | Rarely (singleton pattern)    |
| `lib/api.tsx`             | tRPC React provider                      | Adding React Query options    |
| `lib/env.ts`              | Environment validation                   | Adding new env vars           |
| `prisma/schema.prisma`    | Database models                          | Adding/changing data models   |

## Code Patterns

### Creating a tRPC Router

```typescript
// server/api/routers/posts.ts
import { z } from "zod";
import { createTRPCRouter, publicProcedure, protectedProcedure } from "@/server/api/trpc";

export const postsRouter = createTRPCRouter({
  // Query - for fetching data
  getAll: publicProcedure.query(async ({ ctx }) => {
    return await ctx.db.post.findMany({
      orderBy: { createdAt: "desc" },
    });
  }),

  // Query with input
  getById: publicProcedure.input(z.object({ id: z.number() })).query(async ({ ctx, input }) => {
    return await ctx.db.post.findUnique({
      where: { id: input.id },
    });
  }),

  // Mutation - for creating/updating/deleting
  create: protectedProcedure
    .input(
      z.object({
        title: z.string().min(1),
        content: z.string(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      return await ctx.db.post.create({
        data: {
          ...input,
          authorId: ctx.session.user.id,
        },
      });
    }),
});
```

### Registering a Router

```typescript
// server/api/root.ts
import { createTRPCRouter } from "./trpc";
import { postsRouter } from "./routers/posts";

export const appRouter = createTRPCRouter({
  posts: postsRouter, // Add new routers here
});

export type AppRouter = typeof appRouter;
```

### Client Component with tRPC

```typescript
// components/posts-list.tsx
"use client";

import { api } from "@/lib/api";

export function PostsList() {
  // Query hook
  const posts = api.posts.getAll.useQuery();

  // Mutation hook
  const createPost = api.posts.create.useMutation({
    onSuccess: () => {
      // Invalidate and refetch
      posts.refetch();
    },
  });

  if (posts.isLoading) return <div>Loading...</div>;
  if (posts.error) return <div>Error: {posts.error.message}</div>;

  return (
    <div>
      {posts.data?.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.content}</p>
        </article>
      ))}
    </div>
  );
}
```

### Server Component with tRPC

```typescript
// app/posts/page.tsx (Server Component - NO "use client")
import { api } from "@/lib/api";

export default async function PostsPage() {
  // Direct server-side call
  const posts = await api.posts.getAll();

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### Protected Procedures (Auth Required)

```typescript
// server/api/trpc.ts
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({ code: "UNAUTHORIZED" });
  }
  return next({
    ctx: {
      session: ctx.session,
    },
  });
});
```

## Database Workflow

### Creating Migrations

```bash
# Create a new migration
npx prisma migrate dev --name add_posts_table

# Apply migrations (production)
npx prisma migrate deploy
```

### Prisma Client Generation

```bash
# Regenerate after schema changes
npx prisma generate
```

### Database Inspection

```bash
# Open Prisma Studio (GUI)
npx prisma studio

# Introspect existing database
npx prisma db pull
```

### Schema Example

```prisma
// prisma/schema.prisma
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([email])
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([authorId])
}
```

## Troubleshooting

### tRPC Type Errors

**Symptom**: Types not updating after adding procedures

**Solutions**:

1. Ensure router is registered in `server/api/root.ts`
2. Restart TypeScript server (VS Code: Cmd/Ctrl+Shift+P → "Restart TS Server")
3. Check for circular imports

### Database Connection Errors

**Symptom**: Cannot connect to database

**Solutions**:

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` format in `.env`
3. Ensure database exists
4. Run `npx prisma generate`

### Hydration Mismatches

**Symptom**: Server/client content mismatch warnings

**Solutions**:

1. Ensure dates are serialized consistently
2. Don't use `Math.random()` or `Date.now()` in render
3. Use SuperJSON for complex types

### Serialization Errors

**Symptom**: Cannot serialize certain values

**Solutions**:

1. SuperJSON handles Date, Map, Set, BigInt automatically
2. For custom classes, transform to plain objects
3. Check for undefined values in responses

## Tailwind CSS v4 Configuration

This template uses **Tailwind CSS v4** with CSS-first configuration. Theme customization is done in CSS rather than JavaScript.

### Configuration Files

| File | Purpose |
| ---- | ------- |
| `app/globals.css` | Main CSS file with `@import "tailwindcss"` and `@theme` block |
| `tailwind.config.ts` | Minimal config (only needed for plugins) |
| `postcss.config.mjs` | PostCSS configuration with `@tailwindcss/postcss` |

### Adding Custom Colors

In Tailwind v4, colors are defined in CSS using the `@theme` directive with `--color-*` namespace:

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  /* Custom colors - generates bg-*, text-*, border-* utilities */
  --color-brand: #3b82f6;
  --color-brand-dark: #1d4ed8;
  --color-surface: #f8fafc;
}
```

This generates utilities like `bg-brand`, `text-brand-dark`, `border-surface`, etc.

### Dark Mode

Dark mode is implemented via CSS media query:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #0a0a0a;
    --color-foreground: #ededed;
  }
}
```

### Custom Utilities

Use the `@utility` directive for custom utilities:

```css
@utility text-balance {
  text-wrap: balance;
}
```

### Adding shadcn/ui Components

To add shadcn/ui components:

1. Run `npx shadcn@latest init`
2. Extend the `@theme` block in `globals.css` with additional color tokens
3. Update `components.json` as needed

### Key Differences from Tailwind v3

| v3 Pattern | v4 Pattern |
| ---------- | ---------- |
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `tailwind.config.ts` theme.extend.colors | `@theme { --color-*: value }` in CSS |
| `content: [...]` in config | Automatic content detection |
| `@layer utilities` | `@utility name { ... }` |

## Resources

- [T3 Stack Documentation](https://create.t3.gg/)
- [tRPC Documentation](https://trpc.io/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zod Documentation](https://zod.dev/)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [Tailwind CSS v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide)
