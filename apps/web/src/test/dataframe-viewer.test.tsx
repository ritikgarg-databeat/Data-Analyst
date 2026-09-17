import { describe, expect, it } from "vitest";
import { fireEvent, screen } from "@testing-library/react";
import type { DataFrameSummarySchema } from "@data-analyst-lab/shared";

import { DataFrameViewer } from "@/components/features/python-lab/dataframe-viewer";

import { renderWithProviders } from "./test-utils";

const dataframe: DataFrameSummarySchema = {
  row_count: 3,
  column_count: 2,
  columns: [
    { name: "id", dtype: "int64", null_count: 0, unique_count: 3 },
    { name: "name", dtype: "object", null_count: 1, unique_count: 2 },
  ],
  preview_rows: [
    [1, "Alice"],
    [2, "Bob"],
    [3, null],
  ],
  preview_row_count: 3,
  truncated: false,
  memory_usage_bytes: 2_516_582, // -> "2.4 MB"
};

describe("DataFrameViewer", () => {
  it("renders the row/column summary and memory usage", () => {
    renderWithProviders(<DataFrameViewer dataframe={dataframe} name="orders" />);

    expect(screen.getByText("orders")).toBeInTheDocument();
    expect(screen.getByText("3 rows × 2 columns")).toBeInTheDocument();
    expect(screen.getByText("· 2.4 MB")).toBeInTheDocument();
  });

  it("shows preview rows (including a NULL cell) on the default Preview tab", () => {
    renderWithProviders(<DataFrameViewer dataframe={dataframe} />);

    expect(screen.getByRole("tab", { name: "Preview" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("NULL")).toBeInTheDocument();
  });

  it("switches to the Schema tab and shows column name/dtype pairs", () => {
    renderWithProviders(<DataFrameViewer dataframe={dataframe} />);

    fireEvent.click(screen.getByRole("tab", { name: "Schema" }));

    expect(screen.getByRole("tab", { name: "Schema" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("int64")).toBeInTheDocument();
    expect(screen.getByText("object")).toBeInTheDocument();
    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
  });

  it("switches to the Statistics tab and shows missing/unique counts plus memory usage", () => {
    renderWithProviders(<DataFrameViewer dataframe={dataframe} />);

    fireEvent.click(screen.getByRole("tab", { name: "Statistics" }));

    expect(screen.getByRole("tab", { name: "Statistics" })).toHaveAttribute("aria-selected", "true");
    const rows = screen.getAllByRole("row").slice(1); // drop the header row
    expect(rows[0]).toHaveTextContent("id");
    expect(rows[0]).toHaveTextContent("0"); // null_count
    expect(rows[0]).toHaveTextContent("3"); // unique_count
    expect(rows[1]).toHaveTextContent("name");
    expect(rows[1]).toHaveTextContent("1"); // null_count
    expect(screen.getByText("Memory usage: 2.4 MB")).toBeInTheDocument();
  });
});
