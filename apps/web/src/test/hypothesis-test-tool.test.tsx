import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { TestResultResponse } from "@data-analyst-lab/shared";

import { HypothesisTestTool } from "@/components/features/statistics/hypothesis-test-tool";
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

describe("HypothesisTestTool", () => {
  it("renders a placeholder instead of crashing when statistic/p_value are null (a degenerate, zero-variance input)", async () => {
    /**
     * Regression test — a real, live-reproduced bug: a constant sample
     * (e.g. testing a metric that hasn't varied yet) makes scipy return NaN
     * for every t-test/ANOVA/chi-square/Mann-Whitney variant, which the API
     * legitimately serializes as JSON null. The component used to call
     * `result.statistic.toFixed(4)`/`result.p_value.toFixed(4)` with no
     * null check, throwing and — with no error boundary at the time —
     * blanking the whole Statistics workspace.
     */
    const response: TestResultResponse = {
      test_type: "one_sample_t",
      test_name: "One-sample t-test",
      statistic: null,
      p_value: null,
      degrees_of_freedom: 2,
      alpha: 0.05,
      alternative: "two-sided",
      reject_null: false,
      interpretation: "p = nan is not less than alpha = 0.05, so we fail to reject the null hypothesis.",
      assumptions: [],
      effect_size: null,
      effect_size_label: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<HypothesisTestTool onJumpToCorrelation={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Run Test" }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalled());
    expect(await screen.findByText(response.interpretation)).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2); // statistic and p-value both placeholder
  });
});
