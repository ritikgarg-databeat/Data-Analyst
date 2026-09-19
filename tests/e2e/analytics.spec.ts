import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 6: Statistics, Experimentation, the
 * Metrics Library, Product Analytics (funnel/cohort), and Analytics Cases.
 *
 * Assumes the API is running and seeded (see README.md "Testing" section) —
 * in particular the "saas-product" SQL Lab database (data/sample/saas_product/*.csv)
 * for the Product Analytics funnel/cohort explorers, and at least one
 * `case-study`-tagged exercise for the Analytics Cases flow (the Phase 5
 * EDA-challenge-library exercises already carry this tag, so this doesn't
 * depend on any specific Phase 6 case existing).
 */

test.describe("Phase 6 Statistics/Experimentation/Analytics", () => {
  test("compute summary statistics and run a hypothesis test", async ({ page }) => {
    await page.goto("/dashboard");
    await page.getByRole("link", { name: "Statistics" }).first().click();
    await page.waitForURL("**/statistics");
    await expect(page.getByRole("heading", { name: "Statistics" })).toBeVisible();

    await page.getByLabel("Values").fill("10, 12, 11, 13, 9, 14, 10, 12, 11, 13");
    await page.getByRole("button", { name: "Compute" }).click();
    await expect(page.getByText("Mean", { exact: true })).toBeVisible();
    await expect(page.getByText("95% CI for the mean:")).toBeVisible();

    await page.getByRole("tab", { name: "Hypothesis Test" }).click();
    await page.getByLabel("Sample A").fill("1, 2, 3, 2, 1");
    await page.getByLabel("Sample B").fill("20, 21, 19, 22, 20");
    await page.getByRole("button", { name: "Run Test" }).click();
    await expect(page.getByText("Reject H₀")).toBeVisible();
    await expect(page.getByText(/Welch's t-test/)).toBeVisible();
  });

  test("calculate a sample size and analyze an A/B test", async ({ page }) => {
    await page.goto("/experiments");
    await expect(page.getByRole("heading", { name: "Experimentation" })).toBeVisible();

    await expect(page.getByRole("button", { name: "Calculate Sample Size" })).toBeVisible();
    await page.getByRole("button", { name: "Calculate Sample Size" }).click();
    await expect(page.getByText("per variant")).toBeVisible();

    await page.getByRole("tab", { name: "A/B Test Analyzer" }).click();
    await page.getByRole("button", { name: "Analyze" }).click();
    await expect(page.getByText(/Ship-worthy evidence|Statistically significant|Practically meaningful|Inconclusive/)).toBeVisible();

    await page.getByRole("tab", { name: "Power Simulator" }).click();
    await page.getByRole("button", { name: "Run Simulation" }).click();
    await expect(page.getByText("Empirical power", { exact: true })).toBeVisible();
  });

  test("browse the Metrics Library and open a metric's detail", async ({ page }) => {
    await page.goto("/metrics");
    await expect(page.getByRole("heading", { name: "Metrics Library" })).toBeVisible();
    await expect(page.getByText("Customer Acquisition Cost (CAC)")).toBeVisible();

    await page.getByText("Customer Acquisition Cost (CAC)").click();
    await expect(page.locator('[data-slot="sheet-title"]')).toHaveText("Customer Acquisition Cost (CAC)");
    await expect(page.getByText("Formula")).toBeVisible();
  });

  test("build a funnel and a cohort retention matrix from the saas-product dataset", async ({ page }) => {
    await page.goto("/product-analytics");
    await expect(page.getByRole("heading", { name: "Product Analytics" })).toBeVisible();

    await page.getByLabel("Dataset").selectOption({ label: "SaaS Product Analytics" });
    await page.getByRole("button", { name: "Run Funnel" }).click();
    await expect(page.getByText("signup", { exact: true })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/A user 'reaches' a step/)).toBeVisible();

    await page.getByRole("tab", { name: "Cohort Retention" }).click();
    await page.getByRole("button", { name: "Build Matrix" }).click();
    await expect(page.locator("table").getByText("Cohort", { exact: true })).toBeVisible({ timeout: 15_000 });
  });

  test("submit an analytics case", async ({ page }) => {
    await page.goto("/analytics-cases");
    await expect(page.getByRole("heading", { name: "Analytics Cases" })).toBeVisible();

    const firstCase = page.locator("a[href^='/analytics-cases/']").first();
    await expect(firstCase).toBeVisible();
    await firstCase.click();
    await page.waitForURL(/\/analytics-cases\/.+/);

    await page.getByLabel("Your answer").fill("My analysis walks through the data and reaches a conclusion.");
    await page.getByRole("button", { name: "Submit" }).click();
    await expect(page.getByText(/Score: \d+%|Submitted/)).toBeVisible();
  });
});
