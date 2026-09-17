import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { AIStructuredResponse } from "@data-analyst-lab/shared";

import { SqlAskAiPanel } from "@/components/features/sql-lab/sql-ask-ai-panel";
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

describe("SqlAskAiPanel", () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset();
  });

  it("defaults to Debug Error mode when an error is present and sends the real error message", async () => {
    const response: AIStructuredResponse = {
      raw_text: "not-json",
      structured: {
        what_happened: "The query referenced a column that doesn't exist.",
        why_it_likely_happened: "A typo in the column name.",
        where: "The SELECT clause.",
        how_to_investigate: "Check the table schema.",
        suggested_fix: "Correct the column name.",
      },
      structured_valid: true,
      provider: "local",
      model: "local",
      ai_configured: true,
      audit_id: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(
      <SqlAskAiPanel
        open
        onOpenChange={() => {}}
        query="SELECT nope_col FROM orders"
        engine="duckdb"
        database="ecommerce"
        error={{ message: 'Binder Error: Referenced column "nope_col" not found', hint: null }}
      />,
    );

    expect(screen.getByRole("tab", { name: "Debug Error", selected: true })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Ask AI to debug" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/ai/sql/debug",
        expect.objectContaining({
          query: "SELECT nope_col FROM orders",
          error_message: 'Binder Error: Referenced column "nope_col" not found',
        }),
      ),
    );

    expect(await screen.findByText("The query referenced a column that doesn't exist.")).toBeInTheDocument();
    expect(screen.getByText("Correct the column name.")).toBeInTheDocument();
  });

  it("defaults to Review Query mode when there is no error", () => {
    renderWithProviders(
      <SqlAskAiPanel
        open
        onOpenChange={() => {}}
        query="SELECT * FROM orders"
        engine="duckdb"
        database="ecommerce"
        error={null}
      />,
    );
    expect(screen.getByRole("tab", { name: "Review Query", selected: true })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Debug Error" })).toBeDisabled();
  });
});
