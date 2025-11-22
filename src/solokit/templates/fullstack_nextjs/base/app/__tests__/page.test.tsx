import { render, screen } from "@testing-library/react";
import Home from "../page";

// Mock Prisma
jest.mock("@/lib/prisma", () => ({
  prisma: {
    user: {
      count: jest.fn(),
      findFirst: jest.fn(),
    },
  },
}));

// Mock ExampleComponent
jest.mock("@/components/example-component", () => {
  return function MockExampleComponent() {
    return <div data-testid="example-component">Example Component</div>;
  };
});

describe("Home Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main heading", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(5);
    prisma.user.findFirst.mockResolvedValue({
      id: 1,
      name: "John Doe",
      email: "john@example.com",
      createdAt: new Date(),
    });

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Full-Stack");
    expect(container.textContent).toContain("Next.js");
  });

  it("displays user count from database", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(42);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Total Users: 42");
  });

  it("displays latest user information", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(1);
    prisma.user.findFirst.mockResolvedValue({
      id: 1,
      name: "Jane Smith",
      email: "jane@example.com",
      createdAt: new Date(),
    });

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Jane Smith");
    expect(container.textContent).toContain("jane@example.com");
  });

  it("handles case when no users exist", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Total Users: 0");
  });

  it("calls prisma.user.count", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(5);
    prisma.user.findFirst.mockResolvedValue(null);

    await Home();

    expect(prisma.user.count).toHaveBeenCalled();
  });

  it("calls prisma.user.findFirst with correct orderBy", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(5);
    prisma.user.findFirst.mockResolvedValue(null);

    await Home();

    expect(prisma.user.findFirst).toHaveBeenCalledWith({
      orderBy: { createdAt: "desc" },
    });
  });

  it("renders ExampleComponent", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    render(element);

    expect(screen.getByTestId("example-component")).toBeInTheDocument();
  });

  it("displays server-side data fetching section", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(5);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Server-Side Data Fetching Example");
  });

  it("shows API Routes information", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("API Routes");
  });

  it("shows Database information", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    expect(container.textContent).toContain("Database");
    expect(container.textContent).toContain("Prisma");
  });

  it("has link to API route", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    const link = container.querySelector('a[href="/api/example"]');
    expect(link).toBeInTheDocument();
  });

  it("has gradient background styling", async () => {
    const { prisma } = require("@/lib/prisma");
    prisma.user.count.mockResolvedValue(0);
    prisma.user.findFirst.mockResolvedValue(null);

    const element = await Home();
    const { container } = render(element);

    const main = container.querySelector("main");
    expect(main).toHaveClass("bg-gradient-to-b");
  });
});
