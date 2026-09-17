import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 7: the dbt Lab, Data Modeler, and Data
 * Quality Lab.
 *
 * Assumes the API is running and seeded against the standard ecommerce
 * sample dataset, AND that the real local dbt project at repo-root `dbt/`
 * is present and buildable (DBT_DATA_DIR/DBT_WAREHOUSE_PATH resolved by
 * app/dbt_lab/paths.py). Every dbt action here shells out to the real `dbt`
 * CLI — these assertions only pass if the actual project actually builds,
 * not a simulated result.
 *
 * Runs serially, not in parallel workers: the dev API sits on a single
 * SQLite file (see README.md), which serializes concurrent writes — running
 * these three tests (each making several real writes: dbt runs, model
 * saves, quality-rule runs) at the same time causes real, transient
 * "database is locked" failures that are an artifact of the dev DB choice,
 * not a bug in the app itself.
 */
test.describe.configure({ mode: "serial" });

test.describe("Phase 7 dbt Lab", () => {
  test("run the real dbt project, inspect lineage, docs, and test results", async ({ page }) => {
    test.slow(); // real `dbt build`/`dbt test` invocations take several seconds each

    await page.goto("/");
    await page.getByRole("link", { name: "dbt Lab" }).first().click();
    await page.waitForURL("**/dbt-lab");
    await expect(page.getByRole("heading", { name: "dbt Lab" })).toBeVisible();

    // Build the real project (seed + models + snapshots + tests) for real.
    await page.getByRole("button", { name: "Build" }).click();
    await expect(page.getByText(/Last run: dbt build — SUCCESS/)).toBeVisible({ timeout: 30_000 });

    // Run History shows the real run with a real node/result summary.
    await expect(page.getByRole("tab", { name: /Run History/ })).toHaveAttribute("aria-selected", "true");
    await page.getByRole("button", { name: /dbt build/ }).first().click();
    await expect(page.getByText(/node\(s\)/)).toBeVisible();

    // Lineage: a real DAG built from dbt's own manifest.json.
    await page.getByRole("tab", { name: "Lineage" }).click();
    await expect(page.locator(".react-flow__node").filter({ hasText: "fct_orders" })).toBeVisible();
    await page.locator(".react-flow__node").filter({ hasText: "fct_orders" }).click();
    await expect(page.locator('[data-slot="sheet-title"]')).toHaveText("fct_orders");
    await expect(page.getByText("gross_margin_pct")).toBeVisible();
    await page.keyboard.press("Escape");

    // Docs: real column types (from catalog.json) and descriptions (from manifest.json).
    await page.getByRole("tab", { name: "Docs" }).click();
    await page.getByRole("tabpanel").getByRole("button", { name: /fct_orders/ }).click();
    await expect(page.getByText("order_id")).toBeVisible();
    await expect(page.getByText("BIGINT").first()).toBeVisible();

    // Test Results: real pass/fail from the build's `dbt test` phase.
    await page.getByRole("tab", { name: "Test Results" }).click();
    await expect(page.getByText(/\d+ \/ \d+ passed/)).toBeVisible();
  });
});

test.describe("Phase 7 Data Modeler", () => {
  test("create a model, catch a missing primary key, fix it, and validate clean", async ({ page }) => {
    await page.goto("/data-modeler");
    await expect(page.getByRole("heading", { name: "Data Modeler" })).toBeVisible();

    const modelName = `E2E Star Schema ${Date.now()}`;
    await page.getByPlaceholder("e.g. Ecommerce Star Schema").fill(modelName);
    await page.getByRole("button", { name: "Create" }).click();
    await page.waitForURL(/\/data-modeler\/.+/);

    // Add a table with no primary key and save — Validate should catch it for real.
    await page.getByRole("button", { name: "Add table" }).click();
    await page.locator(".react-flow__node").first().click();
    await expect(page.getByRole("heading", { name: "Edit table" })).toBeVisible();
    await page.getByLabel("Name").fill("fct_orders");
    await page.getByLabel("Type").selectOption("FACT");
    await page.getByLabel("Grain").fill("1 row = 1 order");
    await page.getByRole("button", { name: "Add column" }).click();
    await page.getByPlaceholder("column_name").fill("order_id");
    await page.keyboard.press("Escape");

    await page.getByRole("button", { name: "Validate" }).click();
    await expect(page.getByText(/missing_primary_key|has no column marked as a primary key/)).toBeVisible({
      timeout: 10_000,
    });

    // Fix it: mark order_id as the primary key, then re-validate clean.
    await page.locator(".react-flow__node").filter({ hasText: "fct_orders" }).click();
    await page.getByLabel("Primary key").check();
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "Validate" }).click();
    await expect(page.getByText("No issues found.")).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Phase 7 Data Quality Lab", () => {
  test("create a rule, run it against real data, and see a real pass and a real fail", async ({ page }) => {
    await page.goto("/data-quality");
    await expect(page.getByRole("heading", { name: "Data Quality Lab" })).toBeVisible();

    // Unique names (rather than relying on "newest sorts first") keep this test correct even
    // when re-run repeatedly against the same dev database, where many same-shaped rules accumulate.
    const runId = Date.now();
    const notNullName = `E2E not-null ${runId}`;
    const acceptedValuesName = `E2E accepted-values ${runId}`;

    await page.getByLabel("Dataset").selectOption({ label: "E-commerce Analytics" });
    await page.getByLabel("Table").selectOption("orders");
    await page.getByLabel("Rule type").selectOption("NOT_NULL");
    await page.getByLabel("Column").fill("customer_id");
    await page.getByLabel("Name (optional)").fill(notNullName);
    await page.getByRole("button", { name: "Create rule" }).click();

    // Run it and confirm a real PASS against the live data.
    const notNullRow = page.locator("li").filter({ hasText: notNullName });
    await Promise.all([
      page.waitForResponse((r) => r.url().includes("/data-quality/rules/") && r.url().endsWith("/run")),
      notNullRow.getByRole("button", { name: "Run" }).click(),
    ]);
    await notNullRow.getByRole("button").first().click(); // toggles the run-history panel open
    await expect(notNullRow.getByText(/0 violation/)).toBeVisible({ timeout: 10_000 });

    // A rule that should genuinely fail against the real data (real orders have more than just "completed").
    await page.getByLabel("Rule type").selectOption("ACCEPTED_VALUES");
    await page.getByLabel("Column").fill("status");
    await page.getByLabel("Accepted values (comma-separated)").fill("completed");
    await page.getByLabel("Name (optional)").fill(acceptedValuesName);
    await page.getByRole("button", { name: "Create rule" }).click();

    const acceptedValuesRow = page.locator("li").filter({ hasText: acceptedValuesName });
    await Promise.all([
      page.waitForResponse((r) => r.url().includes("/data-quality/rules/") && r.url().endsWith("/run")),
      acceptedValuesRow.getByRole("button", { name: "Run" }).click(),
    ]);
    await acceptedValuesRow.getByRole("button").first().click();
    await expect(acceptedValuesRow.getByText(/violation/)).toBeVisible({ timeout: 10_000 });
  });
});
