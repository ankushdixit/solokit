import { render, screen } from "@testing-library/react";
import { Header } from "../header";

describe("Header Component", () => {
  it("renders the header element", () => {
    const { container } = render(<Header />);
    expect(container.querySelector("header")).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<Header />);
    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();
  });

  it("has accessible search input", () => {
    render(<Header />);
    expect(screen.getByLabelText("Search")).toBeInTheDocument();
  });

  it("renders menu toggle button for mobile", () => {
    render(<Header />);
    expect(screen.getByText("Toggle menu")).toBeInTheDocument();
  });

  it("renders notifications button", () => {
    render(<Header />);
    expect(screen.getByLabelText("Notifications")).toBeInTheDocument();
  });

  it("renders settings button", () => {
    render(<Header />);
    expect(screen.getByLabelText("Settings")).toBeInTheDocument();
  });

  it("has three buttons (menu, notifications, settings)", () => {
    render(<Header />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(3);
  });

  it("search input has correct type", () => {
    render(<Header />);
    const searchInput = screen.getByPlaceholderText("Search...");
    expect(searchInput).toHaveAttribute("type", "search");
  });

  it("has sticky positioning class", () => {
    const { container } = render(<Header />);
    const header = container.querySelector("header");
    expect(header).toHaveClass("sticky");
  });

  it("has proper z-index for layering", () => {
    const { container } = render(<Header />);
    const header = container.querySelector("header");
    expect(header).toHaveClass("z-50");
  });

  it("renders with border bottom", () => {
    const { container } = render(<Header />);
    const header = container.querySelector("header");
    expect(header).toHaveClass("border-b");
  });
});
