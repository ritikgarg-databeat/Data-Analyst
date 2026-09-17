import { describe, expect, it } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";
import type { SqlColumnInfo } from "@data-analyst-lab/shared";

import { ResultsGrid } from "@/components/features/sql-lab/results-grid";

import { renderWithProviders } from "./test-utils";

describe("ResultsGrid", () => {
  it("renders an empty state when there are no columns and no rows", () => {
    renderWithProviders(<ResultsGrid columns={[]} rows={[]} rowCount={0} />);

    expect(screen.getByText("No results yet")).toBeInTheDocument();
  });

  it("renders a no-rows state when the query matched nothing", () => {
    const columns: SqlColumnInfo[] = [{ name: "id", type: "INTEGER" }];
    renderWithProviders(<ResultsGrid columns={columns} rows={[]} rowCount={0} />);

    expect(screen.getByText("No rows returned")).toBeInTheDocument();
  });

  it("renders rows plus the row/column count summary", () => {
    const columns: SqlColumnInfo[] = [
      { name: "id", type: "INTEGER" },
      { name: "name", type: "VARCHAR" },
    ];
    const rows = [
      [1, "Alice"],
      [2, "Bob"],
    ];
    renderWithProviders(<ResultsGrid columns={columns} rows={rows} rowCount={2} />);

    expect(screen.getByText("2 rows · 2 columns")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.queryByText(/truncated/i)).not.toBeInTheDocument();
  });

  it("renders a NULL cell distinctly and shows the truncated notice when truncated", () => {
    const columns: SqlColumnInfo[] = [{ name: "id", type: "INTEGER" }];
    const rows = [[null]];
    renderWithProviders(<ResultsGrid columns={columns} rows={rows} rowCount={2000} truncated />);

    expect(screen.getByText("NULL")).toBeInTheDocument();
    expect(screen.getByText(/Results truncated at 2,000 rows/)).toBeInTheDocument();
  });

  it("sorts rows numerically when a column header is clicked, cycling asc -> desc -> unsorted", () => {
    const columns: SqlColumnInfo[] = [{ name: "amount", type: "DOUBLE" }];
    const rows = [[30], [10], [20]];
    renderWithProviders(<ResultsGrid columns={columns} rows={rows} rowCount={3} />);

    function bodyValues() {
      return screen
        .getAllByRole("row")
        .slice(1) // drop the header row
        .map((row) => within(row).getAllByRole("cell")[0].textContent);
    }

    expect(bodyValues()).toEqual(["30", "10", "20"]);

    const sortButton = screen.getByRole("button", { name: /Sort by amount/i });
    fireEvent.click(sortButton);
    expect(bodyValues()).toEqual(["10", "20", "30"]);

    fireEvent.click(sortButton);
    expect(bodyValues()).toEqual(["30", "20", "10"]);

    fireEvent.click(sortButton);
    expect(bodyValues()).toEqual(["30", "10", "20"]);
  });

  it("paginates rows according to pageSize, with working Previous/Next controls", () => {
    const columns: SqlColumnInfo[] = [{ name: "id", type: "INTEGER" }];
    const rows = [[1], [2], [3], [4], [5]];
    renderWithProviders(<ResultsGrid columns={columns} rows={rows} rowCount={5} pageSize={2} />);

    expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.queryByText("3")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 2 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 3 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
});
