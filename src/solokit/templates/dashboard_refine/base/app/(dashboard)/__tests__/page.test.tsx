import { render, screen } from "@testing-library/react";
import DashboardPage from "../page";

describe("DashboardPage Component", () => {
  it("renders dashboard heading", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders welcome message", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Welcome to your admin dashboard")).toBeInTheDocument();
  });

  it("renders Total Users stat card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Total Users")).toBeInTheDocument();
    expect(screen.getByText("2,543")).toBeInTheDocument();
    expect(screen.getByText("+12.5%")).toBeInTheDocument();
  });

  it("renders Total Orders stat card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Total Orders")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("+8.2%")).toBeInTheDocument();
  });

  it("renders Revenue stat card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getByText("$45,231")).toBeInTheDocument();
    expect(screen.getByText("+23.1%")).toBeInTheDocument();
  });

  it("renders Products stat card", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Products")).toBeInTheDocument();
    expect(screen.getByText("456")).toBeInTheDocument();
    expect(screen.getByText("+4.3%")).toBeInTheDocument();
  });

  it("renders all four stat cards", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Total Users")).toBeInTheDocument();
    expect(screen.getByText("Total Orders")).toBeInTheDocument();
    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getByText("Products")).toBeInTheDocument();
  });

  it("shows trend indicator for each stat", () => {
    render(<DashboardPage />);
    const trendIndicators = screen.getAllByText("from last month");
    expect(trendIndicators).toHaveLength(4);
  });

  it("has grid layout for stat cards", () => {
    const { container } = render(<DashboardPage />);
    const grid = container.querySelector(".grid");
    expect(grid).toBeInTheDocument();
  });

  it("renders heading as h1", () => {
    render(<DashboardPage />);
    const heading = screen.getByText("Dashboard");
    expect(heading.tagName).toBe("H1");
  });

  it("has proper spacing between sections", () => {
    const { container } = render(<DashboardPage />);
    const wrapper = container.querySelector(".space-y-6");
    expect(wrapper).toBeInTheDocument();
  });
});
