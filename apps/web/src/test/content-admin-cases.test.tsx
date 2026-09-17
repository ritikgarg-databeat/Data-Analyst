import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { CaseAdminListItem } from "@data-analyst-lab/shared";

import { CaseAdminPanel } from "@/components/features/admin/case-admin-panel";
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

function makeCase(overrides: Partial<CaseAdminListItem>): CaseAdminListItem {
  return {
    id: "case-1",
    slug: "churn-investigation",
    title: "Churn Investigation",
    category: "CUSTOMER_ANALYTICS",
    difficulty: "INTERMEDIATE",
    is_active: true,
    version: 1,
    ...overrides,
  };
}

describe("CaseAdminPanel", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.patch).mockReset();
  });

  it("lists all cases (active and inactive) from the admin endpoint", async () => {
    const cases = [
      makeCase({ id: "case-1", title: "Churn Investigation", is_active: true }),
      makeCase({ id: "case-2", slug: "pricing-experiment", title: "Pricing Experiment", is_active: false }),
    ];
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/cases/admin") return cases;
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<CaseAdminPanel />);

    expect(await screen.findByText("Churn Investigation")).toBeInTheDocument();
    expect(screen.getByText("Pricing Experiment")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.getAllByText("CUSTOMER_ANALYTICS · INTERMEDIATE")).toHaveLength(2);
  });

  it("deactivates an active case via PATCH and reflects the updated badge", async () => {
    // A tiny in-memory "server" so the refetch triggered by invalidateQueries
    // (which may race with the assertion below) always reflects the PATCH,
    // regardless of exactly when it fires.
    let serverCase = makeCase({ id: "case-1", title: "Churn Investigation", is_active: true });
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/cases/admin") return [serverCase];
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.patch).mockImplementation(async (path: string, body?: unknown) => {
      const { is_active } = body as { is_active: boolean };
      if (path === "/cases/admin/case-1") {
        serverCase = { ...serverCase, is_active };
        return serverCase;
      }
      throw new Error(`Unhandled PATCH ${path}`);
    });

    renderWithProviders(<CaseAdminPanel />);
    await screen.findByText("Churn Investigation");
    expect(screen.getByText("Active")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Deactivate" }));

    await waitFor(() =>
      expect(apiClient.patch).toHaveBeenCalledWith("/cases/admin/case-1", { is_active: false }),
    );
    await waitFor(() => expect(screen.getByText("Inactive")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Activate" })).toBeInTheDocument();
  });

  it("shows an error state with retry when the admin list fails to load", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error("network down"));

    renderWithProviders(<CaseAdminPanel />);

    expect(await screen.findByText("Unable to load cases", {}, { timeout: 3000 })).toBeInTheDocument();
  });
});
