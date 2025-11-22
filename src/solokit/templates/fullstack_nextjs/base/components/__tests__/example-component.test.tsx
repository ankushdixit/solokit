import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ExampleComponent from "../example-component";

describe("ExampleComponent", () => {
  it("renders the component with initial count", () => {
    render(<ExampleComponent />);
    expect(screen.getByText(/Count:/i)).toBeInTheDocument();
    expect(screen.getByText(/Count: 0/)).toBeInTheDocument();
  });

  it("renders the title", () => {
    render(<ExampleComponent />);
    expect(screen.getByText(/Client Component Example/i)).toBeInTheDocument();
  });

  it("has an increment button", () => {
    render(<ExampleComponent />);
    const button = screen.getByRole("button", { name: /increment/i });
    expect(button).toBeInTheDocument();
  });

  it("increments count when button is clicked", async () => {
    const user = userEvent.setup();
    render(<ExampleComponent />);

    const button = screen.getByRole("button", { name: /increment/i });

    // Initial count should be 0
    expect(screen.getByText(/Count: 0/)).toBeInTheDocument();

    // Click the button
    await user.click(button);

    // Count should now be 1
    expect(screen.getByText(/Count: 1/)).toBeInTheDocument();
  });

  it("increments count multiple times", async () => {
    const user = userEvent.setup();
    render(<ExampleComponent />);

    const button = screen.getByRole("button", { name: /increment/i });

    await user.click(button);
    await user.click(button);
    await user.click(button);

    expect(screen.getByText(/Count: 3/)).toBeInTheDocument();
  });

  it("uses fireEvent to increment count", () => {
    render(<ExampleComponent />);
    const button = screen.getByRole("button", { name: /increment/i });

    fireEvent.click(button);

    expect(screen.getByText(/Count: 1/)).toBeInTheDocument();
  });

  it("has proper styling classes", () => {
    const { container } = render(<ExampleComponent />);
    const wrapper = container.querySelector(".flex");
    expect(wrapper).toHaveClass("flex-col");
    expect(wrapper).toHaveClass("items-center");
    expect(wrapper).toHaveClass("rounded-xl");
  });

  it("title has proper heading level", () => {
    render(<ExampleComponent />);
    const title = screen.getByText(/Client Component Example/i);
    expect(title.tagName).toBe("H3");
  });

  it("displays count as paragraph", () => {
    render(<ExampleComponent />);
    const count = screen.getByText(/Count: 0/);
    expect(count.tagName).toBe("P");
  });

  it("button has proper styling", () => {
    render(<ExampleComponent />);
    const button = screen.getByRole("button", { name: /increment/i });
    expect(button).toHaveClass("rounded-lg");
    expect(button).toHaveClass("px-6");
    expect(button).toHaveClass("py-2");
  });
});
