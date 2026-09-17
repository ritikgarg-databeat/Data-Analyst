import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import type {
  Case,
  CaseAttempt,
  CaseCategory,
  CaseDifficulty,
  CaseListItem,
  CaseStage,
  ExecutiveSummaryPayload,
  ProblemFramingPayload,
  RecommendationPayload,
  ReflectionPayload,
  RevealCaseSolutionResponse,
  RevealHintResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Case Study Engine (Phase 8) data layer. Every mutation below returns the
 * full updated `CaseAttempt` from the API (except the hint/reveal-solution
 * endpoints, which have their own small response shapes) — `onSuccess` just
 * writes that straight into the `["case-attempt", id]` cache and invalidates
 * the list queries whose derived fields (attempt_status/attempt_score) may
 * have changed, mirroring the pattern in `features/findings/use-findings.ts`.
 */

export interface CaseFilters {
  category?: CaseCategory;
  difficulty?: CaseDifficulty;
  search?: string;
}

export const caseStudiesQueryKey = (filters?: CaseFilters) => ["case-studies", filters ?? {}] as const;
export const caseAttemptsQueryKey = ["case-attempts"] as const;
export const caseAttemptQueryKey = (attemptId: string | undefined) => ["case-attempt", attemptId ?? null] as const;
export const caseBySlugQueryKey = (slug: string | undefined) => ["case-study", slug ?? null] as const;

function toSearchParams(filters?: CaseFilters): string {
  if (!filters) return "";
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.difficulty) params.set("difficulty", filters.difficulty);
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/** The Case Studies catalog — each item already carries the caller's latest
 * attempt (id/status/score) for that case, so this single endpoint powers
 * both the landing page and (unfiltered) the category-joining needed by the
 * performance dashboard and the workspace's case-by-id lookup. */
export function useCases(filters?: CaseFilters) {
  return useQuery({
    queryKey: caseStudiesQueryKey(filters),
    queryFn: () => apiClient.get<CaseListItem[]>(`/cases${toSearchParams(filters)}`),
    staleTime: 30 * 1000,
  });
}

/** Every attempt (all statuses, full history) belonging to the current user. */
export function useCaseAttempts() {
  return useQuery({
    queryKey: caseAttemptsQueryKey,
    queryFn: () => apiClient.get<CaseAttempt[]>("/cases/attempts"),
    staleTime: 30 * 1000,
  });
}

export function useCaseAttempt(attemptId: string | undefined) {
  return useQuery({
    queryKey: caseAttemptQueryKey(attemptId),
    queryFn: () => apiClient.get<CaseAttempt>(`/cases/attempts/${attemptId}`),
    enabled: Boolean(attemptId),
  });
}

/** The public shape of a single Case by slug — no rubric answer text, hint
 * text, or reference_solution (see Case type). Used on the pre-start detail
 * page; the workspace instead resolves its Case from the already-fetched
 * `useCases()` catalog by `case.id`, since there's no by-id endpoint. */
export function useCaseBySlug(slug: string | undefined) {
  return useQuery({
    queryKey: caseBySlugQueryKey(slug),
    queryFn: () => apiClient.get<Case>(`/cases/${slug}`),
    enabled: Boolean(slug),
  });
}

function writeAttemptCache(queryClient: QueryClient, attempt: CaseAttempt) {
  queryClient.setQueryData(caseAttemptQueryKey(attempt.id), attempt);
  void queryClient.invalidateQueries({ queryKey: ["case-studies"] });
  void queryClient.invalidateQueries({ queryKey: caseAttemptsQueryKey });
}

/** Starts a new attempt for a case, or resumes the existing in-progress one
 * if called again for the same case/user. */
export function useStartCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => apiClient.post<CaseAttempt>(`/cases/${slug}/start`),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useUpdateCaseStage(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stage: CaseStage) => apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/stage`, { stage }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useSaveClarification(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questions: string) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/clarification`, { questions }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useSaveFraming(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (framing: ProblemFramingPayload) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/framing`, { framing }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useSaveDatasetSelection(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (datasetSlugs: string[]) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/datasets`, { dataset_slugs: datasetSlugs }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useSaveRecommendation(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recommendation: RecommendationPayload) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/recommendation`, { recommendation }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useSaveExecutiveSummary(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (executiveSummary: ExecutiveSummaryPayload) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/executive-summary`, {
        executive_summary: executiveSummary,
      }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

export function useRecordStageTime(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ stage, seconds }: { stage: CaseStage; seconds: number }) =>
      apiClient.post<CaseAttempt>(`/cases/attempts/${attemptId}/stage-time`, { stage, seconds }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

/** Reveals the next hint. Errors once `hints_used >= case.hint_count` —
 * callers should catch that and show a friendly "no more hints" state. */
export function useRevealHint(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<RevealHintResponse>(`/cases/attempts/${attemptId}/hint`),
    onSuccess: (result) => {
      queryClient.setQueryData(caseAttemptQueryKey(attemptId), (prev: CaseAttempt | undefined) =>
        prev ? { ...prev, hints_used: result.hints_used } : prev,
      );
    },
  });
}

export function useSubmitCaseAttempt(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rubricSelections: Record<string, string[]>) =>
      apiClient.post<CaseAttempt>(`/cases/attempts/${attemptId}/submit`, { rubric_selections: rubricSelections }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}

/** Only succeeds once the attempt is COMPLETED. */
export function useRevealCaseSolution(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<RevealCaseSolutionResponse>(`/cases/attempts/${attemptId}/reveal-solution`),
    onSuccess: () => {
      queryClient.setQueryData(caseAttemptQueryKey(attemptId), (prev: CaseAttempt | undefined) =>
        prev ? { ...prev, solution_revealed: true } : prev,
      );
    },
  });
}

export function useSaveReflection(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reflection: ReflectionPayload) =>
      apiClient.patch<CaseAttempt>(`/cases/attempts/${attemptId}/reflection`, { reflection }),
    onSuccess: (attempt) => writeAttemptCache(queryClient, attempt),
  });
}
