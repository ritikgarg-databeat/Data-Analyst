import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { Interview, ReadinessResponse } from "@data-analyst-lab/shared";

import { InterviewDashboard } from "@/components/features/interview/interview-dashboard";
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

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function makeReadiness(overrides: Partial<ReadinessResponse> = {}): ReadinessResponse {
  return {
    overall_score: 62,
    mastery_component: 70,
    recent_performance_component: 55,
    consistency_component: 60,
    breakdown: { SQL: 80, BEHAVIORAL: 40 },
    strongest: ["SQL"],
    weakest: ["BEHAVIORAL"],
    ...overrides,
  };
}

function makeInterview(overrides: Partial<Interview> = {}): Interview {
  return {
    id: "interview-1",
    template_id: null,
    mode: "PRACTICE",
    status: "NOT_STARTED",
    title: "Sql Practice",
    total_time_limit_seconds: null,
    time_spent_seconds: 0,
    current_section_index: 0,
    started_at: null,
    paused_at: null,
    completed_at: null,
    score: null,
    feedback: null,
    created_at: "2026-01-01T00:00:00Z",
    sections: [],
    question_attempts: [],
    current_question: null,
    ...overrides,
  };
}

describe("InterviewDashboard", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    pushMock.mockReset();
  });

  it("shows overall readiness and strongest/weakest areas", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interview/readiness") return makeReadiness();
      if (path === "/interviews") return [];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<InterviewDashboard />);

    expect(await screen.findByText("62%")).toBeInTheDocument();
    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.getByText("Behavioral")).toBeInTheDocument();
  });

  it("starts a quick-start interview and navigates to its session", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interview/readiness") return makeReadiness();
      if (path === "/interviews") return [];
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeInterview());

    renderWithProviders(<InterviewDashboard />);
    expect(await screen.findByText("62%")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Practice SQL/ }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/interviews",
        expect.objectContaining({ mode: "PRACTICE", interview_type: "SQL" }),
      ),
    );
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/interview/session/interview-1"));
  });

  it("shows a resume banner when an interview is already in progress", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interview/readiness") return makeReadiness();
      if (path === "/interviews") return [makeInterview({ id: "in-progress-1", status: "IN_PROGRESS" })];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<InterviewDashboard />);

    expect(await screen.findByText("Resume in-progress interview")).toBeInTheDocument();
  });
});
