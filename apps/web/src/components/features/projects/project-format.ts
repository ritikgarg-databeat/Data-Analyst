import type { CaseAttemptStatus, ProjectArtifactType } from "@data-analyst-lab/shared";

/** Turns a SCREAMING_SNAKE_CASE enum value into "Title Case" for display, e.g.
 * `BUSINESS_ANALYTICS` -> "Business Analytics". */
export function formatEnumLabel(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0) + word.slice(1).toLowerCase())
    .join(" ");
}

export const PROJECT_STATUS_LABELS: Record<CaseAttemptStatus, string> = {
  NOT_STARTED: "Not started",
  IN_PROGRESS: "In progress",
  PAUSED: "Paused",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under review",
  COMPLETED: "Completed",
};

export const PROJECT_STATUS_VARIANT: Record<
  CaseAttemptStatus,
  "outline" | "warning" | "success" | "secondary" | "default"
> = {
  NOT_STARTED: "outline",
  IN_PROGRESS: "warning",
  PAUSED: "secondary",
  SUBMITTED: "default",
  UNDER_REVIEW: "warning",
  COMPLETED: "success",
};

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/** The 9 fixed Documentation section keys/labels (spec-mandated, in display order). */
export const DOCUMENTATION_SECTIONS: Array<{ key: string; label: string }> = [
  { key: "business_problem", label: "Business Problem" },
  { key: "approach", label: "Approach" },
  { key: "data", label: "Data" },
  { key: "methodology", label: "Methodology" },
  { key: "key_findings", label: "Key Findings" },
  { key: "visualizations", label: "Visualizations" },
  { key: "recommendations", label: "Recommendations" },
  { key: "limitations", label: "Limitations" },
  { key: "next_steps", label: "Next Steps" },
];

/** The 9 fixed Presentation slides, in canonical order (spec-mandated). */
export const PRESENTATION_SLIDES: string[] = [
  "Business Problem",
  "Executive Summary",
  "Key Metrics",
  "Analysis",
  "Key Findings",
  "Recommendation",
  "Expected Impact",
  "Risks & Limitations",
  "Next Steps",
];

export const ARTIFACT_TYPE_LABELS: Record<ProjectArtifactType, string> = {
  SQL_QUERY: "SQL Query",
  PYTHON_EXECUTION: "Python Execution",
  CHART: "Chart",
  DATA_MODEL: "Data Model",
  DBT_MODEL: "dbt Model",
  NOTE: "Note",
};

export const ARTIFACT_TYPES: ProjectArtifactType[] = [
  "SQL_QUERY",
  "PYTHON_EXECUTION",
  "CHART",
  "DATA_MODEL",
  "DBT_MODEL",
  "NOTE",
];
