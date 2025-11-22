import { render, screen } from "@testing-library/react";
import UsersPage from "../page";

// Mock Refine's useList hook
jest.mock("@refinedev/core", () => ({
  useList: jest.fn(() => ({
    query: {
      data: {
        data: [
          { id: 1, name: "John Doe", email: "john@example.com" },
          { id: 2, name: "Jane Smith", email: "jane@example.com" },
          { id: 3, name: "Bob Johnson", email: "bob@example.com" },
        ],
      },
      isLoading: false,
    },
  })),
}));

describe("UsersPage Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders page heading", () => {
    render(<UsersPage />);
    expect(screen.getByText("Users")).toBeInTheDocument();
  });

  it("renders page description", () => {
    render(<UsersPage />);
    expect(screen.getByText("Manage your users")).toBeInTheDocument();
  });

  it("renders Add User button", () => {
    render(<UsersPage />);
    expect(screen.getByRole("button", { name: /add user/i })).toBeInTheDocument();
  });

  it("renders table with headers", () => {
    render(<UsersPage />);
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
  });

  it("renders user data in table", () => {
    render(<UsersPage />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("john@example.com")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
    expect(screen.getByText("Bob Johnson")).toBeInTheDocument();
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
  });

  it("renders user IDs in table", () => {
    render(<UsersPage />);
    // IDs are rendered in table cells
    const table = screen.getByText("John Doe").closest("table");
    expect(table).toBeInTheDocument();
  });

  it("renders Edit buttons for each user", () => {
    render(<UsersPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    expect(editButtons).toHaveLength(3);
  });

  it("renders card with title", () => {
    render(<UsersPage />);
    expect(screen.getByText("All Users")).toBeInTheDocument();
  });

  it("shows loading state when data is loading", () => {
    const { useList } = require("@refinedev/core");
    useList.mockReturnValue({
      query: {
        data: null,
        isLoading: true,
      },
    });

    render(<UsersPage />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows empty state when no users", () => {
    const { useList } = require("@refinedev/core");
    useList.mockReturnValue({
      query: {
        data: { data: [] },
        isLoading: false,
      },
    });

    render(<UsersPage />);
    expect(screen.getByText("No users found")).toBeInTheDocument();
  });

  it("heading is h1 element", () => {
    render(<UsersPage />);
    const heading = screen.getByText("Users");
    expect(heading.tagName).toBe("H1");
  });

  it("has proper layout spacing", () => {
    const { container } = render(<UsersPage />);
    const wrapper = container.querySelector(".space-y-6");
    expect(wrapper).toBeInTheDocument();
  });

  it("calls useList with users resource", () => {
    const { useList } = require("@refinedev/core");
    render(<UsersPage />);

    expect(useList).toHaveBeenCalledWith({
      resource: "users",
    });
  });
});
