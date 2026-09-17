import type {
  InterviewMode,
  InterviewQuestionType,
  InterviewSectionType,
  InterviewStatus,
  InterviewTargetType,
} from "@data-analyst-lab/shared";

/** Canonical order + human labels for the 14 interview question types. */
export const INTERVIEW_QUESTION_TYPE_ORDER: InterviewQuestionType[] = [
  "SQL",
  "PYTHON",
  "EXCEL",
  "STATISTICS",
  "AB_TESTING",
  "PRODUCT_ANALYTICS",
  "BUSINESS_ANALYTICS",
  "DATA_INTERPRETATION",
  "DATA_VISUALIZATION",
  "DATA_MODELING",
  "DATA_WAREHOUSING",
  "DBT",
  "DATA_ENGINEERING",
  "BEHAVIORAL",
];

export const INTERVIEW_QUESTION_TYPE_LABELS: Record<InterviewQuestionType, string> = {
  SQL: "SQL",
  PYTHON: "Python",
  EXCEL: "Excel",
  STATISTICS: "Statistics",
  AB_TESTING: "A/B Testing",
  PRODUCT_ANALYTICS: "Product Analytics",
  BUSINESS_ANALYTICS: "Business Analytics",
  DATA_INTERPRETATION: "Data Interpretation",
  DATA_VISUALIZATION: "Data Visualization",
  DATA_MODELING: "Data Modeling",
  DATA_WAREHOUSING: "Data Warehousing",
  DBT: "dbt",
  DATA_ENGINEERING: "Data Engineering",
  BEHAVIORAL: "Behavioral",
};

/** A section/round's type, which can also be "CASE_STUDY" (reuses the Phase
 * 8 Case Study Engine directly rather than an InterviewQuestion round). */
export const INTERVIEW_SECTION_TYPE_LABELS: Record<InterviewSectionType, string> = {
  ...INTERVIEW_QUESTION_TYPE_LABELS,
  CASE_STUDY: "Case Study",
};

export const INTERVIEW_MODE_ORDER: InterviewMode[] = [
  "PRACTICE",
  "TIMED",
  "MOCK",
  "COMPANY_STYLE",
  "WEAKNESS_DRILL",
  "FINAL_READINESS",
];

export const INTERVIEW_MODE_LABELS: Record<InterviewMode, string> = {
  PRACTICE: "Practice",
  TIMED: "Timed Assessment",
  MOCK: "Mock Interview",
  COMPANY_STYLE: "Company-Style Assessment",
  WEAKNESS_DRILL: "Weakness Drill",
  FINAL_READINESS: "Final Readiness Assessment",
};

export const INTERVIEW_MODE_DESCRIPTIONS: Record<InterviewMode, string> = {
  PRACTICE: "No timer pressure — work through a question at your own pace.",
  TIMED: "A single round against a fixed time limit, just like the real thing.",
  MOCK: "A full, multi-round simulated interview loop.",
  COMPANY_STYLE: "A configurable structure modeled on a common interview archetype.",
  WEAKNESS_DRILL: "Automatically targets whichever skill you're currently weakest in.",
  FINAL_READINESS: "Every round type in one sitting — the broadest, most demanding assessment.",
};

export const INTERVIEW_STATUS_LABELS: Record<InterviewStatus, string> = {
  NOT_STARTED: "Not Started",
  IN_PROGRESS: "In Progress",
  PAUSED: "Paused",
  COMPLETED: "Completed",
  ABANDONED: "Abandoned",
};

export const INTERVIEW_TARGET_TYPE_LABELS: Record<InterviewTargetType, string> = {
  QUESTION: "Question",
  CASE: "Case",
  ASSESSMENT: "Assessment",
  INTERVIEW: "Interview",
  SKILL: "Skill",
};

export const INTERVIEW_DIMENSION_ORDER = [
  "Technical Correctness",
  "Analytical Reasoning",
  "Business Understanding",
  "Communication",
  "Problem Solving",
  "Efficiency",
] as const;

function formatSeconds(totalSeconds: number): string {
  const clamped = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(clamped / 60);
  const seconds = clamped % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export { formatSeconds };
