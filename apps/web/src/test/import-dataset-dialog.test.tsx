import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { Dataset } from "@data-analyst-lab/shared";

import { ImportDatasetDialog } from "@/components/features/datasets/import-dataset-dialog";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
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

const CREATED_DATASET: Dataset = {
  id: "ds-1",
  name: "Orders",
  slug: "orders",
  description: null,
  source: "local upload",
  source_url: null,
  domain: null,
  file_path: null,
  file_format: null,
  row_count: null,
  column_count: null,
  difficulty: "BEGINNER",
  metadata: null,
  created_at: NOW,
  updated_at: NOW,
  source_type: "LOCAL",
  business_domain: null,
  license: null,
  size_bytes: null,
  status: "IMPORTING",
  status_message: null,
  fingerprint: null,
  version: 1,
  imported_at: null,
  last_profiled_at: null,
  kaggle_ref: null,
  tags: [],
  tables: [],
  sql_ready: false,
  python_ready: false,
};

function makeFile(name: string): File {
  return new File(["a,b\n1,2\n"], name, { type: "text/csv" });
}

describe("ImportDatasetDialog", () => {
  it("opens, accepts a file, fills the name from the filename, and submits via postForm", async () => {
    vi.mocked(apiClient.postForm).mockResolvedValue(CREATED_DATASET);

    renderWithProviders(<ImportDatasetDialog />);
    fireEvent.click(screen.getByRole("button", { name: "Import Dataset" }));

    const fileInput = screen.getByLabelText("Choose files to import") as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [makeFile("customer orders.csv")] } });

    // The dataset name auto-fills from the first file's name.
    expect(await screen.findByDisplayValue("customer orders")).toBeInTheDocument();

    const submitButtons = screen.getAllByRole("button", { name: "Import Dataset" });
    fireEvent.click(submitButtons[submitButtons.length - 1]);

    await waitFor(() =>
      expect(apiClient.postForm).toHaveBeenCalledWith(
        "/datasets/import",
        expect.arrayContaining([expect.objectContaining({ name: "customer orders.csv" })]),
        expect.objectContaining({ name: "customer orders" }),
      ),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/datasets/orders"));
  });

  it("disables the submit button until a file and a name are present", () => {
    renderWithProviders(<ImportDatasetDialog />);
    fireEvent.click(screen.getByRole("button", { name: "Import Dataset" }));

    const submitButtons = screen.getAllByRole("button", { name: "Import Dataset" });
    const submit = submitButtons[submitButtons.length - 1];
    expect(submit).toBeDisabled();
  });
});
