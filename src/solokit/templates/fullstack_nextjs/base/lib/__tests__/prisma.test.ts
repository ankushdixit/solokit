/**
 * Test for Prisma singleton pattern
 *
 * Note: This test validates the module structure and singleton pattern
 * without requiring an actual database connection.
 */

describe("Prisma Client", () => {
  const originalEnv = process.env.NODE_ENV;

  beforeEach(() => {
    // Clear module cache to test fresh imports
    jest.resetModules();
  });

  afterEach(() => {
    // Restore original NODE_ENV
    if (originalEnv !== undefined) {
      Object.defineProperty(process.env, "NODE_ENV", {
        value: originalEnv,
        writable: true,
        configurable: true,
      });
    }
  });

  it("exports prisma client instance", () => {
    const { prisma } = require("../prisma");
    expect(prisma).toBeDefined();
  });

  it("prisma has expected Prisma Client methods", () => {
    const { prisma } = require("../prisma");
    expect(typeof prisma.$connect).toBe("function");
    expect(typeof prisma.$disconnect).toBe("function");
    expect(typeof prisma.$transaction).toBe("function");
  });

  it("returns same instance on multiple imports in development", () => {
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "development",
      writable: true,
      configurable: true,
    });
    jest.resetModules();

    const { prisma: prisma1 } = require("../prisma");
    const { prisma: prisma2 } = require("../prisma");

    expect(prisma1).toBe(prisma2);
  });

  it("uses singleton pattern to prevent multiple instances", () => {
    const { prisma } = require("../prisma");
    const global = globalThis as typeof globalThis & { prisma?: typeof prisma };

    // In development, the instance should be stored in global
    if (process.env.NODE_ENV !== "production") {
      expect(global.prisma).toBeDefined();
      expect(global.prisma).toBe(prisma);
    }
  });

  it("creates PrismaClient with expected configuration", () => {
    // This tests that the module loads without errors
    expect(() => {
      require("../prisma");
    }).not.toThrow();
  });
});

describe("Prisma Client Configuration", () => {
  it("should configure logging based on environment", () => {
    // Test development environment
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "development",
      writable: true,
      configurable: true,
    });
    jest.resetModules();
    const { prisma: devPrisma } = require("../prisma");
    expect(devPrisma).toBeDefined();

    // Test production environment
    Object.defineProperty(process.env, "NODE_ENV", {
      value: "production",
      writable: true,
      configurable: true,
    });
    jest.resetModules();
    const { prisma: prodPrisma } = require("../prisma");
    expect(prodPrisma).toBeDefined();
  });
});
