import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { InterviewBookmark, InterviewQuestionListItem } from "@data-analyst-lab/shared";

import { InterviewQuestionCatalog } from "@/components/features/interview/interview-question-catalog";
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

function makeQuestion(overrides: Partial<InterviewQuestionListItem> = {}): InterviewQuestionListItem {
  return {
    id: "q-1",
    slug: "aov-query",
    interview_type: "SQL",
    difficulty: "INTERMEDIATE",
    title: "Average Order Value",
    points: 10,
    time_limit_seconds: 600,
    company_archetypes: [],
    tags: [],
    is_bookmarked: false,
    best_score: null,
    attempt_count: 0,
    ...overrides,
  };
}

describe("InterviewQuestionCatalog", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.delete).mockReset();
  });

  it("lists questions and re-queries when a type filter is applied", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interview/questions") return [makeQuestion()];
      if (path.startsWith("/interview/questions?interview_type=PYTHON")) return [];
      if (path === "/interview/bookmarks") return [];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<InterviewQuestionCatalog />);
    expect(await screen.findByText("Average Order Value")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filter by type"), { target: { value: "PYTHON" } });

    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining("interview_type=PYTHON")),
    );
    await waitFor(() => expect(screen.queryByText("Average Order Value")).not.toBeInTheDocument());
  });

  it("bookmarks a question and reflects it after toggling", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interview/questions") return [makeQuestion()];
      if (path === "/interview/bookmarks") return [];
      throw new Error(`Unhandled GET ${path}`);
    });
    const bookmark: InterviewBookmark = { id: "bm-1", target_type: "QUESTION", target_id: "q-1", created_at: "2026-01-01T00:00:00Z" };
    vi.mocked(apiClient.post).mockResolvedValue(bookmark);

    renderWithProviders(<InterviewQuestionCatalog />);
    expect(await screen.findByText("Average Order Value")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Add bookmark" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/interview/bookmarks", { target_type: "QUESTION", target_id: "q-1" }),
    );
  });
});
