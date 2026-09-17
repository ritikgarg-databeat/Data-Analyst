import { defineConfig, devices } from "@playwright/test";

/**
 * E2E smoke tests for Personal Data Analyst Lab.
 *
 * Assumes the API (http://localhost:8000) is already running and seeded —
 * see README.md "Testing" section. `webServer` below only boots the Next.js
 * frontend; it does not start Postgres/the API, since those need
 * migrations + seed data applied first.
 */
export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.E2E_SKIP_WEBSERVER
    ? undefined
    : {
        command: "npm run dev --workspace=apps/web",
        cwd: "../..",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
