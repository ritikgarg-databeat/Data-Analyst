import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { AnswerInterviewQuestionResponse, Interview } from "@data-analyst-lab/shared";

import { InterviewSessionWorkspace } from "@/components/features/interview/interview-session-workspace";
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
  useParams: () => ({ id: "interview-1" }),
}));

// Monaco touches `window` in ways jsdom doesn't support — the SQL editor
// isn't under test here (that's covered by test-selection-assistant.test.tsx-
// style existing SQL Lab tests), so stub it to a plain textarea.
vi.mock("@/components/features/sql-lab/sql-editor", () => ({
  SqlEditor: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="SQL query editor" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

function makeInterview(overrides: Partial<Interview> = {}): Interview {
  return {
    id: "interview-1",
    template_id: null,
    mode: "PRACTICE",
    status: "IN_PROGRESS",
    title: "Sql Practice",
    total_time_limit_seconds: null,
    time_spent_seconds: 0,
    current_section_index: 0,
    started_at: "2026-01-01T00:00:00Z",
    paused_at: null,
    completed_at: null,
    score: null,
    feedback: null,
    created_at: "2026-01-01T00:00:00Z",
    sections: [
      {
        id: "section-1",
        interview_type: "SQL",
        title: "SQL",
        time_limit_seconds: null,
        display_order: 0,
        started_at: "2026-01-01T00:00:00Z",
        completed_at: null,
        time_spent_seconds: 0,
      },
    ],
    question_attempts: [
      {
        id: "attempt-1",
        section_id: "section-1",
        interview_question_id: "q-1",
        case_attempt_id: null,
        exercise_attempt_id: null,
        parent_attempt_id: null,
        is_follow_up: false,
        display_order: 0,
        started_at: "2026-01-01T00:00:00Z",
        time_spent_seconds: 0,
        question: {
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
          exercise_slug: "aov-query",
          exercise_type: "SQL",
          prompt: "Compute the average order value for completed payments.",
          business_context: null,
          stakeholder: null,
          constraints: [],
          expected_deliverables: [],
          rubric: [],
          choices: null,
          hint_count: 0,
          follow_up_question_ids: [],
          dataset: "ecommerce",
          sql_starter_query: "SELECT * FROM payments LIMIT 10;",
          python_starter_code: null,
          excel_starter_sheets: [],
          excel_check_cells: [],
        },
        exercise_attempt_score: null,
        case_attempt_status: null,
      },
    ],
    current_question: {
      id: "attempt-1",
      section_id: "section-1",
      interview_question_id: "q-1",
      case_attempt_id: null,
      exercise_attempt_id: null,
      parent_attempt_id: null,
      is_follow_up: false,
      display_order: 0,
      started_at: "2026-01-01T00:00:00Z",
      time_spent_seconds: 0,
      question: {
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
        exercise_slug: "aov-query",
        exercise_type: "SQL",
        prompt: "Compute the average order value for completed payments.",
        business_context: null,
        stakeholder: null,
        constraints: [],
        expected_deliverables: [],
        rubric: [],
        choices: null,
        hint_count: 0,
        follow_up_question_ids: [],
        dataset: "ecommerce",
        sql_starter_query: "SELECT * FROM payments LIMIT 10;",
        python_starter_code: null,
        excel_starter_sheets: [],
        excel_check_cells: [],
      },
      exercise_attempt_score: null,
      case_attempt_status: null,
    },
    ...overrides,
  };
}

describe("InterviewSessionWorkspace", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    pushMock.mockReset();
  });

  it("renders the current question and submits an answer", async () => {
    const interview = makeInterview();
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/interviews/interview-1") return interview;
      throw new Error(`Unhandled GET ${path}`);
    });
    const response: AnswerInterviewQuestionResponse = {
      interview: { ...interview, score: { overall: 100, dimensions: [] } },
      is_auto_graded: true,
      score: 100,
      explanation: "Correct!",
      correct_answer: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<InterviewSessionWorkspace interviewId="interview-1" />);

    expect(await screen.findByText("Average Order Value")).toBeInTheDocument();
    expect(screen.getByText(/average order value for completed payments/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("SQL query editor"), {
      target: { value: "SELECT AVG(amount) FROM payments WHERE status = 'success'" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit Answer" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/interviews/interview-1/answer", {
        submitted_query: "SELECT AVG(amount) FROM payments WHERE status = 'success'",
      }),
    );
    expect(await screen.findByText("Scored 100%")).toBeInTheDocument();
  });

  it("shows a Start button before the interview begins and starts it", async () => {
    const interview = makeInterview({ status: "NOT_STARTED", current_question: null, question_attempts: [] });
    vi.mocked(apiClient.get).mockResolvedValue(interview);
    vi.mocked(apiClient.post).mockResolvedValue({ ...interview, status: "IN_PROGRESS" });

    renderWithProviders(<InterviewSessionWorkspace interviewId="interview-1" />);

    const startButton = await screen.findByRole("button", { name: /Start Interview/ });
    fireEvent.click(startButton);

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/interviews/interview-1/start"));
  });

  it("redirects to the review page once the interview is completed", async () => {
    const interview = makeInterview({ status: "COMPLETED" });
    vi.mocked(apiClient.get).mockResolvedValue(interview);

    renderWithProviders(<InterviewSessionWorkspace interviewId="interview-1" />);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/interview/session/interview-1/review"));
  });
});
