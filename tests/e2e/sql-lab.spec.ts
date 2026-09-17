import { expect, test, type Page } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 3: the SQL Lab playground and the SQL
 * exercise workspace embedded in Practice.
 *
 * Assumes the API is running and seeded against the standard ecommerce
 * sample dataset (data/sample/ecommerce/*.csv — 8 tables; SQL Lab caps
 * execution results at 1,000 rows, see apps/api/app/core/config.py
 * `sql_lab_row_limit`) and the `aov-query` SQL exercise
 * (content/exercises/business-analytics/aov-query.yaml).
 */

const ECOMMERCE_TABLES = [
  "categories",
  "customers",
  "marketing_campaigns",
  "order_items",
  "orders",
  "payments",
  "products",
  "sessions",
];

/** Clicks into the Monaco-backed SQL editor (identified by its aria-label), selects everything, and types a new query. */
async function setEditorQuery(page: Page, editorLabel: string, query: string) {
  const editor = page.getByRole("group", { name: editorLabel }).locator(".monaco-editor");
  await editor.click();
  await page.keyboard.press("Control+a");
  await page.keyboard.type(query);
}

/** Asserts the editor's rendered content contains a token (a single word, to sidestep Monaco's whitespace rendering quirks). */
async function expectEditorContains(page: Page, editorLabel: string, token: string) {
  await expect(page.getByRole("group", { name: editorLabel }).locator(".view-lines")).toContainText(token);
}

test.describe("Phase 3 SQL Lab", () => {
  test("explore the schema, run/sort/save queries, and see errors + history in the playground", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "SQL Lab" }).first().click();
    await page.waitForURL("**/sql-lab");
    await expect(page.getByRole("heading", { name: "SQL Lab" })).toBeVisible();

    // The ecommerce database is selected by default and lists all 8 seeded tables.
    await expect(page.getByLabel("Database")).toHaveValue("ecommerce");
    for (const table of ECOMMERCE_TABLES) {
      await expect(page.getByRole("button", { name: new RegExp(`^${table}\\b`) })).toBeVisible();
    }

    // Expand a table and see its real columns.
    await page.getByRole("button", { name: /^orders\b/ }).click();
    await expect(page.getByText("order_id")).toBeVisible();
    await expect(page.getByText("customer_id")).toBeVisible();
    await expect(page.getByText("order_date")).toBeVisible();

    // Preview the table's sample rows.
    await page.getByRole("button", { name: "Preview orders" }).click();
    await expect(page.locator('[data-slot="sheet-title"]')).toHaveText("orders");
    await expect(page.getByText(/Sample of 20 rows out of [\d,]+ total\./)).toBeVisible();
    await page.keyboard.press("Escape");

    // Type a fresh query and run it.
    const query = "SELECT order_id, customer_id FROM orders ORDER BY order_id LIMIT 20;";
    await setEditorQuery(page, "SQL query editor", query);
    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText("20 rows · 2 columns")).toBeVisible();

    // Sort the customer_id column ascending and verify the row order actually changed.
    await page.getByRole("button", { name: /Sort by customer_id/i }).click();
    const customerIdCells = page.locator("table tbody tr td:nth-child(2)");
    const values = (await customerIdCells.allTextContents()).map(Number);
    const sortedAscending = [...values].sort((a, b) => a - b);
    expect(values).toEqual(sortedAscending);

    // A query matching more than SQL Lab's 1,000-row cap is truncated with a visible notice.
    await setEditorQuery(page, "SQL query editor", "SELECT * FROM sessions;");
    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText(/Results truncated at 1,000 rows/)).toBeVisible();

    // A deliberate typo (misspelled table name) surfaces the real engine error plus its derived hint.
    await setEditorQuery(page, "SQL query editor", "SELECT * FROM orderz;");
    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText("Query failed")).toBeVisible();
    await expect(page.getByText(/orderz/)).toBeVisible();
    await expect(page.getByText(/does not exist/)).toBeVisible();
    await expect(
      page.getByText("Check the table name for typos, or expand the schema explorer to see available tables."),
    ).toBeVisible();

    // Every execution — including the failed one — lands in History.
    await page.getByRole("tab", { name: "History" }).click();
    await expect(page.getByText(query)).toBeVisible();

    // Clicking a history entry reloads it into the editor.
    await setEditorQuery(page, "SQL query editor", "SELECT * FROM orders LIMIT 5;");
    await page.getByText(query).click();
    await expectEditorContains(page, "SQL query editor", "customer_id");

    // Save the current query, then find it in Saved.
    await page.getByRole("tab", { name: "Saved" }).click();
    await page.getByRole("button", { name: "Save current query" }).click();
    await page.getByLabel("Title").fill("Orders by customer");
    await page.getByRole("button", { name: "Save", exact: true }).click();
    await expect(page.getByText("Orders by customer")).toBeVisible();

    // Load a different query, then load the saved one back.
    await setEditorQuery(page, "SQL query editor", "SELECT * FROM orders LIMIT 5;");
    await page.getByText("Orders by customer").click();
    await expectEditorContains(page, "SQL query editor", "customer_id");
  });

  test("run then submit a correct SQL exercise query, then submit an incorrect one", async ({ page }) => {
    await page.goto("/practice/aov-query");

    await expect(page.getByText("Calculate Average Order Value")).toBeVisible();
    await expect(page.getByText(/Finance is benchmarking marketing spend efficiency/)).toBeVisible();
    await expect(page.getByText("payments", { exact: true })).toBeVisible();

    const correctQuery = "SELECT ROUND(AVG(amount), 2) AS aov FROM payments WHERE status = 'success';";
    await setEditorQuery(page, "SQL exercise query editor", correctQuery);

    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText("1 row · 1 column")).toBeVisible();

    await page.getByRole("button", { name: "Submit" }).click();
    await expect(page.getByText("Passed!")).toBeVisible();
    await expect(page.getByText("Score: 100%")).toBeVisible();
    await expect(page.getByText(/The core of the answer is/)).toBeVisible();

    // Reset back to the starter query, then submit an incorrect one (missing the status filter)
    // and see the real diff message from the grading pipeline (not a fabricated one).
    await page.getByRole("button", { name: "Reset" }).click();
    const incorrectQuery = "SELECT ROUND(AVG(amount), 2) AS aov FROM payments;";
    await setEditorQuery(page, "SQL exercise query editor", incorrectQuery);
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Not quite.")).toBeVisible();
    await expect(page.getByText("Values differ in column 1 of a row of your result.")).toBeVisible();
  });
});
