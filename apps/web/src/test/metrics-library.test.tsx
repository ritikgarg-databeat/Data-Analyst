import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { MetricDefinition } from "@data-analyst-lab/shared";

import { MetricsLibrary } from "@/components/features/metrics/metrics-library";
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

function makeMetric(overrides: Partial<MetricDefinition> = {}): MetricDefinition {
  return {
    id: "m-1",
    slug: "cac",
    name: "Customer Acquisition Cost (CAC)",
    category: "marketing",
    definition: "The average cost to acquire one new paying customer.",
    formula: "Total acquisition spend / new customers",
    examples: [],
    sql_example: null,
    python_example: null,
    common_mistakes: [],
    related_metrics: ["ltv"],
    business_questions: [],
    interview_questions: [{ question: "Is CAC of $50 good?", answer: "Depends on LTV." }],
    display_order: 1,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("MetricsLibrary", () => {
  it("lists metrics and opens a detail sheet on click", async () => {
    const metrics = [
      makeMetric(),
      makeMetric({ id: "m-2", slug: "dau", name: "Daily Active Users (DAU)", category: "product" }),
    ];
    vi.mocked(apiClient.get).mockResolvedValue(metrics);
    renderWithProviders(<MetricsLibrary />);

    expect(await screen.findByText("Customer Acquisition Cost (CAC)")).toBeInTheDocument();
    expect(screen.getByText("Daily Active Users (DAU)")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Customer Acquisition Cost (CAC)"));
    await waitFor(() => expect(screen.getByText(/Is CAC of \$50 good\?/)).toBeInTheDocument());
  });

  it("filters by category chip", async () => {
    const metrics = [
      makeMetric(),
      makeMetric({ id: "m-2", slug: "dau", name: "Daily Active Users (DAU)", category: "product" }),
    ];
    vi.mocked(apiClient.get).mockResolvedValue(metrics);
    renderWithProviders(<MetricsLibrary />);

    await screen.findByText("Customer Acquisition Cost (CAC)");
    fireEvent.click(screen.getByRole("tab", { name: "product" }));

    expect(screen.queryByText("Customer Acquisition Cost (CAC)")).not.toBeInTheDocument();
    expect(screen.getByText("Daily Active Users (DAU)")).toBeInTheDocument();
  });

  it("shows an empty state when the API errors", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error("network error"));
    renderWithProviders(<MetricsLibrary />);
    expect(await screen.findByText("Unable to load the metrics library", {}, { timeout: 3000 })).toBeInTheDocument();
  });
});
