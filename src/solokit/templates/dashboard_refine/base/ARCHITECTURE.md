# Dashboard Refine Architecture Guide

This document describes the architecture, patterns, and conventions used in this Refine.dev dashboard application.

## Overview

This stack is optimized for building admin dashboards and data-intensive CRUD applications:

| Component | Purpose |
|-----------|---------|
| **Refine.dev** | Headless CRUD framework |
| **Next.js 16** | React framework with App Router |
| **shadcn/ui** | High-quality UI components |
| **Tailwind CSS** | Utility-first styling |
| **React Hook Form** | Form state management |
| **Zod** | Schema validation |

## Architecture Decisions

### Decision 1: Refine.dev for CRUD Operations

**What**: All data operations (Create, Read, Update, Delete) go through Refine's data provider system.

**Why**:
- Standardized data layer abstraction
- Built-in hooks for common patterns (useTable, useForm, useShow)
- Easy backend switching (REST, GraphQL, Supabase, etc.)
- Automatic caching and refetching

**Trade-offs**:
- Learning curve for Refine concepts
- Some custom scenarios need workarounds

**Implication**: Never write custom fetch/axios calls for CRUD operations. Always use Refine hooks.

### Decision 2: Mock Data Provider for Development

**What**: The template includes a mock data provider that simulates a backend.

**Why**:
- Quick start without backend setup
- Explore all features immediately
- Test UI independently

**CRITICAL WARNING**:
The mock data provider is for **DEVELOPMENT ONLY**. You MUST replace it with a real data provider before production.

**Migration Path**:
```typescript
// Current (development - uses mock/simple data)
// See lib/refine.tsx for current data provider configuration

// Production (example with REST)
import dataProvider from "@refinedev/simple-rest";
const API_URL = "https://api.example.com";
```

### Decision 3: shadcn/ui Component System

**What**: Use shadcn/ui components with the built-in theming system.

**Why**:
- High-quality, accessible components
- Full customization via CSS variables
- Dark mode support built-in
- Consistent design language

**Theme Configuration**:
- CSS variables defined in `app/globals.css`
- 16 semantic color tokens (background, foreground, primary, etc.)
- Automatic light/dark mode switching

**Implication**: Always use components from `@/components/ui/`. Don't install competing UI libraries.

### Decision 4: Route Groups for Layout

**What**: Dashboard pages live in the `(dashboard)` route group.

**Why**:
- Shared layout without URL prefix
- Clear separation of dashboard vs public pages
- Layout components applied automatically

**Structure**:
```
app/
├── (dashboard)/           # Dashboard route group
│   ├── layout.tsx        # Dashboard layout (sidebar, header)
│   ├── page.tsx          # Dashboard home
│   └── users/            # Resource pages
└── layout.tsx            # Root layout
```

### Decision 5: Resource-Based Routing

**What**: Each Refine resource maps to a folder in `(dashboard)/`.

**Why**:
- Predictable URL structure
- Co-located resource pages
- Refine's routing integration

**Pattern**:
```
resources: [
  {
    name: "users",
    list: "/users",
    create: "/users/create",
    edit: "/users/edit/:id",
    show: "/users/show/:id",
  }
]
```

## Project Structure

```
.
├── app/
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── layout.tsx           # Dashboard layout with sidebar/header
│   │   ├── page.tsx             # Dashboard home page
│   │   └── users/
│   │       └── page.tsx         # Example list page
│   │
│   ├── api/
│   │   └── health/route.ts     # Health check endpoint
│   │
│   ├── layout.tsx               # Root layout (Refine provider)
│   ├── globals.css              # Global styles & theme variables
│   ├── error.tsx                # Error boundary
│   └── loading.tsx              # Loading UI
│
├── components/
│   ├── client-refine-wrapper.tsx  # Client-side Refine wrapper
│   │
│   ├── layout/                  # Layout components
│   │   ├── header.tsx          # Top navigation
│   │   └── sidebar.tsx         # Side navigation
│   │
│   ├── forms/                   # Form components
│   │   └── user-form.tsx       # Example form with validation
│   │
│   └── ui/                      # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       └── table.tsx
│
├── lib/
│   ├── refine.tsx              # Refine configuration and data provider
│   ├── validations.ts          # Zod schemas
│   └── utils.ts                # Utility functions
│
├── providers/
│   └── refine-provider.tsx     # Refine context provider
│
└── components.json             # shadcn/ui configuration
```

**Note**: The template provides a basic users list page. To add full CRUD functionality, create additional pages following the patterns in Code Patterns section:
- `users/create/page.tsx` for create
- `users/edit/[id]/page.tsx` for edit
- `users/show/[id]/page.tsx` for detail view

## Key Files Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `lib/refine.tsx` | Refine resources and data provider | Adding resources, changing backend |
| `lib/validations.ts` | Zod schemas for forms | Adding/changing form validation |
| `providers/refine-provider.tsx` | Refine context provider | Changing provider config |
| `app/(dashboard)/layout.tsx` | Dashboard layout | Changing sidebar/header |
| `components/ui/*` | UI primitives | Rarely (customize via CSS) |
| `app/globals.css` | Theme variables | Changing colors/theming |

## Code Patterns

### List Page with useList

The template uses `useList` for simple data fetching:

```typescript
// app/(dashboard)/users/page.tsx
"use client";

import { useList } from "@refinedev/core";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface User {
  id: number | string;
  name: string;
  email: string;
}

export default function UsersPage() {
  const {
    query: { data, isLoading },
  } = useList<User>({
    resource: "users",
  });

  const users = data?.data ?? [];

  if (isLoading) return <div>Loading...</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>All Users</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.id}</TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.email}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
```

