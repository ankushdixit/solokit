import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserForm } from "../user-form";

describe("UserForm Component", () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders form with name and email fields", () => {
    render(<UserForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /submit/i })).toBeInTheDocument();
  });

  it("renders with default values", () => {
    const defaultValues = {
      name: "John Doe",
      email: "john@example.com",
    };

    render(<UserForm onSubmit={mockOnSubmit} defaultValues={defaultValues} />);

    expect(screen.getByLabelText("Name")).toHaveValue("John Doe");
    expect(screen.getByLabelText("Email")).toHaveValue("john@example.com");
  });

  it("submits form with valid data", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText("Name"), "John Doe");
    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
      expect(mockOnSubmit.mock.calls[0][0]).toEqual({
        name: "John Doe",
        email: "john@example.com",
      });
    });
  });

  it("shows error for name too short", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText("Name"), "J");
    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Name must be at least 2 characters")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows error for invalid email", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText("Name"), "John Doe");
    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid email address")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows error for missing name", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Name must be at least 2 characters")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows error for missing email", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText("Name"), "John Doe");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid email address")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows error for name too long", async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={mockOnSubmit} />);

    const longName = "a".repeat(101);
    await user.type(screen.getByLabelText("Name"), longName);
    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Name must be less than 100 characters")).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("disables form fields when isLoading is true", () => {
    render(<UserForm onSubmit={mockOnSubmit} isLoading={true} />);

    expect(screen.getByLabelText("Name")).toBeDisabled();
    expect(screen.getByLabelText("Email")).toBeDisabled();
    expect(screen.getByRole("button", { name: /submitting/i })).toBeDisabled();
  });

  it("shows 'Submitting...' text when isLoading is true", () => {
    render(<UserForm onSubmit={mockOnSubmit} isLoading={true} />);

    expect(screen.getByRole("button", { name: /submitting/i })).toBeInTheDocument();
  });

  it("shows 'Submit' text when isLoading is false", () => {
    render(<UserForm onSubmit={mockOnSubmit} isLoading={false} />);

    expect(screen.getByRole("button", { name: /^submit$/i })).toBeInTheDocument();
  });

  it("allows editing with default values", async () => {
    const user = userEvent.setup();
    const defaultValues = {
      name: "John Doe",
      email: "john@example.com",
    };

    render(<UserForm onSubmit={mockOnSubmit} defaultValues={defaultValues} />);

    const nameInput = screen.getByLabelText("Name");
    await user.clear(nameInput);
    await user.type(nameInput, "Jane Smith");

    const emailInput = screen.getByLabelText("Email");
    await user.clear(emailInput);
    await user.type(emailInput, "jane@example.com");

    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
      expect(mockOnSubmit.mock.calls[0][0]).toEqual({
        name: "Jane Smith",
        email: "jane@example.com",
      });
    });
  });

  it("handles async onSubmit", async () => {
    const user = userEvent.setup();
    const asyncOnSubmit = jest.fn().mockResolvedValue(Promise.resolve());

    render(<UserForm onSubmit={asyncOnSubmit} />);

    await user.type(screen.getByLabelText("Name"), "John Doe");
    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(asyncOnSubmit).toHaveBeenCalled();
      expect(asyncOnSubmit.mock.calls[0][0]).toEqual({
        name: "John Doe",
        email: "john@example.com",
      });
    });
  });

  it("has proper input types", () => {
    render(<UserForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText("Name")).toHaveAttribute("type", "text");
    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
  });

  it("has accessible labels with htmlFor", () => {
    render(<UserForm onSubmit={mockOnSubmit} />);

    const nameLabel = screen.getByText("Name").closest("label");
    const emailLabel = screen.getByText("Email").closest("label");

    expect(nameLabel).toHaveAttribute("for", "name");
    expect(emailLabel).toHaveAttribute("for", "email");
  });
});
