import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { ExerciseContent, SqlExerciseContent, SubmitSqlExerciseResponse } from "@data-analyst-lab/shared";

import { SqlExerciseWorkspace } from "@/components/features/exercises/sql-exercise-workspace";
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

// The real SqlEditor mounts Monaco (via next/dynamic, client-only), which
// isn't viable in jsdom. Stub it with a plain textarea that preserves the
// value/onChange/onRun contract the workspace depends on.
vi.mock("@/components/features/sql-lab/sql-editor", () => ({
  SqlEditor: ({
    value,
    onChange,
    onRun,
    isRunning,
  }: {
    value: string;
    onChange: (next: string) => void;
    onRun?: () => void;
    isRunning?: boolean;
  }) => (
    <div>
      <textarea aria-label="SQL exercise query editor" value={value} onChange={(event) => onChange(event.target.value)} />
      {onRun ? (
        <button type="button" onClick={onRun} disabled={isRunning}>
          {isRunning ? "Running..." : "Run"}
        </button>
      ) : null}
    </div>
  ),
}));

const exercise: ExerciseContent = {
  id: "ex-sql-1",
  lesson_id: null,
  skill_id: "skill-1",
  skill_slug: "business-metrics",
  dataset_id: null,
  dataset_slug: "ecommerce",
  slug: "aov-query",
  title: "Calculate Average Order Value",
  description: "Write a SQL query that computes average order value from successful payments.",
  exercise_type: "SQL",
  difficulty: "BEGINNER",
  points: 15,
  display_order: 0,
  content_reference: "business-analytics/aov-query.yaml",
  is_active: true,
  tags: [],
  prompt:
    "Using the `payments` table, write a SQL query that returns the average order value (AOV) across successful payments only.",
  choices: null,
  hint_count: 2,
  best_attempt: null,
  attempt_count: 0,
  business_context: null,
  stakeholder: null,
  constraints: [],
  expected_deliverables: [],
  rubric: [],
};

const sqlContent: SqlExerciseContent = {
  business_context: "Finance wants a single AOV number across every order that was actually paid for.",
  dataset: "ecommerce",
  tables: [{ table_name: "payments", grain: "one row per payment", row_count: 1200, column_count: 6 }],
  starter_query: "-- Explore the payments table first\nSELECT * FROM payments LIMIT 20;",
  hint_count: 2,
};

describe("SqlExerciseWorkspace", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.get).mockResolvedValue(sqlContent);
  });

  it("renders business context, table summary, and pre-fills the editor with the starter query", async () => {
    renderWithProviders(<SqlExerciseWorkspace slug="aov-query" exercise={exercise} />);

    expect(await screen.findByText("Calculate Average Order Value")).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/sql/exercises/aov-query");

    expect(await screen.findByText(sqlContent.business_context as string)).toBeInTheDocument();
    expect(screen.getByText("payments")).toBeInTheDocument();
    expect(screen.getByText("1,200")).toBeInTheDocument();

    const editor = screen.getByLabelText("SQL exercise query editor") as HTMLTextAreaElement;
    await waitFor(() => expect(editor.value).toBe(sqlContent.starter_query));
  });

  it("submits the edited query and renders a PASSED result with score and test outcomes", async () => {
    const response: SubmitSqlExerciseResponse = {
      attempt_id: "attempt-1",
      status: "PASSED",
      score: 100,
      passed: true,
      test_outcomes: [
        { name: "Correct results", passed: true, is_hidden: false, message: "Matches the expected output." },
        { name: "Uses a filter", passed: true, is_hidden: true, message: "Hidden check passed." },
      ],
      result: {
        status: "success",
        engine: "duckdb",
        columns: [{ name: "aov", type: "DOUBLE" }],
        rows: [[42.5]],
        row_count: 1,
        truncated: false,
        execution_time_ms: 12,
        error: null,
        metadata: {},
      },
      explanation: "AVG(amount) filtered to successful payments is the AOV.",
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<SqlExerciseWorkspace slug="aov-query" exercise={exercise} />);

    const editor = (await screen.findByLabelText("SQL exercise query editor")) as HTMLTextAreaElement;
    await waitFor(() => expect(editor.value).toBe(sqlContent.starter_query));

    const query = "SELECT ROUND(AVG(amount), 2) AS aov FROM payments WHERE status = 'success'";
    fireEvent.change(editor, { target: { value: query } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(screen.getByText("Passed!")).toBeInTheDocument());
    expect(screen.getByText("Score: 100%")).toBeInTheDocument();
    expect(screen.getByText("Correct results")).toBeInTheDocument();
    expect(screen.getByText("Uses a filter")).toBeInTheDocument();
    expect(screen.getByText("hidden")).toBeInTheDocument();
    expect(screen.getByText("AVG(amount) filtered to successful payments is the AOV.")).toBeInTheDocument();

    expect(apiClient.post).toHaveBeenCalledWith("/sql/exercises/aov-query/submit", { submitted_query: query });
  });

  it("renders a FAILED result without an explanation when the submission is wrong", async () => {
    const response: SubmitSqlExerciseResponse = {
      attempt_id: "attempt-2",
      status: "FAILED",
      score: 0,
      passed: false,
      test_outcomes: [
        { name: "Correct results", passed: false, is_hidden: false, message: "Output didn't match the expected result." },
      ],
      result: {
        status: "success",
        engine: "duckdb",
        columns: [{ name: "aov", type: "DOUBLE" }],
        rows: [[47.1]],
        row_count: 1,
        truncated: false,
        execution_time_ms: 9,
        error: null,
        metadata: {},
      },
      explanation: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<SqlExerciseWorkspace slug="aov-query" exercise={exercise} />);

    await screen.findByLabelText("SQL exercise query editor");
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(screen.getByText("Not quite.")).toBeInTheDocument());
    expect(screen.getByText("Output didn't match the expected result.")).toBeInTheDocument();
    expect(screen.queryByText("AVG(amount) filtered to successful payments is the AOV.")).not.toBeInTheDocument();
  });

  it("reveals hints via the generic exercise hint endpoint", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ hint: "Filter to status = 'success' first." });

    renderWithProviders(<SqlExerciseWorkspace slug="aov-query" exercise={exercise} />);

    await screen.findByLabelText("SQL exercise query editor");
    fireEvent.click(screen.getByRole("button", { name: "Show hint" }));

    await waitFor(() => expect(screen.getByText(/Filter to status = 'success' first\./)).toBeInTheDocument());
    expect(apiClient.post).toHaveBeenCalledWith("/exercises/aov-query/hint");
  });
});
