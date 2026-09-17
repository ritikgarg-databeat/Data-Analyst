import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 9: the Interview & Assessment Engine.
 *
 * Assumes the API is running and seeded with the real, content-authored
 * interview question bank (335 questions), interview cases (15, tagged
 * "interview"), and interview templates (6) — see content/interview/ and
 * content/cases/*.yaml. The SQL round is pinned to a specific, stable
 * question (`sql-discount-percent-revenue`) via its detail page, matching
 * this suite's existing convention (cf. case-studies.spec.ts hardcoding a
 * specific real case) rather than trusting adaptive selection. The
 * `mock-analyst-quick` template's Case Study round is deliberately NOT
 * pinned to one case — `_pick_interview_case` in interview_service.py just
 * takes the first not-yet-used case tagged "interview" ordered by title,
 * ignoring category, so which of the 15 interview cases appears depends on
 * current content and isn't asserted on here. Every step inside the Case
 * Workspace below is written generically against whatever case that is
 * (real content, unpredictable identity) rather than one hardcoded case.
 *
 * Covers the full spec-mandated journey in one serial flow: Interview Prep ->
 * SQL assessment -> timer -> solve -> submit -> score -> review -> Case
 * Study round -> complete -> full mock -> finish -> readiness -> personalized plan.
 *
 * Runs serially: every step is a real write against the same dev SQLite
 * database used by other serial specs.
 */
test.describe.configure({ mode: "serial" });

const CORRECT_SQL =
  "SELECT ROUND(SUM(quantity * unit_price * (1 - discount / 100.0)), 2) AS total_revenue FROM order_items;";

