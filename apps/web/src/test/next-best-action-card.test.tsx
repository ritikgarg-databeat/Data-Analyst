import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import type { NextBestActionResponse } from "@data-analyst-lab/shared";

import { NextBestActionCard } from "@/components/features/dashboard/next-best-action-card";
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

describe("NextBestActionCard", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it("renders each returned action with its source badge and a link to url_path", async () => {
    const response: NextBestActionResponse = {
      actions: [
        { title: "Finish your resume", why: "You haven't added a resume yet.", source: "portfolio", url_path: "/career/resume" },
        { title: "Practice interview questions", why: "Your readiness score dipped.", source: "interview", url_path: "/interview" },
      ],
    };
    vi.mocked(apiClient.get).mockResolvedValue(response);

    renderWithProviders(<NextBestActionCard />);

    expect(await screen.findByText("Finish your resume")).toBeInTheDocument();
    expect(screen.getByText("Practice interview questions")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Finish your resume/ })).toHaveAttribute("href", "/career/resume");
    expect(vi.mocked(apiClient.get)).toHaveBeenCalledWith("/platform/next-best-actions?limit=3");
  });

  it("shows an empty state when there are no actions", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ actions: [] });

    renderWithProviders(<NextBestActionCard />);

    expect(await screen.findByText("Nothing queued yet")).toBeInTheDocument();
  });
});
