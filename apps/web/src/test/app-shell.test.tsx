import { describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import { APP_NAME, NAV_SECTIONS } from "@data-analyst-lab/shared";

import { AppShell } from "@/components/layout/app-shell";

import { renderWithProviders } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockImplementation(async (path: string) => {
      // AIMentorLauncher (mounted globally in AppShell) fetches its
      // settings on every route — a realistic shape avoids the
      // "Query data cannot be undefined" React Query warning this test
      // otherwise triggers, matching how other test files mock every
      // endpoint a rendered component actually calls.
      if (path === "/ai/settings") {
        return {
          id: "settings-1",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
          enabled: true,
          provider_override: null,
          model_override: null,
          response_style: "balanced",
          learning_mode: "socratic",
          privacy_preference: "standard",
          max_context_chars: null,
          daily_request_limit: null,
          effective_provider: "local",
          ai_configured: true,
        };
      }
      return undefined;
    }),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

describe("AppShell", () => {
  it(
    "renders the app name and every NAV_SECTIONS item as a link",
    async () => {
      renderWithProviders(
        <AppShell>
          <div>Page content</div>
        </AppShell>,
      );

      // Brand mark shows the full app name. Awaited so the AI settings query
      // AIMentorLauncher fires on mount settles before the assertions below.
      expect(await screen.findByText(APP_NAME)).toBeInTheDocument();

      // Every section label and every nav item link from the shared config is
      // rendered — scoped per-section since a couple of labels (e.g.
      // "Overview" under both Interview and Career) are intentionally reused
      // across different sections.
      for (const section of NAV_SECTIONS) {
        // Section labels are rendered as <h2> headings — queried by role
        // (not text) since a couple of labels (e.g. "Settings") are also
        // reused as an item label within their own section.
        const heading = screen.getByRole("heading", { name: section.label, level: 2 });
        const sectionContainer = heading.parentElement as HTMLElement;
        for (const item of section.items) {
          expect(within(sectionContainer).getByRole("link", { name: item.label })).toBeInTheDocument();
        }
      }
    },
    // AppShell now also mounts AIMentorLauncher (an extra React-Query-backed
    // component on every route) — this full render + query settle can run
    // past Vitest's default 5000ms under a loaded machine/full-suite run
    // even though it passes comfortably in isolation; a longer, explicit
    // timeout is the correct fix (more real work, not a stuck test).
    10_000,
  );
});
