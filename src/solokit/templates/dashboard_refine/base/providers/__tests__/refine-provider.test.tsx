import { render, screen } from "@testing-library/react";
import { RefineProvider } from "../refine-provider";

// Mock Refine component
jest.mock("@refinedev/core", () => ({
  Refine: ({
    children,
    dataProvider,
    routerProvider,
    resources,
    options,
  }: {
    children?: React.ReactNode;
    dataProvider?: unknown;
    routerProvider?: unknown;
    resources?: Array<{ name: string }>;
    options?: unknown;
  }) => {
    return (
      <div data-testid="refine-mock">
        {children}
        <div data-testid="refine-props">
          {JSON.stringify({
            hasDataProvider: !!dataProvider,
            hasRouterProvider: !!routerProvider,
            resourceCount: resources?.length,
            hasOptions: !!options,
          })}
        </div>
      </div>
    );
  },
}));

// Mock refine config
jest.mock("@/lib/refine", () => ({
  refineDataProvider: { getList: jest.fn() },
  refineRouterProvider: {},
  refineResources: [],
  refineOptions: { syncWithLocation: true },
}));

describe("RefineProvider Component", () => {
  it("renders children", () => {
    render(
      <RefineProvider>
        <div>Test Child</div>
      </RefineProvider>
    );
    expect(screen.getByText("Test Child")).toBeInTheDocument();
  });

  it("passes dataProvider to Refine", () => {
    render(
      <RefineProvider>
        <div>Child</div>
      </RefineProvider>
    );
    const props = JSON.parse(screen.getByTestId("refine-props").textContent || "{}");
    expect(props.hasDataProvider).toBe(true);
  });

  it("passes routerProvider to Refine", () => {
    render(
      <RefineProvider>
        <div>Child</div>
      </RefineProvider>
    );
    const props = JSON.parse(screen.getByTestId("refine-props").textContent || "{}");
    expect(props.hasRouterProvider).toBe(true);
  });

  it("passes resources to Refine", () => {
    render(
      <RefineProvider>
        <div>Child</div>
      </RefineProvider>
    );
    const props = JSON.parse(screen.getByTestId("refine-props").textContent || "{}");
    expect(props.resourceCount).toBe(0);
  });

  it("passes options to Refine", () => {
    render(
      <RefineProvider>
        <div>Child</div>
      </RefineProvider>
    );
    const props = JSON.parse(screen.getByTestId("refine-props").textContent || "{}");
    expect(props.hasOptions).toBe(true);
  });

  it("renders Refine wrapper", () => {
    render(
      <RefineProvider>
        <div>Child</div>
      </RefineProvider>
    );
    expect(screen.getByTestId("refine-mock")).toBeInTheDocument();
  });
});
