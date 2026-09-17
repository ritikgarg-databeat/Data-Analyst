import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { Project, ProjectTemplate } from "@data-analyst-lab/shared";

import { ProjectMilestonesTab } from "@/components/features/projects/project-milestones-tab";
import { ProjectSubmissionTab } from "@/components/features/projects/project-submission-tab";
import { ProjectTemplateGrid } from "@/components/features/projects/project-template-grid";
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

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function makeTemplate(overrides: Partial<ProjectTemplate> = {}): ProjectTemplate {
  return {
    id: "template-1",
    slug: "ecommerce-analytics-platform",
    title: "E-commerce Analytics Platform",
    category: "BUSINESS_ANALYTICS",
    business_context: "A growing online retailer wants a full analytics buildout.",
    objective: "Build a data model, analysis, and dashboard.",
    requirements: [],
    suggested_datasets: ["ecommerce"],
    milestones: [
      { title: "Understand the Business", description: "Talk to stakeholders" },
      { title: "Data Discovery", description: "Find relevant datasets" },
    ],
    required_skills: [],
    rubric: [
      {
        category: "Business Understanding",
        weight: 40,
        is_technical: false,
        criteria: [{ criterion: "Correctly frames the business problem", points: 100 }],
      },
      {
        category: "Technical Execution",
        weight: 60,
        is_technical: true,
        criteria: [{ criterion: "Data model is correctly built", points: 100 }],
      },
    ],
    learning_objectives: [],
    estimated_hours: 6,
    tags: ["e-commerce", "sql"],
    version: 1,
    ...overrides,
  };
}

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "project-1",
    dataset_id: null,
    template_id: "template-1",
    data_model_id: null,
    name: "E-commerce Analytics Platform",
    description: null,
    notes: null,
    status: "IN_PROGRESS",
    objective: "Build a data model, analysis, and dashboard.",
    business_context: null,
    requirements: [],
    dbt_model_refs: [],
    documentation: {},
    presentation: [],
    rubric_selections: {},
    score: null,
    reflection: null,
    started_at: "2026-01-01T00:00:00Z",
    submitted_at: null,
    completed_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    milestones: [
      { id: "m1", title: "Understand the Business", description: null, display_order: 0, is_completed: false, completed_at: null },
      { id: "m2", title: "Data Discovery", description: null, display_order: 1, is_completed: false, completed_at: null },
    ],
    artifacts: [],
    project_datasets: [],
    ...overrides,
  };
}

describe("ProjectTemplateGrid", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
  });

  it("starts a project from a template via POST /projects/from-template", async () => {
    const template = makeTemplate();
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/projects/templates") return [template];
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeProject());

    renderWithProviders(<ProjectTemplateGrid />);

    expect(await screen.findByText("E-commerce Analytics Platform")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start Project" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/projects/from-template", { template_slug: "ecommerce-analytics-platform" }),
    );
  });
});

describe("ProjectMilestonesTab", () => {
  beforeEach(() => {
    vi.mocked(apiClient.patch).mockReset();
  });

  it("shows seeded milestones with a progress bar and toggles completion via PATCH", async () => {
    const project = makeProject();
    vi.mocked(apiClient.patch).mockResolvedValue({
      ...project,
      milestones: project.milestones.map((m) => (m.id === "m1" ? { ...m, is_completed: true } : m)),
    });

    renderWithProviders(<ProjectMilestonesTab project={project} />);

    expect(screen.getByText("Understand the Business")).toBeInTheDocument();
    expect(screen.getByText("Data Discovery")).toBeInTheDocument();
    expect(screen.getByText("0 / 2 completed")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);

    await waitFor(() =>
      expect(apiClient.patch).toHaveBeenCalledWith("/projects/project-1/milestones/m1", { is_completed: true }),
    );
  });
});

describe("ProjectSubmissionTab", () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset();
  });

  it("builds rubric_selections from checked criteria and submits", async () => {
    const project = makeProject();
    const template = makeTemplate();
    vi.mocked(apiClient.post).mockResolvedValue({
      ...project,
      status: "COMPLETED",
      score: {
        overall: 100,
        categories: [
          { category: "Business Understanding", weight: 40, earned_points: 100, total_points: 100, pct: 100, is_technical: false },
          { category: "Technical Execution", weight: 60, earned_points: 100, total_points: 100, pct: 100, is_technical: true },
        ],
        feedback: {
          what_went_well: ["Business Understanding (100%)", "Technical Execution (100%)"],
          what_missed: [],
          technical_issues: [],
          business_reasoning_issues: [],
          communication_issues: [],
        },
      },
    });

    renderWithProviders(<ProjectSubmissionTab project={project} template={template} />);

    fireEvent.click(screen.getByRole("checkbox", { name: /Correctly frames the business problem/ }));
    fireEvent.click(screen.getByRole("button", { name: "Submit project" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/projects/project-1/submit", {
        rubric_selections: { "Business Understanding": ["Correctly frames the business problem"] },
      }),
    );
  });

  it("shows a message instead of a rubric for free-form (non-template) projects", () => {
    const project = makeProject({ template_id: null });
    renderWithProviders(<ProjectSubmissionTab project={project} template={undefined} />);
    expect(screen.getByText(/free-form project/)).toBeInTheDocument();
  });

  it("shows the computed score and feedback once the project is completed", () => {
    const project = makeProject({
      status: "COMPLETED",
      score: {
        overall: 70,
        categories: [
          { category: "Business Understanding", weight: 40, earned_points: 100, total_points: 100, pct: 100, is_technical: false },
          { category: "Technical Execution", weight: 60, earned_points: 50, total_points: 100, pct: 50, is_technical: true },
        ],
        feedback: {
          what_went_well: ["Business Understanding (100%)"],
          what_missed: ["Technical Execution (50%)"],
          technical_issues: ["Technical Execution"],
          business_reasoning_issues: [],
          communication_issues: [],
        },
      },
    });
    renderWithProviders(<ProjectSubmissionTab project={project} template={makeTemplate()} />);

    expect(screen.getByText("Score: 70.0%")).toBeInTheDocument();
    expect(screen.getByText("Business Understanding (100%)")).toBeInTheDocument();
    expect(screen.getByText("Technical Execution (50%)")).toBeInTheDocument();
  });
});
