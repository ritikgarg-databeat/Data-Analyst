import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 8: the Project Engine.
 *
 * Assumes the API is running and seeded with the 8 real content-authored
 * project templates (see content/projects/*.yaml). Exercises starting a
 * project from a template, working through milestones/datasets/artifacts/
 * documentation/presentation, and a real rubric-based submission.
 */
test.describe.configure({ mode: "serial" });

test.describe("Phase 8 Project Engine", () => {
  test("start a project from a template, work through it, and submit for a real score", async ({ page }) => {
    test.slow();

    await page.goto("/projects");
    await expect(page.getByRole("heading", { name: "Projects", exact: true })).toBeVisible();

    // Scoped to the template grid's own <section> — a rerun that already has
    // a started project of the same name would otherwise also match that
    // project's row in "Your Projects" below, which has no button of its
    // own and so widens the ancestor search to the whole page.
    const templateSection = page
      .locator("section")
      .filter({ has: page.getByRole("heading", { name: "Start from a Template" }) });
    const templateCard = templateSection
      .getByText("Customer Churn Analytics", { exact: true })
      .locator("xpath=ancestor::div[.//button][1]");
    await templateCard.getByRole("button", { name: "Start Project" }).click();
    await page.waitForURL(/\/projects\/.+/);

    await expect(page.getByRole("heading", { name: "Customer Churn Analytics" })).toBeVisible();

    // Milestones — seeded from the template, toggle the first one complete.
    await page.getByRole("tab", { name: "Milestones" }).click();
    const firstMilestoneCheckbox = page.getByRole("checkbox").first();
    await firstMilestoneCheckbox.click();
    await expect(firstMilestoneCheckbox).toBeChecked();
    await expect(page.getByText(/1 \/ \d+ completed/)).toBeVisible();

    // Datasets — attach the real saas-product dataset with a reason.
    await page.getByRole("tab", { name: "Datasets" }).click();
    await page.getByRole("combobox").selectOption({ label: "SaaS Product Analytics" });
    await page.getByPlaceholder(/Why does this project need it/).fill("Needed for churn-by-plan analysis.");
    await page.getByRole("button", { name: "Add" }).click();
    await expect(page.getByText("Needed for churn-by-plan analysis.")).toBeVisible();

    // Artifacts — link a note-type artifact.
    await page.getByRole("tab", { name: "Artifacts" }).click();
    await page.getByPlaceholder("Label (required)").fill("Churn-by-plan SQL query");
    await page.getByRole("button", { name: "Add artifact" }).click();
    await expect(page.getByText("Churn-by-plan SQL query")).toBeVisible();

    // Documentation — fill one section, confirm it saves (survives a tab switch + reload).
    // Sections are Card-titled (not <label>-associated), so query by placeholder.
    await page.getByRole("tab", { name: "Documentation" }).click();
    const businessProblemField = page.getByPlaceholder("Write the business problem section...");
    await businessProblemField.fill("Churn is rising and leadership wants to know which plan tier to prioritize.");
    await page.keyboard.press("Tab");
    await page.reload();
    await page.getByRole("tab", { name: "Documentation" }).click();
    await expect(page.getByPlaceholder("Write the business problem section...")).toHaveValue(
      "Churn is rising and leadership wants to know which plan tier to prioritize.",
    );

    // Presentation — fill the first storyboard slide.
    await page.getByRole("tab", { name: "Presentation" }).click();
    await page
      .getByPlaceholder(/Write the "Business Problem" slide/)
      .fill("Churn is concentrated in a specific plan tier.");
    await page.keyboard.press("Tab");

    // Submission — check every rubric criterion, submit, get a real score.
    await page.getByRole("tab", { name: "Submission" }).click();
    const rubricCheckboxes = page.getByRole("tabpanel").getByRole("checkbox");
    const count = await rubricCheckboxes.count();
    for (let i = 0; i < count; i++) {
      await rubricCheckboxes.nth(i).check();
    }
    await page.getByRole("button", { name: "Submit project" }).click();
    await expect(page.getByText(/^Score: \d+(\.\d+)?%$/)).toBeVisible({ timeout: 10_000 });

    // Reflection.
    await page
      .getByLabel("What did you learn?", { exact: true })
      .fill("Segmenting by plan tier revealed the real driver.");
    await page.keyboard.press("Tab");
  });
});
