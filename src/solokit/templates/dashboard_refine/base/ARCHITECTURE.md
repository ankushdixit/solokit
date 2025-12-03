# Dashboard Refine Architecture Guide

This document describes the architecture, patterns, and conventions used in this Refine.dev dashboard application.

## Overview

This stack is optimized for building admin dashboards and data-intensive CRUD applications:

| Component           | Purpose                         |
| ------------------- | ------------------------------- |
| **Refine.dev**      | Headless CRUD framework         |
| **Next.js 16**      | React framework with App Router |
| **shadcn/ui**       | High-quality UI components      |
| **Tailwind CSS**    | Utility-first styling           |
| **React Hook Form** | Form state management           |
| **Zod**             | Schema validation               |

## Building From Scratch

This is a minimal scaffolding project. You'll create files from scratch following the patterns below.

### Adding a New Resource

1. **Data Provider**: Configure your backend connection in `lib/refine.tsx`
2. **Resource Config**: Add resource definition to `lib/refine.tsx`
3. **List Page**: Create `app/(dashboard)/[resource]/page.tsx`
4. **Create Page**: Create `app/(dashboard)/[resource]/create/page.tsx`
5. **Edit Page**: Create `app/(dashboard)/[resource]/edit/[id]/page.tsx`
6. **Show Page**: Create `app/(dashboard)/[resource]/show/[id]/page.tsx`
7. **Navigation**: Add route to `components/layout/sidebar.tsx`
8. **Tests**: Create `__tests__/` alongside each page

### Example: Adding a "Products" Resource

These are files you will CREATE (not existing template files):

```
lib/refine.tsx              # UPDATE: Add resource definition + data provider
lib/validations.ts          # CREATE: Zod schemas for Product validation
app/(dashboard)/products/
├── page.tsx                # CREATE: List products (useList/useTable)
├── create/page.tsx         # CREATE: Create form (useForm)
├── edit/[id]/page.tsx      # CREATE: Edit form (useForm)
├── show/[id]/page.tsx      # CREATE: Detail view (useShow)
└── __tests__/              # CREATE: Tests for each page
components/layout/sidebar.tsx  # UPDATE: Add Products nav link
```

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

### Decision 2: Data Provider Required

**What**: You must configure a data provider to connect to your backend.

**Why**:

- Refine needs a data provider to function
- The placeholder provider throws helpful errors guiding you to configure it

**Configuration** (in `lib/refine.tsx`):

```typescript
// Option 1: REST API
import dataProvider from "@refinedev/simple-rest";
export const refineDataProvider = dataProvider("https://api.example.com");

// Option 2: GraphQL
import dataProvider, { GraphQLClient } from "@refinedev/graphql";
const client = new GraphQLClient("https://api.example.com/graphql");
export const refineDataProvider = dataProvider(client);

// Option 3: Supabase
import { dataProvider } from "@refinedev/supabase";
import { supabaseClient } from "./supabase";
export const refineDataProvider = dataProvider(supabaseClient);
```

