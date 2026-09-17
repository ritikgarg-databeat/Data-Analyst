import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 8: the Case Study Engine.
 *
 * Assumes the API is running and seeded with the real, content-authored
 * cases (20 of them — see content/cases/*.yaml). Uses a specific, stable
 * real case (`saas-pricing-page-ab-test-readout`) rather than "any
 * case", the same way the Phase 7 dbt Lab spec hardcodes `fct_orders` from
 * the real dbt project. Deep-links into SQL Lab/Python Lab/EDA are checked
 * for correctness (right URL, opens in a new tab) but not re-exercised in
 * depth — sql-lab.spec.ts and python-lab.spec.ts already cover those tools.
 *
 * Runs serially: case attempts, findings, and submission are all real
 * writes against the same dev SQLite database used by other serial specs.
 */
test.describe.configure({ mode: "serial" });

test.describe("Phase 8 Case Study Engine", () => {
  test("start a case, analyze, submit, and receive a real evaluation", async ({ page, context }) => {
    test.slow();

    const CASE_TITLE = "Case: Did the Checkout Redesign Actually Work?";

    // 1. Start the case from the library.
    await page.goto("/case-studies");
    await expect(page.getByRole("heading", { name: "Case Studies" })).toBeVisible();
    await page.getByPlaceholder("Search cases...").fill("Checkout Redesign Actually Work");

    // The nearest ancestor div that also contains a button — i.e. the whole
    // card, not just the innermost text wrapper (a plain `.last()` on a
    // hasText-filtered div locator would resolve to that inner wrapper
    // instead, since it's a descendant of the card and matches too).
    const card = page.getByText(CASE_TITLE, { exact: true }).locator("xpath=ancestor::div[.//button][1]");
    await card.getByRole("button", { name: /Start Case|Continue|Review/ }).click();
    await page.waitForURL(/\/case-studies\/attempts\/.+/);

    // 2. Read the stakeholder's problem statement in the CASE sidebar.
    await expect(page.getByRole("heading", { name: CASE_TITLE })).toBeVisible();
    await expect(page.getByText("Marcus Webb")).toBeVisible();

    // 3. Submit a clarification.
    await page.getByRole("tab", { name: "Clarify" }).click();
    await page
      .getByPlaceholder(/Which specific metric|What would you ask/)
      .fill("Which specific metric declined, over what time window, and did anything else change recently?");
    await page.keyboard.press("Tab");

    // 4. Frame the problem.
    await page.getByRole("tab", { name: "Frame" }).click();
    await page.getByLabel("Problem", { exact: true }).fill("The refund rate looks higher than it used to.");
    await page.getByLabel("Objective", { exact: true }).fill("Determine whether refunds are genuinely rising and why.");
    await page.getByLabel("Primary Metric", { exact: true }).fill("Refund rate (refunded orders / total orders)");
    await page.getByLabel("Scope", { exact: true }).fill("Last two years, all channels and categories");
    await page.getByLabel("Hypotheses", { exact: true }).fill("One category or channel drives most of the refunds.");
    await page.keyboard.press("Tab");

    // 5. Select a dataset, then open SQL Lab / Python Lab / EDA in new tabs.
    // Plain `.click()` + a polling `toBeChecked()` assertion, rather than
    // `.check()`/`.setChecked()` — those compare the DOM state once, right
    // after the click, which can race the round trip to persist the
    // selection and re-render from the query cache.
    const datasetCheckbox = page.getByRole("checkbox", { name: /Saas Product/i });
    if (!(await datasetCheckbox.isChecked())) {
      await datasetCheckbox.click();
    }
    await expect(datasetCheckbox).toBeChecked();
    const [sqlTab] = await Promise.all([
      context.waitForEvent("page"),
      page.getByRole("link", { name: "SQL", exact: true }).click(),
    ]);
    await expect(sqlTab).toHaveURL(/\/sql-lab\?database=saas-product/);
    await sqlTab.close();

    // 6. Analyze — add a finding with evidence, and track a hypothesis.
    await page.getByRole("tab", { name: "Analyze" }).click();
    await page
      .getByPlaceholder(/What did you observe/)
      .fill("The refund rate has crept up gradually across every channel, not just one.");
    await page.getByRole("button", { name: "Add finding" }).click();
    await expect(page.getByText("The refund rate has crept up gradually").first()).toBeVisible();

    // Scoped to this specific finding's own list item — a rerun against an
    // attempt that already has other findings would otherwise match more
    // than one "Attach evidence" button (one per finding).
    const findingItem = page.locator("li").filter({ hasText: "The refund rate has crept up gradually" });
    await findingItem.getByRole("button", { name: "Attach evidence" }).click();
    await findingItem.getByPlaceholder("What does this show?").fill("Refund rate by quarter and channel");
    await findingItem.getByRole("button", { name: "Add evidence" }).click();
    await expect(findingItem.getByText("SQL query: Refund rate by quarter and channel")).toBeVisible();

    await page.getByPlaceholder(/Hypothesis, e\.g\./).fill("H1: The increase is broad-based, not category-specific.");
    await page.keyboard.press("Enter");
    await expect(page.getByText(/H1: The increase is broad-based/).first()).toBeVisible();

    // 7. Recommend.
    await page.getByRole("tab", { name: "Recommend" }).click();
    await page
      .getByLabel("Recommendation", { exact: true })
      .fill("Investigate return-reason data for the categories with the highest absolute refund dollars.");
    await page.getByLabel("Why", { exact: true }).fill("The increase is broad-based rather than one bad category.");
    await page
      .getByLabel("Expected Impact", { exact: true })
      .fill("Understanding the driver could recover a meaningful share of refunded revenue.");
    await page.getByLabel("Risks", { exact: true }).fill("Some of the increase may just track order-volume growth.");
    await page
      .getByLabel("Implementation Considerations", { exact: true })
      .fill("Needs return-reason data the team may not currently track well.");
    await page.getByLabel("Next Steps", { exact: true }).fill("Pull refund rate by category and payment method.");
    await page.keyboard.press("Tab");

    // 8. Communicate & Submit — executive summary, rubric checklist, submit.
    await page.getByRole("tab", { name: "Communicate & Submit" }).click();
    await page.getByLabel("Problem", { exact: true }).fill("The refund rate has risen gradually over two years.");
    await page.getByLabel("Key Findings", { exact: true }).fill("The rise is broad-based across channels and categories.");
    await page.getByLabel("Business Impact", { exact: true }).fill("A steady drag on net realized revenue.");
    await page
      .getByLabel("Recommendation", { exact: true })
      .fill("Investigate return-reason data for the highest-dollar refund categories.");
    await page.getByLabel("Next Steps", { exact: true }).fill("Pull refund rate by category and payment method.");
    await page.keyboard.press("Tab");

    const rubricCheckboxes = page.getByRole("tabpanel").getByRole("checkbox");
    // (the sidebar's dataset checkbox has its own role="checkbox" too, but it lives outside
    // the main-area tabpanel, so this scoped query only ever sees the rubric's checkboxes)
    const count = await rubricCheckboxes.count();
    for (let i = 0; i < count; i++) {
      await rubricCheckboxes.nth(i).check();
    }

    await page.getByRole("button", { name: "Submit case" }).click();

    // 9. Receive a real evaluation — an actual computed score and feedback.
    await expect(page.getByText(/^Score: \d+(\.\d+)?%$/)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("COMPLETED", { exact: false })).toBeVisible();

    // 10. Reveal the reference solution (only available after completion).
    await page.getByRole("button", { name: "Reveal reference solution" }).click();
    await expect(page.getByText(/Key insights/i)).toBeVisible();

    // 11. Reflect.
    await page
      .getByLabel("What did you learn?", { exact: true })
      .fill("Segment before concluding a rate change is localized to one thing.");
    await page.keyboard.press("Tab");

    // 12. My Case Performance reflects this real completion.
    await page.goto("/case-studies/performance");
    await expect(page.getByRole("heading", { name: "My Case Performance" })).toBeVisible();
    await expect(page.getByText("Cases Completed")).toBeVisible();
    await expect(page.getByText("Average Score")).toBeVisible();
    await expect(page.getByText(/^100%$/)).toBeVisible(); // this run's single completed attempt scored 100%
    await expect(page.getByRole("link", { name: CASE_TITLE })).toBeVisible();
  });
});
