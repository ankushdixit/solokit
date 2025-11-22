import { render, screen } from "@testing-library/react";
import Home from "../page";

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

describe("Home Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main heading", () => {
    render(<Home />);
    expect(screen.getByText(/Create/i)).toBeInTheDocument();
    // T3 appears multiple times, so use getAllByText
    expect(screen.getAllByText(/T3/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/App/i)).toBeInTheDocument();
  });

  it("displays greeting from tRPC", () => {
    render(<Home />);
    expect(screen.getByText("Hello from tRPC")).toBeInTheDocument();
  });

  it("shows loading state when data is loading", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<Home />);
    expect(screen.getByText("Loading tRPC query...")).toBeInTheDocument();
  });

  it("shows loading when data is undefined", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    render(<Home />);
    expect(screen.getByText("Loading tRPC query...")).toBeInTheDocument();
  });

  it("calls useQuery with correct input", () => {
    const { api } = require("@/lib/api");

    render(<Home />);

    expect(api.example.hello.useQuery).toHaveBeenCalledWith({
      text: "from tRPC",
    });
  });

  it("renders First Steps card", () => {
    render(<Home />);
    expect(screen.getByText("First Steps →")).toBeInTheDocument();
  });

  it("renders Documentation card", () => {
    render(<Home />);
    expect(screen.getByText("Documentation →")).toBeInTheDocument();
  });

  it("displays documentation description", () => {
    render(<Home />);
    expect(
      screen.getByText("Learn more about the T3 Stack and its components.")
    ).toBeInTheDocument();
  });

  it("has gradient background styling", () => {
    const { container } = render(<Home />);
    const main = container.querySelector("main");
    expect(main).toHaveClass("bg-gradient-to-b");
  });

  it("has centered layout", () => {
    const { container } = render(<Home />);
    const main = container.querySelector("main");
    expect(main).toHaveClass("flex");
    expect(main).toHaveClass("min-h-screen");
    expect(main).toHaveClass("items-center");
    expect(main).toHaveClass("justify-center");
  });

  it("renders heading as h1", () => {
    render(<Home />);
    const heading = screen.getByText(/Create/);
    expect(heading.tagName).toBe("H1");
  });

  it("has grid layout for cards", () => {
    const { container } = render(<Home />);
    const grid = container.querySelector(".grid");
    expect(grid).toBeInTheDocument();
  });

  it("renders card titles as h3", () => {
    render(<Home />);
    const firstSteps = screen.getByText("First Steps →");
    const documentation = screen.getByText("Documentation →");
    expect(firstSteps.tagName).toBe("H3");
    expect(documentation.tagName).toBe("H3");
  });

  it("cards have hover effect", () => {
    const { container } = render(<Home />);
    const cards = container.querySelectorAll(".hover\\:bg-white\\/20");
    expect(cards.length).toBeGreaterThan(0);
  });

  it("displays different greeting messages", () => {
    const { api } = require("@/lib/api");
    api.example.hello.useQuery.mockReturnValue({
      data: { greeting: "Custom T3 greeting" },
      isLoading: false,
      error: null,
    });

    render(<Home />);
    expect(screen.getByText("Custom T3 greeting")).toBeInTheDocument();
  });

  it("renders without errors", () => {
    expect(() => render(<Home />)).not.toThrow();
  });
});