See [Refine Data Provider Documentation](https://refine.dev/docs/data/data-provider/) for all options.

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
│   └── [resource]/       # Resource pages
└── layout.tsx            # Root layout
```

### Decision 5: Resource-Based Routing

**What**: Each Refine resource maps to a folder in `(dashboard)/`.

**Why**:

- Predictable URL structure
- Co-located resource pages
- Refine's routing integration

**Pattern**:

```typescript
// lib/refine.tsx
export const refineResources = [
  {
    name: "users",
    list: "/users",
    create: "/users/create",
    edit: "/users/edit/:id",
    show: "/users/show/:id",
  },
];
```

## Project Structure

```
.
├── app/
│   ├── (dashboard)/              # Dashboard route group
│   │   ├── layout.tsx           # Dashboard layout with sidebar/header
│   │   └── page.tsx             # Dashboard home page
│   │
│   ├── api/
│   │   └── health/route.ts      # Health check endpoint
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
│   └── ui/                      # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       └── table.tsx
│
├── lib/
│   ├── refine.tsx              # Refine configuration and data provider
│   └── utils.ts                # Utility functions
│
├── providers/
│   └── refine-provider.tsx     # Refine context provider
│
└── components.json             # shadcn/ui configuration
```

**Note**: The template provides a minimal starting point. As you build, add:

- `app/(dashboard)/[resource]/` for resource pages
- `components/forms/` for form components
- `lib/validations.ts` for Zod schemas

## Key Files Reference

| File                            | Purpose                            | When to Modify                     |
| ------------------------------- | ---------------------------------- | ---------------------------------- |
| `lib/refine.tsx`                | Refine resources and data provider | Adding resources, changing backend |
| `providers/refine-provider.tsx` | Refine context provider            | Changing provider config           |
| `app/(dashboard)/layout.tsx`    | Dashboard layout                   | Changing sidebar/header            |
| `components/ui/*`               | UI primitives                      | Rarely (customize via CSS)         |
| `app/globals.css`               | Theme variables                    | Changing colors/theming            |

## Code Patterns

### List Page with useList

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
import { z } from "zod";
import { Button } from "@/components/ui/button";

const userSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
});

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
          <label htmlFor="name">Name</label>
          <input id="name" {...register("name")} className="w-full border p-2" />
          {errors.name && <p className="text-red-500 text-sm">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" {...register("email")} className="w-full border p-2" />
          {errors.email && <p className="text-red-500 text-sm">{errors.email.message}</p>}
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
export const refineResources = [
  {
    name: "users",
    list: "/users",
    create: "/users/create",
    edit: "/users/edit/:id",
    show: "/users/show/:id",
    meta: {
      label: "Users",
      canDelete: true,
    },
  },
  {
    name: "products",
    list: "/products",
    create: "/products/create",
    edit: "/products/edit/:id",
    meta: {
      label: "Products",
    },
  },
];
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

## Data Provider Options

### REST API

```typescript
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

### Custom Data Provider

```typescript
import type { DataProvider } from "@refinedev/core";

const customDataProvider: DataProvider = {
  getList: async ({ resource, pagination, filters, sorters }) => {
    const response = await fetch(`/api/${resource}`);
    const data = await response.json();
    return { data, total: data.length };
  },
  getOne: async ({ resource, id }) => {
    const response = await fetch(`/api/${resource}/${id}`);
    const data = await response.json();
    return { data };
  },
  create: async ({ resource, variables }) => {
    const response = await fetch(`/api/${resource}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(variables),
    });
    const data = await response.json();
    return { data };
  },
  update: async ({ resource, id, variables }) => {
    const response = await fetch(`/api/${resource}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(variables),
    });
    const data = await response.json();
    return { data };
  },
  deleteOne: async ({ resource, id }) => {
    await fetch(`/api/${resource}/${id}`, { method: "DELETE" });
    return { data: { id } };
  },
  getApiUrl: () => "/api",
};
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

### Data Provider Not Configured

**Symptom**: Error "Data provider not configured"

**Solution**: Configure a real data provider in `lib/refine.tsx`. See the Data Provider Options section above.

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

## Tailwind CSS v4 Configuration

This template uses **Tailwind CSS v4** with CSS-first configuration. The comprehensive shadcn/ui theming system is implemented via `@theme` blocks in CSS.

### Configuration Files

| File | Purpose |
| ---- | ------- |
| `app/globals.css` | Main CSS with `@import "tailwindcss"`, `@theme` block, and shadcn/ui color tokens |
| `tailwind.config.ts` | Minimal config (only needed for plugins) |
| `postcss.config.mjs` | PostCSS configuration with `@tailwindcss/postcss` |

### Color System

The template includes a complete shadcn/ui color system defined in `globals.css`:

```css
@import "tailwindcss";

@theme {
  /* Color tokens - generates utilities like bg-primary, text-muted-foreground */
  --color-background: hsl(0 0% 100%);
  --color-foreground: hsl(222.2 84% 4.9%);
  --color-primary: hsl(222.2 47.4% 11.2%);
  --color-primary-foreground: hsl(210 40% 98%);
  --color-secondary: hsl(210 40% 96.1%);
  --color-secondary-foreground: hsl(222.2 47.4% 11.2%);
  --color-muted: hsl(210 40% 96.1%);
  --color-muted-foreground: hsl(215.4 16.3% 46.9%);
  /* ... more tokens */
}
```

### Available Color Utilities

The theme generates these utility classes:

| Utility | Usage |
| ------- | ----- |
| `bg-background`, `text-foreground` | Base colors |
| `bg-primary`, `text-primary-foreground` | Primary actions |
| `bg-secondary`, `text-secondary-foreground` | Secondary actions |
| `bg-destructive`, `text-destructive-foreground` | Destructive actions |
| `bg-muted`, `text-muted-foreground` | Muted/disabled states |
| `bg-accent`, `text-accent-foreground` | Accent/highlight |
| `bg-card`, `text-card-foreground` | Card components |
| `bg-popover`, `text-popover-foreground` | Popover/dropdown |
| `border-border`, `bg-input`, `ring-ring` | Form elements |

### Dark Mode

Dark mode is implemented via the `.dark` class on the `<html>` or `<body>` element:

```css
.dark {
  --color-background: hsl(222.2 84% 4.9%);
  --color-foreground: hsl(210 40% 98%);
  /* ... dark mode overrides */
}
```

To toggle dark mode programmatically:

```typescript
document.documentElement.classList.toggle('dark');
```

### Adding Custom Colors

Add new colors to the `@theme` block:

```css
@theme {
  /* Existing colors... */

  /* Custom additions */
  --color-success: hsl(142.1 76.2% 36.3%);
  --color-success-foreground: hsl(355.7 100% 97.3%);
  --color-warning: hsl(47.9 95.8% 53.1%);
  --color-warning-foreground: hsl(26 83.3% 14.1%);
}
```

### Border Radius

Custom radius tokens are defined in `@theme`:

```css
@theme {
  --radius-lg: 0.5rem;
  --radius-md: calc(0.5rem - 2px);
  --radius-sm: calc(0.5rem - 4px);
}
```

Use via utilities: `rounded-lg`, `rounded-md`, `rounded-sm`.

### Key Differences from Tailwind v3

| v3 Pattern | v4 Pattern |
| ---------- | ---------- |
| `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| `tailwind.config.ts` theme.extend.colors | `@theme { --color-*: value }` in CSS |
| `hsl(var(--primary))` in config | `--color-primary: hsl(...)` directly in CSS |
| `content: [...]` in config | Automatic content detection |
| `darkMode: "class"` in config | `.dark { }` CSS overrides |

## Resources

- [Refine.dev Documentation](https://refine.dev/docs/)
- [Refine Hooks Reference](https://refine.dev/docs/api-reference/core/hooks/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [Tailwind CSS v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide)
