import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type {
  ExerciseContent,
  PythonExecutionResultSchema,
  PythonExerciseContent,
  PythonRuntimeSchema,
  SubmitPythonExerciseResponse,
} from "@data-analyst-lab/shared";

import { PythonExerciseWorkspace } from "@/components/features/exercises/python-exercise-workspace";
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

// The real PythonCellEditor mounts Monaco (via next/dynamic, client-only), which isn't viable in
// jsdom. Stub it with a plain textarea that preserves the value/onChange/onRun contract the
// workspace depends on — mirrors sql-exercise-workspace.test.tsx's SqlEditor mock.
vi.mock("@/components/features/python-lab/python-cell-editor", () => ({
  PythonCellEditor: ({
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
      <textarea
        aria-label="Python exercise code editor"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      {onRun ? (
        <button type="button" onClick={onRun} disabled={isRunning}>
          {isRunning ? "Running..." : "Run"}
        </button>
      ) : null}
    </div>
  ),
}));

const exercise: ExerciseContent = {
  id: "ex-py-1",
  lesson_id: null,
  skill_id: "skill-2",
  skill_slug: "pandas-fundamentals",
  dataset_id: null,
  dataset_slug: "ecommerce",
  slug: "quarterly-revenue-by-segment",
  title: "Quarterly Revenue by Segment",
  description: "Write pandas code that computes quarterly revenue broken out by customer segment.",
  exercise_type: "PYTHON",
  difficulty: "INTERMEDIATE",
  points: 20,
  display_order: 0,
  content_reference: "business-analytics/quarterly-revenue-by-segment.yaml",
  is_active: true,
  tags: [],
  prompt:
    "Using `orders`, compute total revenue per quarter per customer segment and assign the result to `result`.",
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

const pythonContent: PythonExerciseContent = {
  business_context: "Finance wants quarterly revenue broken out by customer segment for the board deck.",
  dataset: "ecommerce",
  dataset_files: [
    {
      dataset_slug: "ecommerce",
      dataset_name: "Ecommerce",
      label: "orders.csv",
      container_path: "/data/ecommerce/orders.csv",
      file_format: "csv",
      grain: "one row per order",
      row_count: 1200,
      column_count: 8,
      suggested_code: 'orders = pd.read_csv("/data/ecommerce/orders.csv")',
    },
  ],
  starter_code: "# Explore the orders table first\nresult = orders.head()",
  result_variable: "result",
  hint_count: 2,
};

describe("PythonExerciseWorkspace", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.get).mockResolvedValue(pythonContent);
  });

  it("renders business context, dataset files, and pre-fills the editor with the starter code", async () => {
    renderWithProviders(<PythonExerciseWorkspace slug="quarterly-revenue-by-segment" exercise={exercise} />);

    expect(await screen.findByText("Quarterly Revenue by Segment")).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/python/exercises/quarterly-revenue-by-segment");

    expect(await screen.findByText(pythonContent.business_context as string)).toBeInTheDocument();
    expect(screen.getByText("orders.csv")).toBeInTheDocument();
    expect(screen.getByText("1,200")).toBeInTheDocument();

    const editor = screen.getByLabelText("Python exercise code editor") as HTMLTextAreaElement;
    await waitFor(() => expect(editor.value).toBe(pythonContent.starter_code));
  });

  it("submits the edited code and renders a PASSED result with score and test outcomes", async () => {
    const response: SubmitPythonExerciseResponse = {
      attempt_id: "attempt-1",
      status: "PASSED",
      score: 100,
      passed: true,
      test_outcomes: [
        { name: "Correct results", passed: true, is_hidden: false, message: "Matches the expected output." },
        { name: "Uses groupby", passed: true, is_hidden: true, message: "Hidden check passed." },
      ],
      result: {
        status: "success",
        stdout: "",
        stdout_truncated: false,
        display_value: null,
        variables: [],
        charts: [],
        error: null,
        execution_time_ms: 45,
      },
      explanation: "Group by quarter and segment, then sum revenue.",
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<PythonExerciseWorkspace slug="quarterly-revenue-by-segment" exercise={exercise} />);

    const editor = (await screen.findByLabelText("Python exercise code editor")) as HTMLTextAreaElement;
    await waitFor(() => expect(editor.value).toBe(pythonContent.starter_code));

    const code = "result = orders.groupby(['quarter', 'segment'])['revenue'].sum().reset_index()";
    fireEvent.change(editor, { target: { value: code } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(screen.getByText("Passed!")).toBeInTheDocument());
    expect(screen.getByText("Score: 100%")).toBeInTheDocument();
    expect(screen.getByText("Correct results")).toBeInTheDocument();
    expect(screen.getByText("Uses groupby")).toBeInTheDocument();
    expect(screen.getByText("hidden")).toBeInTheDocument();
    expect(screen.getByText("Group by quarter and segment, then sum revenue.")).toBeInTheDocument();

    expect(apiClient.post).toHaveBeenCalledWith("/python/exercises/quarterly-revenue-by-segment/submit", {
      submitted_code: code,
    });
  });

  it("renders a FAILED result without an explanation when the submission is wrong", async () => {
    const response: SubmitPythonExerciseResponse = {
      attempt_id: "attempt-2",
      status: "FAILED",
      score: 0,
      passed: false,
      test_outcomes: [
        {
          name: "Correct results",
          passed: false,
          is_hidden: false,
          message: "`result` didn't match the expected DataFrame.",
        },
      ],
      result: {
        status: "success",
        stdout: "",
        stdout_truncated: false,
        display_value: null,
        variables: [],
        charts: [],
        error: null,
        execution_time_ms: 30,
      },
      explanation: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(response);

    renderWithProviders(<PythonExerciseWorkspace slug="quarterly-revenue-by-segment" exercise={exercise} />);

    await screen.findByLabelText("Python exercise code editor");
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(screen.getByText("Not quite.")).toBeInTheDocument());
    expect(screen.getByText("`result` didn't match the expected DataFrame.")).toBeInTheDocument();
    expect(screen.queryByText("Group by quarter and segment, then sum revenue.")).not.toBeInTheDocument();
  });

  it("reveals hints via the generic exercise hint endpoint", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ hint: "Use groupby on quarter and segment." });

    renderWithProviders(<PythonExerciseWorkspace slug="quarterly-revenue-by-segment" exercise={exercise} />);

    await screen.findByLabelText("Python exercise code editor");
    fireEvent.click(screen.getByRole("button", { name: "Show hint" }));

    await waitFor(() => expect(screen.getByText(/Use groupby on quarter and segment\./)).toBeInTheDocument());
    expect(apiClient.post).toHaveBeenCalledWith("/exercises/quarterly-revenue-by-segment/hint");
  });

  it("running the code creates a runtime, loads the dataset, executes the code, and shows its output", async () => {
    const runtime: PythonRuntimeSchema = {
      id: "rt-1",
      status: "READY",
      workspace_id: null,
      timeout_seconds: 30,
      error_message: null,
      created_at: "2026-01-01T00:00:00Z",
      last_used_at: "2026-01-01T00:00:00Z",
    };
    const setupResult: PythonExecutionResultSchema = {
      status: "success",
      stdout: "",
      stdout_truncated: false,
      display_value: null,
      variables: [],
      charts: [],
      error: null,
      execution_time_ms: 5,
    };
    const runResult: PythonExecutionResultSchema = {
      status: "success",
      stdout: "quarter segment revenue\n",
      stdout_truncated: false,
      display_value: null,
      variables: [],
      charts: [],
      error: null,
      execution_time_ms: 8,
    };

    vi.mocked(apiClient.post).mockImplementation(async (path: string, body?: unknown) => {
      if (path === "/python/runtimes") return runtime;
      if (path === `/python/runtimes/${runtime.id}/execute`) {
        const requestBody = body as { code: string };
        return requestBody.code.includes("read_csv") ? setupResult : runResult;
      }
      throw new Error(`Unhandled POST ${path}`);
    });

    renderWithProviders(<PythonExerciseWorkspace slug="quarterly-revenue-by-segment" exercise={exercise} />);

    const editor = (await screen.findByLabelText("Python exercise code editor")) as HTMLTextAreaElement;
    await waitFor(() => expect(editor.value).toBe(pythonContent.starter_code));

    fireEvent.click(screen.getByRole("button", { name: /^Run/ }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/python/runtimes"));
    expect(await screen.findByText("quarter segment revenue")).toBeInTheDocument();
  });
});
