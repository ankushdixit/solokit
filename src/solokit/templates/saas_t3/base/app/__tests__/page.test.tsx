import { render, screen } from "@testing-library/react";
import Home from "../page";

describe("Home Page", () => {
  it("renders the main heading", () => {
    render(<Home />);
    expect(screen.getByText(/Welcome to/i)).toBeInTheDocument();
    expect(screen.getAllByText(/T3/i).length).toBeGreaterThan(0);
  });

  it("displays the getting started message", () => {
    render(<Home />);
    expect(screen.getByText(/Your T3 Stack application is ready/i)).toBeInTheDocument();
  });

  it("shows guidance about ARCHITECTURE.md", () => {
    render(<Home />);
    expect(screen.getByText(/Read ARCHITECTURE.md/i)).toBeInTheDocument();
  });

  it("shows guidance about PRD", () => {
    render(<Home />);
    expect(screen.getByText(/Create your PRD/i)).toBeInTheDocument();
  });

  it("has theme-based background styling", () => {
    const { container } = render(<Home />);
    const main = container.querySelector("main");
    expect(main).toHaveClass("bg-background");
    expect(main).toHaveClass("text-foreground");
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
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeInTheDocument();
  });

  it("renders without errors", () => {
    expect(() => render(<Home />)).not.toThrow();
  });
});
