import { expect, test } from "@playwright/test";

test.describe("Ritik's Personal Data Analyst Lab — smoke test", () => {
  test("the application opens and the dashboard loads", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Ritik's Personal Data Analyst Lab" })).toBeVisible();
    await expect(
      page.getByText("Ritik's end-to-end environment for becoming a modern Data Analyst."),
    ).toBeVisible();
  });

  test("the desktop navigation is present and links to Learn", async ({ page }) => {
    await page.goto("/");

    // Phase 12 grouped the nav under section headings ("Learn", "Analyze", ...);
    // "Learn" is now a heading, not a link — the actual link into /learn is "Curriculum".
    await expect(page.getByRole("heading", { name: "Learn", exact: true })).toBeVisible();
    const curriculumLink = page.getByRole("link", { name: "Curriculum", exact: true });
    await expect(curriculumLink).toBeVisible();
    await curriculumLink.click();

    await expect(page).toHaveURL(/\/learn$/);
  });

  test("seeded domains appear on the Learn page", async ({ page }) => {
    await page.goto("/learn");

    // Seeded via database/seeds/domains.yaml (app.db.seed) — assumes the API
    // is running and migrated/seeded (see README.md "Testing"). Scoped to
    // headings since domain descriptions also mention these words in prose.
    await expect(page.getByRole("heading", { name: "Data Analyst Foundations" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByRole("heading", { name: "SQL", exact: true })).toBeVisible();
  });
});
