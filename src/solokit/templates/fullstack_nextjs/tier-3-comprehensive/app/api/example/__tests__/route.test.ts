/**
 * @jest-environment @stryker-mutator/jest-runner/jest-env/node
 */
/**
 * API Route Tests for /api/example
 */
import { NextRequest } from "next/server";
import { GET, POST } from "../route";

// Mock Prisma
jest.mock("@/lib/prisma", () => ({
  prisma: {
    user: {
      findMany: jest.fn(),
      create: jest.fn(),
      count: jest.fn(),
      findFirst: jest.fn(),
    },
  },
}));

// Mock validations
interface ZodErrorLike extends Error {
  name: string;
  issues: Array<{ message: string }>;
}

jest.mock("@/lib/validations", () => ({
  createUserSchema: {
    parse: jest.fn((data) => {
      if (!data.name || !data.email) {
        const error = new Error("Validation failed") as ZodErrorLike;
        error.name = "ZodError";
        error.issues = [{ message: "Required field missing" }];
        throw error;
      }
      if (!data.email.includes("@")) {
        const error = new Error("Validation failed") as ZodErrorLike;
        error.name = "ZodError";
        error.issues = [{ message: "Invalid email" }];
        throw error;
      }
      return data;
    }),
  },
}));

describe("GET /api/example", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns success message and users", async () => {
    const mockUsers = [
      {
        id: 1,
        name: "John Doe",
        email: "john@example.com",
        createdAt: new Date().toISOString(),
      },
      {
        id: 2,
        name: "Jane Smith",
        email: "jane@example.com",
        createdAt: new Date().toISOString(),
      },
    ];

    const { prisma } = require("@/lib/prisma");
    prisma.user.findMany.mockResolvedValue(mockUsers);

    const response = await GET();
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.message).toBe("Hello from Next.js API!");
    expect(data.users).toEqual(mockUsers);
  });

  it("calls findMany with correct parameters", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.findMany.mockResolvedValue([]);

    await GET();

    expect(prisma.user.findMany).toHaveBeenCalledWith({
      take: 10,
      orderBy: { createdAt: "desc" },
    });
  });

  it("handles database errors", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.findMany.mockRejectedValue(new Error("Database error"));

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    const response = await GET();
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe("Failed to fetch users");
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it("returns empty users array when no users exist", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.findMany.mockResolvedValue([]);

    const response = await GET();
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.users).toEqual([]);
  });
});

describe("POST /api/example", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("creates a new user with valid data", async () => {
    const mockUser = {
      id: 1,
      name: "John Doe",
      email: "john@example.com",
      createdAt: new Date().toISOString(),
    };

    const { prisma } = require("@/lib/prisma");
    prisma.user.create.mockResolvedValue(mockUser);

    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "John Doe",
        email: "john@example.com",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(201);
    expect(data).toEqual(mockUser);
  });

  it("calls create with correct data", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.create.mockResolvedValue({
      id: 1,
      name: "Test User",
      email: "test@example.com",
      createdAt: new Date().toISOString(),
    });

    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "Test User",
        email: "test@example.com",
      }),
    });

    await POST(request);

    expect(prisma.user.create).toHaveBeenCalledWith({
      data: {
        name: "Test User",
        email: "test@example.com",
      },
    });
  });

  it("returns 400 for invalid data", async () => {
    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "Test",
        email: "invalid-email",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe("Validation failed");
    expect(data.details).toBeDefined();
  });

  it("returns 400 for missing required fields", async () => {
    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "Test",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.error).toBe("Validation failed");
  });

  it("handles database errors during creation", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.create.mockRejectedValue(new Error("Database error"));

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "John Doe",
        email: "john@example.com",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe("Failed to create user");
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it("handles malformed JSON", async () => {
    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: "invalid json",
    });

    const response = await POST(request);

    // The response will depend on how the error is handled
    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  it("handles generic errors (non-Zod) during creation", async () => {
    const { prisma } = require("@/lib/prisma");
    // Simulate a generic error (not ZodError, not database error)
    const genericError = new Error("Unexpected error");
    Object.defineProperty(genericError, "name", { value: "Error" });

    prisma.user.create.mockRejectedValue(genericError);

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    const request = new NextRequest("http://localhost:3000/api/example", {
      method: "POST",
      body: JSON.stringify({
        name: "John Doe",
        email: "john@example.com",
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.error).toBe("Failed to create user");
    expect(consoleErrorSpy).toHaveBeenCalledWith("Error creating user:", genericError);

    consoleErrorSpy.mockRestore();
  });
});
