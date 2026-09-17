import type { CaseAttemptStatus } from "@data-analyst-lab/shared";

/** What the primary action button on a case card/detail page should say,
 * based on the learner's latest attempt status for that case (`null` means
 * no attempt yet). */
export function caseActionLabel(status: CaseAttemptStatus | null | undefined): "Start Case" | "Continue" | "Review" {
  if (status === "COMPLETED") return "Review";
  if (status === "IN_PROGRESS" || status === "PAUSED" || status === "SUBMITTED" || status === "UNDER_REVIEW") {
    return "Continue";
  }
  return "Start Case";
}

/** Turns a dataset slug like "ecommerce-orders" into "Ecommerce Orders" for
 * display when the full Dataset record hasn't been fetched/isn't available. */
export function titleizeSlug(slug: string): string {
  return slug
    .split(/[-_]/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Deep-link hrefs into the other lab tools for a given selected dataset slug. */
export function labDeepLinks(datasetSlug: string): { sql: string; eda: string; python: string } {
  return {
    sql: `/sql-lab?database=${encodeURIComponent(datasetSlug)}`,
    eda: `/eda?dataset=${encodeURIComponent(datasetSlug)}`,
    python: "/python-lab",
  };
}

/** Formats a whole seconds count as "Xh Ym" / "Ym Zs" for compact display. */
export function formatDuration(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) return "0m";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.round((totalSeconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${Math.round(totalSeconds)}s`;
}
