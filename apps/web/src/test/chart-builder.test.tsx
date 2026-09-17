import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { RecommendResponse, SchemaColumnSchema } from "@data-analyst-lab/shared";

import { ChartBuilder } from "@/components/features/charts/chart-builder";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    postForm: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

const COLUMNS: SchemaColumnSchema[] = [
  {
    column_name: "country",
    inferred_sql_type: "VARCHAR",
    data_type: "categorical",
    null_count: 0,
    null_percentage: 0,
    unique_count: 5,
    unique_percentage: 5,
  },
  {
    column_name: "revenue",
    inferred_sql_type: "DOUBLE",
    data_type: "numeric",
    null_count: 0,
    null_percentage: 0,
    unique_count: 100,
    unique_percentage: 100,
  },
];

describe("ChartBuilder", () => {
  it("defaults to a bar chart with the first categorical/numeric columns pre-selected", () => {
    renderWithProviders(<ChartBuilder columns={COLUMNS} onCreate={vi.fn()} isCreating={false} />);
    expect(screen.getByLabelText("Chart Type")).toHaveValue("bar");
    expect(screen.getByLabelText("X Axis")).toHaveValue("country");
    expect(screen.getByLabelText("Y Axis")).toHaveValue("revenue");
  });

  it("asks for and displays a chart-type recommendation", async () => {
    const recommendation: RecommendResponse = {
      chart_type: "bar",
      reason: "A category on the X axis against a numeric Y axis compares groups best as a bar chart.",
    };
    vi.mocked(apiClient.post).mockResolvedValueOnce(recommendation);

    renderWithProviders(<ChartBuilder columns={COLUMNS} onCreate={vi.fn()} isCreating={false} />);
    fireEvent.click(screen.getByRole("button", { name: /What chart should I use/ }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/charts/recommend", { x_type: "categorical", y_type: "numeric" }),
    );
    expect(await screen.findByText(/A category on the X axis/)).toBeInTheDocument();
  });

  it("hides Y-axis/aggregation fields and shows bins for a histogram", () => {
    renderWithProviders(<ChartBuilder columns={COLUMNS} onCreate={vi.fn()} isCreating={false} />);
    fireEvent.change(screen.getByLabelText("Chart Type"), { target: { value: "histogram" } });

    expect(screen.queryByLabelText("Y Axis")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Bins")).toBeInTheDocument();
  });

  it("calls onCreate with an assembled config when the user clicks Create Chart", () => {
    const onCreate = vi.fn();
    renderWithProviders(<ChartBuilder columns={COLUMNS} onCreate={onCreate} isCreating={false} />);

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Revenue by country" } });
    fireEvent.click(screen.getByRole("button", { name: "Create Chart" }));

    expect(onCreate).toHaveBeenCalledWith({
      chartType: "bar",
      title: "Revenue by country",
      config: expect.objectContaining({ x: "country", y: "revenue", aggregation: "SUM", title: "Revenue by country" }),
    });
  });
});
