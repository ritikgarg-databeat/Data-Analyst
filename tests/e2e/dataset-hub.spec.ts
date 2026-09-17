import path from "node:path";
import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 5: the Dataset Hub, automatic profiling,
 * the EDA Workspace, the Visualization Workspace (Plotly chart rendering),
 * and the SQL Lab / Python Lab integration links.
 *
 * Assumes the API is running (see README.md "Testing" section). Unlike
 * sql-lab.spec.ts / python-lab.spec.ts, this spec doesn't depend on seeded
 * fixture data — it imports its own CSV (data/sample/ecommerce/products.csv)
 * through the real Dataset Hub upload flow, so every run is self-contained
 * (each run creates a new dataset with a timestamped name/slug).
 *
 * In-page navigation ("Open EDA", "Visualize", "SQL Lab", "Python Lab") is
 * scoped to the `main` landmark, since the persistent sidebar has its own
 * "SQL Lab"/"Python Lab" nav links with identical accessible names.
 *
 * The Python Lab check is written to pass whether or not Docker is running:
 * that feature gates its entire UI behind a Docker availability check (see
 * apps/web/src/components/features/python-lab/python-lab-page.tsx), so this
 * spec asserts on whichever of the two valid states actually renders.
 */

const PRODUCTS_CSV = path.resolve(__dirname, "../../data/sample/ecommerce/products.csv");

test.describe("Phase 5 Dataset Hub", () => {
  test("import a CSV, profile it, explore it in EDA, build a chart, and reach SQL/Python Lab", async ({ page }) => {
    test.setTimeout(90_000);
    const datasetName = `E2E Products ${Date.now()}`;

    await page.goto("/");
    await page.getByRole("link", { name: "Datasets" }).first().click();
    await page.waitForURL("**/datasets");
    await expect(page.getByRole("heading", { name: "Dataset Hub" })).toBeVisible();

    // Import a real CSV through the drag-and-drop-or-browse dialog.
    await page.getByRole("button", { name: "Import Dataset" }).click();
    const importDialog = page.getByRole("dialog");
    await expect(importDialog.getByRole("heading", { name: "Import Dataset" })).toBeVisible();
    await importDialog.getByLabel("Choose files to import").setInputFiles(PRODUCTS_CSV);

    const nameField = importDialog.getByLabel("Dataset name");
    await expect(nameField).toHaveValue("products");
    await nameField.fill(datasetName);
    await importDialog.getByLabel("Domain").fill("E-commerce");
    await importDialog.getByRole("button", { name: "Import Dataset" }).click();

    // On success we're routed to the new dataset's detail page.
    await page.waitForURL(/\/datasets\/.+/);
    const slug = new URL(page.url()).pathname.split("/").pop()!;
    await expect(page.getByRole("heading", { name: datasetName })).toBeVisible();
    const main = page.getByRole("main");

    // Profiling runs in the background; the Schema tab polls until real columns appear.
    await main.getByRole("tab", { name: "Schema" }).click();
    await expect(main.getByText("product_id")).toBeVisible({ timeout: 20_000 });
    await expect(main.getByText("product_name")).toBeVisible();
    await expect(main.getByText("unit_price")).toBeVisible();
    await expect(main.getByText("numeric").first()).toBeVisible();
    await expect(main.getByText("boolean").first()).toBeVisible();

    // Clicking a column opens its detail sheet with real profiling stats.
    await main.getByText("unit_price").click();
    await expect(page.locator('[data-slot="sheet-title"]')).toHaveText("unit_price");
    await expect(page.getByText("Completeness & uniqueness")).toBeVisible();
    await page.keyboard.press("Escape");

    // The deterministic quality score is broken down into its four weighted components.
    await main.getByRole("tab", { name: "Quality" }).click();
    await expect(main.getByText("Data Quality")).toBeVisible();
    await expect(main.getByText("Completeness", { exact: true })).toBeVisible();
    await expect(main.getByText("Uniqueness", { exact: true })).toBeVisible();
    await expect(main.getByText("Validity", { exact: true })).toBeVisible();
    await expect(main.getByText("Consistency", { exact: true })).toBeVisible();

    // "SQL Lab" carries the dataset's table into the real SQL Lab schema explorer.
    await main.getByRole("link", { name: "SQL Lab" }).click();
    await page.waitForURL(/\/sql-lab\?database=/);
    await expect(page.getByLabel("Database")).toHaveValue(slug);
    await expect(page.getByRole("button", { name: /^products\b/ })).toBeVisible();

    // Back to the dataset: the Python Lab link is gated by Docker availability, so
    // accept either the real dataset browser or the graceful fallback message.
    await page.goto(`/datasets/${slug}`);
    await page.getByRole("main").getByRole("link", { name: "Python Lab" }).click();
    await page.waitForURL("**/python-lab");
    await expect(
      page.getByRole("heading", { name: "Python Lab requires Docker" }).or(page.getByText(datasetName)),
    ).toBeVisible({ timeout: 30_000 });

    // Open EDA: generates a deterministic overview and question list for the dataset.
    await page.goto(`/datasets/${slug}`);
    await page.getByRole("main").getByRole("link", { name: "Open EDA" }).click();
    await page.waitForURL(/\/eda\/.+/);
    await expect(page.getByRole("button", { name: "Generate EDA Overview" })).toBeVisible();
    await page.getByRole("button", { name: "Generate EDA Overview" }).click();

    await expect(page.getByText("Dataset overview")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Numeric distributions")).toBeVisible();
    await expect(page.getByText("Categorical summaries")).toBeVisible();
    await expect(page.getByText("Questions to explore")).toBeVisible();

    // Capture a structured finding.
    await page.getByRole("button", { name: "Add Finding" }).click();
    await page.getByPlaceholder("Revenue increased 18% YoY.").fill("Prices cluster in a narrow band.");
    await page.getByRole("button", { name: "Save Finding" }).click();
    await expect(page.getByText("Prices cluster in a narrow band.")).toBeVisible();

    // Visualization: build a chart with the point-and-click builder and confirm it
    // actually renders via Plotly (not just that the API call succeeded).
    await page.goto(`/datasets/${slug}`);
    const visualizeHref = await page.getByRole("main").getByRole("link", { name: "Visualize" }).getAttribute("href");
    const datasetId = new URL(visualizeHref!, page.url()).searchParams.get("dataset")!;
    await page.getByRole("main").getByRole("link", { name: "Visualize" }).click();
    await page.waitForURL(/\/visualization\?dataset=/);
    await expect(page.getByLabel("Dataset")).toHaveValue(datasetId);

    await page.getByLabel("Y Axis").selectOption({ label: "unit_price (numeric)" });
    await page.getByLabel("Title").fill("Products by price");
    await page.getByRole("button", { name: "Create Chart" }).click();

    await expect(page.locator(".js-plotly-plot svg.main-svg").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: "Products by price", exact: true })).toBeVisible();
  });
});
