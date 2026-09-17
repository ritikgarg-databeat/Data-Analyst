import type { CaseCategory, CaseDifficulty, CaseStage } from "@data-analyst-lab/shared";

/** Canonical order + human labels for the 8 Case categories. */
export const CASE_CATEGORY_ORDER: CaseCategory[] = [
  "BUSINESS_ANALYTICS",
  "PRODUCT_ANALYTICS",
  "CUSTOMER_ANALYTICS",
  "MARKETING_ANALYTICS",
  "OPERATIONS",
  "EXPERIMENTATION",
  "DATA_QUALITY",
  "DATA_ARCHITECTURE",
];

export const CASE_CATEGORY_LABELS: Record<CaseCategory, string> = {
  BUSINESS_ANALYTICS: "Business Analytics",
  PRODUCT_ANALYTICS: "Product Analytics",
  CUSTOMER_ANALYTICS: "Customer Analytics",
  MARKETING_ANALYTICS: "Marketing Analytics",
  OPERATIONS: "Operations",
  EXPERIMENTATION: "Experimentation",
  DATA_QUALITY: "Data Quality",
  DATA_ARCHITECTURE: "Data Architecture",
};

/** Canonical order + human labels for the 4 Case difficulties. */
export const CASE_DIFFICULTY_ORDER: CaseDifficulty[] = ["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"];

export const CASE_DIFFICULTY_LABELS: Record<CaseDifficulty, string> = {
  BEGINNER: "Beginner",
  INTERMEDIATE: "Intermediate",
  ADVANCED: "Advanced",
  EXPERT: "Expert",
};

/** All 10 possible granular Case stages, in canonical flow order. A given
 * Case only uses a subset of these (see `case.stages`). */
export const CASE_STAGE_ORDER: CaseStage[] = [
  "UNDERSTAND",
  "CLARIFY",
  "FRAME",
  "EXPLORE",
  "ANALYZE",
  "VALIDATE",
  "INSIGHTS",
  "RECOMMEND",
  "COMMUNICATE",
  "SUBMIT",
];

export const CASE_STAGE_LABELS: Record<CaseStage, string> = {
  UNDERSTAND: "Understand",
  CLARIFY: "Clarify",
  FRAME: "Frame",
  EXPLORE: "Explore",
  ANALYZE: "Analyze",
  VALIDATE: "Validate",
  INSIGHTS: "Insights",
  RECOMMEND: "Recommend",
  COMMUNICATE: "Communicate",
  SUBMIT: "Submit",
};
