/**
 * Tests for example tRPC router
 */
import { exampleRouter } from "../example";
import { createCallerFactory } from "../../trpc";

// Mock superjson to avoid ES module issues in Jest
jest.mock("superjson", () => ({
  serialize: (obj: unknown) => ({ json: obj, meta: undefined }),
  deserialize: (payload: { json: unknown }) => payload.json,
  stringify: (obj: unknown) => JSON.stringify(obj),
  parse: (str: string) => JSON.parse(str),
}));

// Mock db - initialized inside jest.mock to avoid hoisting issues
jest.mock("@/server/db", () => ({
  db: {
    user: {
      create: jest.fn(),
      findMany: jest.fn(),
    },
  },
}));

// Get the mocked db for use in tests
const { db: mockDb } = jest.requireMock<{
  db: {
    user: {
      create: jest.Mock;
      findMany: jest.Mock;
    };
  };
}>("@/server/db");

describe("Example Router", () => {
  const createCaller = createCallerFactory(exampleRouter);

  // Helper to create test context with mocked db
  const createTestContext = () => ({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    db: mockDb as any,
    headers: new Headers(),
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("hello procedure", () => {
    it("returns greeting with input text", async () => {
      const caller = createCaller(createTestContext());

      const result = await caller.hello({ text: "World" });

      expect(result.greeting).toBe("Hello World");
    });

    it("works with different text values", async () => {
      const caller = createCaller(createTestContext());

      const result1 = await caller.hello({ text: "tRPC" });
      expect(result1.greeting).toBe("Hello tRPC");

      const result2 = await caller.hello({ text: "Test" });
      expect(result2.greeting).toBe("Hello Test");
    });

    it("requires text input", async () => {
      const caller = createCaller(createTestContext());

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await expect(caller.hello({} as any)).rejects.toThrow();
    });

    it("validates input type", async () => {
      const caller = createCaller(createTestContext());

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await expect(caller.hello({ text: 123 } as any)).rejects.toThrow();
    });
  });

  describe("create procedure", () => {
    it("creates a new user with valid data", async () => {
      const mockUser = {
        id: 1,
        name: "John Doe",
        email: "john@example.com",
        createdAt: new Date(),
      };

      (mockDb.user.create as unknown as jest.Mock).mockResolvedValue(mockUser);

      const caller = createCaller(createTestContext());

      const result = await caller.create({
        name: "John Doe",
        email: "john@example.com",
      });

      expect(result).toEqual(mockUser);
    });

    it("calls db.user.create with correct data", async () => {
      (mockDb.user.create as unknown as jest.Mock).mockResolvedValue({
        id: 1,
        name: "Test User",
        email: "test@example.com",
        createdAt: new Date(),
      });

      const caller = createCaller(createTestContext());

      await caller.create({
        name: "Test User",
        email: "test@example.com",
      });

      expect(mockDb.user.create).toHaveBeenCalledWith({
        data: {
          name: "Test User",
          email: "test@example.com",
        },
      });
    });

    it("validates name is required", async () => {
      const caller = createCaller(createTestContext());

      await expect(caller.create({ name: "", email: "test@example.com" })).rejects.toThrow();
    });

    it("validates email format", async () => {
      const caller = createCaller(createTestContext());

      await expect(caller.create({ name: "Test", email: "invalid-email" })).rejects.toThrow();
    });

    it("validates name minimum length", async () => {
      const caller = createCaller(createTestContext());

      await expect(caller.create({ name: "", email: "test@example.com" })).rejects.toThrow();
    });

    it("handles database errors", async () => {
      (mockDb.user.create as unknown as jest.Mock).mockRejectedValue(new Error("Database error"));

      const caller = createCaller(createTestContext());

      await expect(caller.create({ name: "Test", email: "test@example.com" })).rejects.toThrow(
        "Database error"
      );
    });
  });

  describe("getAll procedure", () => {
    it("returns all users from database", async () => {
      const mockUsers = [
        {
          id: 1,
          name: "John Doe",
          email: "john@example.com",
          createdAt: new Date(),
        },
        {
          id: 2,
          name: "Jane Smith",
          email: "jane@example.com",
          createdAt: new Date(),
        },
      ];

      (mockDb.user.findMany as unknown as jest.Mock).mockResolvedValue(mockUsers);

      const caller = createCaller(createTestContext());

      const result = await caller.getAll();

      expect(result).toEqual(mockUsers);
    });

    it("calls db.user.findMany with correct orderBy", async () => {
      (mockDb.user.findMany as unknown as jest.Mock).mockResolvedValue([]);

      const caller = createCaller(createTestContext());

      await caller.getAll();

      expect(mockDb.user.findMany).toHaveBeenCalledWith({
        orderBy: { createdAt: "desc" },
      });
    });

    it("returns empty array when no users exist", async () => {
      (mockDb.user.findMany as unknown as jest.Mock).mockResolvedValue([]);

      const caller = createCaller(createTestContext());

      const result = await caller.getAll();

      expect(result).toEqual([]);
    });

    it("handles database errors", async () => {
      (mockDb.user.findMany as unknown as jest.Mock).mockRejectedValue(new Error("Database error"));

      const caller = createCaller(createTestContext());

      await expect(caller.getAll()).rejects.toThrow("Database error");
    });
  });

  describe("Router Structure", () => {
    it("exports a router with all procedures", () => {
      expect(exampleRouter).toBeDefined();
      expect(typeof exampleRouter).toBe("object");
    });
  });
});
