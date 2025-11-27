import { createCallerFactory, createTRPCRouter } from "@/server/api/trpc";

// Import your routers here
// Example: import { postsRouter } from "@/server/api/routers/posts";

/**
 * This is the primary router for your server.
 *
 * All routers added in /api/routers should be manually added here.
 */
export const appRouter = createTRPCRouter({
  // Add your routers here
  // Example: posts: postsRouter,
});

// export type definition of API
export type AppRouter = typeof appRouter;

/**
 * Create a server-side caller for the tRPC API.
 */
export const createCaller = createCallerFactory(appRouter);
