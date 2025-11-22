import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ErrorPage from "../error";

describe("Error Component", () => {
  const mockReset = jest.fn();
  const mockError = new globalThis.Error("Test error message");

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders error message", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(screen.getByText("Something went wrong!")).toBeInTheDocument();
    expect(screen.getByText("Test error message")).toBeInTheDocument();
  });

  it("renders default message when error has no message", () => {
    const emptyError = new globalThis.Error();
    render(<ErrorPage error={emptyError} reset={mockReset} />);
    expect(screen.getByText("An unexpected error occurred")).toBeInTheDocument();
  });

  it("renders Try again button", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("calls reset function when Try again button is clicked", async () => {
    const user = userEvent.setup();
    render(<ErrorPage error={mockError} reset={mockReset} />);

    const button = screen.getByRole("button", { name: /try again/i });
    await user.click(button);

    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it("renders error with digest", () => {
    const errorWithDigest = Object.assign(new globalThis.Error("Error with digest"), {
      digest: "abc123",
    });
    render(<ErrorPage error={errorWithDigest} reset={mockReset} />);

    expect(screen.getByText("Error with digest")).toBeInTheDocument();
  });

  it("has centered layout", () => {
    const { container } = render(<ErrorPage error={mockError} reset={mockReset} />);
    const wrapper = container.querySelector("div");
    expect(wrapper).toHaveClass("flex");
    expect(wrapper).toHaveClass("min-h-screen");
    expect(wrapper).toHaveClass("items-center");
    expect(wrapper).toHaveClass("justify-center");
  });

  it("renders with card styling", () => {
    const { container } = render(<ErrorPage error={mockError} reset={mockReset} />);
    const card = container.querySelector(".rounded-xl");
    expect(card).toBeInTheDocument();
  });

  it("renders heading with proper semantic level", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    const heading = screen.getByText("Something went wrong!");
    expect(heading.tagName).toBe("H2");
  });

  it("has proper spacing in layout", () => {
    const { container } = render(<ErrorPage error={mockError} reset={mockReset} />);
    const spacedDiv = container.querySelector(".space-y-4");
    expect(spacedDiv).toBeInTheDocument();
  });

  it("button has hover effect styling", () => {
    render(<ErrorPage error={mockError} reset={mockReset} />);
    const button = screen.getByRole("button", { name: /try again/i });
    expect(button).toHaveClass("transition");
  });
});
