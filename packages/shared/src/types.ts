/**
 * Shared API contract types for Data Lab.
 * These mirror the FastAPI Pydantic response schemas 1:1 (apps/api/app/schemas).
 * Frontend code should import types from here rather than redefining shapes.
 */

import type { ContentBlock, InterviewQuestionRef, ResourceRef } from "./content-types";

// ---------------------------------------------------------------------------
// Enums (kept as string unions to match Pydantic `str, Enum` JSON output)
// ---------------------------------------------------------------------------

export type DifficultyLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";

export type LessonContentType =
  | "READING"
  | "VIDEO"
  | "INTERACTIVE"
  | "EXERCISE"
  | "QUIZ";

export type LessonProgressStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "COMPLETED";

export type ExerciseType =
  | "MULTIPLE_CHOICE"
  | "TRUE_FALSE"
  | "SHORT_ANSWER"
  | "CODE"
  | "SQL"
  | "PYTHON"
  | "DBT"
  | "BUSINESS_REASONING"
  | "DATA_INTERPRETATION"
  | "MODELING"
  | "INTERVIEW_RESPONSE";

export type ExerciseAttemptStatus =
  | "PENDING"
  | "SUBMITTED" // recorded but not auto-graded (no execution engine yet)
  | "PASSED"
  | "FAILED"
  | "ERROR";

export type AssessmentRetryPolicy = "UNLIMITED" | "LIMITED";

export type AssessmentAttemptStatus = "IN_PROGRESS" | "PASSED" | "FAILED";

export type MasteryLevel = "BEGINNER" | "DEVELOPING" | "INTERMEDIATE" | "STRONG" | "MASTERED";

export type SkillCategory =
  | "SQL"
  | "PYTHON"
  | "STATISTICS"
  | "EXCEL"
  | "DATA_VISUALIZATION"
  | "BUSINESS_ANALYTICS"
  | "PRODUCT_ANALYTICS"
  | "DATA_ENGINEERING"
  | "DATA_WAREHOUSING"
  | "DATA_MODELING"
  | "MACHINE_LEARNING"
  | "INTERVIEW_READINESS";

// ---------------------------------------------------------------------------
// Core entities
// ---------------------------------------------------------------------------

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Domain {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  display_order: number;
  icon: string | null;
  is_active: boolean;
  module_count: number;
  progress_percent: number; // 0-100, average lesson completion across this domain
  created_at: string;
  updated_at: string;
}

export interface Module {
  id: string;
  domain_id: string;
  domain_slug: string;
  slug: string;
  title: string;
  description: string | null;
  difficulty: DifficultyLevel;
  estimated_minutes: number;
  display_order: number;
  is_active: boolean;
  lesson_count: number;
  progress_percent: number; // 0-100
  has_assessment: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  slug: string;
  name: string;
}

export interface Lesson {
  id: string;
  module_id: string;
  module_slug: string;
  domain_slug: string;
  slug: string;
  title: string;
  description: string | null;
  content_type: LessonContentType;
  difficulty: DifficultyLevel;
  estimated_minutes: number;
  display_order: number;
  content_reference: string | null;
  is_active: boolean;
  tags: Tag[];
  skills: Skill[];
  created_at: string;
  updated_at: string;
}

/** Lesson plus the current user's progress/lock state — used in list views. */
export interface LessonWithProgress extends Lesson {
  status: LessonProgressStatus;
  progress_percent: number;
  is_locked: boolean;
}

export interface Skill {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  category: SkillCategory;
  target_level: DifficultyLevel;
  created_at: string;
  updated_at: string;
}

export interface UserSkill {
  user_id: string;
  skill_id: string;
  skill: Skill;
  mastery_score: number; // 0-100
  mastery_level: MasteryLevel;
  confidence_score: number; // 0-100
  questions_attempted: number;
  questions_correct: number;
  last_practiced_at: string | null;
  updated_at: string;
}

export interface LessonProgress {
  user_id: string;
  lesson_id: string;
  status: LessonProgressStatus;
  progress_percent: number;
  started_at: string | null;
  completed_at: string | null;
  last_accessed_at: string | null;
  time_spent_seconds: number;
  last_position: string | null;
  exercises_completed: number;
}

export interface Exercise {
  id: string;
  lesson_id: string | null;
  skill_id: string | null;
  skill_slug: string | null;
  dataset_id: string | null;
  dataset_slug: string | null;
  slug: string;
  title: string;
  description: string | null;
  exercise_type: ExerciseType;
  difficulty: DifficultyLevel;
  points: number;
  display_order: number;
  content_reference: string | null;
  is_active: boolean;
  tags: Tag[];
}

export interface RubricCriterion {
  criterion: string;
  points: number;
}

/** Exercise content for attempting — deliberately excludes correct_answer/solution. */
export interface ExerciseContent extends Exercise {
  prompt: string;
  choices: string[] | null;
  hint_count: number;
  best_attempt: ExerciseAttempt | null;
  attempt_count: number;
  // Phase 6: case-framing + rubric fields, populated only for case-study exercises.
  business_context: string | null;
  stakeholder: string | null;
  constraints: string[];
  expected_deliverables: string[];
  rubric: RubricCriterion[];
}

export interface ExerciseAttempt {
  id: string;
  user_id: string;
  exercise_id: string;
  status: ExerciseAttemptStatus;
  score: number | null;
  submitted_answer: string | null;
  hints_used: number;
  solution_revealed: boolean;
  execution_time_ms: number | null;
  attempted_at: string;
}

export interface SubmitExerciseAttemptRequest {
  submitted_answer: string;
  /** Only meaningful for non-auto-gradable types; a self-assessment 0-100. */
  self_reported_score?: number;
  /** Which rubric criteria (by `criterion` string) the learner self-assessed
   * their answer as satisfying — only meaningful when the exercise has a `rubric`. */
  rubric_selections?: string[];
}

export interface SubmitExerciseAttemptResponse {
  attempt: ExerciseAttempt;
  is_auto_graded: boolean;
  explanation: string | null;
  correct_answer: string | null; // only populated once graded/revealed
}

export interface RevealHintResponse {
  hint_index: number;
  hint: string;
  hints_remaining: number;
}

export interface RevealSolutionResponse {
  solution: string | null;
  explanation: string;
}

export type DatasetSourceType = "LOCAL" | "KAGGLE" | "GENERATED" | "PUBLIC_API" | "OTHER";
export type DatasetStatus = "AVAILABLE" | "IMPORTING" | "PROFILING" | "READY" | "FAILED" | "ARCHIVED";

export interface DatasetTableSchema {
  id: string;
  table_name: string;
  file_format: string;
  row_count: number | null;
  column_count: number | null;
  size_bytes: number | null;
  grain: string | null;
  display_order: number;
}

export interface Dataset {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  source: string | null;
  source_url: string | null;
  domain: string | null;
  file_path: string | null;
  file_format: string | null;
  row_count: number | null;
  column_count: number | null;
  difficulty: DifficultyLevel;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  // --- Phase 5 (Dataset Hub) ---
  source_type: DatasetSourceType;
  business_domain: string | null;
  license: string | null;
  size_bytes: number | null;
  status: DatasetStatus;
  status_message: string | null;
  fingerprint: string | null;
  version: number;
  imported_at: string | null;
  last_profiled_at: string | null;
  kaggle_ref: string | null;
  tags: string[];
  tables: DatasetTableSchema[];
  sql_ready: boolean;
  python_ready: boolean;
}

// ---------------------------------------------------------------------------
// Lesson content (rendered reader view)
// ---------------------------------------------------------------------------

export interface LessonPrerequisiteRef {
  lesson: Lesson;
  is_hard_blocker: boolean;
  is_completed: boolean;
}

export interface LessonContentResponse {
  lesson: Lesson;
  progress: LessonProgress;
  is_locked: boolean;
  prerequisites: LessonPrerequisiteRef[];
  objectives: string[];
  key_takeaways: string[];
  common_mistakes: string[];
  practical_applications: string[];
  interview_questions: InterviewQuestionRef[];
  resources: ResourceRef[];
  blocks: ContentBlock[];
  exercises: Exercise[];
  datasets: Dataset[];
  related_lessons: Lesson[];
  completion_criteria: { type: string; threshold: number };
  previous_lesson: Lesson | null;
  next_lesson: Lesson | null;
}

export interface UpdateLessonPositionRequest {
  last_position?: string;
  time_spent_delta_seconds?: number;
}

// ---------------------------------------------------------------------------
// Assessments
// ---------------------------------------------------------------------------

export interface Assessment {
  id: string;
  module_id: string;
  module_slug: string;
  slug: string;
  title: string;
  description: string | null;
  time_limit_minutes: number | null;
  passing_score: number;
  retry_policy: AssessmentRetryPolicy;
  max_attempts: number | null;
  question_count: number;
  is_active: boolean;
}

export interface AssessmentAttempt {
  id: string;
  user_id: string;
  assessment_id: string;
  status: AssessmentAttemptStatus;
  score: number | null;
  time_spent_seconds: number;
  started_at: string;
  completed_at: string | null;
}

export interface StartAssessmentResponse {
  attempt: AssessmentAttempt;
  questions: ExerciseContent[];
}

export interface AssessmentAnswerSubmission {
  exercise_id: string;
  submitted_answer: string;
}

export interface SubmitAssessmentRequest {
  answers: AssessmentAnswerSubmission[];
  time_spent_seconds: number;
}

export interface AssessmentAnswerResult {
  exercise_id: string;
  is_correct: boolean | null;
  score: number | null;
  correct_answer: string | null;
  explanation: string;
}

export interface SubmitAssessmentResponse {
  attempt: AssessmentAttempt;
  passed: boolean;
  answers: AssessmentAnswerResult[];
}

// ---------------------------------------------------------------------------
// Aggregate / dashboard shapes
// ---------------------------------------------------------------------------

export interface SkillCategoryOverview {
  category: SkillCategory;
  label: string;
  skill_count: number;
  average_mastery: number; // 0-100
}

export interface ContinueLearningItem {
  lesson: Lesson;
  module_title: string;
  domain_slug: string;
  domain_name: string;
  progress_percent: number;
}

export interface RecentlyCompletedItem {
  lesson: Lesson;
  completed_at: string;
}

export interface WeakArea {
  skill: Skill;
  mastery_score: number;
  reason: string;
}

export interface ActivityDay {
  date: string; // YYYY-MM-DD
  lessons_progressed: number;
  exercises_attempted: number;
}

export interface ProgressSummary {
  overall_progress_percent: number;
  current_level: DifficultyLevel;
  learning_streak_days: number;
  skills_mastered: number;
  total_skills: number;
  continue_learning: ContinueLearningItem[];
  recently_completed: RecentlyCompletedItem[];
  weak_areas: WeakArea[];
  activity: ActivityDay[];
  skill_overview: SkillCategoryOverview[];
}

