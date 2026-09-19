import { expect, test, type Page } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 4: the Python Lab notebook and the Python
 * exercise workspace embedded in Practice.
 *
 * Assumes Docker is running (the API's Python sandbox backend, see
 * apps/api/app/python_lab/docker_backend.py), the API is running and seeded
 * against the standard ecommerce sample dataset (data/sample/ecommerce/*.csv),
 * and the `quarterly-revenue-by-segment` Python exercise
 * (content/exercises/python/quarterly-revenue-by-segment.yaml).
 *
 * NOT run as part of this change — it needs a live Docker daemon + API +
 * seeded DB, none of which are available in the environment that authored
 * this spec. Written to match tests/e2e/sql-lab.spec.ts's conventions
 * (selectors, helper shape, one `test.describe` per phase) for a human (or a
 * future CI run) to execute and adjust against real output if needed.
 */

const ECOMMERCE_FILES = [
  "categories.csv",
  "customers.csv",
  "marketing_campaigns.csv",
  "order_items.csv",
  "orders.csv",
  "payments.csv",
  "products.csv",
  "sessions.csv",
];

/** Clicks into a Monaco-backed Python editor (identified by its aria-label), selects everything, and types new code. */
async function setEditorCode(page: Page, editorLabel: string, code: string) {
  const editor = page.getByRole("group", { name: editorLabel }).locator(".monaco-editor");
  await editor.click();
  await page.keyboard.press("Control+a");
  await page.keyboard.type(code);
}

test.describe("Phase 4 Python Lab", () => {
  test("browse datasets, run cells with persisted state, render a chart, inspect a DataFrame, and restart the runtime", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await page.getByRole("link", { name: "Python Lab" }).first().click();
    await page.waitForURL("**/python-lab");
    await expect(page.getByRole("heading", { name: "Python Lab" })).toBeVisible();

    // The dataset browser lists the ecommerce dataset's files, grouped under the dataset name.
    await page.getByRole("button", { name: /^Ecommerce/ }).click();
    for (const file of ECOMMERCE_FILES) {
      await expect(page.getByText(file)).toBeVisible();
    }

    // Before any code has run, there is no live runtime yet — "Restart Runtime" has nothing to restart.
    await expect(page.getByRole("button", { name: "Restart Runtime" })).toBeDisabled();

    // Type code in cell 1 and run it — this lazily starts a new Docker-sandboxed runtime.
    const cell1Code = ['import pandas as pd', 'orders = pd.read_csv("/data/ecommerce/orders.csv")', "orders"].join(
      "\n",
    );
    await setEditorCode(page, "Python cell 1 editor", cell1Code);
    await page.getByRole("button", { name: /^Run 1/ }).click();

    // A DataFrame result (the auto-displayed trailing `orders` expression) renders under the cell.
    await expect(page.getByText(/[\d,]+ rows? × \d+ columns?/).first()).toBeVisible();

    // The runtime is now live.
    await expect(page.getByRole("button", { name: "Restart Runtime" })).toBeEnabled();

    // Add a second cell that references `orders` from cell 1 — proving kernel state persists
    // across cells within the same runtime.
    await page.getByRole("button", { name: "Add Cell" }).click();
    await setEditorCode(page, "Python cell 2 editor", "orders.shape");
    await page.getByRole("button", { name: /^Run 2/ }).click();
    await expect(page.getByText(/\(\d+, \d+\)/)).toBeVisible();

    // Plot something in a third cell and see the chart render.
    await page.getByRole("button", { name: "Add Cell" }).click();
    await setEditorCode(
      page,
      "Python cell 3 editor",
      ["import matplotlib.pyplot as plt", 'orders["order_id"].head(10).plot(kind="bar")', 'plt.title("Sample")'].join(
        "\n",
      ),
    );
    await page.getByRole("button", { name: /^Run 3/ }).click();
    await expect(page.locator("figure img")).toBeVisible();

    // Open the Variable Explorer and drill into the `orders` DataFrame.
    await expect(page.getByText("orders").first()).toBeVisible();
    await page.getByRole("button", { name: /orders/ }).first().click();
    await expect(page.getByRole("tab", { name: "Preview" })).toBeVisible();
    await page.getByRole("tab", { name: "Schema" }).click();
    await expect(page.getByText("order_id")).toBeVisible();
    await page.getByRole("tab", { name: "Statistics" }).click();
    await expect(page.getByText(/Memory usage:/)).toBeVisible();

    // Restarting the runtime wipes its in-memory state — re-running a cell that references
    // `orders` now fails with a real NameError, and prior outputs are cleared.
    await page.getByRole("button", { name: "Restart Runtime" }).click();
    await expect(page.getByText(/[\d,]+ rows? × \d+ columns?/)).toHaveCount(0);
    await page.getByRole("button", { name: /^Run 2/ }).click();
    await expect(page.getByText("NameError")).toBeVisible();
    await expect(page.getByText(/orders/).first()).toBeVisible();
  });

  test("run then submit a correct Python exercise, then submit an incorrect one", async ({ page }) => {
    await page.goto("/practice/quarterly-revenue-by-segment");

    await expect(page.getByText("Quarterly Revenue by Customer Segment")).toBeVisible();
    await expect(page.getByText(/leading customer segment by revenue/)).toBeVisible();
    await expect(page.getByText("payments.csv")).toBeVisible();

    const correctCode = [
      'payments_success = payments[payments["status"] == "success"].copy()',
      'merged = payments_success.merge(',
      '    orders[["order_id", "customer_id", "order_date"]], on="order_id"',
      ').merge(customers[["customer_id", "customer_segment"]], on="customer_id")',
      'merged["quarter"] = pd.to_datetime(merged["payment_date"]).dt.to_period("Q").astype(str)',
      "result = (",
      '    merged.groupby(["quarter", "customer_segment"])["amount"]',
      "    .sum()",
      "    .round(2)",
      "    .reset_index()",
      '    .rename(columns={"amount": "revenue"})',
      '    .sort_values(["quarter", "revenue"], ascending=[True, False])',
      "    .reset_index(drop=True)",
      ")",
    ].join("\n");
    await setEditorCode(page, "Python exercise code editor", correctCode);

    await page.getByRole("button", { name: /^Run/ }).click();
    await expect(page.getByText(/[\d,]+ rows? × \d+ columns?/).first()).toBeVisible();

    await page.getByRole("button", { name: "Submit" }).click();
    await expect(page.getByText("Passed!")).toBeVisible();
    await expect(page.getByText("Score: 100%")).toBeVisible();
    await expect(page.getByText(/filters to successful payments/)).toBeVisible();

    // Reset back to the starter code, then submit an incorrect one (missing the
    // `status == "success"` filter) and see the real diff message from the grading pipeline
    // (derived from app/python_lab/evaluation.py's compare_dataframes — not a fabricated one).
    await page.getByRole("button", { name: "Reset" }).click();
    const incorrectCode = [
      'merged = payments.merge(',
      '    orders[["order_id", "customer_id", "order_date"]], on="order_id"',
      ').merge(customers[["customer_id", "customer_segment"]], on="customer_id")',
      'merged["quarter"] = pd.to_datetime(merged["payment_date"]).dt.to_period("Q").astype(str)',
      "result = (",
      '    merged.groupby(["quarter", "customer_segment"])["amount"]',
      "    .sum()",
      "    .round(2)",
      "    .reset_index()",
      '    .rename(columns={"amount": "revenue"})',
      '    .sort_values(["quarter", "revenue"], ascending=[True, False])',
      "    .reset_index(drop=True)",
      ")",
    ].join("\n");
    await setEditorCode(page, "Python exercise code editor", incorrectCode);
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByText("Not quite.")).toBeVisible();
    await expect(page.getByText(/Values differ in column 'revenue' of row \d+ of your result\./)).toBeVisible();
  });
});
