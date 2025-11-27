/**
 * Health Check API Tests
 *
 * Note: We mock NextResponse because the Web APIs (Request, Response)
 * are not available in the Jest/jsdom environment.
 */

// Mock NextResponse before importing the route
jest.mock("next/server", () => ({
  NextResponse: {
    json: jest.fn((data: unknown, init?: { status?: number }) => ({
      status: init?.status ?? 200,
      json: async () => data,
      headers: new Map([["content-type", "application/json"]]),
    })),
  },
}));

import { GET } from "../route";

describe("Health Check API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("returns healthy status", async () => {
    const response = await GET();
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.status).toBe("healthy");
  });

  it("includes timestamp in response", async () => {
    const response = await GET();
    const data = await response.json();

    expect(data.timestamp).toBeDefined();
    expect(new Date(data.timestamp).getTime()).not.toBeNaN();
  });
});
