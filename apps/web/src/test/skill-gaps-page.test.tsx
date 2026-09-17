import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen } from "@testing-library/react";
import type { CareerSkillMatrixEntry } from "@data-analyst-lab/shared";

import { SkillGapsPage } from "@/components/features/career/skill-gaps-page";
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

function makeEntry(overrides: Partial<CareerSkillMatrixEntry> = {}): CareerSkillMatrixEntry {
  return {
    skill_slug: "sql-fundamentals",
    name: "SQL Fundamentals",
    category: "SQL",
    mastery_score: 40,
    evidence_level: "PRACTICED",
    exercises_passed: 3,
    assessment_pct: 60,
    projects_count: 0,
    cases_count: 0,
    mock_interview_score: null,
    is_gap_for_primary_role: true,
    ...overrides,
  };
}

describe("SkillGapsPage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it("renders the skill matrix and flags gaps for the primary role", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/skill-matrix") {
        return [
          makeEntry(),
          makeEntry({ skill_slug: "python-pandas", name: "Python (pandas)", category: "PYTHON", is_gap_for_primary_role: false }),
        ];
      }
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<SkillGapsPage />);

    expect(await screen.findByText("SQL Fundamentals")).toBeInTheDocument();
    expect(screen.getByText("Python (pandas)")).toBeInTheDocument();
    expect(screen.getByText("Gap")).toBeInTheDocument();
    expect(screen.getByText(/1 skill.*flagged as a gap/)).toBeInTheDocument();
  });

  it("filters the matrix by search text", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/career/skill-matrix") {
        return [
          makeEntry(),
          makeEntry({ skill_slug: "python-pandas", name: "Python (pandas)", category: "PYTHON", is_gap_for_primary_role: false }),
        ];
      }
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<SkillGapsPage />);
    expect(await screen.findByText("SQL Fundamentals")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search skills"), { target: { value: "python" } });

    expect(screen.queryByText("SQL Fundamentals")).not.toBeInTheDocument();
    expect(screen.getByText("Python (pandas)")).toBeInTheDocument();
  });
});
