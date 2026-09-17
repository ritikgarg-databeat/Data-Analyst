import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { SearchResponse } from "@data-analyst-lab/shared";

import SearchPage from "@/app/search/page";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

function makeResponse(overrides: Partial<SearchResponse> = {}): SearchResponse {
  return {
    query: "sql",
    results: [
      { kind: "lesson", id: "l1", slug: "where", title: "WHERE clauses", description: null, url_path: "/learn/sql/x/where" },
      { kind: "metric", id: "m1", slug: "dau", title: "DAU", description: null, url_path: "/metrics" },
    ],
    ...overrides,
  };
}

describe("SearchPage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it("shows a prompt before searching, then renders grouped results by kind", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(makeResponse());

    renderWithProviders(<SearchPage />);

    expect(screen.getByText("Search the platform")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search the platform"), { target: { value: "sql" } });

    expect(await screen.findByText("WHERE clauses")).toBeInTheDocument();
    expect(screen.getByText("DAU")).toBeInTheDocument();
    // "Lessons"/"Metrics" also appear as filter chip labels, so scope to the
    // result-group headings specifically.
    expect(screen.getByRole("heading", { name: "Lessons" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Metrics" })).toBeInTheDocument();
  });

  it("omits the kind filter entirely while every kind chip is selected", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(makeResponse());

    renderWithProviders(<SearchPage />);
    fireEvent.change(screen.getByLabelText("Search the platform"), { target: { value: "sql" } });

    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringMatching(/^\/search\?q=sql$/)),
    );
  });

  it("filters to the selected kinds once a chip is deselected", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(makeResponse());

    renderWithProviders(<SearchPage />);
    fireEvent.change(screen.getByLabelText("Search the platform"), { target: { value: "sql" } });
    await screen.findByText("WHERE clauses");

    fireEvent.click(screen.getByRole("button", { name: "Metrics" }));

    await waitFor(() => {
      const lastCall = vi.mocked(apiClient.get).mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("kind=");
      expect(lastCall).not.toContain("kind=metric");
    });
  });
});
