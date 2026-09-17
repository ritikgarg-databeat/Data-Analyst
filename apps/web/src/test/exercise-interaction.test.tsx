import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { ExerciseContent, SubmitExerciseAttemptResponse } from "@data-analyst-lab/shared";

import { ExerciseInteraction } from "@/components/features/exercises/exercise-interaction";
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

const exercise: ExerciseContent = {
  id: "ex-1",
  lesson_id: null,
  skill_id: "skill-1",
  skill_slug: "sql-fundamentals",
  dataset_id: null,
  dataset_slug: null,
  slug: "sample-exercise",
  title: "Sample Exercise",
  description: "A sample multiple-choice exercise.",
  exercise_type: "MULTIPLE_CHOICE",
  difficulty: "BEGINNER",
  points: 10,
  display_order: 0,
  content_reference: null,
  is_active: true,
  tags: [],
  prompt: "Which is correct?",
  choices: ["Wrong answer", "Right answer"],
  hint_count: 1,
  best_attempt: null,
  attempt_count: 0,
  business_context: null,
  stakeholder: null,
  constraints: [],
  expected_deliverables: [],
  rubric: [],
};

describe("ExerciseInteraction", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.get).mockResolvedValue(exercise);
  });

  it("submits the selected choice and renders a PASSED result", async () => {
    const response: SubmitExerciseAttemptResponse = {
      attempt: {
        id: "attempt-1",
        user_id: "user-1",
        exercise_id: "ex-1",
        status: "PASSED",
        score: 100,
        submitted_answer: "Right answer",
        hints_used: 0,
        solution_revealed: false,
        execution_time_ms: null,
        attempted_at: new Date().toISOString(),
      },
      is_auto_graded: true,
      explanation: "Because it's right.",
      correct_answer: "Right answer",
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<ExerciseInteraction slug="sample-exercise" />);

    expect(await screen.findByText("Sample Exercise")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Right answer" }));
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(screen.getByText("Correct!")).toBeInTheDocument());
    expect(screen.getByText("Because it's right.")).toBeInTheDocument();
    expect(apiClient.post).toHaveBeenCalledWith(
      "/exercises/sample-exercise/attempts",
      { submitted_answer: "Right answer" },
    );
  });

  it("disables submit until a choice is selected", async () => {
    renderWithProviders(<ExerciseInteraction slug="sample-exercise" />);

    await screen.findByText("Sample Exercise");

    expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();

    fireEvent.click(screen.getByRole("radio", { name: "Wrong answer" }));

    expect(screen.getByRole("button", { name: "Submit" })).toBeEnabled();
  });

  it("shows an error state when the exercise fails to load", async () => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.get).mockRejectedValue(new Error("network down"));

    renderWithProviders(<ExerciseInteraction slug="sample-exercise" />);

    expect(await screen.findByText("Unable to load this exercise", {}, { timeout: 5000 })).toBeInTheDocument();
  }, 10000);
});
