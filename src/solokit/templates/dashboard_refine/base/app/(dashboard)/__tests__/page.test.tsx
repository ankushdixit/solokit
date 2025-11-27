import { render, screen } from "@testing-library/react";
import DashboardPage from "../page";

describe("DashboardPage Component", () => {
  it("renders welcome heading", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Welcome to Refine Dashboard")).toBeInTheDocument();
  });

  it("renders welcome message", () => {
    render(<DashboardPage />);
    expect(
      screen.getByText("Your Refine.dev admin dashboard is ready. Start building!")
    ).toBeInTheDocument();
  });

  it("renders Getting Started card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Getting Started")).toBeInTheDocument();
    expect(
      screen.getByText("Read ARCHITECTURE.md to understand the dashboard patterns.")
    ).toBeInTheDocument();
  });

  it("renders Next Steps card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Next Steps")).toBeInTheDocument();
    expect(screen.getByText("1. Set up your backend API connection")).toBeInTheDocument();
  });

  it("renders guidance about PRD", () => {
    render(<DashboardPage />);
    expect(
      screen.getByText("Create your PRD at docs/PRD.md to define your features.")
    ).toBeInTheDocument();
  });

  it("renders guidance about data provider", () => {
    render(<DashboardPage />);
    expect(
      screen.getByText("Configure your data provider in lib/refine.tsx.")
    ).toBeInTheDocument();
  });

  it("has grid layout for cards", () => {
    const { container } = render(<DashboardPage />);
    const grid = container.querySelector(".grid");
    expect(grid).toBeInTheDocument();
  });

  it("renders heading as h1", () => {
    render(<DashboardPage />);
    const heading = screen.getByText("Welcome to Refine Dashboard");
    expect(heading.tagName).toBe("H1");
  });

  it("has proper spacing between sections", () => {
    const { container } = render(<DashboardPage />);
    const wrapper = container.querySelector(".space-y-6");
    expect(wrapper).toBeInTheDocument();
  });
});
