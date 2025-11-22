import { render, screen } from "@testing-library/react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../card";

describe("Card Components", () => {
  describe("Card", () => {
    it("renders children correctly", () => {
      render(
        <Card>
          <p>Card content</p>
        </Card>
      );
      expect(screen.getByText("Card content")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(<Card className="custom-card">Content</Card>);
      const card = container.querySelector(".custom-card");
      expect(card).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<Card ref={ref}>Content</Card>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe("CardHeader", () => {
    it("renders children correctly", () => {
      render(
        <CardHeader>
          <p>Header content</p>
        </CardHeader>
      );
      expect(screen.getByText("Header content")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(<CardHeader className="custom-header">Header</CardHeader>);
      const header = container.querySelector(".custom-header");
      expect(header).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<CardHeader ref={ref}>Header</CardHeader>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe("CardTitle", () => {
    it("renders children correctly", () => {
      render(<CardTitle>Title Text</CardTitle>);
      expect(screen.getByText("Title Text")).toBeInTheDocument();
    });

    it("renders as h2 element", () => {
      const { container } = render(<CardTitle>Title</CardTitle>);
      const h2 = container.querySelector("h2");
      expect(h2).toBeInTheDocument();
      expect(h2).toHaveTextContent("Title");
    });

    it("applies custom className", () => {
      const { container } = render(<CardTitle className="custom-title">Title</CardTitle>);
      const title = container.querySelector(".custom-title");
      expect(title).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<CardTitle ref={ref}>Title</CardTitle>);
      expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
    });
  });

  describe("CardDescription", () => {
    it("renders children correctly", () => {
      render(<CardDescription>Description text</CardDescription>);
      expect(screen.getByText("Description text")).toBeInTheDocument();
    });

    it("renders as p element", () => {
      const { container } = render(<CardDescription>Description</CardDescription>);
      const p = container.querySelector("p");
      expect(p).toBeInTheDocument();
      expect(p).toHaveTextContent("Description");
    });

    it("applies custom className", () => {
      const { container } = render(
        <CardDescription className="custom-description">Description</CardDescription>
      );
      const description = container.querySelector(".custom-description");
      expect(description).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<CardDescription ref={ref}>Description</CardDescription>);
      expect(ref.current).toBeInstanceOf(HTMLParagraphElement);
    });
  });

  describe("CardContent", () => {
    it("renders children correctly", () => {
      render(
        <CardContent>
          <p>Content text</p>
        </CardContent>
      );
      expect(screen.getByText("Content text")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(<CardContent className="custom-content">Content</CardContent>);
      const content = container.querySelector(".custom-content");
      expect(content).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<CardContent ref={ref}>Content</CardContent>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe("CardFooter", () => {
    it("renders children correctly", () => {
      render(
        <CardFooter>
          <p>Footer text</p>
        </CardFooter>
      );
      expect(screen.getByText("Footer text")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(<CardFooter className="custom-footer">Footer</CardFooter>);
      const footer = container.querySelector(".custom-footer");
      expect(footer).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(<CardFooter ref={ref}>Footer</CardFooter>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe("Card with all parts", () => {
    it("renders complete card structure", () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Test Card</CardTitle>
            <CardDescription>Test description</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Card content</p>
          </CardContent>
          <CardFooter>
            <p>Card footer</p>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText("Test Card")).toBeInTheDocument();
      expect(screen.getByText("Test description")).toBeInTheDocument();
      expect(screen.getByText("Card content")).toBeInTheDocument();
      expect(screen.getByText("Card footer")).toBeInTheDocument();
    });

    it("works with minimal structure", () => {
      render(
        <Card>
          <CardContent>
            <p>Minimal card</p>
          </CardContent>
        </Card>
      );

      expect(screen.getByText("Minimal card")).toBeInTheDocument();
    });
  });
});
