import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import type { ProgressSummary, RecommendationItem } from "@data-analyst-lab/shared";

import DashboardPage from "@/app/dashboard/page";
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

vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ user: { name: "Jordan Lee" } }),
}));

const baseSummary: ProgressSummary = {
  overall_progress_percent: 42,
  current_level: "INTERMEDIATE",
  learning_streak_days: 5,
  skills_mastered: 3,
  total_skills: 12,
  continue_learning: [],
  recently_completed: [],
  weak_areas: [],
  activity: [],
  skill_overview: [],
};

/** Routes each GET by path so /progress/summary and /recommendations don't collide. */
function mockApiGet(overrides: { summary?: ProgressSummary; recommendations?: RecommendationItem[] } = {}) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path.startsWith("/recommendations")) {
      return Promise.resolve(overrides.recommendations ?? []);
    }
    // Phase 12 dashboard additions — realistic empty responses so they don't
    // collide with the ProgressSummary shape returned by the fallback below.
    if (path.startsWith("/platform/next-best-actions")) {
      return Promise.resolve({ actions: [] });
    }
    if (path === "/career/readiness/latest") {
      return Promise.resolve(null);
    }
    return Promise.resolve(overrides.summary ?? baseSummary);
  });
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it("renders the header, subtitle, and all four progress cards", async () => {
    mockApiGet();

    renderWithProviders(<DashboardPage />);

    expect(screen.getByRole("heading", { name: "Jordan's Personal Data Lab" })).toBeInTheDocument();
    expect(screen.getByText("Your focused space to learn, practice, build, and grow.")).toBeInTheDocument();

    expect(await screen.findByText("Overall Progress")).toBeInTheDocument();
    expect(screen.getByText("Current Level")).toBeInTheDocument();
    expect(screen.getByText("Learning Streak")).toBeInTheDocument();
    expect(screen.getByText("Skills Mastered")).toBeInTheDocument();

    expect(screen.getByText("42%")).toBeInTheDocument();
    expect(screen.getByText("Intermediate")).toBeInTheDocument();
    expect(screen.getByText("5 days")).toBeInTheDocument();
    expect(screen.getByText("3 / 12")).toBeInTheDocument();
  });

  it("shows the 'journey starts here' empty state when continue_learning is empty", async () => {
    mockApiGet();

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("Your learning journey starts here.")).toBeInTheDocument();
  });

  it("renders Today's Mission recommendations and its empty state", async () => {
    mockApiGet({
      recommendations: [
        {
          lesson: {
            id: "lesson-1",
            module_id: "module-1",
            module_slug: "sql-fundamentals",
            domain_slug: "sql",
            slug: "where",
            title: "WHERE",
            description: null,
            content_type: "READING",
            difficulty: "BEGINNER",
            estimated_minutes: 10,
            display_order: 2,
            content_reference: null,
            is_active: true,
            tags: [],
            skills: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          reason: "next_in_module",
          explanation: "Continues where you left off.",
        },
      ],
    });

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("WHERE")).toBeInTheDocument();
    expect(screen.getByText("Next Up")).toBeInTheDocument();
  });

  it("shows an empty state for Today's Mission when there are no recommendations", async () => {
    mockApiGet({ recommendations: [] });

    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText("No mission yet")).toBeInTheDocument();
  });
});
