import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { BehavioralStory, BehavioralStoryCoverageResponse } from "@data-analyst-lab/shared";

import { BehavioralStoriesPage } from "@/components/features/career/behavioral-stories-page";
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

function makeStory(overrides: Partial<BehavioralStory> = {}): BehavioralStory {
  return {
    id: "story-1",
    category: "OWNERSHIP",
    title: "Owned a broken dashboard",
    situation: "A key dashboard was silently wrong.",
    task: "Diagnose and fix it before the weekly review.",
    action: "Traced the pipeline, found a join fanout, and rebuilt the model.",
    result: "Stakeholders trusted the numbers again within a day.",
    related_question_ids: [],
    last_practiced_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeCoverage(overrides: Partial<BehavioralStoryCoverageResponse> = {}): BehavioralStoryCoverageResponse {
  return {
    coverage: [
      { category: "OWNERSHIP", story_count: 1, has_coverage: true },
      { category: "CONFLICT", story_count: 0, has_coverage: false },
    ],
    missing_categories: ["CONFLICT"],
    ...overrides,
  };
}

describe("BehavioralStoriesPage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
  });

  it("groups stories by category and highlights missing coverage", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/behavioral-stories") return [makeStory()];
      if (path === "/career/behavioral-stories/coverage") return makeCoverage();
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<BehavioralStoriesPage />);

    expect(await screen.findByText("Owned a broken dashboard")).toBeInTheDocument();
    // Coverage badges show story counts, including the 0-story missing category.
    expect(screen.getByText(/Conflict \(0\)/)).toBeInTheDocument();
    expect(screen.getByText(/Ownership \(1\)/)).toBeInTheDocument();
  });

  it("submits a new story via the create form", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/behavioral-stories") return [];
      if (path === "/career/behavioral-stories/coverage") return makeCoverage({ coverage: [], missing_categories: [] });
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeStory());

    renderWithProviders(<BehavioralStoriesPage />);
    await screen.findByLabelText("Title");

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Owned a broken dashboard" } });
    fireEvent.change(screen.getByLabelText("Situation"), { target: { value: "A key dashboard was silently wrong." } });
    fireEvent.change(screen.getByLabelText("Task"), { target: { value: "Diagnose and fix it." } });
    fireEvent.change(screen.getByLabelText("Action"), { target: { value: "Traced the pipeline." } });
    fireEvent.change(screen.getByLabelText("Result"), { target: { value: "Trust restored." } });
    fireEvent.click(screen.getByRole("button", { name: "Add Story" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/career/behavioral-stories",
        expect.objectContaining({ title: "Owned a broken dashboard", category: "OWNERSHIP" }),
      ),
    );
  });
});
