# Full-Stack Next.js Architecture Guide

This document describes the architecture, patterns, and conventions used in this Next.js application.

## Overview

This stack provides a minimal but complete full-stack foundation:

| Component        | Purpose                         |
| ---------------- | ------------------------------- |
| **Next.js 16**   | React framework with App Router |
| **Prisma**       | Type-safe database ORM          |
| **PostgreSQL**   | Production database             |
| **Zod**          | Runtime validation              |
| **Tailwind CSS** | Utility-first styling           |

## Architecture Decisions

### Decision 1: Server Components First

**What**: Default to React Server Components. Only use Client Components when necessary.

**Why**:

- Better performance (less JavaScript shipped to client)
- Direct database access in components
- Improved SEO
- Simpler data fetching

**When to use `"use client"`**:

- Event handlers (onClick, onChange, etc.)
- Browser APIs (localStorage, window, etc.)
- React hooks (useState, useEffect, etc.)
- Third-party client libraries

**Pattern**:

```typescript
// Server Component (default) - NO "use client"
export default async function Page() {
  const data = await prisma.user.findMany();  // Direct DB access
  return <div>{/* render data */}</div>;
}

// Client Component - only when needed
"use client";
export function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

**Implication**: If only a small part of a page needs interactivity, extract just that part into a Client Component.

### Decision 2: Prisma Client as `prisma`

**What**: The Prisma client is exported as `prisma` from `@/lib/prisma`.

**Why**:

- Explicit naming (you know it's Prisma)
- Follows official Prisma documentation
- Clear distinction from other database tools

**Usage**:

```typescript
import { prisma } from "@/lib/prisma";
const users = await prisma.user.findMany();
```

**Implication**: Never instantiate PrismaClient elsewhere. Always use the singleton.

### Decision 3: Server Actions Over API Routes

**What**: Use Server Actions for mutations. Use API Routes only when necessary.

**Why**:

- Simpler mental model
- No need to manage API endpoints
- Automatic form handling
- Progressive enhancement

**When to use Server Actions**:

- Form submissions
- Data mutations (create, update, delete)
- Any action triggered by user interaction

**When to use API Routes**:

- Webhooks from external services
- Public API endpoints
- Third-party integrations
- Long-polling or streaming

**Pattern**:

```typescript
// Server Action (preferred)
"use server";
export async function createUser(formData: FormData) {
  await prisma.user.create({ data: { name: formData.get("name") } });
  revalidatePath("/users");
}

// API Route (when needed)
// app/api/webhook/route.ts
export async function POST(request: Request) {
  const payload = await request.json();
  // Handle webhook
}
```

### Decision 4: Zod for Validation

**What**: All user input is validated with Zod schemas.

**Why**:

- Runtime type safety
- Excellent TypeScript integration
- Reusable validation logic
- Clear error messages

**Pattern**:

```typescript
import { z } from "zod";

const userSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

// In Server Action
const data = userSchema.parse(Object.fromEntries(formData));
```

**Implication**: Never trust client-side data. Always validate on the server.

### Decision 5: Environment Validation

**What**: Environment variables are validated at startup using Zod.

**Why**:

- Fail fast on misconfiguration
- Type-safe env vars
- Clear error messages

**Usage**:

```typescript
import { env } from "@/lib/env";
// NOT process.env.DATABASE_URL
const url = env.DATABASE_URL;
```

## Project Structure

```
.
├── app/                          # Next.js App Router
│   ├── api/
│   │   ├── example/route.ts     # Example API route
│   │   └── health/route.ts      # Health check endpoint
│   │
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   ├── error.tsx                 # Error boundary
│   └── loading.tsx               # Loading UI
│
├── components/
│   └── example-component.tsx    # Example component
│
├── lib/
│   ├── prisma.ts                # Prisma client singleton
│   ├── env.ts                   # Environment validation
│   ├── validations.ts           # Zod schemas
│   └── utils.ts                 # Utility functions
│
├── prisma/
│   └── schema.prisma            # Database schema
│
└── components.json              # shadcn/ui config
```

**Note**: The template provides a minimal starting point. As you build your application, you can add:

- `app/actions/` for Server Actions
- `app/[resource]/` directories for resource pages
- `components/ui/` for shadcn/ui components
- `components/forms/` for form components

## Key Files Reference

| File                       | Purpose                 | When to Modify             |
| -------------------------- | ----------------------- | -------------------------- |
| `lib/prisma.ts`            | Prisma client singleton | Rarely                     |
| `lib/env.ts`               | Environment validation  | Adding env vars            |
| `lib/validations.ts`       | Zod schemas             | Adding/changing validation |
| `app/api/example/route.ts` | Example API route       | Reference for new routes   |
| `app/api/health/route.ts`  | Health check endpoint   | Rarely                     |
| `prisma/schema.prisma`     | Database models         | Schema changes             |

## Code Patterns

The following patterns are recommended for building your application. The template provides a minimal starting point - these examples show how to extend it.

### Server Component Data Fetching

```typescript
// app/users/page.tsx (Server Component - NO "use client")
import { prisma } from "@/lib/prisma";

