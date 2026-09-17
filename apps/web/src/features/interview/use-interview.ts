import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import type {
  AnswerInterviewQuestionRequest,
  AnswerInterviewQuestionResponse,
  CreateBookmarkRequest,
  CreateInterviewNoteRequest,
  CreateInterviewRequest,
  DueReview,
  EvaluateWorkbookResponse,
  ExcelExerciseContent,
  ExcelSheet,
  Interview,
  InterviewBookmark,
  InterviewNote,
  InterviewPlan,
  InterviewQuestionAdminListItem,
  InterviewQuestionDetail,
  InterviewQuestionListItem,
  InterviewQuestionType,
  InterviewReviewResponse,
  InterviewTemplate,
  InterviewTemplateAdminListItem,
  ReadinessResponse,
  ReadinessSnapshot,
  RetryInterviewRequest,
  SubmitExcelExerciseResponse,
  UpdateInterviewNoteRequest,
  UpdateInterviewQuestionAdminRequest,
  UpdateInterviewTemplateAdminRequest,
  WeaknessFinding,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Interview & Assessment Engine (Phase 9) data layer — mirrors
 * features/case-studies/use-case-studies.ts's shape exactly: every mutation
 * writes the full updated resource straight into its query-key cache rather
 * than only invalidating, so the UI updates instantly without an extra
 * round trip.
 */

// --- Query keys --------------------------------------------------------------

export const interviewTemplatesQueryKey = ["interview-templates"] as const;
export const interviewTemplateQueryKey = (slug: string | undefined) => ["interview-template", slug ?? null] as const;
export const interviewTemplatesAdminQueryKey = ["interview-templates-admin"] as const;
export const interviewsQueryKey = ["interviews"] as const;
export const interviewQueryKey = (id: string | undefined) => ["interview", id ?? null] as const;
export const interviewReviewQueryKey = (id: string | undefined) => ["interview-review", id ?? null] as const;

export interface InterviewQuestionFilters {
  interview_type?: InterviewQuestionType;
  difficulty?: string;
  company_archetype?: string;
  tag?: string;
  search?: string;
  bookmarked_only?: boolean;
}

export const interviewQuestionsQueryKey = (filters?: InterviewQuestionFilters) =>
  ["interview-questions", filters ?? {}] as const;
export const interviewQuestionsAdminQueryKey = ["interview-questions-admin"] as const;
export const interviewQuestionQueryKey = (slug: string | undefined) => ["interview-question", slug ?? null] as const;
export const interviewReviewQueueQueryKey = ["interview-review-queue"] as const;
export const interviewBookmarksQueryKey = ["interview-bookmarks"] as const;
export const interviewNotesQueryKey = (targetId?: string) => ["interview-notes", targetId ?? null] as const;
export const readinessQueryKey = ["interview-readiness"] as const;
export const readinessHistoryQueryKey = ["interview-readiness-history"] as const;
export const weaknessesQueryKey = ["interview-weaknesses"] as const;
export const interviewPlanQueryKey = ["interview-plan"] as const;

function toSearchParams(params: Record<string, string | boolean | undefined>): string {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === false) continue;
    usp.set(key, String(value));
  }
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

// --- Templates -----------------------------------------------------------------

export function useInterviewTemplates() {
  return useQuery({
    queryKey: interviewTemplatesQueryKey,
    queryFn: () => apiClient.get<InterviewTemplate[]>("/interviews/templates"),
    staleTime: 60 * 1000,
  });
}

export function useInterviewTemplate(slug: string | undefined) {
  return useQuery({
    queryKey: interviewTemplateQueryKey(slug),
    queryFn: () => apiClient.get<InterviewTemplate>(`/interviews/templates/${slug}`),
    enabled: Boolean(slug),
  });
}

export function useInterviewTemplatesAdmin() {
  return useQuery({
    queryKey: interviewTemplatesAdminQueryKey,
    queryFn: () => apiClient.get<InterviewTemplateAdminListItem[]>("/interviews/templates/admin"),
  });
}

export function useUpdateInterviewTemplateAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateInterviewTemplateAdminRequest) =>
      apiClient.patch<InterviewTemplateAdminListItem>(`/interviews/templates/admin/${id}`, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: interviewTemplatesAdminQueryKey });
      void queryClient.invalidateQueries({ queryKey: interviewTemplatesQueryKey });
    },
  });
}

// --- Interview lifecycle ---------------------------------------------------

function writeInterviewCache(queryClient: QueryClient, interview: Interview) {
  queryClient.setQueryData(interviewQueryKey(interview.id), interview);
  void queryClient.invalidateQueries({ queryKey: interviewsQueryKey });
}

export function useInterviews() {
  return useQuery({
    queryKey: interviewsQueryKey,
    queryFn: () => apiClient.get<Interview[]>("/interviews"),
    staleTime: 15 * 1000,
  });
}

export function useInterview(id: string | undefined, options?: { refetchInterval?: number | false }) {
  return useQuery({
    queryKey: interviewQueryKey(id),
    queryFn: () => apiClient.get<Interview>(`/interviews/${id}`),
    enabled: Boolean(id),
    refetchInterval: options?.refetchInterval,
  });
}

export function useCreateInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateInterviewRequest) => apiClient.post<Interview>("/interviews", payload),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

export function useStartInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Interview>(`/interviews/${id}/start`),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

export function usePauseInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Interview>(`/interviews/${id}/pause`),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

export function useResumeInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Interview>(`/interviews/${id}/resume`),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

export function useAnswerInterviewQuestion(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AnswerInterviewQuestionRequest) =>
      apiClient.post<AnswerInterviewQuestionResponse>(`/interviews/${id}/answer`, payload),
    onSuccess: (result) => writeInterviewCache(queryClient, result.interview),
  });
}

export function useSubmitInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Interview>(`/interviews/${id}/submit`),
    onSuccess: (interview) => {
      writeInterviewCache(queryClient, interview);
      void queryClient.invalidateQueries({ queryKey: readinessQueryKey });
      void queryClient.invalidateQueries({ queryKey: readinessHistoryQueryKey });
    },
  });
}

export function useAbandonInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Interview>(`/interviews/${id}/abandon`),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

export function useInterviewReview(id: string | undefined) {
  return useQuery({
    queryKey: interviewReviewQueryKey(id),
    queryFn: () => apiClient.get<InterviewReviewResponse>(`/interviews/${id}/review`),
    enabled: Boolean(id),
  });
}

export function useRetryInterview(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RetryInterviewRequest) => apiClient.post<Interview>(`/interviews/${id}/retry`, payload),
    onSuccess: (interview) => writeInterviewCache(queryClient, interview),
  });
}

// --- Question catalog / bookmarks / notes / review queue ------------------------

export function useInterviewQuestions(filters?: InterviewQuestionFilters) {
  const qs = toSearchParams({ ...filters });
  return useQuery({
    queryKey: interviewQuestionsQueryKey(filters),
    queryFn: () => apiClient.get<InterviewQuestionListItem[]>(`/interview/questions${qs}`),
    staleTime: 30 * 1000,
  });
}

export function useInterviewQuestion(slug: string | undefined) {
  return useQuery({
    queryKey: interviewQuestionQueryKey(slug),
    queryFn: () => apiClient.get<InterviewQuestionDetail>(`/interview/questions/${slug}`),
    enabled: Boolean(slug),
  });
}

export function useInterviewQuestionsAdmin() {
  return useQuery({
    queryKey: interviewQuestionsAdminQueryKey,
    queryFn: () => apiClient.get<InterviewQuestionAdminListItem[]>("/interview/questions/admin"),
  });
}

export function useUpdateInterviewQuestionAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateInterviewQuestionAdminRequest) =>
      apiClient.patch<InterviewQuestionAdminListItem>(`/interview/questions/admin/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: interviewQuestionsAdminQueryKey }),
  });
}

export function useInterviewReviewQueue(limit = 20) {
  return useQuery({
    queryKey: [...interviewReviewQueueQueryKey, limit],
    queryFn: () => apiClient.get<DueReview[]>(`/interview/questions/review-queue?limit=${limit}`),
    staleTime: 60 * 1000,
  });
}

export function useInterviewBookmarks() {
  return useQuery({
    queryKey: interviewBookmarksQueryKey,
    queryFn: () => apiClient.get<InterviewBookmark[]>("/interview/bookmarks"),
  });
}

export function useCreateInterviewBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateBookmarkRequest) => apiClient.post<InterviewBookmark>("/interview/bookmarks", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: interviewBookmarksQueryKey });
      void queryClient.invalidateQueries({ queryKey: ["interview-questions"] });
      void queryClient.invalidateQueries({ queryKey: ["interview-question"] });
    },
  });
}

export function useDeleteInterviewBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/interview/bookmarks/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: interviewBookmarksQueryKey });
      void queryClient.invalidateQueries({ queryKey: ["interview-questions"] });
      void queryClient.invalidateQueries({ queryKey: ["interview-question"] });
    },
  });
}

export function useInterviewNotes(targetId?: string) {
  const qs = targetId ? `?target_id=${targetId}` : "";
  return useQuery({
    queryKey: interviewNotesQueryKey(targetId),
    queryFn: () => apiClient.get<InterviewNote[]>(`/interview/notes${qs}`),
  });
}

export function useCreateInterviewNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateInterviewNoteRequest) => apiClient.post<InterviewNote>("/interview/notes", payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["interview-notes"] }),
  });
}

export function useUpdateInterviewNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateInterviewNoteRequest) =>
      apiClient.patch<InterviewNote>(`/interview/notes/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["interview-notes"] }),
  });
}

export function useDeleteInterviewNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/interview/notes/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["interview-notes"] }),
  });
}

// --- Readiness / weaknesses / plan --------------------------------------------

export function useReadiness() {
  return useQuery({
    queryKey: readinessQueryKey,
    queryFn: () => apiClient.get<ReadinessResponse>("/interview/readiness"),
    staleTime: 30 * 1000,
  });
}

export function useReadinessHistory() {
  return useQuery({
    queryKey: readinessHistoryQueryKey,
    queryFn: () => apiClient.get<ReadinessSnapshot[]>("/interview/readiness/history"),
    staleTime: 30 * 1000,
  });
}

export function useWeaknesses() {
  return useQuery({
    queryKey: weaknessesQueryKey,
    queryFn: () => apiClient.get<WeaknessFinding[]>("/interview/recommendations/weaknesses"),
    staleTime: 30 * 1000,
  });
}

export function useInterviewPlan() {
  return useQuery({
    queryKey: interviewPlanQueryKey,
    queryFn: () => apiClient.get<InterviewPlan | null>("/interview/recommendations/plan"),
  });
}

export function useGenerateInterviewPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<InterviewPlan>("/interview/recommendations/plan"),
    onSuccess: (plan) => queryClient.setQueryData(interviewPlanQueryKey, plan),
  });
}

// --- Excel Lab (Phase 9) -------------------------------------------------------

export function useEvaluateWorkbook() {
  return useMutation({
    mutationFn: (sheets: ExcelSheet[]) =>
      apiClient.post<EvaluateWorkbookResponse>("/excel/evaluate", { sheets }),
  });
}

export function useExcelExerciseContent(slug: string | undefined) {
  return useQuery({
    queryKey: ["excel-exercise", slug ?? null],
    queryFn: () => apiClient.get<ExcelExerciseContent>(`/excel/exercises/${slug}`),
    enabled: Boolean(slug),
  });
}

export function useSubmitExcelExercise(slug: string) {
  return useMutation({
    mutationFn: (submittedSheets: ExcelSheet[]) =>
      apiClient.post<SubmitExcelExerciseResponse>(`/excel/exercises/${slug}/submit`, {
        submitted_sheets: submittedSheets,
      }),
  });
}
