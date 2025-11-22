import { render, screen } from "@testing-library/react";
import { Sidebar } from "../sidebar";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/"),
}));

describe("Sidebar Component", () => {
  it("renders sidebar navigation", () => {
    const { container } = render(<Sidebar />);
    expect(container.querySelector("aside")).toBeInTheDocument();
  });

  it("renders all navigation links", () => {
    render(<Sidebar />);

    // Dashboard appears twice (logo + nav), so use getAllByText
    expect(screen.getAllByText("Dashboard")).toHaveLength(2);
    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByText("Orders")).toBeInTheDocument();
    expect(screen.getByText("Products")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("has accessible navigation landmark", () => {
    render(<Sidebar />);
    expect(screen.getByLabelText("Main navigation")).toBeInTheDocument();
  });

  it("renders links with correct href attributes", () => {
    render(<Sidebar />);

    const dashboardLink = screen.getAllByText("Dashboard")[0]?.closest("a");
    const usersLink = screen.getByText("Users").closest("a");
    const ordersLink = screen.getByText("Orders").closest("a");
    const productsLink = screen.getByText("Products").closest("a");
    const settingsLink = screen.getByText("Settings").closest("a");

    expect(dashboardLink).toHaveAttribute("href", "/");
    expect(usersLink).toHaveAttribute("href", "/users");
    expect(ordersLink).toHaveAttribute("href", "/orders");
    expect(productsLink).toHaveAttribute("href", "/products");
    expect(settingsLink).toHaveAttribute("href", "/settings");
  });

  it("marks dashboard as active on root path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/");

    render(<Sidebar />);

    // Get the second "Dashboard" link (the one in navigation, not the logo)
    const dashboardLink = screen.getAllByText("Dashboard")[1]?.closest("a");
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
  });

  it("marks users as active on users path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/users");

    render(<Sidebar />);

    const usersLink = screen.getByText("Users").closest("a");
    expect(usersLink).toHaveAttribute("aria-current", "page");
  });

  it("marks orders as active on orders path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/orders");

    render(<Sidebar />);

    const ordersLink = screen.getByText("Orders").closest("a");
    expect(ordersLink).toHaveAttribute("aria-current", "page");
  });

  it("marks products as active on products path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/products");

    render(<Sidebar />);

    const productsLink = screen.getByText("Products").closest("a");
    expect(productsLink).toHaveAttribute("aria-current", "page");
  });

  it("marks settings as active on settings path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/settings");

    render(<Sidebar />);

    const settingsLink = screen.getByText("Settings").closest("a");
    expect(settingsLink).toHaveAttribute("aria-current", "page");
  });

  it("has hidden class for mobile viewports", () => {
    const { container } = render(<Sidebar />);
    const aside = container.querySelector("aside");
    expect(aside).toHaveClass("hidden");
  });

  it("has md:flex for desktop viewports", () => {
    const { container } = render(<Sidebar />);
    const aside = container.querySelector("aside");
    expect(aside).toHaveClass("md:flex");
  });

  it("renders brand logo link in header", () => {
    render(<Sidebar />);
    const brandLinks = screen.getAllByText("Dashboard");
    // First one is in the header/logo area
    const logoLink = brandLinks[0]?.closest("a");
    expect(logoLink).toHaveAttribute("href", "/");
  });

  it("has proper sidebar width", () => {
    const { container } = render(<Sidebar />);
    const aside = container.querySelector("aside");
    expect(aside).toHaveClass("w-64");
  });

  it("has border on the right", () => {
    const { container } = render(<Sidebar />);
    const aside = container.querySelector("aside");
    expect(aside).toHaveClass("border-r");
  });
});