**Alternative: useTable for pagination**

For pages that need built-in pagination, use `useTable`:

```typescript
import { useTable } from "@refinedev/core";

const {
  tableQueryResult: { data, isLoading },
  current,
  setCurrent,
  pageCount,
} = useTable({
  resource: "users",
  pagination: { pageSize: 10 },
});
```

### Create/Edit Form with useForm

```typescript
// app/(dashboard)/users/create/page.tsx
"use client";

import { useForm } from "@refinedev/react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { userSchema } from "@/lib/validations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function UserCreate() {
  const {
    refineCore: { onFinish, formLoading },
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    refineCoreProps: {
      resource: "users",
      action: "create",
      redirect: "list",
    },
    resolver: zodResolver(userSchema),
  });

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-4">Create User</h1>

      <form onSubmit={handleSubmit(onFinish)} className="space-y-4">
        <div>
          <Label htmlFor="name">Name</Label>
          <Input id="name" {...register("name")} />
          {errors.name && (
            <p className="text-red-500 text-sm">{errors.name.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register("email")} />
          {errors.email && (
            <p className="text-red-500 text-sm">{errors.email.message}</p>
          )}
        </div>

        <Button type="submit" disabled={formLoading}>
          {formLoading ? "Creating..." : "Create User"}
        </Button>
      </form>
    </div>
  );
}
```

### Detail Page with useShow

```typescript
// app/(dashboard)/users/show/[id]/page.tsx
"use client";

import { useShow } from "@refinedev/core";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function UserShow({ params }: { params: { id: string } }) {
  const { queryResult } = useShow({
    resource: "users",
    id: params.id,
  });

  const { data, isLoading } = queryResult;
  const user = data?.data;

  if (isLoading) return <div>Loading...</div>;
  if (!user) return <div>User not found</div>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{user.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-2">
          <div>
            <dt className="font-medium">Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt className="font-medium">Created At</dt>
            <dd>{new Date(user.createdAt).toLocaleDateString()}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
```

### Configuring Resources

```typescript
// lib/refine.tsx
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import { mockDataProvider } from "@/providers/mock-data-provider";

export const refineResources = [
  {
    name: "users",
    list: "/users",
    create: "/users/create",
    edit: "/users/edit/:id",
    show: "/users/show/:id",
    meta: {
      label: "Users",
      icon: "users",
    },
  },
  {
    name: "products",
    list: "/products",
    create: "/products/create",
    edit: "/products/edit/:id",
    meta: {
      label: "Products",
      icon: "package",
    },
  },
];

export function RefineProvider({ children }: { children: React.ReactNode }) {
  return (
    <Refine
      dataProvider={mockDataProvider}  // REPLACE IN PRODUCTION
      routerProvider={routerProvider}
      resources={refineResources}
      options={{
        syncWithLocation: true,
        warnWhenUnsavedChanges: true,
      }}
    >
      {children}
    </Refine>
  );
}
```

### Validation Schemas

```typescript
// lib/validations.ts
import { z } from "zod";

export const userSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  role: z.enum(["admin", "user", "guest"]).optional(),
});

export const productSchema = z.object({
  name: z.string().min(1, "Name is required"),
  price: z.number().positive("Price must be positive"),
  description: z.string().optional(),
});

export type UserFormData = z.infer<typeof userSchema>;
export type ProductFormData = z.infer<typeof productSchema>;
```

## Data Provider Migration

### REST API

```typescript
// Replace mock provider with REST
import dataProvider from "@refinedev/simple-rest";

const API_URL = "https://api.example.com";

<Refine dataProvider={dataProvider(API_URL)} />
```

### GraphQL

```typescript
import dataProvider, { GraphQLClient } from "@refinedev/graphql";

const client = new GraphQLClient("https://api.example.com/graphql");

<Refine dataProvider={dataProvider(client)} />
```

### Supabase

```typescript
import { dataProvider } from "@refinedev/supabase";
import { supabaseClient } from "@/lib/supabase";

<Refine dataProvider={dataProvider(supabaseClient)} />
```

## Theming

### CSS Variables

```css
/* app/globals.css */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  /* ... more variables */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... dark mode overrides */
}
```

### Using Theme Colors

```typescript
// In components
<div className="bg-background text-foreground">
  <Button className="bg-primary text-primary-foreground">
    Click me
  </Button>
</div>
```

## Troubleshooting

### Mock Data Not Showing

**Symptom**: Empty tables, no data

**Solutions**:
1. Check browser console for errors
2. Verify mock data provider is properly configured
3. Ensure resource name matches in useTable/useForm

### Form Validation Not Working

**Symptom**: Form submits without validation

**Solutions**:
1. Ensure `zodResolver` is passed to `useForm`
2. Check that schema matches form fields
3. Verify error messages are displayed

### Styling Issues

**Symptom**: Components unstyled or wrong colors

**Solutions**:
1. Verify `globals.css` is imported in root layout
2. Check CSS variable definitions
3. Ensure Tailwind is processing your files

### Type Errors

**Symptom**: TypeScript errors with Refine hooks

**Solutions**:
1. Check resource type definitions
2. Ensure proper typing for data responses
3. Use generics with hooks: `useTable<User>()`

## Resources

- [Refine.dev Documentation](https://refine.dev/docs/)
- [Refine Hooks Reference](https://refine.dev/docs/api-reference/core/hooks/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)
