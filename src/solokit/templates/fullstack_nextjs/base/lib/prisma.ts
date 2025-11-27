/**
 * Prisma Client Instance
 *
 * This file implements the singleton pattern for Prisma Client to prevent
 * multiple instances during development (due to hot-reloading).
 *
 * Export name: "prisma"
 * This template uses the explicit name "prisma" to make it clear you're working
 * with Prisma Client. This is the standard pattern in the Prisma documentation.
 *
 * Usage:
 * import { prisma } from "@/lib/prisma";
 * const items = await prisma.yourModel.findMany();
 */

import { PrismaClient } from "@prisma/client";

const createPrismaClient = () =>
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  });

const globalForPrisma = globalThis as unknown as {
  prisma: ReturnType<typeof createPrismaClient> | undefined;
};

export const prisma = globalForPrisma.prisma ?? createPrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
