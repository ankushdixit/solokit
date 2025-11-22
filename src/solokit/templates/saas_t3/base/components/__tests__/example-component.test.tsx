import { render, screen } from "@testing-library/react";
import ExampleComponent from "../example-component";

// Mock tRPC API
jest.mock("@/lib/api", () => ({
  api: {
    example: {
      hello: {
        useQuery: jest.fn(() => ({
          data: { greeting: "Hello from tRPC" },
          isLoading: false,
          error: null,
        })),
      },
    },
  },
}));

describe("ExampleComponent", () => {
  beforeEach(() => {
    // Reset and restore default mock
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: { greeting: "Hello from tRPC" },
      isLoading: false,
      error: null,
    });
  });

  it("renders the component title", () => {
    render(<ExampleComponent />);
    expect(screen.getByText("tRPC Example Component")).toBeInTheDocument();
  });

  it("displays greeting from tRPC", () => {
    render(<ExampleComponent />);
    expect(screen.getByText("Hello from tRPC")).toBeInTheDocument();
  });

  it("shows loading state when data is loading", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<ExampleComponent />);
    expect(screen.getByText("Loading tRPC query...")).toBeInTheDocument();
  });

  it("shows loading when data is undefined", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    render(<ExampleComponent />);
    expect(screen.getByText("Loading tRPC query...")).toBeInTheDocument();
  });

  it("calls useQuery with correct input", () => {
    const { api } = require("@/lib/api");

    render(<ExampleComponent />);

    expect(api.example.hello.useQuery).toHaveBeenCalledWith({
      text: "from tRPC",
    });
  });

  it("displays description text", () => {
    render(<ExampleComponent />);
    expect(
      screen.getByText("This component demonstrates tRPC usage with type-safe API calls")
    ).toBeInTheDocument();
  });

  it("has proper styling classes", () => {
    const { container } = render(<ExampleComponent />);
    const wrapper = container.querySelector(".flex");
    expect(wrapper).toHaveClass("flex-col");
    expect(wrapper).toHaveClass("items-center");
    expect(wrapper).toHaveClass("rounded-xl");
  });

  it("title has proper heading level", () => {
    render(<ExampleComponent />);
    const title = screen.getByText("tRPC Example Component");
    expect(title.tagName).toBe("H3");
  });

  it("greeting displays as paragraph", () => {
    render(<ExampleComponent />);
    const greeting = screen.getByText("Hello from tRPC");
    expect(greeting.tagName).toBe("P");
  });

  it("handles different greeting messages", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: { greeting: "Custom greeting message" },
      isLoading: false,
      error: null,
    });

    render(<ExampleComponent />);
    expect(screen.getByText("Custom greeting message")).toBeInTheDocument();
  });

  it("renders without errors", () => {
    expect(() => render(<ExampleComponent />)).not.toThrow();
  });
});
