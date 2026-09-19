import { expect, test } from "@playwright/test";

/**
 * End-to-end smoke test for Phase 10: the AI Layer.
 *
 * This environment's real backend runs with AI_PROVIDER=local (the default
 * — see apps/api/app/ai/providers/local_provider.py) since no real
 * OpenAI/Anthropic key is configured. LocalProvider is a deterministic,
 * no-network responder, so this spec asserts on STRUCTURE (a panel opens, a
 * message round-trips, a reply appears, settings persist) rather than on
 * specific AI-generated content — exactly the property LocalProvider exists
 * to make testable without a real external API key.
 *
 * Runs serially: every step is a real write against the same dev SQLite
 * database used by other serial specs.
 */
test.describe.configure({ mode: "serial" });

test.describe("Phase 10 AI Layer", () => {
  test("AI Mentor launcher -> ask a question -> real reply; AI Settings; SQL Lab Ask AI", async ({ page }) => {
    test.slow();

    // 1. The AI Mentor launcher is present on every route.
    await page.goto("/dashboard");
    await expect(page.getByRole("button", { name: "AI Mentor" })).toBeVisible();
    await page.getByRole("button", { name: "AI Mentor" }).click();

    await expect(page.getByRole("heading", { name: "AI Data Analyst Mentor" })).toBeVisible();
    await expect(page.getByText(/may send selected learning\/code\/data context/)).toBeVisible();

    // 2. Ask a general question — a real round trip through Gateway ->
    // LocalProvider -> Response Validator -> conversation persistence.
    await page.getByPlaceholder("Ask anything...").fill("What is a primary key?");
    await page.getByRole("button", { name: "Ask" }).click();
    // Exact match: LocalProvider's own reply echoes the question back as a
    // substring of a much longer message, so a non-exact match would (and
    // did) ambiguously match both the user's own bubble and the reply.
    await expect(page.getByText("What is a primary key?", { exact: true })).toBeVisible();
    await expect(page.getByText(/local \(no-provider\) mode|AI_PROVIDER/i)).toBeVisible({ timeout: 15_000 });

    // Close the panel (Radix Sheet's own close affordance).
    await page.keyboard.press("Escape");
    await expect(page.getByRole("heading", { name: "AI Data Analyst Mentor" })).not.toBeVisible();

    // 3. AI Settings on the Settings page — update a preference and confirm
    // it persists across a reload.
    await page.goto("/settings");
    // Phase 12 made Settings tabbed (Profile/Appearance/AI/Data/System) — AI
    // Settings only renders once its tab is active.
    await page.getByRole("tab", { name: "AI" }).click();
    await expect(page.getByRole("heading", { name: "AI Settings" })).toBeVisible();
    await page.getByLabel("Response style").selectOption("concise");
    await page.reload();
    // Tabs reset to "Profile" (the default) on a fresh mount — re-select "AI".
    await page.getByRole("tab", { name: "AI" }).click();
    await expect(page.getByLabel("Response style")).toHaveValue("concise");
    // restore default so this spec is repeatable against the same dev DB
    await page.getByLabel("Response style").selectOption("balanced");

    // 4. SQL Lab "Ask AI" — Review Query mode on a real query.
    await page.goto("/sql-lab");
    await page.locator(".monaco-editor").click();
    await page.keyboard.press("Control+A");
    await page.keyboard.type("SELECT * FROM orders LIMIT 10;", { delay: 3 });
    await page.getByRole("button", { name: "Ask AI" }).click();
    await expect(page.getByRole("heading", { name: "Ask AI about this query" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Review Query", selected: true })).toBeVisible();
    await page.getByRole("button", { name: "Ask AI to review" }).click();
    await expect(page.getByText(/local \(no-provider\) mode|AI_PROVIDER/i)).toBeVisible({ timeout: 15_000 });

    // 5. Ask the Knowledge Base — a real, grounded RAG retrieval (not
    // dependent on the AI provider at all when nothing relevant matches,
    // and citing a real lesson when it does).
    await page.goto("/ai/knowledge");
    await expect(page.getByRole("heading", { name: "Ask the Knowledge Base" })).toBeVisible();
    await page.getByPlaceholder(/retention and churn/).fill("SQL SELECT statement filtering rows with WHERE");
    await page.getByRole("button", { name: "Ask" }).click();
    await expect(page.getByText("Sources")).toBeVisible({ timeout: 15_000 });

    // 6. Learning Planner explanation — narrates the real, already-generated
    // 7-day plan (generating one first if this DB doesn't have one yet).
    await page.goto("/interview/plan");
    const planButton = page.getByRole("button", { name: /Generate My 7-Day Plan|Regenerate Plan/ });
    await planButton.click();
    await expect(page.getByText("Day 1:")).toBeVisible();
    await page.getByRole("button", { name: "Explain with AI" }).click();
    await expect(page.getByText(/^Why:/).first()).toBeVisible({ timeout: 15_000 });
  });
});
