/**
 * Tests for tRPC root router
 */
import { appRouter, createCaller } from "../root";

// Mock superjson to avoid ES module issues in Jest
jest.mock("superjson", () => ({
  serialize: (obj: unknown) => ({ json: obj, meta: undefined }),
  deserialize: (payload: { json: unknown }) => payload.json,
  stringify: (obj: unknown) => JSON.stringify(obj),
  parse: (str: string) => JSON.parse(str),
}));

// Mock db
jest.mock("@/server/db", () => ({
  db: {},
}));

describe("App Router", () => {
  it("exports appRouter", () => {
    expect(appRouter).toBeDefined();
  });

  it("exports createCaller function", () => {
    expect(createCaller).toBeDefined();
    expect(typeof createCaller).toBe("function");
  });

  it("createCaller creates a server-side caller", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const caller = createCaller({ db: {} as any, headers: new Headers() });
    expect(caller).toBeDefined();
  });

  it("appRouter is properly typed", () => {
    // This test validates that the AppRouter type is exported
    // TypeScript will validate this at compile time
    expect(appRouter).toBeDefined();
  });

  it("has proper router structure", () => {
    expect(appRouter._def).toBeDefined();
  });
});

describe("Router Configuration", () => {
  it("creates router with proper structure", () => {
    expect(typeof appRouter).toBe("object");
    expect(appRouter._def).toBeDefined();
  });

  it("allows creating server-side callers", () => {
    const context = {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      db: {} as any,
      headers: new Headers(),
    };

    const caller = createCaller(context);

    expect(caller).toBeDefined();
  });
});
