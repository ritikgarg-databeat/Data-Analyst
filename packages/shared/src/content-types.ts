/**
 * Content file contract (Phase 2).
 *
 * Lesson and exercise content lives in YAML files under content/lessons/**
 * and content/exercises/** — never hard-coded into React components or the
 * database. These types are the TypeScript mirror of the Pydantic models in
 * apps/api/app/content/schema.py, which is the actual validation source of
 * truth (see `apps/api/app/content/validate.py`). Keep the two in sync by
 * hand — see docs/architecture.md "Content pipeline".
 *
 * The database stores structure + progress; content/ stores the authored
 * material; `apps/api/app/content/sync.py` reconciles the two.
 */

import type { ExerciseType } from "./types";

// ---------------------------------------------------------------------------
// Content blocks — the lesson body is a list of these, never a single blob.
// ---------------------------------------------------------------------------

export type CalloutVariant = "important" | "tip" | "warning" | "interview_tip" | "common_mistake";

export type CodeLanguage = "sql" | "python" | "javascript" | "yaml" | "json" | "text";

export interface TextBlock {
  type: "text";
  body: string; // markdown-formatted (bold/links/lists), rendered inline
}

export interface HeadingBlock {
  type: "heading";
  text: string;
  level?: 2 | 3; // defaults to 2
}

export interface CalloutBlock {
  type: "callout";
  variant: CalloutVariant;
  title?: string;
  body: string;
}

export interface CodeBlock {
  type: "code";
  language: CodeLanguage;
  code: string;
  caption?: string;
}

export interface OutputBlock {
  type: "output";
  body: string;
  caption?: string;
}

export interface TableBlock {
  type: "table";
  headers: string[];
  rows: string[][];
  caption?: string;
}

export interface FormulaBlock {
  type: "formula";
  expression: string; // plain-text / simple notation, e.g. "stddev = sqrt(variance)"
  description?: string;
}

export interface ImageBlock {
  type: "image";
  src: string;
  alt: string;
  caption?: string;
}

export interface ExampleBlock {
  type: "example";
  title: string;
  body: string;
  code?: string;
  language?: CodeLanguage;
}

export interface QuestionBlock {
  type: "question";
  prompt: string;
  choices: string[];
  correct_index: number;
  explanation: string;
}

export interface ChecklistBlock {
  type: "checklist";
  title?: string;
  items: string[];
}

export interface ComparisonBlock {
  type: "comparison";
  title: string;
  columns: string[];
  rows: string[][];
}

export type ContentBlock =
  | TextBlock
  | HeadingBlock
  | CalloutBlock
  | CodeBlock
  | OutputBlock
  | TableBlock
  | FormulaBlock
  | ImageBlock
  | ExampleBlock
  | QuestionBlock
  | ChecklistBlock
  | ComparisonBlock;

// ---------------------------------------------------------------------------
// Lesson content file (content/lessons/<domain>/<module>/<lesson>.yaml)
// ---------------------------------------------------------------------------

export type CompletionRuleType = "reading_percent" | "exercise_score" | "assessment_score";

export interface CompletionCriteria {
  type: CompletionRuleType;
  threshold: number; // reading_percent: 0-100 viewed; exercise_score/assessment_score: 0-100 min score
}

export interface InterviewQuestionRef {
  question: string;
  answer: string;
}

export interface ResourceRef {
  title: string;
  url: string;
}

export interface LessonContentFile {
  slug: string;
  module_slug: string;
  title: string;
  description: string;
  content_type?: "READING" | "VIDEO" | "INTERACTIVE" | "EXERCISE" | "QUIZ"; // defaults to READING
  difficulty: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  estimated_minutes: number;
  display_order: number;
  objectives: string[];
  prerequisites?: string[]; // lesson slugs, hard blockers by default
  soft_prerequisites?: string[]; // lesson slugs, recommended not required
  skills?: string[]; // skill slugs
  datasets?: string[]; // dataset slugs
  tags?: string[]; // tag slugs
  related_lessons?: string[]; // lesson slugs
  completion_criteria?: CompletionCriteria; // defaults to {type: reading_percent, threshold: 90}
  key_takeaways: string[];
  common_mistakes?: string[];
  practical_applications?: string[];
  interview_questions?: InterviewQuestionRef[];
  resources?: ResourceRef[];
  blocks: ContentBlock[];
}

