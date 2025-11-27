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

  it("renders Dashboard navigation link", () => {
    render(<Sidebar />);
    // Dashboard appears twice (logo + nav), so use getAllByText
    expect(screen.getAllByText("Dashboard")).toHaveLength(2);
  });

  it("has accessible navigation landmark", () => {
    render(<Sidebar />);
    expect(screen.getByLabelText("Main navigation")).toBeInTheDocument();
  });

  it("renders links with correct href attributes", () => {
    render(<Sidebar />);
    const dashboardLinks = screen.getAllByText("Dashboard");
    // Both should link to root
    dashboardLinks.forEach((link) => {
      const anchor = link.closest("a");
      expect(anchor).toHaveAttribute("href", "/");
    });
  });

  it("marks dashboard as active on root path", () => {
    const { usePathname } = require("next/navigation");
    usePathname.mockReturnValue("/");

    render(<Sidebar />);

    // Get the second "Dashboard" link (the one in navigation, not the logo)
    const dashboardLink = screen.getAllByText("Dashboard")[1]?.closest("a");
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
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
