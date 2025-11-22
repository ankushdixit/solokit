import React from "react";
import { render, screen } from "@testing-library/react";
import ClientRefineWrapper from "../client-refine-wrapper";

// Mock next/dynamic
jest.mock("next/dynamic", () => {
  return <T extends React.ComponentType>(
    loader: () => Promise<{ default: T }>,
    options?: { loading?: () => React.ReactElement | null; ssr?: boolean }
  ) => {
    const Component = () => {
      if (options?.loading) {
        return options.loading();
      }
      return null;
    };
    Component.displayName = "DynamicComponent";
    return Component;
  };
});

describe("ClientRefineWrapper Component", () => {
  it("renders loading state", () => {
    render(
      <ClientRefineWrapper>
        <div>Child content</div>
      </ClientRefineWrapper>
    );
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("has centered loading layout", () => {
    const { container } = render(
      <ClientRefineWrapper>
        <div>Child content</div>
      </ClientRefineWrapper>
    );
    const wrapper = container.querySelector(".flex");
    expect(wrapper).toHaveClass("min-h-screen");
    expect(wrapper).toHaveClass("items-center");
    expect(wrapper).toHaveClass("justify-center");
  });

  it("loading text has proper styling", () => {
    render(
      <ClientRefineWrapper>
        <div>Child content</div>
      </ClientRefineWrapper>
    );
    const loadingText = screen.getByText("Loading...");
    expect(loadingText).toHaveClass("text-lg");
  });
});
