import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { JobDescription } from "@data-analyst-lab/shared";

import { JobDescriptionsPage } from "@/components/features/career/job-descriptions-page";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    postForm: vi.fn(),
    postFile: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

function makeJobDescription(overrides: Partial<JobDescription> = {}): JobDescription {
  return {
    id: "jd-1",
    target_role_id: null,
    company: "Acme Analytics",
    title: "Data Analyst II",
    source: "PASTED",
    raw_text: "We are looking for a data analyst with strong SQL skills...",
    location: "Remote",
    notes: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    requirements: [],
    ...overrides,
  };
}

describe("JobDescriptionsPage", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
  });

  it("lists saved job descriptions with a link to their detail page", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/jobs/descriptions") return [makeJobDescription()];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<JobDescriptionsPage />);

    const link = await screen.findByRole("link", { name: "Data Analyst II" });
    expect(link).toHaveAttribute("href", "/career/job-descriptions/jd-1");
    expect(screen.getByText(/Acme Analytics/)).toBeInTheDocument();
  });

  it("saves a newly pasted job description", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/jobs/descriptions") return [];
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeJobDescription());

    renderWithProviders(<JobDescriptionsPage />);
    await screen.findByLabelText("Job title");

    fireEvent.change(screen.getByLabelText("Job title"), { target: { value: "Data Analyst II" } });
    fireEvent.change(screen.getByLabelText("Job description text"), {
      target: { value: "We are looking for a data analyst with strong SQL skills..." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Job Description" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/jobs/descriptions",
        expect.objectContaining({ title: "Data Analyst II", source: "PASTED" }),
      ),
    );
  });
});
