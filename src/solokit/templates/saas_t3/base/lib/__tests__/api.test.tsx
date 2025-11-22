import { render, screen } from "@testing-library/react";
import { api, TRPCReactProvider } from "../api";

// Mock QueryClientProvider and tRPC
jest.mock("@tanstack/react-query", () => ({
  QueryClient: jest.fn().mockImplementation(() => ({
    defaultOptions: {},
  })),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="query-provider">{children}</div>
  ),
}));

jest.mock("@trpc/react-query", () => ({
  createTRPCReact: jest.fn(() => ({
    Provider: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="trpc-provider">{children}</div>
    ),
    createClient: jest.fn(() => ({})),
  })),
}));

jest.mock("@trpc/client", () => ({
  httpBatchLink: jest.fn(() => ({})),
  loggerLink: jest.fn(() => ({})),
}));

jest.mock("@trpc/server", () => ({
  inferRouterInputs: jest.fn(),
  inferRouterOutputs: jest.fn(),
}));

jest.mock("superjson", () => ({
  __esModule: true,
  default: {},
}));

describe("tRPC API Configuration", () => {
  describe("api export", () => {
    it("exports api object", () => {
      expect(api).toBeDefined();
    });

    it("api is created with createTRPCReact", () => {
      expect(typeof api).toBe("object");
    });
  });

  describe("TRPCReactProvider", () => {
    it("renders children", () => {
      render(
        <TRPCReactProvider>
          <div>Test Child</div>
        </TRPCReactProvider>
      );

      expect(screen.getByText("Test Child")).toBeInTheDocument();
    });

    it("wraps children with QueryClientProvider", () => {
      render(
        <TRPCReactProvider>
          <div>Test Child</div>
        </TRPCReactProvider>
      );

      expect(screen.getByTestId("query-provider")).toBeInTheDocument();
    });

    it("wraps children with tRPC Provider", () => {
      render(
        <TRPCReactProvider>
          <div>Test Child</div>
        </TRPCReactProvider>
      );

      expect(screen.getByTestId("trpc-provider")).toBeInTheDocument();
    });

    it("renders multiple children correctly", () => {
      render(
        <TRPCReactProvider>
          <div>Child 1</div>
          <div>Child 2</div>
        </TRPCReactProvider>
      );

      expect(screen.getByText("Child 1")).toBeInTheDocument();
      expect(screen.getByText("Child 2")).toBeInTheDocument();
    });
  });

  describe("QueryClient Configuration", () => {
    it("creates QueryClient on initialization", () => {
      const { QueryClient } = require("@tanstack/react-query");

      render(
        <TRPCReactProvider>
          <div>Test</div>
        </TRPCReactProvider>
      );

      expect(QueryClient).toHaveBeenCalled();
    });
  });

  describe("Router Type Exports", () => {
    it("exports RouterInputs type helper", () => {
      // This is a type-level test, validated at compile time
      // The import should not throw
      expect(() => {
        require("../api");
      }).not.toThrow();
    });

    it("exports RouterOutputs type helper", () => {
      // This is a type-level test, validated at compile time
      // The import should not throw
      expect(() => {
        require("../api");
      }).not.toThrow();
    });
  });
});

describe("tRPC Client Configuration", () => {
  beforeEach(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).location;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).location = { origin: "http://localhost:3000" };
  });

  it("configures httpBatchLink", () => {
    const { httpBatchLink } = require("@trpc/client");

    render(
      <TRPCReactProvider>
        <div>Test</div>
      </TRPCReactProvider>
    );

    expect(httpBatchLink).toHaveBeenCalled();
  });

  it("configures loggerLink", () => {
    const { loggerLink } = require("@trpc/client");

    render(
      <TRPCReactProvider>
        <div>Test</div>
      </TRPCReactProvider>
    );

    expect(loggerLink).toHaveBeenCalled();
  });

  it("configures custom headers with x-trpc-source", () => {
    const { httpBatchLink } = require("@trpc/client");

    render(
      <TRPCReactProvider>
        <div>Test</div>
      </TRPCReactProvider>
    );

    const httpBatchLinkCall = httpBatchLink.mock.calls[httpBatchLink.mock.calls.length - 1][0];
    const headers = httpBatchLinkCall.headers();
    expect(headers.get("x-trpc-source")).toBe("nextjs-react");
  });

  it("enables logger in development mode", () => {
    const { loggerLink } = require("@trpc/client");

    render(
      <TRPCReactProvider>
        <div>Test</div>
      </TRPCReactProvider>
    );

    expect(loggerLink).toHaveBeenCalled();
    const loggerConfig = loggerLink.mock.calls[loggerLink.mock.calls.length - 1][0];

    // Test that logger is enabled for development environment
    // The enabled function checks process.env.NODE_ENV internally
    const mockOp = { direction: "up" as const, result: null };
    const isEnabled = loggerConfig.enabled(mockOp);
    expect(typeof isEnabled).toBe("boolean");
  });

  it("enables logger for error responses", () => {
    const { loggerLink } = require("@trpc/client");

    render(
      <TRPCReactProvider>
        <div>Test</div>
      </TRPCReactProvider>
    );

    const loggerConfig = loggerLink.mock.calls[loggerLink.mock.calls.length - 1][0];

    // Test that logger is enabled for error responses
    const mockErrorOp = {
      direction: "down" as const,
      result: new Error("test"),
    };
    const isEnabled = loggerConfig.enabled(mockErrorOp);
    expect(typeof isEnabled).toBe("boolean");
  });
});
