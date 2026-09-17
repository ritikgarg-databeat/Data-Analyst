import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { CareerDashboardResponse, CareerWeeklyReviewResponse } from "@data-analyst-lab/shared";

import { CareerDashboard } from "@/components/features/career/career-dashboard";
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

function makeDashboard(overrides: Partial<CareerDashboardResponse> = {}): CareerDashboardResponse {
  return {
    profile: {
      id: "profile-1",
      headline: "Aspiring Data Analyst",
      summary: null,
      primary_target_role_id: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    },
    primary_target_role: null,
    target_role_count: 0,
    latest_assessment: null,
    active_goal_count: 0,
    recent_milestones: [],
    achievement_count: 0,
    saved_job_count: 0,
    ...overrides,
  };
}

function makeWeeklyReview(overrides: Partial<CareerWeeklyReviewResponse> = {}): CareerWeeklyReviewResponse {
  return {
    period_start: "2026-01-01",
    period_end: "2026-01-07",
    exercises_attempted: 5,
    exercises_passed: 3,
    cases_completed: 1,
    projects_completed: 0,
    interviews_completed: 1,
    new_milestones: [],
    weak_skill_slugs: [],
    ...overrides,
  };
}

describe("CareerDashboard", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.patch).mockReset();
  });

  it("shows the career profile headline and quick links", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/dashboard") return makeDashboard();
      if (path === "/career/weekly-review") return makeWeeklyReview();
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<CareerDashboard />);

    expect(await screen.findByText("Aspiring Data Analyst")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Target Roles/ })).toHaveAttribute("href", "/career/target-roles");
    expect(screen.getByRole("link", { name: /Portfolio/ })).toHaveAttribute("href", "/career/portfolio");
  });

  it("shows the latest readiness score with the platform-estimate disclaimer", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/dashboard") {
        return makeDashboard({
          latest_assessment: {
            id: "assessment-1",
            target_role_id: null,
            rubric_scores: {
              TECHNICAL: 70,
              ANALYTICAL: 65,
              BUSINESS: 60,
              PRODUCT: 55,
              DATA_ENGINEERING_AWARENESS: 50,
              COMMUNICATION: 60,
              INTERVIEW: 58,
              PORTFOLIO: 40,
            },
            overall_score: 62,
            overall_readiness_level: "DEVELOPING",
            gating_passed: true,
            explanation: { overall: ["A blend of mastery and practice history."] },
            computed_at: "2026-01-05T00:00:00Z",
          },
        });
      }
      if (path === "/career/weekly-review") return makeWeeklyReview();
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<CareerDashboard />);

    expect(await screen.findByText("62%")).toBeInTheDocument();
    expect(screen.getByText("Developing")).toBeInTheDocument();
    expect(screen.getByText(/platform estimate/)).toBeInTheDocument();
  });

  it("saves an edited headline via the profile PATCH endpoint", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/dashboard") return makeDashboard();
      if (path === "/career/weekly-review") return makeWeeklyReview();
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.patch).mockResolvedValue({
      id: "profile-1",
      headline: "Data Analyst, SQL-focused",
      summary: null,
      primary_target_role_id: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    });

    renderWithProviders(<CareerDashboard />);
    expect(await screen.findByText("Aspiring Data Analyst")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    const headlineInput = screen.getByLabelText("Headline");
    fireEvent.change(headlineInput, { target: { value: "Data Analyst, SQL-focused" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(apiClient.patch).toHaveBeenCalledWith(
        "/career/profile",
        expect.objectContaining({ headline: "Data Analyst, SQL-focused" }),
      ),
    );
  });
});