export default async function UsersPage() {
  // Direct database access in Server Component
  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
  });

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Server Action for Mutations

```typescript
// app/actions/users.ts
"use server";

import { prisma } from "@/lib/prisma";
import { userSchema } from "@/lib/validations";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function createUser(formData: FormData) {
  // Validate input
  const data = userSchema.parse({
    name: formData.get("name"),
    email: formData.get("email"),
  });

  // Create in database
  await prisma.user.create({ data });

  // Revalidate cache and redirect
  revalidatePath("/users");
  redirect("/users");
}

export async function updateUser(id: number, formData: FormData) {
  const data = userSchema.partial().parse({
    name: formData.get("name"),
    email: formData.get("email"),
  });

  await prisma.user.update({
    where: { id },
    data,
  });

  revalidatePath(`/users/${id}`);
  revalidatePath("/users");
}

export async function deleteUser(id: number) {
  await prisma.user.delete({ where: { id } });
  revalidatePath("/users");
  redirect("/users");
}
```

### Form with Server Action

```typescript
// app/users/new/page.tsx
import { createUser } from "@/app/actions/users";

export default function NewUserPage() {
  return (
    <form action={createUser}>
      <label>
        Name:
        <input name="name" required />
      </label>

      <label>
        Email:
        <input name="email" type="email" required />
      </label>

      <button type="submit">Create User</button>
    </form>
  );
}
```

### Client Component with Server Action

```typescript
// components/forms/user-form.tsx
"use client";

import { useFormStatus } from "react-dom";
import { createUser } from "@/app/actions/users";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Creating..." : "Create User"}
    </button>
  );
}

export function UserForm() {
  return (
    <form action={createUser}>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />
      <SubmitButton />
    </form>
  );
}
```

### API Route (When Needed)

```typescript
// app/api/users/route.ts
import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { userSchema } from "@/lib/validations";

export async function GET() {
  const users = await prisma.user.findMany();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  try {
    const json = await request.json();
    const data = userSchema.parse(json);

    const user = await prisma.user.create({ data });
    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
```

### Validation Schemas

```typescript
// lib/validations.ts
import { z } from "zod";

export const userSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email"),
});

export const postSchema = z.object({
  title: z.string().min(1, "Title is required"),
  content: z.string().optional(),
  published: z.boolean().default(false),
});

// Type inference
export type UserInput = z.infer<typeof userSchema>;
export type PostInput = z.infer<typeof postSchema>;
```

### Prisma Client Singleton

```typescript
// lib/prisma.ts
import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query"] : [],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
```

## Database Workflow

### Creating Migrations

```bash
# Create migration from schema changes
npx prisma migrate dev --name add_posts_table

# Apply migrations in production
npx prisma migrate deploy
```

### Prisma Client Generation

```bash
# Regenerate after schema changes
npx prisma generate
```

### Database Tools

```bash
# Open Prisma Studio (GUI)
npx prisma studio

# Reset database (development only!)
npx prisma migrate reset

# Seed database
npx prisma db seed
```

### Schema Example

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

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

## Caching and Revalidation

### Static vs Dynamic

```typescript
// Static (cached by default)
export default async function Page() {
  const data = await prisma.post.findMany();  // Cached
  return <div>{/* ... */}</div>;
}

// Dynamic (opt out of caching)
export const dynamic = "force-dynamic";
export default async function Page() {
  const data = await prisma.post.findMany();  // Fresh every request
  return <div>{/* ... */}</div>;
}
```

### Revalidation

```typescript
// Time-based revalidation
export const revalidate = 60; // Revalidate every 60 seconds

// On-demand revalidation (in Server Actions)
import { revalidatePath, revalidateTag } from "next/cache";

revalidatePath("/users"); // Revalidate specific path
revalidateTag("users"); // Revalidate by tag
```

## Troubleshooting

### Database Connection Errors

**Symptom**: Cannot connect to PostgreSQL

**Solutions**:

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` format
3. Ensure database exists: `createdb mydb`
4. Check firewall settings

### Prisma Client Not Found

**Symptom**: `@prisma/client` not found

**Solution**: Run `npx prisma generate`

### Type Errors After Schema Changes

**Symptom**: TypeScript errors with Prisma types

**Solutions**:

1. Run `npx prisma generate`
2. Restart TypeScript server in editor

### Server Action Errors

**Symptom**: Server Action not working

**Solutions**:

1. Ensure `"use server"` directive is at top of file
2. Check that action is async
3. Verify form is using action attribute correctly

### Hydration Errors

**Symptom**: Server/client content mismatch

**Solutions**:

1. Don't use random values in Server Components
2. Ensure dates are serialized consistently
3. Check for browser-only APIs in Server Components

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions)
- [Prisma Documentation](https://www.prisma.io/docs)
- [Zod Documentation](https://zod.dev/)
- [Tailwind CSS](https://tailwindcss.com/docs)
