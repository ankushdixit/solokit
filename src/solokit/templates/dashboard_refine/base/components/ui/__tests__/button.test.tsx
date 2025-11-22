import { render, screen } from "@testing-library/react";
import { Button } from "../button";
import userEvent from "@testing-library/user-event";

describe("Button Component", () => {
  it("renders children correctly", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies default variant", () => {
    const { container } = render(<Button>Default</Button>);
    const button = container.querySelector("button");
    expect(button).toBeInTheDocument();
  });

  it("applies destructive variant", () => {
    render(<Button variant="destructive">Delete</Button>);
    const button = screen.getByText("Delete");
    expect(button).toBeInTheDocument();
  });

  it("applies outline variant", () => {
    render(<Button variant="outline">Outline</Button>);
    const button = screen.getByText("Outline");
    expect(button).toBeInTheDocument();
  });

  it("applies secondary variant", () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByText("Secondary");
    expect(button).toBeInTheDocument();
  });

  it("applies ghost variant", () => {
    render(<Button variant="ghost">Ghost</Button>);
    const button = screen.getByText("Ghost");
    expect(button).toBeInTheDocument();
  });

  it("applies link variant", () => {
    render(<Button variant="link">Link</Button>);
    const button = screen.getByText("Link");
    expect(button).toBeInTheDocument();
  });

  it("applies small size", () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByText("Small");
    expect(button).toBeInTheDocument();
  });

  it("applies large size", () => {
    render(<Button size="lg">Large</Button>);
    const button = screen.getByText("Large");
    expect(button).toBeInTheDocument();
  });

  it("applies icon size", () => {
    render(<Button size="icon">Icon</Button>);
    const button = screen.getByText("Icon");
    expect(button).toBeInTheDocument();
  });

  it("handles click events", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByText("Click");
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByText("Disabled");
    expect(button).toBeDisabled();
  });

  it("does not trigger click when disabled", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    );

    const button = screen.getByText("Disabled");
    await user.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it("applies custom className", () => {
    const { container } = render(<Button className="custom-class">Custom</Button>);
    const button = container.querySelector(".custom-class");
    expect(button).toBeInTheDocument();
  });

  it("is accessible with proper aria attributes", () => {
    render(<Button aria-label="Submit form">Submit</Button>);
    expect(screen.getByLabelText("Submit form")).toBeInTheDocument();
  });

  it("has proper button role", () => {
    render(<Button>Button</Button>);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("can be of type submit", () => {
    render(<Button type="submit">Submit</Button>);
    const button = screen.getByText("Submit");
    expect(button).toHaveAttribute("type", "submit");
  });

  it("can be of type button", () => {
    render(<Button type="button">Button</Button>);
    const button = screen.getByText("Button");
    expect(button).toHaveAttribute("type", "button");
  });

  it("forwards ref correctly", () => {
    const ref = { current: null };
    render(<Button ref={ref}>Ref Button</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("renders with multiple props combined", () => {
    render(
      <Button variant="destructive" size="lg" disabled>
        Complex Button
      </Button>
    );
    const button = screen.getByText("Complex Button");
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
  });
});
