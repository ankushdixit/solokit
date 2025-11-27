import routerProvider from "@refinedev/nextjs-router";
import type { DataProvider } from "@refinedev/core";

/**
 * Refine configuration
 * This file centralizes all Refine-related configuration
 */

/**
 * Data Provider Configuration
 *
 * You MUST implement a data provider to connect Refine to your backend.
 * See ARCHITECTURE.md for detailed examples.
 *
 * Options:
 *
 * 1. REST API (@refinedev/simple-rest):
 *    npm install @refinedev/simple-rest
 *    import dataProvider from "@refinedev/simple-rest";
 *    export const refineDataProvider = dataProvider("https://api.example.com");
 *
 * 2. GraphQL (@refinedev/graphql):
 *    npm install @refinedev/graphql graphql-request
 *    import dataProvider, { GraphQLClient } from "@refinedev/graphql";
 *    const client = new GraphQLClient("https://api.example.com/graphql");
 *    export const refineDataProvider = dataProvider(client);
 *
 * 3. Supabase (@refinedev/supabase):
 *    npm install @refinedev/supabase @supabase/supabase-js
 *    import { dataProvider } from "@refinedev/supabase";
 *    import { supabaseClient } from "./supabase";
 *    export const refineDataProvider = dataProvider(supabaseClient);
 *
 * 4. Custom: Implement the DataProvider interface
 *
 * Documentation: https://refine.dev/docs/data/data-provider/
 */

// Placeholder data provider - Replace with your backend implementation
// This throws helpful errors to guide implementation
const placeholderDataProvider: DataProvider = {
  getList: async ({ resource }) => {
    throw new Error(
      `Data provider not configured. Attempted getList for "${resource}". ` +
        `See lib/refine.tsx and ARCHITECTURE.md for setup instructions.`
    );
  },
  getOne: async ({ resource, id }) => {
    throw new Error(
      `Data provider not configured. Attempted getOne for "${resource}" with id "${id}". ` +
        `See lib/refine.tsx and ARCHITECTURE.md for setup instructions.`
    );
  },
  create: async ({ resource }) => {
    throw new Error(
      `Data provider not configured. Attempted create for "${resource}". ` +
        `See lib/refine.tsx and ARCHITECTURE.md for setup instructions.`
    );
  },
  update: async ({ resource, id }) => {
    throw new Error(
      `Data provider not configured. Attempted update for "${resource}" with id "${id}". ` +
        `See lib/refine.tsx and ARCHITECTURE.md for setup instructions.`
    );
  },
  deleteOne: async ({ resource, id }) => {
    throw new Error(
      `Data provider not configured. Attempted deleteOne for "${resource}" with id "${id}". ` +
        `See lib/refine.tsx and ARCHITECTURE.md for setup instructions.`
    );
  },
  getApiUrl: () => "",
};

export const refineDataProvider = placeholderDataProvider;

/**
 * Router provider configuration
 * Integrates Refine with Next.js App Router
 */
export const refineRouterProvider = routerProvider;

/**
 * Resource definitions
 *
 * Define your resources here. Each resource maps to a backend endpoint.
 *
 * Example:
 * export const refineResources = [
 *   {
 *     name: "users",
 *     list: "/users",
 *     create: "/users/create",
 *     edit: "/users/edit/:id",
 *     show: "/users/show/:id",
 *     meta: { canDelete: true },
 *   },
 *   {
 *     name: "products",
 *     list: "/products",
 *     create: "/products/create",
 *     edit: "/products/edit/:id",
 *   },
 * ];
 */
export const refineResources: {
  name: string;
  list?: string;
  create?: string;
  edit?: string;
  show?: string;
  meta?: Record<string, unknown>;
}[] = [
  // Add your resources here
  // See ARCHITECTURE.md for examples
];

/**
 * Refine options
 * Global configuration for Refine behavior
 */
export const refineOptions = {
  syncWithLocation: true,
  warnWhenUnsavedChanges: true,
  useNewQueryKeys: true,
  projectId: "refine-dashboard",
};
