import { render } from "@testing-library/react";
import Home from "../page";

describe("Home Page", () => {
  it("renders the main heading", () => {
    const { container } = render(<Home />);

    expect(container.textContent).toContain("Full-Stack");
    expect(container.textContent).toContain("Next.js");
  });

  it("displays getting started message", () => {
    const { container } = render(<Home />);

    expect(container.textContent).toContain("Your project is ready");
  });

  it("has link to health check endpoint", () => {
    const { container } = render(<Home />);

    const link = container.querySelector('a[href="/api/health"]');
    expect(link).toBeInTheDocument();
    expect(container.textContent).toContain("Health Check");
  });

  it("references ARCHITECTURE.md", () => {
    const { container } = render(<Home />);

    expect(container.textContent).toContain("ARCHITECTURE.md");
  });

  it("has theme-based background styling", () => {
    const { container } = render(<Home />);

    const main = container.querySelector("main");
    expect(main).toHaveClass("bg-background");
    expect(main).toHaveClass("text-foreground");
  });
});