export interface RecommendationItem {
  lesson: Lesson;
  reason:
    | "incomplete_prerequisite"
    | "next_in_module"
    | "weak_skill"
    | "unfinished_lesson"
    | "review";
  explanation: string;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export type SearchResultKind =
  | "domain"
  | "module"
  | "lesson"
  | "skill"
  | "exercise"
  | "case"
  | "project"
  | "interview_question"
  | "metric";

export interface SearchResultItem {
  kind: SearchResultKind;
  id: string;
  slug: string;
  title: string;
  description: string | null;
  url_path: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}

// ---------------------------------------------------------------------------
// Requests
// ---------------------------------------------------------------------------

export interface UpdateUserProfileRequest {
  name?: string;
}

export interface UpsertLessonProgressRequest {
  status: LessonProgressStatus;
  progress_percent: number;
}

export interface CreateDomainRequest {
  slug: string;
  name: string;
  description?: string;
  icon?: string;
  display_order?: number;
}
export type UpdateDomainRequest = Partial<CreateDomainRequest> & { is_active?: boolean };

export interface CreateModuleRequest {
  domain_id: string;
  slug: string;
  title: string;
  description?: string;
  difficulty?: DifficultyLevel;
  estimated_minutes?: number;
  display_order?: number;
}
export type UpdateModuleRequest = Partial<Omit<CreateModuleRequest, "domain_id">> & {
  domain_id?: string;
  is_active?: boolean;
};

export interface CreateSkillRequest {
  slug: string;
  name: string;
  description?: string;
  category: SkillCategory;
  target_level?: DifficultyLevel;
}
export type UpdateSkillRequest = Partial<CreateSkillRequest>;

export interface CreateTagRequest {
  slug: string;
  name: string;
}
export type UpdateTagRequest = Partial<CreateTagRequest>;

/** Lessons/exercises are content-file-owned — admin can only reorder/activate, not edit body content. */
export interface UpdateLessonAdminRequest {
  is_active?: boolean;
  display_order?: number;
}
export interface UpdateExerciseAdminRequest {
  is_active?: boolean;
  display_order?: number;
}

// ---------------------------------------------------------------------------
// Envelopes / errors
// ---------------------------------------------------------------------------

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  };
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthStatus {
  status: "ok";
  version: string;
  environment: string;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// SQL Lab
// ---------------------------------------------------------------------------

export interface SqlEngineInfo {
  name: string;
  label: string;
  is_available: boolean;
  reason: string | null;
}

export interface SqlDatabaseInfo {
  name: string;
  label: string;
  engine: string;
  description: string | null;
  table_count: number;
}

export interface SqlTableSummary {
  table_name: string;
  grain: string | null;
  row_count: number | null;
  column_count: number | null;
}

export interface SqlColumnInfo {
  name: string;
  type: string;
}

export interface SqlTableColumn {
  name: string;
  type: string;
  nullable: boolean;
}

export interface SqlTableSchema {
  table_name: string;
  columns: SqlTableColumn[];
  row_count: number | null;
}

export interface SqlTablePreview {
  table_name: string;
  columns: SqlColumnInfo[];
  rows: unknown[][];
  row_count: number;
  column_count: number;
  sample_row_count: number;
  null_counts: Record<string, number>;
}

export interface SqlErrorInfo {
  message: string;
  hint: string | null;
}

export interface SqlExecutionResultSchema {
  status: "success" | "error" | string;
  engine: string;
  columns: SqlColumnInfo[];
  rows: unknown[][];
  row_count: number;
  truncated: boolean;
  execution_time_ms: number;
  error: SqlErrorInfo | null;
  metadata: Record<string, unknown>;
}

export interface ExecuteSqlRequest {
  engine: string;
  database: string;
  query: string;
}

export interface SqlQueryHistoryItem {
  id: string;
  engine: string;
  database: string;
  query: string;
  status: string;
  row_count: number | null;
  execution_time_ms: number | null;
  error_message: string | null;
  executed_at: string;
}

export interface SqlWorkspaceSchema {
  id: string;
  name: string;
  engine: string;
  database: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSqlWorkspaceRequest {
  name: string;
  engine?: string;
  database: string;
}

export interface SqlSavedQuerySchema {
  id: string;
  workspace_id: string | null;
  title: string;
  description: string | null;
  query: string;
  engine: string;
  database: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateSqlSavedQueryRequest {
  title: string;
  description?: string;
  query: string;
  engine: string;
  database: string;
  workspace_id?: string;
  tags?: string[];
}

export interface UpdateSqlSavedQueryRequest {
  title?: string;
  description?: string;
  query?: string;
  workspace_id?: string;
  tags?: string[];
}

// --- SQL exercises ---

/** SQL-specific exercise content — schema/business context/starter query.
 * Never includes the solution query or hidden tests. */
export interface SqlExerciseContent {
  business_context: string | null;
  dataset: string;
  tables: SqlTableSummary[];
  starter_query: string | null;
  hint_count: number;
}

export interface SubmitSqlExerciseRequest {
  submitted_query: string;
}

export interface SqlTestOutcome {
  name: string;
  passed: boolean;
  is_hidden: boolean;
  message: string;
}

export interface SubmitSqlExerciseResponse {
  attempt_id: string;
  status: string;
  score: number | null;
  passed: boolean;
  test_outcomes: SqlTestOutcome[];
  result: SqlExecutionResultSchema;
  explanation: string | null;
}

// ---------------------------------------------------------------------------
// Python Lab
// ---------------------------------------------------------------------------

export interface DataFrameColumnSchema {
  name: string;
  dtype: string;
  null_count: number;
  unique_count: number;
}

export interface DataFrameSummarySchema {
  row_count: number;
  column_count: number;
  columns: DataFrameColumnSchema[];
  preview_rows: unknown[][];
  preview_row_count: number;
  truncated: boolean;
  memory_usage_bytes: number | null;
}

export interface PythonVariableSchema {
  name: string;
  type_name: string;
  preview: string;
  dataframe: DataFrameSummarySchema | null;
  shape: number[] | null;
  value: unknown;
}

export interface ChartOutputSchema {
  kind: string;
  format: string;
  data: string;
  title: string | null;
}

export interface PythonErrorSchema {
  error_type: string;
  message: string;
  line: number | null;
  traceback_text: string;
  hint: string | null;
}

export interface PythonExecutionResultSchema {
  status: string;
  stdout: string;
  stdout_truncated: boolean;
  display_value: PythonVariableSchema | null;
  variables: PythonVariableSchema[];
  charts: ChartOutputSchema[];
  error: PythonErrorSchema | null;
  execution_time_ms: number;
}

// --- Runtimes ---

export interface PythonRuntimeSchema {
  id: string;
  status: string;
  workspace_id: string | null;
  timeout_seconds: number;
  error_message: string | null;
  created_at: string;
  last_used_at: string;
}

export interface ExecutePythonRequest {
  code: string;
  workspace_id?: string;
}

export interface PythonAvailabilitySchema {
  available: boolean;
  reason: string | null;
}

// --- Datasets ---

export interface PythonDatasetFileSchema {
  dataset_slug: string;
  dataset_name: string;
  label: string;
  container_path: string;
  file_format: string;
  grain: string | null;
  row_count: number | null;
  column_count: number | null;
  suggested_code: string;
}

// --- History ---

export interface PythonHistoryItemSchema {
  id: string;
  workspace_id: string | null;
  code: string;
  status: string;
  error_message: string | null;
  execution_time_ms: number | null;
  executed_at: string;
}

// --- Workspaces & cells ---

export interface PythonCellSchema {
  id: string;
  workspace_id: string;
  display_order: number;
  code: string;
  last_result: PythonExecutionResultSchema | null;
  last_executed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PythonWorkspaceSchema {
  id: string;
  name: string;
  selected_dataset: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreatePythonWorkspaceRequest {
  name: string;
  selected_dataset?: string;
  starter_code?: string;
}

export interface UpdatePythonWorkspaceRequest {
  name?: string;
  selected_dataset?: string;
  notes?: string;
}

export interface CreatePythonCellRequest {
  code?: string;
}

export interface UpdatePythonCellRequest {
  code?: string;
  display_order?: number;
}

export interface RecordCellResultRequest {
  result: PythonExecutionResultSchema;
}

// --- Python exercises ---

/** Python-specific exercise content — business context/dataset files/starter code.
 * Never includes the solution code or hidden tests. */
export interface PythonExerciseContent {
  business_context: string | null;
  dataset: string | null;
  dataset_files: PythonDatasetFileSchema[];
  starter_code: string | null;
  result_variable: string;
  hint_count: number;
}

export interface SubmitPythonExerciseRequest {
  submitted_code: string;
}

export interface PythonTestOutcomeSchema {
  name: string;
  passed: boolean;
  is_hidden: boolean;
  message: string;
}

export interface SubmitPythonExerciseResponse {
  attempt_id: string;
  status: string;
  score: number | null;
  passed: boolean;
  test_outcomes: PythonTestOutcomeSchema[];
  result: PythonExecutionResultSchema;
  explanation: string | null;
}

// ---------------------------------------------------------------------------
// Dataset Hub (Phase 5)
// ---------------------------------------------------------------------------

export interface LocalImportForm {
  name: string;
  description?: string;
  business_domain?: string;
  difficulty?: DifficultyLevel;
  tags?: string[];
}

export interface SchemaColumnSchema {
  column_name: string;
  inferred_sql_type: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
}

export interface TableSchemaResponse {
  table_name: string;
  columns: SchemaColumnSchema[];
  row_count: number;
  generated_at: string;
}

export interface ColumnProfileSchema {
  column_name: string;
  data_type: string;
  inferred_sql_type: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  min_value: string | null;
  max_value: string | null;
  mean: number | null;
  median: number | null;
  std_dev: number | null;
  quantiles: Record<string, number | null> | null;
  zero_count: number | null;
  negative_count: number | null;
  outlier_count: number | null;
  outlier_method: string | null;
  top_values: { value: string; count: number; percentage: number }[] | null;
  sample_values: unknown[] | null;
  min_length: number | null;
  max_length: number | null;
  avg_length: number | null;
  extra: Record<string, unknown> | null;
}

export interface TableProfileSchema {
  table_name: string;
  row_count: number;
  column_count: number;
  size_bytes: number | null;
  duplicate_row_count: number;
  generated_at: string;
  columns: ColumnProfileSchema[];
}

export interface DatasetProfileResponse {
  dataset_id: string;
  tables: TableProfileSchema[];
}

export interface QualityIssueSchema {
  type: string;
  detail: string;
  severity: "low" | "medium" | "high";
  column: string | null;
}

export interface QualityReportSchema {
  table_name: string;
  overall_score: number;
  completeness_score: number;
  uniqueness_score: number;
  validity_score: number;
  consistency_score: number;
  duplicate_row_count: number;
  issues: QualityIssueSchema[];
  methodology: string;
  generated_at: string;
}

export interface DatasetQualityResponse {
  dataset_id: string;
  tables: QualityReportSchema[];
}

export interface DuplicatesResponse {
  table_name: string;
  duplicate_row_count: number;
  sample_rows: unknown[][];
  columns: string[];
}

export interface OutliersResponse {
  table_name: string;
  column_name: string;
  method: string;
  outlier_count: number;
  lower_bound: number | null;
  upper_bound: number | null;
  sample_rows: unknown[][];
  columns: string[];
}

export interface DatasetRelationshipSchema {
  id: string;
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship_type: string;
}

export interface CreateRelationshipRequest {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship_type?: string;
}

export interface DatasetNoteSchema {
  id: string;
  table_name: string | null;
  column_name: string | null;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface CreateNoteRequest {
  body: string;
  table_name?: string | null;
  column_name?: string | null;
}

export interface DatasetVersionSchema {
  id: string;
  version: number;
  fingerprint: string;
  row_count: number | null;
  column_count: number | null;
  size_bytes: number | null;
  change_summary: string | null;
  created_at: string;
}

export interface DatasetUsageSchema {
  sql_exercises: number;
  python_exercises: number;
  other_exercises: number;
  eda_workspaces: number;
  charts: number;
  projects: number;
}

export interface CorrelationResponse {
  table_name: string;
  method: string;
  columns: string[];
  matrix: (number | null)[][];
  note: string;
}

export interface DistributionBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface DistributionResponse {
  table_name: string;
  column_name: string;
  bins: DistributionBin[];
  mean: number | null;
  median: number | null;
  std_dev: number | null;
  quantiles: Record<string, number> | null;
  skewness: number | null;
}

export interface TimeSeriesPoint {
  period: string;
  value: number | null;
  rolling_avg: number | null;
}

export interface TimeSeriesResponse {
  table_name: string;
  date_column: string;
  metric_column: string;
  aggregation: string;
  granularity: string;
  points: TimeSeriesPoint[];
}

// ---------------------------------------------------------------------------
// Product analytics: funnel & cohort retention (Phase 6)
// ---------------------------------------------------------------------------

export interface FunnelStep {
  step: string;
  users: number;
  conversion_from_previous: number;
  conversion_from_start: number;
  drop_off: number;
}

export interface FunnelResponse {
  table_name: string;
  steps: FunnelStep[];
  methodology: string;
}

export interface CohortRow {
  cohort: string;
  cohort_size: number;
  retention_pct: (number | null)[];
}

export interface CohortRetentionResponse {
  table_name: string;
  granularity: string;
  periods: number;
  cohorts: CohortRow[];
}

export interface RawColumnSchema {
  column_name: string;
  sql_type: string;
}

export interface RawSchemaResponse {
  table_name: string;
  columns: RawColumnSchema[];
}

// ---------------------------------------------------------------------------
// Kaggle (Phase 5)
// ---------------------------------------------------------------------------

export interface KaggleStatusResponse {
  configured: boolean;
  reason: string | null;
  setup_instructions: string | null;
}

export interface KaggleDatasetSummary {
  ref: string;
  title: string;
  subtitle: string | null;
  owner: string | null;
  url: string | null;
  size_bytes: number | null;
  last_updated: string | null;
  download_count: number | null;
  vote_count: number | null;
  usability_rating: number | null;
  license_name: string | null;
  tags: string[];
}

export interface KaggleSearchResponse {
  query: string;
  page: number;
  results: KaggleDatasetSummary[];
}

export interface KaggleFileSummary {
  name: string;
  size_bytes: number | null;
  creation_date: string | null;
}

export interface KaggleFilesResponse {
  ref: string;
  files: KaggleFileSummary[];
}

export interface KaggleImportRequest {
  name: string;
  files: string[];
  description?: string;
  business_domain?: string;
  tags?: string[];
}

// ---------------------------------------------------------------------------
// EDA workspaces (Phase 5)
// ---------------------------------------------------------------------------

export interface EdaFindingSchema {
  id: string;
  observation: string;
  evidence: string | null;
  business_implication: string | null;
  recommended_action: string | null;
  created_at: string;
}

export interface CreateFindingRequest {
  observation: string;
  evidence?: string;
  business_implication?: string;
  recommended_action?: string;
}

export interface EdaWorkspaceSchema {
  id: string;
  dataset_id: string;
  name: string;
  table_name: string | null;
  state: Record<string, unknown> | null;
  overview: EdaOverview | null;
  created_at: string;
  updated_at: string;
  findings: EdaFindingSchema[];
}

export interface CreateEdaWorkspaceRequest {
  dataset_id: string;
  name: string;
  table_name?: string;
}

export interface UpdateEdaWorkspaceRequest {
  name?: string;
  table_name?: string;
  state?: Record<string, unknown>;
}

export interface MissingnessEntry {
  column: string;
  null_percentage: number;
}

export interface DistributionSummary {
  column: string;
  mean: number | null;
  median: number | null;
  std_dev: number | null;
  quantiles: Record<string, number> | null;
}

export interface CategoricalSummary {
  column: string;
  top_values: { value: string; count: number; percentage: number }[];
}

export interface CorrelationPair {
  column_a: string;
  column_b: string;
  correlation: number;
}

export interface DateTrendSummary {
  column: string;
  min_date: string | null;
  max_date: string | null;
  missing_calendar_days: number | null;
}

export interface OutlierSummary {
  column: string;
  outlier_count: number;
  method: string;
}

export interface EdaOverview {
  table_name: string;
  row_count: number;
  column_count: number;
  duplicate_row_count: number;
  missingness: MissingnessEntry[];
  distributions: DistributionSummary[];
  categorical_summaries: CategoricalSummary[];
  correlations: CorrelationPair[];
  date_trends: DateTrendSummary[];
  outliers: OutlierSummary[];
  generated_at: string;
}

export interface EdaQuestion {
  question: string;
  category: string;
}

// ---------------------------------------------------------------------------
// Charts (Phase 5)
// ---------------------------------------------------------------------------

export type ChartType = "bar" | "line" | "scatter" | "histogram" | "box" | "heatmap" | "pie" | "donut";

export interface ChartFilter {
  column: string;
  operator: "=" | "!=" | ">" | "<" | ">=" | "<=";
  value: unknown;
}

export interface ChartConfig {
  x?: string | null;
  y?: string | null;
  aggregation?: string | null;
  color?: string | null;
  filters?: ChartFilter[];
  sort?: "x_asc" | "x_desc" | "y_asc" | "y_desc" | null;
  bins?: number | null;
  date_granularity?: "day" | "week" | "month" | "quarter" | "year" | null;
  title?: string | null;
  x_label?: string | null;
  y_label?: string | null;
}

export interface Chart {
  id: string;
  dataset_id: string;
  table_name: string;
  workspace_id: string | null;
  title: string;
  chart_type: string;
  config: ChartConfig;
  insight_observation: string | null;
  insight_why_it_matters: string | null;
  insight_recommended_action: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateChartRequest {
  dataset_id: string;
  table_name: string;
  chart_type: string;
  title: string;
  config: ChartConfig;
  workspace_id?: string | null;
}

export interface UpdateChartRequest {
  title?: string;
  chart_type?: string;
  config?: ChartConfig;
  insight_observation?: string;
  insight_why_it_matters?: string;
  insight_recommended_action?: string;
}

export interface ChartSeries {
  name: string;
  y_values: unknown[];
  color_values?: unknown[];
}

export interface ChartDataResponse {
  chart_type: string;
  x_values: unknown[];
  series: ChartSeries[];
  warnings: string[];
  recommendation: string | null;
}

export interface RecommendRequest {
  x_type: "numeric" | "categorical" | "datetime";
  y_type?: "numeric" | "categorical" | "datetime" | null;
}

export interface RecommendResponse {
  chart_type: string;
  reason: string;
}

// ---------------------------------------------------------------------------
// Projects — the Phase 5 shell extended in place by the Phase 8 Project Engine
// ---------------------------------------------------------------------------

export interface ProjectMilestone {
  id: string;
  title: string;
  description: string | null;
  display_order: number;
  is_completed: boolean;
  completed_at: string | null;
}

export type ProjectArtifactType = "SQL_QUERY" | "PYTHON_EXECUTION" | "CHART" | "DATA_MODEL" | "DBT_MODEL" | "NOTE";

export interface ProjectArtifact {
  id: string;
  artifact_type: ProjectArtifactType;
  ref_id: string | null;
  label: string;
  snapshot: string | null;
  notes: string | null;
  created_at: string;
}

export interface ProjectDataset {
  id: string;
  dataset_id: string;
  reason: string | null;
}

export interface Project {
  id: string;
  dataset_id: string | null;
  template_id: string | null;
  data_model_id: string | null;
  name: string;
  description: string | null;
  notes: string | null;
  status: CaseAttemptStatus;
  objective: string | null;
  business_context: string | null;
  requirements: string[];
  dbt_model_refs: string[];
  documentation: Record<string, string>;
  presentation: Array<Record<string, string>>;
  rubric_selections: Record<string, string[]>;
  score: RubricScoreResult | null;
  reflection: ReflectionPayload | null;
  started_at: string | null;
  submitted_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  milestones: ProjectMilestone[];
  artifacts: ProjectArtifact[];
  project_datasets: ProjectDataset[];
}

export interface CreateProjectRequest {
  name: string;
  dataset_id?: string;
  description?: string;
}

export interface CreateProjectFromDatasetRequest {
  name?: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  notes?: string;
  status?: CaseAttemptStatus;
}

export interface ProjectTemplateMilestoneSpec {
  title: string;
  description: string | null;
}

export interface ProjectTemplate {
  id: string;
  slug: string;
  title: string;
  category: CaseCategory;
  business_context: string | null;
  objective: string;
  requirements: string[];
  suggested_datasets: string[];
  milestones: ProjectTemplateMilestoneSpec[];
  required_skills: string[];
  rubric: RubricCategory[];
  learning_objectives: string[];
  estimated_hours: number | null;
  tags: string[];
  version: number;
}

export interface ProjectTemplateAdmin {
  id: string;
  slug: string;
  title: string;
  category: CaseCategory;
  is_active: boolean;
  version: number;
}

export interface UpdateProjectTemplateAdminRequest {
  is_active: boolean;
}

export interface StartProjectFromTemplateRequest {
  template_slug: string;
}

export interface UpdateMilestoneRequest {
  is_completed: boolean;
}

export interface CreateProjectArtifactRequest {
  artifact_type: ProjectArtifactType;
  ref_id?: string | null;
  label: string;
  snapshot?: string | null;
  notes?: string | null;
}

export interface UpdateProjectDocumentationRequest {
  documentation: Record<string, string>;
}

export interface UpdateProjectPresentationRequest {
  presentation: Array<Record<string, string>>;
}

export interface AddProjectDatasetRequest {
  dataset_id: string;
  reason?: string;
}

export interface LinkProjectDataModelRequest {
  data_model_id: string | null;
}

export interface UpdateProjectDbtRefsRequest {
  dbt_model_refs: string[];
}

export interface SubmitProjectRequest {
  rubric_selections: Record<string, string[]>;
}

export interface SaveProjectReflectionRequest {
  reflection: ReflectionPayload;
}

// ---------------------------------------------------------------------------
// Case Study Engine (Phase 8)
// ---------------------------------------------------------------------------

export type CaseCategory =
  | "BUSINESS_ANALYTICS"
  | "PRODUCT_ANALYTICS"
  | "CUSTOMER_ANALYTICS"
  | "MARKETING_ANALYTICS"
  | "OPERATIONS"
  | "EXPERIMENTATION"
  | "DATA_QUALITY"
  | "DATA_ARCHITECTURE";

export type CaseDifficulty = "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "EXPERT";

export type CaseAttemptStatus = "NOT_STARTED" | "IN_PROGRESS" | "PAUSED" | "SUBMITTED" | "UNDER_REVIEW" | "COMPLETED";

export type CaseStage =
  | "UNDERSTAND"
  | "CLARIFY"
  | "FRAME"
  | "EXPLORE"
  | "ANALYZE"
  | "VALIDATE"
  | "INSIGHTS"
  | "RECOMMEND"
  | "COMMUNICATE"
  | "SUBMIT";

export interface RubricCriterion {
  criterion: string;
  points: number;
}

export interface RubricCategory {
  category: string;
  weight: number;
  criteria: RubricCriterion[];
  is_technical: boolean;
}

export interface RubricCategoryScore {
  category: string;
  weight: number;
  earned_points: number;
  total_points: number;
  pct: number;
  is_technical: boolean;
}

export interface CaseFeedback {
  what_went_well: string[];
  what_missed: string[];
  technical_issues: string[];
  business_reasoning_issues: string[];
  communication_issues: string[];
}

export interface RubricScoreResult {
  overall: number;
  categories: RubricCategoryScore[];
  feedback?: CaseFeedback;
}

export interface Case {
  id: string;
  slug: string;
  title: string;
  category: CaseCategory;
  difficulty: CaseDifficulty;
  estimated_minutes: number;
  company_context: string | null;
  stakeholder_name: string;
  stakeholder_role: string;
  problem_statement: string;
  business_context: string | null;
  objective: string;
  initial_information: string | null;
  constraints: string[];
  available_datasets: string[];
  expected_deliverables: string[];
  learning_objectives: string[];
  stages: CaseStage[];
  tags: string[];
  skills: string[];
  rubric: RubricCategory[];
  hint_count: number;
  version: number;
}

export interface CaseListItem {
  case: Case;
  attempt_id: string | null;
  attempt_status: CaseAttemptStatus | null;
  attempt_score: number | null;
}

export interface CaseAdminListItem {
  id: string;
  slug: string;
  title: string;
  category: CaseCategory;
  difficulty: CaseDifficulty;
  is_active: boolean;
  version: number;
}

export interface UpdateCaseAdminRequest {
  is_active: boolean;
}

export interface ProblemFramingPayload {
  problem: string;
  objective: string;
  primary_metric: string;
  scope: string;
  hypotheses: string;
}

export interface RecommendationPayload {
  recommendation: string;
  why: string;
  expected_impact: string;
  risks: string;
  implementation_considerations: string;
  next_steps: string;
}

export interface ExecutiveSummaryPayload {
  problem: string;
  key_findings: string;
  business_impact: string;
  recommendation: string;
  next_steps: string;
}

export interface ReflectionPayload {
  what_learned: string;
  what_difficult: string;
  what_differently: string;
  skill_improved: string;
  what_review: string;
}

export interface CaseSubmissionReadiness {
  problem_framed: boolean;
  data_understood: boolean;
  findings_documented: boolean;
  recommendation_written: boolean;
  executive_summary_written: boolean;
}

export interface CaseAttempt {
  id: string;
  case_id: string;
  case_version_snapshot: number;
  attempt_number: number;
  status: CaseAttemptStatus;
  current_stage: CaseStage | null;
  clarification_questions: string | null;
  problem_framing: ProblemFramingPayload | null;
  selected_dataset_slugs: string[];
  recommendation: RecommendationPayload | null;
  executive_summary: ExecutiveSummaryPayload | null;
  reflection: ReflectionPayload | null;
  hints_used: number;
  solution_revealed: boolean;
  rubric_selections: Record<string, string[]>;
  score: RubricScoreResult | null;
  feedback: CaseFeedback | null;
  time_per_stage_seconds: Record<string, number>;
  started_at: string | null;
  submitted_at: string | null;
  completed_at: string | null;
  last_activity_at: string | null;
  submission_readiness: CaseSubmissionReadiness;
}

export interface UpdateStageRequest {
  stage: CaseStage;
}

export interface SaveClarificationRequest {
  questions: string;
}

export interface SaveFramingRequest {
  framing: ProblemFramingPayload;
}

export interface SaveDatasetSelectionRequest {
  dataset_slugs: string[];
}

export interface SaveRecommendationRequest {
  recommendation: RecommendationPayload;
}

export interface SaveExecutiveSummaryRequest {
  executive_summary: ExecutiveSummaryPayload;
}

export interface RecordStageTimeRequest {
  stage: CaseStage;
  seconds: number;
}

export interface RevealHintResponse {
  hint: string;
  hints_used: number;
}

export interface SubmitCaseAttemptRequest {
  rubric_selections: Record<string, string[]>;
}

export interface SaveReflectionRequest {
  reflection: ReflectionPayload;
}

export interface RevealCaseSolutionResponse {
  summary: string;
  key_insights: string[];
  recommendation: string | null;
  acceptable_alternatives: string[];
}

// ---------------------------------------------------------------------------
// Findings / Hypotheses / Evidence — shared by Cases and Projects (Phase 8)
// ---------------------------------------------------------------------------

export type FindingConfidence = "LOW" | "MEDIUM" | "HIGH";

export type HypothesisStatus = "UNCHECKED" | "INVESTIGATING" | "SUPPORTED" | "REJECTED" | "INCONCLUSIVE";

export type EvidenceType =
  | "SQL_QUERY"
  | "PYTHON_EXECUTION"
  | "CHART"
  | "STATISTIC"
  | "DATASET"
  | "DATA_MODEL"
  | "DBT_MODEL";

export interface Evidence {
  id: string;
  evidence_type: EvidenceType;
  ref_id: string | null;
  label: string;
  snapshot: string | null;
  created_at: string;
}

export interface AddEvidenceRequest {
  evidence_type: EvidenceType;
  ref_id?: string | null;
  label: string;
  snapshot?: string | null;
}

export interface Finding {
  id: string;
  case_attempt_id: string | null;
  project_id: string | null;
  observation: string;
  evidence_text: string | null;
  impact: string | null;
  confidence: FindingConfidence | null;
  related_analysis: string | null;
  display_order: number;
  created_at: string;
  evidence: Evidence[];
}

export interface CreateFindingRequest {
  case_attempt_id?: string;
  project_id?: string;
  observation: string;
  evidence_text?: string;
  impact?: string;
  confidence?: FindingConfidence;
  related_analysis?: string;
}

export interface UpdateFindingRequest {
  observation?: string;
  evidence_text?: string;
  impact?: string;
  confidence?: FindingConfidence;
  related_analysis?: string;
}

export interface Hypothesis {
  id: string;
  case_attempt_id: string | null;
  project_id: string | null;
  statement: string;
  status: HypothesisStatus;
  evidence_text: string | null;
  display_order: number;
  created_at: string;
  evidence: Evidence[];
}

export interface CreateHypothesisRequest {
  case_attempt_id?: string;
  project_id?: string;
  statement: string;
}

export interface UpdateHypothesisRequest {
  statement?: string;
  status?: HypothesisStatus;
  evidence_text?: string;
}

// ---------------------------------------------------------------------------
// Statistics (Phase 6)
// ---------------------------------------------------------------------------

export interface DatasetColumnRef {
  dataset_id: string;
  table_name: string;
  column: string;
}

export interface ConfidenceIntervalSchema {
  level: number;
  lower: number;
  upper: number;
  margin_of_error: number;
}

export interface SummaryStatsRequest {
  values?: number[];
  dataset?: DatasetColumnRef;
  confidence?: number;
}

export interface SummaryStatsResponse {
  count: number;
  mean: number;
  median: number;
  mode: number[];
  min: number;
  max: number;
  range: number;
  variance: number;
  std_dev: number;
  coefficient_of_variation: number | null;
  q1: number;
  q3: number;
  iqr: number;
  percentiles: Record<string, number>;
  skewness: number;
  outlier_count: number;
  outlier_bounds: [number, number];
  mean_confidence_interval: ConfidenceIntervalSchema;
  methodology: string;
}

export type StatTestType =
  | "one_sample_t"
  | "independent_t"
  | "paired_t"
  | "two_proportion_z"
  | "chi_square"
  | "mann_whitney"
  | "anova";

export interface StatTestRequest {
  test_type: StatTestType;
  alpha?: number;
  alternative?: "two-sided" | "less" | "greater";
  sample_a?: number[];
  sample_b?: number[];
  groups?: number[][];
  population_mean?: number;
  successes_a?: number;
  n_a?: number;
  successes_b?: number;
  n_b?: number;
  contingency_table?: number[][];
  dataset_a?: DatasetColumnRef;
  dataset_b?: DatasetColumnRef;
}

export interface TestResultResponse {
  test_type: string;
  test_name: string;
  // Null for a degenerate/zero-variance input (e.g. a constant sample) —
  // scipy/statsmodels return NaN, which serializes to JSON null. A real,
  // routine input a learner would try (pasting the same value a few times).
  statistic: number | null;
  p_value: number | null;
  degrees_of_freedom: number | null;
  alpha: number;
  alternative: string;
  reject_null: boolean;
  interpretation: string;
  assumptions: string[];
  effect_size: number | null;
  effect_size_label: string | null;
}

export interface CorrelationTestRequest {
  x?: number[];
  y?: number[];
  dataset_x?: DatasetColumnRef;
  dataset_y?: DatasetColumnRef;
  method?: "pearson" | "spearman";
  alpha?: number;
}

export interface RegressionRequest {
  features?: Record<string, number[]>;
  y?: number[];
  y_name?: string;
  dataset_id?: string;
  table_name?: string;
  feature_columns?: string[];
  target_column?: string;
}

export interface Coefficient {
  name: string;
  value: number;
  std_error: number;
  t_statistic: number;
  p_value: number;
  confidence_interval_95: [number, number];
  significant: boolean;
}

export interface RegressionResponse {
  formula_description: string;
  intercept: Coefficient;
  coefficients: Coefficient[];
  r_squared: number;
  adjusted_r_squared: number;
  n_observations: number;
  residual_std_error: number;
  interpretation: string;
  multicollinearity_warning: string | null;
}

// ---------------------------------------------------------------------------
// Experimentation (Phase 6)
// ---------------------------------------------------------------------------

export interface SampleSizeRequest {
  baseline_conversion: number;
  expected_uplift_relative: number;
  alpha?: number;
  power?: number;
}

export interface SampleSizeResponse {
  baseline_conversion: number;
  expected_uplift: number;
  absolute_mde: number;
  alpha: number;
  power: number;
  sample_size_per_variant: number;
  total_sample_size: number;
  assumptions: string;
}

export interface PowerRequest {
  baseline_conversion: number;
  sample_size_per_variant: number;
  expected_uplift_relative: number;
  alpha?: number;
}

export interface PowerResponse {
  baseline_conversion: number;
  sample_size_per_variant: number;
  absolute_mde: number;
  alpha: number;
  achieved_power: number;
  assumptions: string;
  interpretation: string;
}

export interface AnalyzeABTestRequest {
  control_users: number;
  control_conversions: number;
  treatment_users: number;
  treatment_conversions: number;
  alpha?: number;
  minimum_practical_effect?: number;
}

export interface AnalyzeABTestResponse {
  control_users: number;
  control_conversions: number;
  treatment_users: number;
  treatment_conversions: number;
  control_rate: number;
  treatment_rate: number;
  absolute_difference: number;
  relative_uplift: number | null;
  confidence_interval_95: [number, number];
  // Null when the pooled-variance term is zero (e.g. both groups have zero
  // conversions) — statsmodels' proportions_ztest returns NaN, which
  // serializes to JSON null. A routine day-one-of-a-test scenario.
  z_statistic: number | null;
  p_value: number | null;
  alpha: number;
  is_statistically_significant: boolean;
  minimum_practical_effect: number | null;
  is_practically_significant: boolean | null;
  verdict: string;
  interpretation: string;
}

export interface SimulateABTestRequest {
  control_rate: number;
  treatment_rate: number;
  sample_size_per_variant: number;
  alpha?: number;
  num_simulations?: number;
  seed?: number;
}

export interface SimulateABTestResponse {
  control_rate: number;
  treatment_rate: number;
  sample_size_per_variant: number;
  alpha: number;
  num_simulations: number;
  seed: number;
  significant_count: number;
  empirical_power: number;
  example_run: Record<string, unknown>;
  interpretation: string;
}

// ---------------------------------------------------------------------------
// Metrics Library (Phase 6)
// ---------------------------------------------------------------------------

export interface MetricInterviewQA {
  question: string;
  answer: string;
}

export interface MetricDefinition {
  id: string;
  slug: string;
  name: string;
  category: string;
  definition: string;
  formula: string | null;
  examples: string[];
  sql_example: string | null;
  python_example: string | null;
  common_mistakes: string[];
  related_metrics: string[];
  business_questions: string[];
  interview_questions: MetricInterviewQA[];
  display_order: number;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Analytics Cases (Phase 6)
// ---------------------------------------------------------------------------

export interface AnalyticsCase extends Exercise {
  prompt: string;
  business_context: string | null;
  stakeholder: string | null;
  constraints: string[];
  expected_deliverables: string[];
  rubric: RubricCriterion[];
}

// ---------------------------------------------------------------------------
// Data Modeling / Architecture / Pipeline (Phase 7) — one shared graph schema
// backs the Data Modeler (DIMENSIONAL), Architecture Diagram Builder
// (ARCHITECTURE), and Pipeline Playground (PIPELINE); see
// apps/api/app/models/data_model.py.
// ---------------------------------------------------------------------------

export type DataModelKind = "DIMENSIONAL" | "ARCHITECTURE" | "PIPELINE";

export type DataModelTableType =
  | "FACT"
  | "DIMENSION"
  | "BRIDGE"
  | "SOURCE"
  | "STORAGE"
  | "WAREHOUSE"
  | "TRANSFORM"
  | "SERVICE"
  | "STREAM"
  | "BI"
  | "OTHER";

export type DataModelRelationshipType =
  | "ONE_TO_ONE"
  | "ONE_TO_MANY"
  | "MANY_TO_ONE"
  | "MANY_TO_MANY"
  | "FLOW"
  | "DEPENDS_ON";

export interface DataModelColumnSchema {
  name: string;
  data_type?: string | null;
  is_primary_key?: boolean;
  is_foreign_key?: boolean;
  references_table?: string | null;
  references_column?: string | null;
}

export interface CreateDataModelRequest {
  name: string;
  description?: string | null;
  model_kind: DataModelKind;
}

export interface UpdateDataModelRequest {
  name?: string | null;
  description?: string | null;
}

export interface DataModelTableSchema {
  id: string;
  name: string;
  table_type: DataModelTableType;
  grain: string | null;
  notes: string | null;
  columns: DataModelColumnSchema[];
  position_x: number;
  position_y: number;
}

export interface DataModelRelationshipSchema {
  id: string;
  from_table_id: string;
  to_table_id: string;
  from_column: string | null;
  to_column: string | null;
  relationship_type: DataModelRelationshipType;
  label: string | null;
}

export interface DataModelSchema {
  id: string;
  name: string;
  description: string | null;
  model_kind: DataModelKind;
  created_at: string;
  updated_at: string;
  tables: DataModelTableSchema[];
  relationships: DataModelRelationshipSchema[];
}

export interface DataModelSummarySchema {
  id: string;
  name: string;
  description: string | null;
  model_kind: DataModelKind;
  created_at: string;
  updated_at: string;
}

export interface SaveTableInput {
  key: string;
  name: string;
  table_type?: DataModelTableType;
  grain?: string | null;
  notes?: string | null;
  columns?: DataModelColumnSchema[];
  position_x?: number;
  position_y?: number;
}

export interface SaveRelationshipInput {
  from_key: string;
  to_key: string;
  from_column?: string | null;
  to_column?: string | null;
  relationship_type?: DataModelRelationshipType;
  label?: string | null;
}

export interface SaveDataModelGraphRequest {
  tables: SaveTableInput[];
  relationships?: SaveRelationshipInput[];
}

export interface ValidationFindingSchema {
  severity: "warning" | "error" | string;
  code: string;
  message: string;
  table_id?: string | null;
  table_name?: string | null;
}

export interface ValidationResultSchema {
  findings: ValidationFindingSchema[];
  error_count: number;
  warning_count: number;
}

// ---------------------------------------------------------------------------
// Data Quality Lab (Phase 7) — rule engine running real checks via DuckDB
// against a dataset's own tables; see apps/api/app/data_quality/engine.py.
// ---------------------------------------------------------------------------

export type DataQualityRuleType =
  | "NOT_NULL"
  | "UNIQUE"
  | "ACCEPTED_VALUES"
  | "RELATIONSHIP"
  | "MIN_MAX"
  | "FRESHNESS"
  | "ROW_COUNT";

export type DataQualityStatus = "PASS" | "FAIL" | "ERROR";

export interface CreateDataQualityRuleRequest {
  dataset_id: string;
  table_name: string;
  column_name?: string | null;
  rule_type: DataQualityRuleType;
  config?: Record<string, unknown>;
  name?: string | null;
}

export interface DataQualityRuleSchema {
  id: string;
  dataset_id: string;
  table_name: string;
  column_name: string | null;
  rule_type: DataQualityRuleType;
  config: Record<string, unknown>;
  name: string | null;
  created_at: string;
}

export interface DataQualityRunSchema {
  id: string;
  rule_id: string;
  status: DataQualityStatus;
  expected_value: string | null;
  actual_value: string | null;
  details: Record<string, unknown>;
  executed_at: string;
}

// ---------------------------------------------------------------------------
// dbt Lab (Phase 7) — a real, local dbt Core project against DuckDB; see
// apps/api/app/dbt_lab/.
// ---------------------------------------------------------------------------

export type DbtCommand = "run" | "test" | "build" | "compile" | "docs generate";
export type DbtRunStatus = "SUCCESS" | "FAILED" | "ERROR";

export interface RunDbtCommandRequest {
  command: DbtCommand;
  selector?: string | null;
}

export interface DbtRunSchema {
  id: string;
  command: DbtCommand;
  selector: string | null;
  status: DbtRunStatus;
  summary: Record<string, unknown>;
  log: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface ProjectTreeItemSchema {
  category: string;
  name: string;
  relative_path: string;
}

export interface LineageNodeSchema {
  unique_id: string;
  name: string;
  resource_type: "model" | "seed" | "snapshot" | "source" | string;
  layer: string | null;
  materialized: string | null;
  description: string;
  depends_on: string[];
}

export interface LineageEdgeSchema {
  from_unique_id: string;
  to_unique_id: string;
}

export interface LineageGraphSchema {
  nodes: LineageNodeSchema[];
  edges: LineageEdgeSchema[];
  generated_at: string | null;
}

export interface ColumnDocSchema {
  name: string;
  data_type: string | null;
  description: string;
}

export interface NodeDocSchema {
  unique_id: string;
  name: string;
  resource_type: string;
  description: string;
  materialized: string | null;
  schema_name: string | null;
  columns: ColumnDocSchema[];
  test_unique_ids: string[];
}

export interface TestResultSchema {
  unique_id: string;
  name: string;
  status: "pass" | "fail" | "error" | "skipped" | string;
  failures: number | null;
  message: string | null;
  execution_time: number | null;
}

export interface DbtExerciseContent {
  business_context: string | null;
  dbt_model_name: string;
  starter_sql: string | null;
  hint_count: number;
}

export interface SubmitDbtExerciseRequest {
  submitted_sql: string;
}

export interface DbtExerciseTestOutcome {
  name: string;
  passed: boolean;
  message?: string | null;
}

export interface SubmitDbtExerciseResponse {
  attempt_id: string;
  status: string;
  score: number;
  passed: boolean;
  model_built: boolean;
  test_outcomes: DbtExerciseTestOutcome[];
  log: string | null;
  explanation: string | null;
}

// ---------------------------------------------------------------------------
// Excel Lab (Phase 9)
// ---------------------------------------------------------------------------

export interface ExcelSheet {
  name: string;
  cells: Record<string, string>;
}

export interface ExcelExerciseContent {
  business_context: string | null;
  starter_sheets: ExcelSheet[];
  check_cells: string[];
  hint_count: number;
}

export type ExcelCellValue = number | string | boolean | null;

export interface EvaluatedExcelSheet {
  name: string;
  cells: Record<string, ExcelCellValue>;
}

export interface EvaluateWorkbookRequest {
  sheets: ExcelSheet[];
}

export interface EvaluateWorkbookResponse {
  sheets: EvaluatedExcelSheet[];
}

export interface ExcelTestOutcome {
  name: string;
  passed: boolean;
  is_hidden: boolean;
  message: string;
}

export interface SubmitExcelExerciseRequest {
  submitted_sheets: ExcelSheet[];
}

export interface SubmitExcelExerciseResponse {
  attempt_id: string;
  status: ExerciseAttemptStatus;
  score: number;
  passed: boolean;
  test_outcomes: ExcelTestOutcome[];
  evaluated_sheets: EvaluatedExcelSheet[];
  explanation: string | null;
}

// ---------------------------------------------------------------------------
// Interview & Assessment Engine (Phase 9)
// ---------------------------------------------------------------------------

export type InterviewQuestionType =
  | "SQL"
  | "PYTHON"
  | "EXCEL"
  | "STATISTICS"
  | "AB_TESTING"
  | "PRODUCT_ANALYTICS"
  | "BUSINESS_ANALYTICS"
  | "DATA_INTERPRETATION"
  | "DATA_VISUALIZATION"
  | "DATA_MODELING"
  | "DATA_WAREHOUSING"
  | "DBT"
  | "DATA_ENGINEERING"
  | "BEHAVIORAL";

/** A section's `interview_type` can also be the literal "CASE_STUDY" (a Case
 * Study round reuses the Phase 8 Case Study Engine directly, rather than
 * being one of the InterviewQuestionType-backed question rounds above). */
export type InterviewSectionType = InterviewQuestionType | "CASE_STUDY";

export type InterviewMode = "PRACTICE" | "TIMED" | "MOCK" | "COMPANY_STYLE" | "WEAKNESS_DRILL" | "FINAL_READINESS";

export type InterviewStatus = "NOT_STARTED" | "IN_PROGRESS" | "PAUSED" | "COMPLETED" | "ABANDONED";

export type InterviewTargetType = "QUESTION" | "CASE" | "ASSESSMENT" | "INTERVIEW" | "SKILL";

// --- Question catalog -------------------------------------------------------

export interface InterviewQuestionListItem {
  id: string;
  slug: string;
  interview_type: InterviewQuestionType;
  difficulty: DifficultyLevel;
  title: string;
  points: number;
  time_limit_seconds: number | null;
  company_archetypes: string[];
  tags: string[];
  is_bookmarked: boolean;
  best_score: number | null;
  attempt_count: number;
}

export interface InterviewQuestionDetail extends InterviewQuestionListItem {
  exercise_slug: string;
  exercise_type: string;
  prompt: string;
  business_context: string | null;
  stakeholder: string | null;
  constraints: string[];
  expected_deliverables: string[];
  rubric: RubricCriterion[];
  choices: string[] | null;
  hint_count: number;
  follow_up_question_ids: string[];
  dataset: string | null;
  sql_starter_query: string | null;
  python_starter_code: string | null;
  excel_starter_sheets: ExcelSheet[];
  excel_check_cells: string[];
}

// --- Interview templates ("company-style assessments") ----------------------

export interface InterviewSectionSpec {
  interview_type: InterviewSectionType;
  title: string;
  duration_minutes: number;
  question_count: number;
  difficulty: DifficultyLevel | null;
}

export interface InterviewTemplate {
  id: string;
  slug: string;
  title: string;
  target_profile: string;
  description: string | null;
  sections: InterviewSectionSpec[];
  rubric_weights: Record<string, number>;
  tags: string[];
  version: number;
}

export interface InterviewTemplateAdminListItem {
  id: string;
  slug: string;
  title: string;
  target_profile: string;
  section_count: number;
  is_active: boolean;
  version: number;
}

export interface UpdateInterviewTemplateAdminRequest {
  is_active: boolean;
}

// --- Live interview session --------------------------------------------------

export interface InterviewDimensionScore {
  dimension: string;
  score: number;
  question_count: number;
}

export interface InterviewScore {
  overall: number;
  dimensions: InterviewDimensionScore[];
}

export interface InterviewSection {
  id: string;
  interview_type: InterviewSectionType;
  title: string;
  time_limit_seconds: number | null;
  display_order: number;
  started_at: string | null;
  completed_at: string | null;
  time_spent_seconds: number;
}

export interface InterviewQuestionAttempt {
  id: string;
  section_id: string | null;
  interview_question_id: string | null;
  case_attempt_id: string | null;
  exercise_attempt_id: string | null;
  parent_attempt_id: string | null;
  is_follow_up: boolean;
  display_order: number;
  started_at: string | null;
  time_spent_seconds: number;
  question: InterviewQuestionDetail | null;
  exercise_attempt_score: number | null;
  case_attempt_status: string | null;
}

export interface Interview {
  id: string;
  template_id: string | null;
  mode: InterviewMode;
  status: InterviewStatus;
  title: string;
  total_time_limit_seconds: number | null;
  time_spent_seconds: number;
  current_section_index: number;
  started_at: string | null;
  paused_at: string | null;
  completed_at: string | null;
  score: InterviewScore | null;
  feedback: Record<string, unknown> | null;
  created_at: string;
  sections: InterviewSection[];
  question_attempts: InterviewQuestionAttempt[];
  current_question: InterviewQuestionAttempt | null;
}

export interface CreateInterviewRequest {
  mode: InterviewMode;
  template_slug?: string | null;
  interview_type?: InterviewQuestionType | null;
  time_limit_seconds?: number | null;
  question_count?: number;
  question_id?: string | null;
}

export interface AnswerInterviewQuestionRequest {
  submitted_answer?: string | null;
  rubric_selections?: string[] | null;
  self_reported_score?: number | null;
  submitted_query?: string | null;
  submitted_code?: string | null;
  submitted_sheets?: ExcelSheet[] | null;
}

export interface AnswerInterviewQuestionResponse {
  interview: Interview;
  is_auto_graded: boolean;
  score: number | null;
  explanation: string | null;
  correct_answer: string | null;
}

// --- Post-interview review & retry ---------------------------------------------

export interface InterviewTestOutcome {
  name: string;
  passed: boolean;
  is_hidden: boolean;
  message: string;
}

export interface InterviewQuestionReview {
  attempt_id: string;
  display_order: number;
  interview_type: InterviewSectionType;
  is_follow_up: boolean;
  question_slug: string | null;
  title: string;
  prompt: string | null;
  time_limit_seconds: number | null;
  time_spent_seconds: number;
  over_time: boolean;
  score: number | null;
  passed: boolean | null;
  submitted_answer: string | null;
  correct_answer: string | null;
  explanation: string | null;
  solution: string | null;
  test_outcomes: InterviewTestOutcome[];
  skill_slug: string | null;
  skill_name: string | null;
  recommended_lesson_slug: string | null;
  recommended_lesson_title: string | null;
  case_attempt_id: string | null;
  case_slug: string | null;
}

export interface InterviewReviewResponse {
  interview: Interview;
  questions: InterviewQuestionReview[];
}

export type RetryInterviewScope = "FULL" | "SECTION" | "QUESTION";

export interface RetryInterviewRequest {
  scope: RetryInterviewScope;
  section_id?: string | null;
  interview_question_id?: string | null;
}

// --- Spaced review ---------------------------------------------------------------

export interface DueReview {
  question_id: string;
  slug: string;
  title: string;
  interview_type: InterviewSectionType;
  last_score: number;
  days_since_last_attempt: number;
  interval_days: number;
  days_overdue: number;
  priority: number;
  reason: string;
}

// --- Readiness / weaknesses / plan / history ---------------------------------

export interface ReadinessResponse {
  overall_score: number;
  mastery_component: number;
  recent_performance_component: number;
  consistency_component: number;
  breakdown: Record<string, number>;
  strongest: string[];
  weakest: string[];
}

export interface WeaknessFinding {
  gap_type: "Knowledge" | "Execution" | "Reasoning" | "Communication" | "Speed";
  interview_type: string;
  occurrences: number;
  average_score: number;
  detail: string;
}

export interface InterviewPlanDay {
  day_number: number;
  focus_area: string;
  title: string;
  task_type: "PRACTICE" | "MOCK_INTERVIEW" | "REVIEW";
  task_ref: string | null;
  description: string;
}

export interface InterviewPlan {
  id: string;
  generated_at: string;
  days: InterviewPlanDay[];
}

export interface ReadinessSnapshot {
  id: string;
  computed_at: string;
  overall_score: number;
  breakdown: Record<string, number>;
}

// --- Bookmarks / notes -------------------------------------------------------

export interface InterviewBookmark {
  id: string;
  target_type: InterviewTargetType;
  target_id: string;
  created_at: string;
}

export interface CreateBookmarkRequest {
  target_type: InterviewTargetType;
  target_id: string;
}

export interface InterviewNote {
  id: string;
  target_type: InterviewTargetType;
  target_id: string;
  note: string;
  created_at: string;
  updated_at: string;
}

export interface CreateInterviewNoteRequest {
  target_type: InterviewTargetType;
  target_id: string;
  note: string;
}

export interface UpdateInterviewNoteRequest {
  note: string;
}

// --- Content Admin -------------------------------------------------------------

export interface InterviewQuestionAdminListItem {
  id: string;
  slug: string;
  interview_type: InterviewQuestionType;
  exercise_slug: string;
  time_limit_seconds: number | null;
  is_active: boolean;
  version: number;
}

export interface UpdateInterviewQuestionAdminRequest {
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// AI Layer (Phase 10)
// ---------------------------------------------------------------------------
// Mirrors apps/api/app/schemas/ai.py field-for-field. Every AI feature is a
// thin coaching/explanation layer on top of Phases 1-9's real, deterministic
// systems (SQL/Python execution, statistics, case/interview scoring) — see
// apps/api/app/ai/AUTHORITY.md. Structured AI output is always validated
// server-side before it reaches the frontend (never trusted blindly).

export type AIClaimType = "OBSERVED" | "INFERRED" | "HYPOTHESIS" | "UNKNOWN";
export type AIMode = "TUTOR" | "COACH" | "REVIEWER" | "INTERVIEWER" | "ANALYST" | "EXPLAINER";
export type AICaseCoachingMode = "GUIDED" | "STANDARD" | "INTERVIEW" | "STRICT";
export type AIContextType = "sql" | "python" | "lesson" | "case" | "interview" | "general";
export type AIDomain =
  | "STATISTICS"
  | "EXPERIMENTATION"
  | "PRODUCT_ANALYTICS"
  | "BUSINESS_ANALYTICS"
  | "DATA_MODELING"
  | "DBT";

// --- Structured AI output shapes --------------------------------------------

export interface AIClaim {
  claim: string;
  claim_type: AIClaimType;
  evidence: string | null;
}

export interface AIReviewResult {
  summary: string;
  strengths: string[];
  issues: string[];
  suggestions: string[];
  claims: AIClaim[];
  confidence: number;
}

export interface AIInsightReviewResult {
  observation_supported: boolean;
  observation_note: string;
  evidence_sufficient: boolean;
  evidence_note: string;
  impact_reasonable: boolean;
  impact_note: string;
  recommendation_follows: boolean;
  recommendation_note: string;
  overall_assessment: string;
}

export interface AIDebugResult {
  what_happened: string;
  why_it_likely_happened: string;
  where: string;
  how_to_investigate: string;
  suggested_fix: string;
}

export interface AINlToSqlResult {
  sql: string;
  explanation_steps: string[];
  assumptions: string[];
}

export interface AINlToPythonResult {
  plan: string[];
  code: string;
}

export interface AIEdaResult {
  what_to_inspect: string[];
  observed_issues: string[];
  suggested_investigations: string[];
  important_variables: string[];
  suggested_visualizations: string[];
  suggested_questions: string[];
  potential_hypotheses: string[];
}

export interface AIInterviewerTurnResult {
  interviewer_message: string;
  revealed_info_keys: string[];
  follow_up_asked: boolean;
}

export interface AIDebriefResult {
  strengths: string[];
  weaknesses: string[];
  missed_opportunities: string[];
  suggested_practice: string[];
}

export interface AIExecSummaryResult {
  what_happened: string;
  why: string;
  impact: string;
  recommendation: string;
  next_step: string;
}

export interface AIPlanDayExplanation {
  day_number: number;
  why: string;
}

export interface AIPlanExplanationResult {
  day_explanations: AIPlanDayExplanation[];
}

export interface AISkillObservation {
  skill: string;
  assessment: string;
}

export interface AISkillDiagnosisResult {
  diagnosis_summary: string;
  skill_observations: AISkillObservation[];
  recommended_practice: string[];
}

export interface AIProjectReviewResult {
  strong: string[];
  needs_improvement: string[];
  technical: string[];
  business: string[];
  communication: string[];
  top_3_improvements: string[];
}

export interface AIKnowledgeSource {
  title: string;
  lesson_slug: string | null;
  module_slug: string | null;
  domain_slug: string | null;
  kind: string;
}

export interface AIKnowledgeAnswerResult {
  answer: string;
  sources: AIKnowledgeSource[];
  insufficient_knowledge: boolean;
}

// --- Settings / usage / conversations ---------------------------------------

export interface AISettings {
  id: string;
  created_at: string;
  updated_at: string;
  enabled: boolean;
  provider_override: string | null;
  model_override: string | null;
  response_style: string;
  learning_mode: string;
  privacy_preference: string;
  max_context_chars: number | null;
  daily_request_limit: number | null;
  effective_provider: string;
  ai_configured: boolean;
}

export interface UpdateAISettingsRequest {
  enabled?: boolean;
  provider_override?: string | null;
  model_override?: string | null;
  response_style?: string;
  learning_mode?: string;
  privacy_preference?: string;
  max_context_chars?: number | null;
  daily_request_limit?: number | null;
}

export interface AIUsage {
  date: string;
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  daily_request_limit: number;
  requests_remaining: number;
  privacy_notice: string;
}

export interface AIMessage {
  id: string;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  structured_output: Record<string, unknown> | null;
  hint_level: number | null;
  created_at: string;
}

export interface AIConversation {
  id: string;
  created_at: string;
  updated_at: string;
  feature: string;
  title: string | null;
  context_type: string | null;
  context_id: string | null;
  is_archived: boolean;
  last_message_at: string;
  messages: AIMessage[];
}

export interface AIConversationListItem {
  id: string;
  created_at: string;
  updated_at: string;
  feature: string;
  title: string | null;
  context_type: string | null;
  context_id: string | null;
  is_archived: boolean;
  last_message_at: string;
}

export interface AskMentorRequest {
  message: string;
  context_type: AIContextType;
  context_id?: string | null;
  conversation_id?: string | null;
  mode?: AIMode;
}

export interface HintLevelRequest {
  context_type: "sql" | "python" | "lesson";
  context_id: string;
  hint_level: number; // 1-3 = Hint 1/2/3, 4 = full Solution
  conversation_id?: string | null;
}

export interface AIChatResponse {
  conversation_id: string;
  message_id: string;
  reply: string;
  structured: Record<string, unknown> | null;
  hint_level: number | null;
  provider: string;
  model: string;
  ai_configured: boolean;
}

export interface AIStructuredResponse {
  raw_text: string;
  structured: Record<string, unknown> | null;
  structured_valid: boolean;
  provider: string;
  model: string;
  ai_configured: boolean;
  audit_id: string | null;
}

// --- SQL / Python -------------------------------------------------------------

export interface ReviewSqlRequest {
  query: string;
  question?: string | null;
  engine?: string;
  database?: string | null;
}

export interface DebugSqlRequest {
  query: string;
  error_message: string;
  engine?: string;
  database?: string | null;
}

export interface OptimizeSqlRequest {
  query: string;
  engine?: string;
  database?: string | null;
  execution_time_ms?: number | null;
}

export interface NlToSqlRequest {
  request: string;
  database: string;
  engine?: string;
}

export interface ReviewPythonRequest {
  code: string;
  question?: string | null;
  error_type?: string | null;
  error_message?: string | null;
  traceback_text?: string | null;
}

export interface NlToPythonRequest {
  request: string;
  dataset_slugs: string[];
}

// --- Analysis / Insight / EDA --------------------------------------------------

export interface ReviewAnalysisRequest {
  business_question: string;
  dataset_slug?: string | null;
  code?: string | null;
  findings?: string | null;
}

export interface ReviewInsightRequest {
  observation: string;
  evidence: string;
  impact: string;
  recommendation: string;
  case_attempt_id?: string | null;
}

export interface EdaAssistRequest {
  dataset_id: string;
  table_name?: string | null;
  user_goal?: string | null;
}

export interface DomainCoachRequest {
  domain: AIDomain;
  question?: string | null;
  result_ref: Record<string, unknown>;
}

// --- Case / Interview coaching --------------------------------------------------

export interface CaseCoachRequest {
  message: string;
  coaching_mode: AICaseCoachingMode;
  conversation_id?: string | null;
}

export interface CaseInterviewerTurnRequest {
  message: string;
  conversation_id?: string | null;
}

export interface BehavioralInterviewerTurnRequest {
  message: string;
  interview_question_attempt_id: string;
  conversation_id?: string | null;
}

export interface CommunicationReviewRequest {
  text: string;
  audience?: string | null;
}

export interface StorytellingReviewRequest {
  findings_text: string;
  chart_description?: string | null;
}

export interface ExecSummaryRequest {
  analysis_text: string;
}

export interface PlanExplanationRequest {
  plan_id: string;
}

export interface SkillDiagnosisRequest {
  exercise_attempt_id: string;
}

export interface AIMistakeMemory {
  id: string;
  created_at: string;
  updated_at: string;
  skill_slug: string | null;
  category: string | null;
  mistake_summary: string;
  first_observed_at: string;
  last_observed_at: string;
  occurrences: number;
  recommended_review: string | null;
}

export interface AISkillDiagnosis {
  id: string;
  skill_slug: string | null;
  exercise_attempt_id: string | null;
  diagnosis: string;
  strength_areas: string[];
  improvement_areas: string[];
  recommended_exercise_slugs: string[];
  created_at: string;
}

export interface KnowledgeSearchRequest {
  query: string;
  limit?: number;
}

// ---------------------------------------------------------------------------
// Career Readiness, Portfolio, Resume/JD Intelligence & Job Preparation
// (Phase 11) — mirrors apps/api/app/schemas/career.py, apps/api/app/schemas/
// jobs.py, apps/api/app/schemas/resume.py and apps/api/app/schemas/
// portfolio.py field-for-field. Every readiness/score number this layer
// produces is a platform estimate derived from the deterministic
// mastery/progress/interview-readiness engines (Phases 3-9) plus the Phase 10
// AI layer for explanations only — never a hiring guarantee.
// ---------------------------------------------------------------------------

export type TargetRoleCategory =
  | "DATA_ANALYST"
  | "PRODUCT_ANALYST"
  | "BUSINESS_ANALYST"
  | "BI_ANALYST"
  | "MARKETING_ANALYST"
  | "ANALYTICS_ENGINEER_ENTRY"
  | "ANALYTICS_ENGINEER_INTERMEDIATE";

export type JDSource = "PASTED" | "UPLOADED";

export type JDRequirementKind =
  | "SKILL"
  | "TOOL"
  | "RESPONSIBILITY"
  | "EXPERIENCE"
  | "EDUCATION"
  | "DOMAIN_KNOWLEDGE"
  | "SOFT_SKILL"
  | "BUSINESS_EXPECTATION";

export type JDRequirementPriority = "MUST_HAVE" | "STRONGLY_PREFERRED" | "NICE_TO_HAVE";

export type ResumeSource = "PASTED" | "UPLOADED";

export type PortfolioItemType = "PROJECT" | "CASE_STUDY" | "CERTIFICATION" | "ACHIEVEMENT" | "SKILL_HIGHLIGHT";

/** Always defaults to PRIVATE server-side unless explicitly set otherwise. */
export type PrivacyLevel = "PRIVATE" | "PORTFOLIO" | "PUBLIC_READY";

export type CareerGoalType =
  | "TARGET_ROLE"
  | "SKILL_MASTERY"
  | "READINESS_LEVEL"
  | "PORTFOLIO_COMPLETION"
  | "INTERVIEW_PREP"
  | "CUSTOM";

export type CareerGoalStatus = "ACTIVE" | "COMPLETED" | "ABANDONED";

export type CareerMilestoneType =
  | "SKILL_LEVEL_UP"
  | "PROJECT_COMPLETED"
  | "CASE_COMPLETED"
  | "INTERVIEW_COMPLETED"
  | "ASSESSMENT_PASSED"
  | "GOAL_COMPLETED"
  | "READINESS_LEVEL_UP"
  | "ACHIEVEMENT_EARNED";

export type CareerReadinessLevel =
  | "FOUNDATION"
  | "DEVELOPING"
  | "INTERMEDIATE"
  | "INTERVIEW_READY"
  | "STRONG_CANDIDATE"
  | "EXCEPTIONAL";

export type CareerRubricDimension =
  | "TECHNICAL"
  | "ANALYTICAL"
  | "BUSINESS"
  | "PRODUCT"
  | "DATA_ENGINEERING_AWARENESS"
  | "COMMUNICATION"
  | "INTERVIEW"
  | "PORTFOLIO";

/** The real 12 behavioral story categories — matches the Phase 9 behavioral-exercise tags. */
export type BehavioralStoryCategory =
  | "AMBIGUITY"
  | "COMMUNICATION"
  | "CONFLICT"
  | "DEADLINES"
  | "DISAGREEMENT"
  | "WORKING_WITH_ENGINEERS"
  | "FAILURE"
  | "INCOMPLETE_DATA"
  | "INFLUENCING"
  | "OWNERSHIP"
  | "PRIORITIZATION"
  | "STAKEHOLDER_MANAGEMENT";

export type JobPrepStatus = "SAVED" | "IN_PROGRESS" | "READY" | "ARCHIVED";

export type CareerSkillEvidenceLevel = "LEARNED" | "PRACTICED" | "APPLIED" | "INTERVIEW_READY" | "DEMONSTRATED";

export type CareerCoachTopic = "goal" | "readiness" | "weekly_review" | "jd_prep" | "general";

// --- Career profile / roles ---------------------------------------------------

export interface CareerProfile {
  id: string;
  headline: string | null;
  summary: string | null;
  primary_target_role_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateCareerProfileRequest {
  headline?: string;
  summary?: string;
  primary_target_role_id?: string;
}

export interface RoleTemplate {
  id: string;
  slug: string;
  title: string;
  category: TargetRoleCategory;
  description: string | null;
  core_skills: string[];
  preferred_skills: string[];
  nice_to_have_skills: string[];
  typical_responsibilities: string[];
  version: number;
}

export interface TargetRole {
  id: string;
  role_template_id: string | null;
  custom_title: string | null;
  notes: string | null;
  is_primary: boolean;
  created_at: string;
  role_template: RoleTemplate | null;
}

export interface CreateTargetRoleRequest {
  role_template_slug?: string | null;
  custom_title?: string | null;
  notes?: string | null;
  is_primary?: boolean;
}

// --- Readiness assessment / skill matrix --------------------------------------

export interface CareerAssessment {
  id: string;
  target_role_id: string | null;
  rubric_scores: Record<CareerRubricDimension, number>;
  overall_score: number;
  overall_readiness_level: CareerReadinessLevel;
  /** false means one weak dimension capped the level even though the raw
   * score looked higher — always surface `explanation` alongside this. */
  gating_passed: boolean;
  explanation: Record<string, string[]>;
  computed_at: string;
}

export interface ComputeCareerAssessmentRequest {
  target_role_id?: string | null;
}

export interface CareerSkillMatrixEntry {
  skill_slug: string;
  name: string;
  category: SkillCategory;
  mastery_score: number;
  evidence_level: CareerSkillEvidenceLevel;
  exercises_passed: number;
  assessment_pct: number | null;
  projects_count: number;
  cases_count: number;
  mock_interview_score: number | null;
  is_gap_for_primary_role: boolean;
}

// --- Goals / milestones / achievements ----------------------------------------

export interface CareerGoal {
  id: string;
  goal_type: CareerGoalType;
  title: string;
  description: string | null;
  target_value: string | null;
  current_value: string | null;
  target_date: string | null;
  status: CareerGoalStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateCareerGoalRequest {
  goal_type: CareerGoalType;
  title: string;
  description?: string;
  target_value?: string;
  target_date?: string;
}

export interface UpdateCareerGoalRequest {
  title?: string;
  description?: string;
  target_value?: string;
  current_value?: string;
  target_date?: string;
  status?: CareerGoalStatus;
}

export interface CareerMilestone {
  id: string;
  milestone_type: CareerMilestoneType;
  title: string;
  detail: string | null;
  related_goal_id: string | null;
  achieved_at: string;
}

export interface Achievement {
  id: string;
  slug: string;
  title: string;
  description: string;
  icon: string | null;
  criteria: Record<string, unknown>;
}

export interface UserAchievement {
  id: string;
  earned_at: string;
  achievement: Achievement;
}

// --- Behavioral story bank -----------------------------------------------------

export interface BehavioralStory {
  id: string;
  category: BehavioralStoryCategory;
  title: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  related_question_ids: string[];
  last_practiced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateBehavioralStoryRequest {
  category: BehavioralStoryCategory;
  title: string;
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface UpdateBehavioralStoryRequest {
  title?: string;
  situation?: string;
  task?: string;
  action?: string;
  result?: string;
}

export interface BehavioralStoryCoverageEntry {
  category: BehavioralStoryCategory;
  story_count: number;
  has_coverage: boolean;
}

export interface BehavioralStoryCoverageResponse {
  coverage: BehavioralStoryCoverageEntry[];
  missing_categories: BehavioralStoryCategory[];
}

// --- Career notes ---------------------------------------------------------------

export interface CareerNote {
  id: string;
  topic: string | null;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCareerNoteRequest {
  topic?: string;
  body: string;
}

export interface UpdateCareerNoteRequest {
  topic?: string;
  body?: string;
}

// --- Dashboard / weekly review / report / coach -------------------------------

export interface CareerDashboardResponse {
  profile: CareerProfile;
  primary_target_role: TargetRole | null;
  target_role_count: number;
  latest_assessment: CareerAssessment | null;
  active_goal_count: number;
  recent_milestones: CareerMilestone[];
  achievement_count: number;
  saved_job_count: number;
}

export interface CareerWeeklyReviewResponse {
  period_start: string;
  period_end: string;
  exercises_attempted: number;
  exercises_passed: number;
  cases_completed: number;
  projects_completed: number;
  interviews_completed: number;
  new_milestones: CareerMilestone[];
  weak_skill_slugs: string[];
}

export interface CareerReportSchema {
  generated_at: string;
  profile: CareerProfile;
  target_roles: TargetRole[];
  latest_assessment: CareerAssessment | null;
  top_skill_gaps: CareerSkillMatrixEntry[];
  active_goals: CareerGoal[];
  recent_milestones: CareerMilestone[];
  achievement_count: number;
}

export interface CareerCoachRequest {
  message: string;
  topic: CareerCoachTopic;
  conversation_id?: string | null;
}

// ---------------------------------------------------------------------------
// Job Description Intelligence & Preparation (Phase 11)
// ---------------------------------------------------------------------------

export interface JDRequirement {
  id: string;
  kind: JDRequirementKind;
  priority: JDRequirementPriority;
  raw_text: string;
  matched_skill_slug: string | null;
  confidence: number | null;
}

export interface JobDescription {
  id: string;
  target_role_id: string | null;
  company: string | null;
  title: string;
  source: JDSource;
  raw_text: string;
  location: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  requirements: JDRequirement[];
}

export interface CreateJobDescriptionRequest {
  company?: string;
  title: string;
  source: JDSource;
  raw_text: string;
  location?: string;
  notes?: string;
  target_role_id?: string;
}

export interface UpdateJobDescriptionRequest {
  company?: string;
  title?: string;
  notes?: string;
  target_role_id?: string;
}

export interface JDComparisonEntry {
  job_description_id: string;
  title: string;
  company: string | null;
  readiness_score: number | null;
  must_have_gap_count: number;
}

export interface JDComparisonResponse {
  entries: JDComparisonEntry[];
  common_must_have_skill_slugs: string[];
}

export interface SkillGap {
  id: string;
  skill_slug: string;
  required: boolean;
  priority: JDRequirementPriority | null;
  current_mastery_score: number;
  gap_size: number;
  computed_at: string;
}

export interface SkillGapsResponse {
  gaps: SkillGap[];
  covered_skill_slugs: string[];
}

export interface AnalyzeJDRequest {
  weights?: Record<string, number> | null;
}

export interface JDAnalysis {
  id: string;
  readiness_score: number;
  weights: Record<string, number>;
  breakdown: Record<string, unknown>;
  summary: string | null;
  ai_explanation: string | null;
  computed_at: string;
}

export interface JDPreparationTask {
  skill_slug: string;
  priority: JDRequirementPriority | null;
  recommended_exercise_slugs: string[];
  recommended_case_slugs: string[];
  recommended_project_slugs: string[];
}

export interface JDPreparationPlanResponse {
  job_description_id: string;
  tasks: JDPreparationTask[];
}

/** `note` always explains this is an estimate, not the real employer's process. */
export interface JDInterviewPlanResponse {
  job_description_id: string;
  focus_interview_types: string[];
  suggested_question_slugs: string[];
  suggested_case_slugs: string[];
  note: string;
}

export interface JobPrepChecklistItem {
  label: string;
  is_done: boolean;
}

export interface JobPreparationWorkspace {
  id: string;
  job_description_id: string;
  notes: string | null;
  checklist: JobPrepChecklistItem[];
  status: JobPrepStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateJobWorkspaceRequest {
  job_description_id: string;
}

export interface UpdateJobWorkspaceRequest {
  notes?: string;
  checklist?: JobPrepChecklistItem[];
  status?: JobPrepStatus;
}

// ---------------------------------------------------------------------------
// Resume Intelligence (Phase 11)
// ---------------------------------------------------------------------------

export interface ResumeVersionListItem {
  id: string;
  version_number: number;
  source: ResumeSource;
  file_name: string | null;
  is_current: boolean;
  created_at: string;
}

export interface Resume {
  id: string;
  title: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
  versions: ResumeVersionListItem[];
}

export interface CreateResumeRequest {
  title: string;
  is_primary?: boolean;
}

export interface UpdateResumeRequest {
  title?: string;
  is_primary?: boolean;
}

export interface CreateResumeVersionRequest {
  source: ResumeSource;
  raw_text: string;
  file_name?: string | null;
}

export interface ResumeEvidence {
  id: string;
  skill_slug: string;
  /** Always a verbatim quoted line from the resume, never fabricated. */
  evidence_text: string;
  project_id: string | null;
  confidence: number | null;
}

export interface ResumeReview {
  id: string;
  /** Deterministic score — never AI-generated. */
  quality_score: number;
  clarity_score: number | null;
  impact_score: number | null;
  /** May be AI-sourced ("AI suggestions") — can be empty when AI is unavailable in local mode. */
  issues: string[];
  suggestions: string[];
  ai_generated: boolean;
  created_at: string;
}

export interface ResumeVersion {
  id: string;
  version_number: number;
  source: ResumeSource;
  raw_text: string;
  file_name: string | null;
  is_current: boolean;
  created_at: string;
  evidence: ResumeEvidence[];
  reviews: ResumeReview[];
}

export interface ResumeGapEntry {
  skill_slug: string;
  has_evidence: boolean;
}

export interface ResumeGapAnalysisResponse {
  resume_version_id: string;
  target_role_id: string | null;
  gaps: ResumeGapEntry[];
}

// ---------------------------------------------------------------------------
// Portfolio Builder (Phase 11)
// ---------------------------------------------------------------------------

export interface PortfolioItem {
  id: string;
  item_type: PortfolioItemType;
  ref_id: string | null;
  title: string;
  description: string | null;
  privacy: PrivacyLevel;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: string;
  headline: string | null;
  about: string | null;
  is_public_ready: boolean;
  created_at: string;
  updated_at: string;
  items: PortfolioItem[];
}

export interface UpdatePortfolioRequest {
  headline?: string;
  about?: string;
  is_public_ready?: boolean;
}

export interface CreatePortfolioItemRequest {
  item_type: PortfolioItemType;
  ref_id?: string | null;
  title: string;
  description?: string | null;
  /** Defaults to PRIVATE server-side when omitted. */
  privacy?: PrivacyLevel;
}

export interface UpdatePortfolioItemRequest {
  title?: string;
  description?: string;
  privacy?: PrivacyLevel;
  display_order?: number;
}

export interface PortfolioQualityScoreResponse {
  score: number;
  item_count: number;
  items_with_description: number;
  portfolio_ready_item_count: number;
  suggestions: string[];
}

export interface PortfolioGapEntry {
  skill_slug: string;
  recommended_project_template_slugs: string[];
}

// ---------------------------------------------------------------------------
// Platform: cross-domain recommendations, system health, backup/restore (Phase 12)
// ---------------------------------------------------------------------------

export type NextBestActionSource = "lesson" | "interview" | "job_description" | "portfolio" | "goal";

export interface NextBestActionItem {
  title: string;
  why: string;
  source: NextBestActionSource;
  url_path: string;
}

export interface NextBestActionResponse {
  actions: NextBestActionItem[];
}

export type ServiceStatusLevel = "ok" | "degraded" | "unavailable" | "not_configured";

export interface ServiceStatus {
  name: string;
  status: ServiceStatusLevel;
  detail: string | null;
}

export interface SystemHealthResponse {
  checked_at: string;
  services: ServiceStatus[];
}

export interface BackupManifest {
  created_at: string;
  app_version: string;
  schema_version: string;
  user_email: string;
  counts: Record<string, number>;
}

export interface BackupBundle {
  manifest: BackupManifest;
  data: Record<string, unknown[]>;
}

export interface RestorePreviewResponse {
  manifest: BackupManifest;
  compatible: boolean;
  issues: string[];
}

export interface RestoreRequest {
  bundle: BackupBundle;
  confirm: true;
}

export interface RestoreResponse {
  restored: Record<string, number>;
}
export type UserRole = "USER" | "ADMIN";
export type AccountStatus = "ACTIVE" | "SUSPENDED";

export interface AuthUserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: AccountStatus;
  must_change_password: boolean;
  ai_access_enabled: boolean;
  ai_daily_quota: number;
  ai_requests_today: number;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: AuthUserProfile;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface AdminDashboardSummary {
  users: number;
  active_users: number;
  suspended_users: number;
  locked_users: number;
  signups_today: number;
  ai_requests_today: number;
}

export interface AdminUserSummary {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: AccountStatus;
  must_change_password: boolean;
  is_locked: boolean;
  ai_grant_enabled: boolean;
  ai_daily_quota: number;
  ai_requests_today: number;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserDetail extends AdminUserSummary {
  failed_login_count: number;
  locked_until: string | null;
  temporary_password_expires_at: string | null;
  ai_preference_enabled: boolean;
  effective_ai_access_enabled: boolean;
}

export interface AdminAuditEntry {
  id: string;
  actor_user_id: string | null;
  target_user_id: string | null;
  action: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminDataRow {
  type: string;
  data: Record<string, unknown>;
}
