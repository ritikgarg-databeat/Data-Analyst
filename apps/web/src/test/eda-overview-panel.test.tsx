import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import type { EdaOverview } from "@data-analyst-lab/shared";

import { EdaOverviewPanel } from "@/components/features/eda/eda-overview-panel";

import { renderWithProviders } from "./test-utils";

const OVERVIEW: EdaOverview = {
  table_name: "orders",
  row_count: 1000,
  column_count: 4,
  duplicate_row_count: 12,
  missingness: [
    { column: "phone", null_percentage: 8.7 },
    { column: "country", null_percentage: 1.2 },
  ],
  distributions: [{ column: "revenue", mean: 52.3, median: 45.0, std_dev: 20.1, quantiles: { p25: 30, p50: 45, p75: 60 } }],
  categorical_summaries: [
    { column: "country", top_values: [{ value: "US", count: 500, percentage: 50 }] },
  ],
  correlations: [{ column_a: "revenue", column_b: "quantity", correlation: 0.82 }],
  date_trends: [{ column: "order_date", min_date: "2024-01-01", max_date: "2024-06-01", missing_calendar_days: 3 }],
  outliers: [{ column: "revenue", outlier_count: 7, method: "iqr" }],
  generated_at: "2026-01-01T00:00:00Z",
};

describe("EdaOverviewPanel", () => {
  it("renders dataset shape stats", () => {
    renderWithProviders(<EdaOverviewPanel overview={OVERVIEW} />);
    expect(screen.getByText("1,000")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("sorts missingness worst-first (already sorted by the backend) and shows percentages", () => {
    renderWithProviders(<EdaOverviewPanel overview={OVERVIEW} />);
    expect(screen.getByText("8.7%")).toBeInTheDocument();
    expect(screen.getByText("1.2%")).toBeInTheDocument();
  });

  it("renders correlation pairs with the causation disclaimer", () => {
    renderWithProviders(<EdaOverviewPanel overview={OVERVIEW} />);
    expect(screen.getByText("revenue ↔ quantity")).toBeInTheDocument();
    expect(screen.getByText("0.82")).toBeInTheDocument();
    expect(screen.getByText("Correlation does not imply causation.")).toBeInTheDocument();
  });

  it("renders outliers with the legitimate-observations disclaimer", () => {
    renderWithProviders(<EdaOverviewPanel overview={OVERVIEW} />);
    expect(screen.getByText(/7 potential outlier\(s\) \(iqr\)/)).toBeInTheDocument();
    expect(screen.getByText(/may be legitimate business observations/)).toBeInTheDocument();
  });

  it("shows a friendly message when a section has nothing to report", () => {
    const empty: EdaOverview = { ...OVERVIEW, missingness: [], correlations: [], outliers: [] };
    renderWithProviders(<EdaOverviewPanel overview={empty} />);
    expect(screen.getByText("No missing values found.")).toBeInTheDocument();
    expect(screen.getByText(/No notable correlations/)).toBeInTheDocument();
    expect(screen.getByText("No outliers flagged.")).toBeInTheDocument();
  });
});
