import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for the Phase 2 core learning loop:
 * dashboard -> Learn -> domain -> module -> lesson -> read + complete ->
 * attempt an exercise -> progress reflected back on the dashboard.
 *
 * Assumes the API is running and seeded (see README.md "Testing") against
 * the standard seed data (58 lessons / 24 exercises / 1 assessment).
 */
test.describe("Phase 2 core learning loop", () => {
  // Serial: "completed lesson appears in Recently Completed" depends on the
  // lesson-completion side effect from the first test — under the config's
  // default fullyParallel:true these raced (previously masked entirely by
  // both tests failing at the same earlier nav step).
  test.describe.configure({ mode: "serial" });

  test("open dashboard, drill into a lesson, read it, and complete it", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Ritik's Personal Data Analyst Lab" })).toBeVisible();

    // Phase 12 grouped the nav under section headings — "Learn" is a heading now,
    // "Curriculum" is the actual link into /learn.
    await page.getByRole("link", { name: "Curriculum" }).first().click();
    await page.waitForURL("**/learn");

    // Scoped to #main-content — the sidebar nav (present on every page) also has a
    // "SQL Lab" link whose text matches a bare "SQL" filter.
    const main = page.locator("#main-content");
    await main.getByRole("link").filter({ hasText: "SQL" }).first().click();
    await page.waitForURL("**/learn/sql");

    await main.getByRole("link").filter({ hasText: "SQL Fundamentals" }).first().click();
    await page.waitForURL("**/learn/sql/sql-fundamentals");

    await main.getByRole("link").filter({ hasText: "SELECT" }).first().click();
    await page.waitForURL("**/learn/sql/sql-fundamentals/select");

    await expect(page.getByRole("heading", { name: "SELECT", exact: true })).toBeVisible();
    await expect(page.getByText("Learning Objectives")).toBeVisible();

    // Scroll to the bottom to build reading progress via the block-visibility tracker.
    for (let i = 0; i < 12; i++) {
      await page.mouse.wheel(0, 800);
      await page.waitForTimeout(250);
    }

    // A prior run of this suite may have already completed this lesson (the
    // seed database persists between runs) — the "Mark Complete" button is
    // hidden once a lesson is COMPLETED, so treat an existing "Completed"
    // badge as success too rather than assuming a button must be present.
    const markComplete = page.getByRole("button", { name: "Mark Complete" });
    // exact: true — a non-exact match also hits a `'completed'` string literal
    // inside this lesson's own SQL code sample.
    const alreadyCompleted = page.getByText("Completed", { exact: true }).first();
    await expect(markComplete.or(alreadyCompleted)).toBeVisible({ timeout: 10_000 });

    if (await markComplete.isVisible()) {
      await expect(markComplete).toBeEnabled({ timeout: 10_000 });
      await markComplete.click();
    }
    await expect(page.getByText("Completed").first()).toBeVisible();
  });

  test("attempt an exercise and see a graded result", async ({ page }) => {
    await page.goto("/practice/select-star-tradeoffs");

    await expect(page.getByText("The Cost of SELECT *")).toBeVisible();

    const correctChoice = page.getByRole("radio", { name: /silently gains an extra column/ });
    await correctChoice.click();
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Correct!")).toBeVisible();
  });

  test("completed lesson appears in Recently Completed on the dashboard", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Recently Completed")).toBeVisible();
    await expect(page.getByText("SELECT", { exact: true }).first()).toBeVisible({ timeout: 10_000 });
  });

  test("module assessment can be started, answered, and submitted", async ({ page }) => {
    await page.goto("/learn/sql/sql-fundamentals/assessment");

    await expect(page.getByText("SQL Fundamentals Assessment")).toBeVisible();
    await page.getByRole("button", { name: "Start Assessment" }).click();

    await expect(page.getByText("Question 1")).toBeVisible();

    const radiogroups = page.getByRole("radiogroup");
    const groupCount = await radiogroups.count();
    for (let i = 0; i < groupCount; i++) {
      await radiogroups.nth(i).getByRole("radio").first().click();
    }
    const textareas = page.locator("textarea");
    const textareaCount = await textareas.count();
    for (let i = 0; i < textareaCount; i++) {
      await textareas.nth(i).fill("a plausible free-text answer");
    }

    await page.getByRole("button", { name: "Submit Assessment" }).click();

    await expect(page.getByText(/Passed|Not passed/)).toBeVisible();
    await expect(page.getByRole("link", { name: "Back to Module" })).toBeVisible();
  });
});
