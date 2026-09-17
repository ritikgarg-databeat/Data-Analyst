import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { AnalyzeABTestResponse } from "@data-analyst-lab/shared";

import { ABTestAnalyzer } from "@/components/features/experiments/ab-test-analyzer";
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

const RESPONSE: AnalyzeABTestResponse = {
  control_users: 10000,
  control_conversions: 1000,
  treatment_users: 10000,
  treatment_conversions: 1250,
  control_rate: 0.1,
  treatment_rate: 0.125,
  absolute_difference: 0.025,
  relative_uplift: 0.25,
  confidence_interval_95: [0.014, 0.036],
  z_statistic: 4.5,
  p_value: 0.00001,
  alpha: 0.05,
  is_statistically_significant: true,
  minimum_practical_effect: null,
  is_practically_significant: null,
  verdict: "Ship-worthy evidence",
  interpretation: "Control converts at 10.00%, treatment at 12.50% (+2.50 points, +25.0% relative).",
};

describe("ABTestAnalyzer", () => {
  it("submits control/treatment counts and renders the verdict", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(RESPONSE);
    renderWithProviders(<ABTestAnalyzer />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/experiments/analyze",
        expect.objectContaining({ control_users: 10000, treatment_conversions: 1080 }),
      ),
    );
    expect(await screen.findByText("Ship-worthy evidence")).toBeInTheDocument();
    expect(screen.getByText(RESPONSE.interpretation)).toBeInTheDocument();
  });

  it("renders a placeholder instead of crashing when p_value is null (zero conversions on both sides)", async () => {
    /**
     * Regression test — a real, live-reproduced bug: analyzing a brand-new
     * experiment before either variant has a conversion yet (a routine,
     * day-one scenario, not an edge case) makes statsmodels' proportions_ztest
     * divide by a zero pooled-variance term, and the API legitimately
     * returns null for z_statistic/p_value. The component used to call
     * `result.p_value.toFixed(4)` with no null check, throwing
     * `TypeError: Cannot read properties of null` and — since the app had no
     * error boundary at the time — blanking the entire Experiments workspace.
     */
    vi.mocked(apiClient.post).mockResolvedValue({
      ...RESPONSE,
      control_conversions: 0,
      treatment_conversions: 0,
      control_rate: 0,
      treatment_rate: 0,
      absolute_difference: 0,
      relative_uplift: null,
      z_statistic: null,
      p_value: null,
      is_statistically_significant: false,
      verdict: "Not enough evidence yet",
    } satisfies AnalyzeABTestResponse);
    renderWithProviders(<ABTestAnalyzer />);

    fireEvent.click(screen.getByRole("button", { name: "Analyze" }));

    expect(await screen.findByText("Not enough evidence yet")).toBeInTheDocument();
    // "—" appears for both relative_uplift (already null-guarded before this
    // fix) and p_value (the newly-fixed field).
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);
  });
});
