import { render, screen } from "@testing-library/react";
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from "../table";

describe("Table Components", () => {
  describe("Table", () => {
    it("renders table element", () => {
      const { container } = render(
        <Table>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </Table>
      );
      expect(container.querySelector("table")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <Table className="custom-table">
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </Table>
      );
      const table = container.querySelector(".custom-table");
      expect(table).toBeInTheDocument();
    });

    it("wraps table in scrollable div", () => {
      const { container } = render(
        <Table>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </Table>
      );
      const wrapper = container.querySelector("div");
      expect(wrapper).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(
        <Table ref={ref}>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </Table>
      );
      expect(ref.current).toBeInstanceOf(HTMLTableElement);
    });
  });

  describe("TableHeader", () => {
    it("renders thead element", () => {
      const { container } = render(
        <table>
          <TableHeader>
            <tr>
              <th>Header</th>
            </tr>
          </TableHeader>
        </table>
      );
      expect(container.querySelector("thead")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <TableHeader className="custom-header">
            <tr>
              <th>Header</th>
            </tr>
          </TableHeader>
        </table>
      );
      const thead = container.querySelector(".custom-header");
      expect(thead).toBeInTheDocument();
    });
  });

  describe("TableBody", () => {
    it("renders tbody element", () => {
      const { container } = render(
        <table>
          <TableBody>
            <tr>
              <td>Cell</td>
            </tr>
          </TableBody>
        </table>
      );
      expect(container.querySelector("tbody")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <TableBody className="custom-body">
            <tr>
              <td>Cell</td>
            </tr>
          </TableBody>
        </table>
      );
      const tbody = container.querySelector(".custom-body");
      expect(tbody).toBeInTheDocument();
    });
  });

  describe("TableFooter", () => {
    it("renders tfoot element", () => {
      const { container } = render(
        <table>
          <TableFooter>
            <tr>
              <td>Footer</td>
            </tr>
          </TableFooter>
        </table>
      );
      expect(container.querySelector("tfoot")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <TableFooter className="custom-footer">
            <tr>
              <td>Footer</td>
            </tr>
          </TableFooter>
        </table>
      );
      const tfoot = container.querySelector(".custom-footer");
      expect(tfoot).toBeInTheDocument();
    });
  });

  describe("TableRow", () => {
    it("renders tr element", () => {
      const { container } = render(
        <table>
          <tbody>
            <TableRow>
              <td>Cell</td>
            </TableRow>
          </tbody>
        </table>
      );
      expect(container.querySelector("tr")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <tbody>
            <TableRow className="custom-row">
              <td>Cell</td>
            </TableRow>
          </tbody>
        </table>
      );
      const tr = container.querySelector(".custom-row");
      expect(tr).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(
        <table>
          <tbody>
            <TableRow ref={ref}>
              <td>Cell</td>
            </TableRow>
          </tbody>
        </table>
      );
      expect(ref.current).toBeInstanceOf(HTMLTableRowElement);
    });
  });

  describe("TableHead", () => {
    it("renders th element", () => {
      const { container } = render(
        <table>
          <thead>
            <tr>
              <TableHead>Header</TableHead>
            </tr>
          </thead>
        </table>
      );
      expect(container.querySelector("th")).toBeInTheDocument();
    });

    it("renders children correctly", () => {
      render(
        <table>
          <thead>
            <tr>
              <TableHead>Column Header</TableHead>
            </tr>
          </thead>
        </table>
      );
      expect(screen.getByText("Column Header")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <thead>
            <tr>
              <TableHead className="custom-head">Header</TableHead>
            </tr>
          </thead>
        </table>
      );
      const th = container.querySelector(".custom-head");
      expect(th).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(
        <table>
          <thead>
            <tr>
              <TableHead ref={ref}>Header</TableHead>
            </tr>
          </thead>
        </table>
      );
      expect(ref.current).toBeInstanceOf(HTMLTableCellElement);
    });
  });

  describe("TableCell", () => {
    it("renders td element", () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <TableCell>Cell</TableCell>
            </tr>
          </tbody>
        </table>
      );
      expect(container.querySelector("td")).toBeInTheDocument();
    });

    it("renders children correctly", () => {
      render(
        <table>
          <tbody>
            <tr>
              <TableCell>Cell Content</TableCell>
            </tr>
          </tbody>
        </table>
      );
      expect(screen.getByText("Cell Content")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <TableCell className="custom-cell">Cell</TableCell>
            </tr>
          </tbody>
        </table>
      );
      const td = container.querySelector(".custom-cell");
      expect(td).toBeInTheDocument();
    });

    it("forwards ref correctly", () => {
      const ref = { current: null };
      render(
        <table>
          <tbody>
            <tr>
              <TableCell ref={ref}>Cell</TableCell>
            </tr>
          </tbody>
        </table>
      );
      expect(ref.current).toBeInstanceOf(HTMLTableCellElement);
    });
  });

  describe("TableCaption", () => {
    it("renders caption element", () => {
      const { container } = render(
        <table>
          <TableCaption>Table Caption</TableCaption>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </table>
      );
      expect(container.querySelector("caption")).toBeInTheDocument();
    });

    it("renders children correctly", () => {
      render(
        <table>
          <TableCaption>User List</TableCaption>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </table>
      );
      expect(screen.getByText("User List")).toBeInTheDocument();
    });

    it("applies custom className", () => {
      const { container } = render(
        <table>
          <TableCaption className="custom-caption">Caption</TableCaption>
          <tbody>
            <tr>
              <td>Cell</td>
            </tr>
          </tbody>
        </table>
      );
      const caption = container.querySelector(".custom-caption");
      expect(caption).toBeInTheDocument();
    });
  });

  describe("Complete Table Structure", () => {
    it("renders full table with all components", () => {
      render(
        <Table>
          <TableCaption>A list of users</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>John Doe</TableCell>
              <TableCell>john@example.com</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Jane Smith</TableCell>
              <TableCell>jane@example.com</TableCell>
            </TableRow>
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell>Total</TableCell>
              <TableCell>2 users</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );

      expect(screen.getByText("A list of users")).toBeInTheDocument();
      expect(screen.getByText("Name")).toBeInTheDocument();
      expect(screen.getByText("Email")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("john@example.com")).toBeInTheDocument();
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
      expect(screen.getByText("jane@example.com")).toBeInTheDocument();
      expect(screen.getByText("Total")).toBeInTheDocument();
      expect(screen.getByText("2 users")).toBeInTheDocument();
    });
  });
});
