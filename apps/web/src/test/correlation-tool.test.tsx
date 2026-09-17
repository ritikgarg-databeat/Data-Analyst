import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { TestResultResponse } from "@data-analyst-lab/shared";

import { CorrelationTool } from "@/components/features/statistics/correlation-tool";
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

describe("CorrelationTool", () => {
  it("renders a placeholder instead of crashing when statistic/p_value are null (a constant X)", async () => {
    /**
     * Regression test — a real, live-reproduced bug: correlating a constant
     * column against anything (zero variance — e.g. a dataset column that
     * never changes, a very plausible first thing a learner tries) makes
     * scipy's pearsonr/spearmanr return NaN, which the API legitimately
     * serializes as JSON null. The component used to call
     * `result.statistic.toFixed(4)`/`result.p_value.toFixed(4)` with no
     * null check, throwing and blanking the whole Statistics workspace.
     */
    const response: TestResultResponse = {
      test_type: "pearson_correlation",
      test_name: "Pearson correlation test",
      statistic: null,
      p_value: null,
      degrees_of_freedom: 1,
      alpha: 0.05,
      alternative: "two-sided",
      reject_null: false,
      interpretation: "p = nan is not less than alpha = 0.05, so we fail to reject the null hypothesis.",
      assumptions: [],
      effect_size: null,
      effect_size_label: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<CorrelationTool />);
    fireEvent.change(screen.getByLabelText("X values"), { target: { value: "5, 5, 5" } });
    fireEvent.change(screen.getByLabelText("Y values"), { target: { value: "1, 2, 3" } });
    fireEvent.click(screen.getByRole("button", { name: "Compute Correlation" }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalled());
    expect(await screen.findByText(response.interpretation)).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);
  });
});
