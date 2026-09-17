import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { Case, CaseAttempt, CaseListItem } from "@data-analyst-lab/shared";

import { CaseLibrary } from "@/components/features/case-studies/case-library";
import { CaseSubmitTab } from "@/components/features/case-studies/case-submit-tab";
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

function makeCase(overrides: Partial<Case> = {}): Case {
  return {
    id: "case-1",
    slug: "revenue-drop-investigation",
    title: "Revenue Drop Investigation",
    category: "BUSINESS_ANALYTICS",
    difficulty: "INTERMEDIATE",
    estimated_minutes: 90,
    company_context: null,
    stakeholder_name: "Priya Shah",
    stakeholder_role: "VP of Sales",
    problem_statement: "Our revenue dropped last quarter and I don't know why.",
    business_context: null,
    objective: "Figure out why revenue dropped.",
    initial_information: null,
    constraints: [],
    available_datasets: ["orders-sample"],
    expected_deliverables: [],
    learning_objectives: ["Diagnose a revenue decline"],
    stages: ["CLARIFY", "FRAME", "ANALYZE", "RECOMMEND", "SUBMIT"],
    tags: [],
    skills: [],
    rubric: [
      {
        category: "Problem Framing",
        weight: 100,
        is_technical: false,
        criteria: [{ criterion: "Identifies the revenue driver", points: 100 }],
      },
    ],
    hint_count: 1,
    version: 1,
    ...overrides,
  };
}

function makeListItem(overrides: Partial<CaseListItem> = {}): CaseListItem {
  return {
    case: makeCase(),
    attempt_id: null,
    attempt_status: null,
    attempt_score: null,
    ...overrides,
  };
}

function makeAttempt(overrides: Partial<CaseAttempt> = {}): CaseAttempt {
  return {
    id: "attempt-1",
    case_id: "case-1",
    case_version_snapshot: 1,
    attempt_number: 1,
    status: "IN_PROGRESS",
    current_stage: "CLARIFY",
    clarification_questions: null,
    problem_framing: null,
    selected_dataset_slugs: [],
    recommendation: null,
    executive_summary: null,
    reflection: null,
    hints_used: 0,
    solution_revealed: false,
    rubric_selections: {},
    score: null,
    feedback: null,
    time_per_stage_seconds: {},
    started_at: "2026-01-01T00:00:00Z",
    submitted_at: null,
    completed_at: null,
    last_activity_at: "2026-01-01T00:00:00Z",
    submission_readiness: {
      problem_framed: false,
      data_understood: false,
      findings_documented: false,
      recommendation_written: false,
      executive_summary_written: false,
    },
    ...overrides,
  };
}

describe("CaseLibrary", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    pushMock.mockReset();
  });

  it("lists cases and re-queries the API when a category filter is applied", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/cases") return [makeListItem()];
      if (path.startsWith("/cases?category=PRODUCT_ANALYTICS")) return [];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<CaseLibrary />);
    expect(await screen.findByText("Revenue Drop Investigation")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Filter by category"), { target: { value: "PRODUCT_ANALYTICS" } });

    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith(expect.stringContaining("category=PRODUCT_ANALYTICS")),
    );
    await waitFor(() => expect(screen.queryByText("Revenue Drop Investigation")).not.toBeInTheDocument());
  });

  it("starts a case and navigates to its workspace", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/cases") return [makeListItem()];
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeAttempt());

    renderWithProviders(<CaseLibrary />);
    expect(await screen.findByText("Revenue Drop Investigation")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start Case" }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/cases/revenue-drop-investigation/start"));
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/case-studies/attempts/attempt-1"));
  });
});

describe("CaseSubmitTab", () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset();
  });

  it("builds rubric_selections from checked criteria and submits", async () => {
    const caseData = makeCase();
    const attempt = makeAttempt();
    vi.mocked(apiClient.post).mockResolvedValue({
      ...attempt,
      status: "COMPLETED",
      score: {
        overall: 100,
        categories: [
          { category: "Problem Framing", weight: 100, earned_points: 100, total_points: 100, pct: 100, is_technical: false },
        ],
      },
      feedback: {
        what_went_well: ["Problem Framing (100%)"],
        what_missed: [],
        technical_issues: [],
        business_reasoning_issues: [],
        communication_issues: [],
      },
    });

    renderWithProviders(<CaseSubmitTab caseData={caseData} attempt={attempt} />);

    fireEvent.click(screen.getByRole("checkbox", { name: /Identifies the revenue driver/ }));
    fireEvent.click(screen.getByRole("button", { name: "Submit case" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/cases/attempts/attempt-1/submit", {
        rubric_selections: { "Problem Framing": ["Identifies the revenue driver"] },
      }),
    );
  });

  it("shows the computed score and feedback once the attempt is completed", () => {
    const caseData = makeCase();
    const attempt = makeAttempt({
      status: "COMPLETED",
      score: {
        overall: 100,
        categories: [
          { category: "Problem Framing", weight: 100, earned_points: 100, total_points: 100, pct: 100, is_technical: false },
        ],
      },
      feedback: {
        what_went_well: ["Problem Framing (100%)"],
        what_missed: [],
        technical_issues: [],
        business_reasoning_issues: [],
        communication_issues: [],
      },
    });

    renderWithProviders(<CaseSubmitTab caseData={caseData} attempt={attempt} />);

    expect(screen.getByText("Score: 100.0%")).toBeInTheDocument();
    expect(screen.getByText("Problem Framing (100%)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reveal reference solution" })).toBeInTheDocument();
  });
});
