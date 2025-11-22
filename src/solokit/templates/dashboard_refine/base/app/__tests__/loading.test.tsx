import { render, screen } from "@testing-library/react";
import Loading from "../loading";

describe("Loading Component", () => {
  it("renders loading text", () => {
    render(<Loading />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders spinner element", () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("has centered layout", () => {
    const { container } = render(<Loading />);
    const wrapper = container.querySelector("div");
    expect(wrapper).toHaveClass("flex");
    expect(wrapper).toHaveClass("min-h-screen");
    expect(wrapper).toHaveClass("items-center");
    expect(wrapper).toHaveClass("justify-center");
  });

  it("spinner has rounded border", () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("rounded-full");
  });

  it("spinner has border styling", () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("border-4");
  });

  it("has proper size for spinner", () => {
    const { container } = render(<Loading />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("h-12");
    expect(spinner).toHaveClass("w-12");
  });
});
