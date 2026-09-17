import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { Dataset } from "@data-analyst-lab/shared";

import { DatasetHub } from "@/components/features/datasets/dataset-hub";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

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

const NOW = "2026-01-01T00:00:00Z";

function makeDataset(overrides: Partial<Dataset>): Dataset {
  return {
    id: "ds-1",
    name: "E-commerce Orders",
    slug: "ecommerce-orders",
    description: "Orders, customers, and payments.",
    source: "local upload",
    source_url: null,
    domain: null,
    file_path: null,
    file_format: null,
    row_count: 125_420,
    column_count: 14,
    difficulty: "INTERMEDIATE",
    metadata: null,
    created_at: NOW,
    updated_at: NOW,
    source_type: "LOCAL",
    business_domain: "E-commerce",
    license: null,
    size_bytes: 24_000_000,
    status: "READY",
    status_message: null,
    fingerprint: "abc123",
    version: 1,
    imported_at: NOW,
    last_profiled_at: NOW,
    kaggle_ref: null,
    tags: ["e-commerce", "intermediate"],
    tables: [
      {
        id: "t-1",
        table_name: "orders",
        file_format: "parquet",
        row_count: 125_420,
        column_count: 14,
        size_bytes: 24_000_000,
        grain: "1 row = 1 order",
        display_order: 0,
      },
    ],
    sql_ready: true,
    python_ready: true,
    ...overrides,
  };
}

describe("DatasetHub", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it("lists datasets returned by the catalog endpoint", async () => {
    const datasets = [
      makeDataset({ id: "ds-1", name: "E-commerce Orders", business_domain: "E-commerce" }),
      makeDataset({ id: "ds-2", name: "Marketing Campaigns", slug: "marketing-campaigns", business_domain: "Marketing" }),
    ];
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.startsWith("/datasets")) return datasets;
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<DatasetHub />);

    expect(await screen.findByText("E-commerce Orders")).toBeInTheDocument();
    expect(screen.getByText("Marketing Campaigns")).toBeInTheDocument();
    expect(screen.getAllByText(/SQL Ready/)).toHaveLength(2);
  });

  it("filters the catalog by business-domain chip", async () => {
    const datasets = [
      makeDataset({ id: "ds-1", name: "E-commerce Orders", business_domain: "E-commerce" }),
      makeDataset({ id: "ds-2", name: "Marketing Campaigns", slug: "marketing-campaigns", business_domain: "Marketing" }),
    ];
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.startsWith("/datasets")) return datasets;
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<DatasetHub />);
    await screen.findByText("E-commerce Orders");

    fireEvent.click(screen.getByRole("tab", { name: "Marketing" }));

    await waitFor(() => expect(screen.queryByText("E-commerce Orders")).not.toBeInTheDocument());
    expect(screen.getByText("Marketing Campaigns")).toBeInTheDocument();
  });

  it("shows an empty state when the catalog has no datasets", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.startsWith("/datasets")) return [];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<DatasetHub />);

    expect(await screen.findByText("No datasets yet")).toBeInTheDocument();
  });

  it("shows an error state with retry when the catalog fails to load", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error("network down"));

    renderWithProviders(<DatasetHub />);

    // useDatasets retries once (retry: 1) before settling into isError, so this
    // needs more than testing-library's default 1000ms findBy timeout.
    expect(await screen.findByText("Unable to load datasets", {}, { timeout: 3000 })).toBeInTheDocument();
  });

  it("shows a status badge for a dataset still being profiled", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.startsWith("/datasets")) return [makeDataset({ status: "PROFILING", sql_ready: false, python_ready: false })];
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<DatasetHub />);

    expect(await screen.findByText("Profiling")).toBeInTheDocument();
  });
});