test.describe("Phase 9 Interview & Assessment Engine", () => {
  test("Interview Prep -> timed SQL assessment -> score -> review -> mock interview with a Case Study round -> readiness -> plan", async ({
    page,
  }) => {
    test.slow();

    // 1. Interview Prep dashboard.
    await page.goto("/interview");
    await expect(page.getByRole("heading", { name: "Interview Prep" })).toBeVisible();
    await expect(page.getByText("Overall Readiness")).toBeVisible();

    // 2. Start a SQL assessment (Practice quick-start), pinned to a known
    // question via its detail page so the correct answer is known ahead of
    // time — the dashboard's own quick-start uses adaptive selection over
    // the whole 50+ question SQL pool, which this spec can't predict.
    await page.goto("/interview/questions/sql-discount-percent-revenue");
    await expect(page.getByRole("heading", { name: "Question Detail" })).toBeVisible();
    await page.getByRole("button", { name: "Practice This Question" }).click();
    await page.waitForURL(/\/interview\/session\/.+/);

    // 3. Timer is visible — pinning to a specific question carries over its
    // own suggested time limit, so this shows a live countdown ("X left").
    await expect(page.getByRole("timer")).toBeVisible();
    await expect(page.getByText(/left$/)).toBeVisible();

    // The pinned-question flow auto-starts (IN_PROGRESS) with the question
    // already loaded — no separate "Start Interview" click needed here.
    await expect(page.getByText("A Validity Trap")).toBeVisible();

    // 4. Solve — fill in the real SQL editor with the correct query.
    await page.locator(".monaco-editor").click();
    await page.keyboard.press("Control+A");
    await page.keyboard.type(CORRECT_SQL, { delay: 3 });

    // 5. Submit.
    await page.getByRole("button", { name: "Submit Answer" }).click();

    // 6. Score — a single-question interview auto-completes and redirects
    // straight to its review page.
    await page.waitForURL(/\/interview\/session\/.+\/review/);
    await expect(page.getByRole("heading", { name: "Interview Review" })).toBeVisible();
    await expect(page.getByText("Scorecard")).toBeVisible();
    await expect(page.getByText("100%")).toBeVisible();

    // 7. Review — expand the question and confirm the real explanation shows.
    await page.getByRole("button", { name: /discount.*percent.*revenue|Validity Trap/i }).click();
    await expect(page.getByText(/percentage, not a fraction/i)).toBeVisible();

    // 8. A mock, company-style interview whose second round is a real Case
    // Study round — start it from the templates catalog.
    await page.goto("/interview/templates");
    await expect(page.getByRole("heading", { name: "Company-Style Assessments" })).toBeVisible();
    const templateCard = page
      .getByText("Quick Mock Interview — SQL + Case Study", { exact: true })
      .locator("xpath=ancestor::div[.//button][1]");
    await templateCard.getByRole("button", { name: "Start" }).click();
    await page.waitForURL(/\/interview\/session\/.+/);

    await page.getByRole("button", { name: "Start Interview" }).click();
    await expect(page.getByText("Round 1 of 2: SQL")).toBeVisible();
    await page.locator(".monaco-editor").click();
    await page.keyboard.press("Control+A");
    await page.keyboard.type(CORRECT_SQL, { delay: 3 });
    await page.getByRole("button", { name: "Submit Answer" }).click();

    // Round 2: a real Case Study round — redirects into the actual Case
    // Workspace (Phase 8), reused as-is with zero new backend code. This is
    // a same-tab client-side navigation (a plain Next.js <Link>), so just
    // remember the interview session URL to come back to afterward.
    await expect(page.getByRole("heading", { name: "Case Study Round" })).toBeVisible();
    const sessionUrl = page.url();
    await page.getByRole("link", { name: "Continue in Case Workspace" }).click();
    await page.waitForURL(/\/case-studies\/attempts\/.+/);

    // 9. Complete the case in the real Case Workspace. Which case this is
    // isn't predictable (see the file docstring), so assert structurally —
    // the workspace's tab bar rendering at all means a real case loaded
    // (as opposed to the loading or error state) — rather than pinning to
    // one case's title text.
    await expect(page.getByRole("tab", { name: "Clarify" })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.getByRole("tab", { name: "Clarify" }).click();
    await page
      .getByPlaceholder(/Which specific metric|What would you ask/)
      .fill("What exact window was this measured over, and did anything else change recently that could explain it?");
    await page.keyboard.press("Tab");

    await page.getByRole("tab", { name: "Frame" }).click();
    await page.getByLabel("Problem", { exact: true }).fill("Confirm and localize the reported change before recommending anything.");
    await page.getByLabel("Objective", { exact: true }).fill("Determine whether the change is real and where it concentrates.");
    await page.getByLabel("Primary Metric", { exact: true }).fill("The metric named in the stakeholder's problem statement.");
    await page.getByLabel("Scope", { exact: true }).fill("Recent history for the affected metric, all segments.");
    await page.getByLabel("Hypotheses", { exact: true }).fill("Data/tracking artifact vs. a genuine underlying shift.");
    await page.keyboard.press("Tab");

    // A dataset checklist (Data section, in the sidebar) only appears if
    // this particular case lists any — and which datasets, if so, vary by
    // case. These are the only checkboxes on screen while the Frame tab is
    // open, so just exercise the first one if present.
    const datasetCheckboxes = page.getByRole("checkbox");
    if ((await datasetCheckboxes.count()) > 0) {
      const first = datasetCheckboxes.first();
      if (!(await first.isChecked())) await first.click();
      await expect(first).toBeChecked();
    }

    await page.getByRole("tab", { name: "Recommend" }).click();
    await page.getByLabel("Recommendation", { exact: true }).fill("Investigate further before broad action.");
    await page.getByLabel("Why", { exact: true }).fill("The recomputed metric confirms a real, localized shift.");
    await page.getByLabel("Expected Impact", { exact: true }).fill("Faster, more targeted root-cause identification.");
    await page.getByLabel("Risks", { exact: true }).fill("Could be a single unrepresentative period.");
    await page.getByLabel("Implementation Considerations", { exact: true }).fill("Needs the affected segment's owner involved.");
    await page.getByLabel("Next Steps", { exact: true }).fill("Segment the metric to localize the change.");
    await page.keyboard.press("Tab");

    await page.getByRole("tab", { name: "Communicate", exact: false }).click();
    await page.getByLabel("Problem", { exact: true }).fill("The stakeholder's reported metric change.");
    await page.getByLabel("Key Findings", { exact: true }).fill("Confirmed via recomputation; concentrated in one segment.");
    await page.getByLabel("Business Impact", { exact: true }).fill("Avoid an overly broad reaction to a localized issue.");
    await page.getByLabel("Recommendation", { exact: true }).fill("Investigate the affected segment further.");
    await page.getByLabel("Next Steps", { exact: true }).fill("Open a focused investigation on that segment.");
    await page.keyboard.press("Tab");
    await page.getByRole("button", { name: "Submit case" }).click();
    await expect(page.getByText(/Score:/)).toBeVisible();

    // Back to the interview session — GET self-heals once it notices the
    // Case Study round finished, and redirects to the finished mock's review.
    await page.goto(sessionUrl);
    await page.waitForURL(/\/interview\/session\/.+\/review/, { timeout: 15000 });

    // 10/11. Full mock complete — the review shows both rounds finished, each
    // as its own round-type badge. Exact text match (not a substring/regex)
    // to avoid the persistent "SQL Lab" sidebar nav link and this mock's own
    // "...SQL + Case Study" title, both of which also contain these words.
    await expect(page.getByText("Scorecard")).toBeVisible();
    await expect(page.getByText("SQL", { exact: true })).toBeVisible();
    await expect(page.getByText("Case Study", { exact: true })).toBeVisible();

    // 12. Readiness — the trend/breakdown reflect the interviews just completed.
    await page.goto("/interview/readiness");
    await expect(page.getByRole("heading", { name: "Readiness Trend" })).toBeVisible();
    await expect(page.getByText("Breakdown by Round Type")).toBeVisible();

    // 13. Personalized plan — generate one from actual performance so far.
    await page.goto("/interview/plan");
    await page.getByRole("button", { name: /Generate My 7-Day Plan|Regenerate Plan/ }).click();
    await expect(page.getByText("Day 1:")).toBeVisible();
    await expect(page.getByText("Day 6:")).toBeVisible();
    await expect(page.getByText("Full Mock Interview")).toBeVisible();
    await expect(page.getByText("Day 7:")).toBeVisible();
  });
});