// ---------------------------------------------------------------------------
// Exercise content file (content/exercises/<domain>/<exercise>.yaml)
// ---------------------------------------------------------------------------

// ExerciseType lives in ./types (the API contract) — content files and API
// responses use the exact same enum, so it's imported, not redefined here.

/** Whether ExerciseContentFile.correct_answer can be auto-graded server-side. */
export const AUTO_GRADABLE_EXERCISE_TYPES: ExerciseType[] = [
  "MULTIPLE_CHOICE",
  "TRUE_FALSE",
  "SHORT_ANSWER",
];

export interface ExerciseContentFile {
  slug: string;
  lesson_slug?: string; // optional — standalone exercises are allowed
  skill?: string; // skill slug this exercise primarily targets
  dataset?: string; // dataset slug this exercise references
  title: string;
  description: string;
  exercise_type: ExerciseType;
  difficulty: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  points: number;
  tags?: string[];
  prompt: string;
  choices?: string[]; // MULTIPLE_CHOICE / TRUE_FALSE
  correct_answer?: string; // MULTIPLE_CHOICE (exact choice text) / TRUE_FALSE ("true"|"false") / SHORT_ANSWER (expected text, case-insensitive contains-match)
  hints?: string[]; // progressively more revealing, shown one at a time
  solution?: string;
  explanation: string;

  // --- SQL exercises only (exercise_type === "SQL") ---
  // (business_context is also reused as the business-framing paragraph for
  // BUSINESS_REASONING/DATA_INTERPRETATION case-study exercises — Phase 6.)
  business_context?: string;
  sql_tables?: string[]; // tables to surface in the schema explorer; empty/absent = all
  sql_starter_query?: string;
  sql_solution_query?: string; // never sent to the client — see GET /sql/exercises/{slug}
  sql_row_order_matters?: boolean;
  sql_numeric_tolerance?: number;
  sql_hidden_tests?: SqlHiddenTestSpec[];

  // --- PYTHON exercises only (exercise_type === "PYTHON") ---
  python_datasets?: string[]; // dataset files to pre-load as DataFrames; empty/absent = all files in `dataset`
  python_starter_code?: string;
  python_solution_code?: string; // never sent to the client — see GET /python/exercises/{slug}
  python_result_variable?: string; // default "result" — the variable both student and solution code must define
  python_row_order_matters?: boolean;
  python_numeric_tolerance?: number;
  python_hidden_tests?: PythonHiddenTestSpec[];

  // --- DBT exercises only (exercise_type === "DBT", Phase 7) ---
  // Graded by real execution: the submitted SQL is written into the real
  // dbt project and `dbt build --select` actually runs — see
  // apps/api/app/services/dbt_exercise_service.py.
  dbt_model_name?: string;
  dbt_starter_sql?: string;
  dbt_schema_yml?: string; // never sent to the client — see GET /dbt/exercises/{slug}

  // --- Case-study / rubric-scored exercises (any exercise_type, Phase 6) ---
  // `business_context` above doubles as the case's business framing.
  stakeholder?: string;
  constraints?: string[];
  expected_deliverables?: string[];
  rubric?: RubricCriterionSpec[];
}

/** One self-assessed evaluation criterion (spec section 46) — shown to the
 * learner before they answer (it's evaluation guidance, not the solution).
 * See apps/api/app/services/grading.py. */
export interface RubricCriterionSpec {
  criterion: string;
  points: number;
}

/** One extra, exercise-authored edge-case check beyond the automatic full-result
 * comparison against sql_solution_query — see docs/architecture.md#sql-lab-phase-3. */
export interface SqlHiddenTestSpec {
  name: string;
  query: string;
  key_columns: number;
}

/** A Python snippet (typically an `assert`) run in the *student's own* kernel
 * namespace after correctness passes — see docs/architecture.md#python-lab-phase-4. */
export interface PythonHiddenTestSpec {
  name: string;
  code: string;
}
