import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { SummaryStatsResponse } from "@data-analyst-lab/shared";

import { SummaryStatsTool } from "@/components/features/statistics/summary-stats-tool";
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

const RESPONSE: SummaryStatsResponse = {
  count: 5,
  mean: 3,
  median: 3,
  mode: [],
  min: 1,
  max: 5,
  range: 4,
  variance: 2.5,
  std_dev: 1.5811,
  coefficient_of_variation: 0.527,
  q1: 2,
  q3: 4,
  iqr: 2,
  percentiles: { "50": 3 },
  skewness: 0,
  outlier_count: 0,
  outlier_bounds: [-1, 7],
  mean_confidence_interval: { level: 0.95, lower: 1.04, upper: 4.96, margin_of_error: 1.96 },
  methodology: "Variance/std dev use the sample formula.",
};

describe("SummaryStatsTool", () => {
  it("computes and displays descriptive statistics for pasted numbers", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(RESPONSE);
    renderWithProviders(<SummaryStatsTool />);

    fireEvent.change(screen.getByLabelText("Values"), { target: { value: "1, 2, 3, 4, 5" } });
    fireEvent.click(screen.getByRole("button", { name: "Compute" }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/statistics/summary", { values: [1, 2, 3, 4, 5] }));
    expect(await screen.findByText("2.500")).toBeInTheDocument();
    expect(screen.getByText(RESPONSE.methodology)).toBeInTheDocument();
  });

  it("disables Compute until at least 2 values are entered", () => {
    renderWithProviders(<SummaryStatsTool />);
    expect(screen.getByRole("button", { name: "Compute" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Values"), { target: { value: "1" } });
    expect(screen.getByRole("button", { name: "Compute" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Values"), { target: { value: "1, 2" } });
    expect(screen.getByRole("button", { name: "Compute" })).toBeEnabled();
  });
});
