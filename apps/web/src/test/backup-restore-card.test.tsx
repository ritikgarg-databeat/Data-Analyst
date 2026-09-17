import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { BackupBundle, RestorePreviewResponse, RestoreResponse } from "@data-analyst-lab/shared";

import { BackupRestoreCard } from "@/app/settings/backup-restore-card";
import { ToastProvider } from "@/components/shared/toast-provider";
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

function renderCard() {
  return renderWithProviders(
    <ToastProvider>
      <BackupRestoreCard />
    </ToastProvider>,
  );
}

const sampleBundle: BackupBundle = {
  manifest: {
    created_at: "2026-01-01T00:00:00Z",
    app_version: "0.1.0",
    schema_version: "abc123",
    user_email: "user@example.com",
    counts: { lessons_progress: 4 },
  },
  data: { lessons_progress: [] },
};

describe("BackupRestoreCard", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    // jsdom doesn't implement the Blob-download primitives this reuses from
    // career-analytics-page.tsx's downloadText helper.
    URL.createObjectURL = vi.fn(() => "blob:mock-url");
    URL.revokeObjectURL = vi.fn();
  });

  it("downloads a backup via GET /platform/backup and shows a success toast", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(sampleBundle);

    renderCard();
    fireEvent.click(screen.getByRole("button", { name: /Download Backup/ }));

    await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith("/platform/backup"));
    expect(await screen.findByText("Backup saved")).toBeInTheDocument();
  });

  it("shows an error toast when the backup request fails", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error("offline"));

    renderCard();
    fireEvent.click(screen.getByRole("button", { name: /Download Backup/ }));

    expect(await screen.findByText("Backup failed")).toBeInTheDocument();
  });

  it("previews then restores a backup only after explicit confirmation, always sending confirm: true", async () => {
    const preview: RestorePreviewResponse = { manifest: sampleBundle.manifest, compatible: true, issues: [] };
    const restoreResult: RestoreResponse = { restored: { lessons_progress: 4 } };
    vi.mocked(apiClient.post).mockImplementation(async (path: string) => {
      if (path === "/platform/restore/preview") return preview;
      if (path === "/platform/restore") return restoreResult;
      throw new Error(`Unhandled POST ${path}`);
    });

    renderCard();

    const file = new File([JSON.stringify(sampleBundle)], "backup.json", { type: "application/json" });
    const fileInput = screen.getByLabelText("Choose a backup file");
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith("/platform/restore/preview", sampleBundle));
    expect(await screen.findByText("Compatible")).toBeInTheDocument();

    // The restore button stays disabled until the confirming checkbox is ticked —
    // restore must never be triggered with an implicit/default confirmation.
    const restoreButton = screen.getByRole("button", { name: "Yes, Restore" });
    expect(restoreButton).toBeDisabled();
    expect(apiClient.post).not.toHaveBeenCalledWith("/platform/restore", expect.anything());

    fireEvent.click(screen.getByRole("checkbox"));
    expect(restoreButton).toBeEnabled();

    fireEvent.click(restoreButton);

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith("/platform/restore", { bundle: sampleBundle, confirm: true }),
    );
    expect(await screen.findByText("Restore complete")).toBeInTheDocument();
  });

  it("surfaces compatibility issues from the preview response", async () => {
    const preview: RestorePreviewResponse = {
      manifest: sampleBundle.manifest,
      compatible: false,
      issues: ["Schema version mismatch — some tables may not restore cleanly."],
    };
    vi.mocked(apiClient.post).mockImplementation(async (path: string) => {
      if (path === "/platform/restore/preview") return preview;
      throw new Error(`Unhandled POST ${path}`);
    });

    renderCard();
    const file = new File([JSON.stringify(sampleBundle)], "backup.json", { type: "application/json" });
    fireEvent.change(screen.getByLabelText("Choose a backup file"), { target: { files: [file] } });

    expect(await screen.findByText("Incompatible")).toBeInTheDocument();
    expect(screen.getByText(/Schema version mismatch/)).toBeInTheDocument();
  });
});
