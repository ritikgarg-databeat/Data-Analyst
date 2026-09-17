import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import type {
  AIChatResponse,
  AIConversation,
  AIConversationListItem,
  AIExecSummaryResult,
  AIKnowledgeAnswerResult,
  AIMistakeMemory,
  AIPlanExplanationResult,
  AISettings,
  AISkillDiagnosis,
  AISkillDiagnosisResult,
  AIStructuredResponse,
  AIUsage,
  AskMentorRequest,
  BehavioralInterviewerTurnRequest,
  CaseCoachRequest,
  CaseInterviewerTurnRequest,
  CommunicationReviewRequest,
  DebugSqlRequest,
  DomainCoachRequest,
  EdaAssistRequest,
  ExecSummaryRequest,
  HintLevelRequest,
  NlToPythonRequest,
  NlToSqlRequest,
  OptimizeSqlRequest,
  PlanExplanationRequest,
  ReviewAnalysisRequest,
  ReviewInsightRequest,
  ReviewPythonRequest,
  ReviewSqlRequest,
  SkillDiagnosisRequest,
  StorytellingReviewRequest,
  UpdateAISettingsRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * AI Layer (Phase 10) data layer — mirrors features/interview/use-interview.ts
 * and features/case-studies/use-case-studies.ts conventions. Most AI
 * endpoints are one-shot request/response (review/coach/debug calls), so
 * most mutations here just invalidate usage + (when they're conversational)
 * the conversation list/detail, rather than writing a long-lived cached
 * resource the way CaseAttempt/Interview mutations do.
 */

export const aiSettingsQueryKey = ["ai-settings"] as const;
export const aiUsageQueryKey = ["ai-usage"] as const;
export const aiConversationsQueryKey = ["ai-conversations"] as const;
export const aiConversationQueryKey = (id: string | undefined) => ["ai-conversation", id ?? null] as const;
export const aiMistakesQueryKey = ["ai-mistakes"] as const;
export const aiSkillDiagnosesQueryKey = ["ai-skill-diagnoses"] as const;

function invalidateAfterAIRequest(queryClient: QueryClient, conversationId?: string) {
  void queryClient.invalidateQueries({ queryKey: aiUsageQueryKey });
  if (conversationId) {
    void queryClient.invalidateQueries({ queryKey: aiConversationsQueryKey });
    void queryClient.invalidateQueries({ queryKey: aiConversationQueryKey(conversationId) });
  }
}

// --- Settings / usage --------------------------------------------------------

export function useAISettings() {
  return useQuery({ queryKey: aiSettingsQueryKey, queryFn: () => apiClient.get<AISettings>("/ai/settings") });
}

export function useUpdateAISettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateAISettingsRequest) => apiClient.patch<AISettings>("/ai/settings", payload),
    onSuccess: (settings) => queryClient.setQueryData(aiSettingsQueryKey, settings),
  });
}

export function useAIUsage() {
  return useQuery({ queryKey: aiUsageQueryKey, queryFn: () => apiClient.get<AIUsage>("/ai/usage"), staleTime: 15_000 });
}

// --- Conversations -------------------------------------------------------------

export function useAIConversations() {
  return useQuery({
    queryKey: aiConversationsQueryKey,
    queryFn: () => apiClient.get<AIConversationListItem[]>("/ai/conversations"),
  });
}

export function useAIConversation(conversationId: string | undefined) {
  return useQuery({
    queryKey: aiConversationQueryKey(conversationId),
    queryFn: () => apiClient.get<AIConversation>(`/ai/conversations/${conversationId}`),
    enabled: Boolean(conversationId),
  });
}

export function useDeleteAIConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: string) => apiClient.delete(`/ai/conversations/${conversationId}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: aiConversationsQueryKey }),
  });
}

// --- Mentor + Socratic hints ---------------------------------------------------

export function useAskMentor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AskMentorRequest) => apiClient.post<AIChatResponse>("/ai/mentor", payload),
    onSuccess: (response) => invalidateAfterAIRequest(queryClient, response.conversation_id),
  });
}

export function useSendHint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: HintLevelRequest) => apiClient.post<AIChatResponse>("/ai/mentor/hint", payload),
    onSuccess: (response) => invalidateAfterAIRequest(queryClient, response.conversation_id),
  });
}

// --- SQL ---------------------------------------------------------------------

export function useReviewSql() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReviewSqlRequest) => apiClient.post<AIStructuredResponse>("/ai/sql/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useDebugSql() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DebugSqlRequest) => apiClient.post<AIStructuredResponse>("/ai/sql/debug", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useOptimizeSql() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OptimizeSqlRequest) => apiClient.post<AIStructuredResponse>("/ai/sql/optimize", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useNlToSql() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: NlToSqlRequest) => apiClient.post<AIStructuredResponse>("/ai/sql/nl-to-sql", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Python ------------------------------------------------------------------

export function useReviewPython() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReviewPythonRequest) => apiClient.post<AIStructuredResponse>("/ai/python/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useNlToPython() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: NlToPythonRequest) => apiClient.post<AIStructuredResponse>("/ai/python/nl-to-python", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Analysis / Insight / EDA -------------------------------------------------

export function useReviewAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReviewAnalysisRequest) => apiClient.post<AIStructuredResponse>("/ai/analysis/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useReviewInsight() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReviewInsightRequest) => apiClient.post<AIStructuredResponse>("/ai/insight/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useEdaAssist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EdaAssistRequest) => apiClient.post<AIStructuredResponse>("/ai/eda/assist", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useExploreWithAI() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EdaAssistRequest) => apiClient.post<AIStructuredResponse>("/ai/eda/explore", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Domain coaches ------------------------------------------------------------

export function useDomainCoach() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DomainCoachRequest) => apiClient.post<AIStructuredResponse>("/ai/coach/domain", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Knowledge search (RAG) ----------------------------------------------------

export function useKnowledgeSearch(query: string, limit = 5) {
  return useQuery({
    queryKey: ["ai-knowledge-search", query, limit] as const,
    queryFn: () => apiClient.get<AIKnowledgeAnswerResult>(`/ai/knowledge/search?q=${encodeURIComponent(query)}&limit=${limit}`),
    enabled: query.trim().length > 0,
    staleTime: 60_000,
  });
}

// --- Mistake memory + skill diagnoses -------------------------------------------

export function useAIMistakes() {
  return useQuery({ queryKey: aiMistakesQueryKey, queryFn: () => apiClient.get<AIMistakeMemory[]>("/ai/mistakes") });
}

export function useDeleteAIMistake() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mistakeId: string) => apiClient.delete(`/ai/mistakes/${mistakeId}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: aiMistakesQueryKey }),
  });
}

export function useAISkillDiagnoses(skillSlug?: string) {
  return useQuery({
    queryKey: [...aiSkillDiagnosesQueryKey, skillSlug ?? null] as const,
    queryFn: () =>
      apiClient.get<AISkillDiagnosis[]>(`/ai/skill-diagnoses${skillSlug ? `?skill_slug=${encodeURIComponent(skillSlug)}` : ""}`),
  });
}

export function useDiagnoseSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SkillDiagnosisRequest) => apiClient.post<AISkillDiagnosisResult>("/ai/skill-diagnosis", payload),
    onSuccess: () => {
      invalidateAfterAIRequest(queryClient);
      void queryClient.invalidateQueries({ queryKey: aiSkillDiagnosesQueryKey });
    },
  });
}

// --- Case Coach / Case Interviewer -----------------------------------------------

export function useCaseCoach(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CaseCoachRequest) => apiClient.post<AIChatResponse>(`/ai/cases/${attemptId}/coach`, payload),
    onSuccess: (response) => invalidateAfterAIRequest(queryClient, response.conversation_id),
  });
}

export function useCaseInterviewerTurn(attemptId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CaseInterviewerTurnRequest) =>
      apiClient.post<AIChatResponse>(`/ai/cases/${attemptId}/interviewer`, payload),
    onSuccess: (response) => invalidateAfterAIRequest(queryClient, response.conversation_id),
  });
}

// --- Behavioral Interviewer / Interview Debrief -------------------------------------

export function useBehavioralInterviewerTurn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BehavioralInterviewerTurnRequest) =>
      apiClient.post<AIChatResponse>("/ai/interviews/behavioral-turn", payload),
    onSuccess: (response) => invalidateAfterAIRequest(queryClient, response.conversation_id),
  });
}

export function useInterviewDebrief(interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<AIStructuredResponse>(`/ai/interviews/${interviewId}/debrief`),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Communication / Storytelling / Executive Summary --------------------------------

export function useCommunicationReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CommunicationReviewRequest) => apiClient.post<AIStructuredResponse>("/ai/communication/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useStorytellingReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StorytellingReviewRequest) => apiClient.post<AIStructuredResponse>("/ai/storytelling/review", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

export function useExecSummary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ExecSummaryRequest) => apiClient.post<AIExecSummaryResult>("/ai/communication/exec-summary", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Learning Planner explanation ------------------------------------------------------

export function useExplainPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PlanExplanationRequest) => apiClient.post<AIPlanExplanationResult>("/ai/plan/explain", payload),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}

// --- Project Review -----------------------------------------------------------------------

export function useProjectReview(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<AIStructuredResponse>(`/ai/projects/${projectId}/review`),
    onSuccess: () => invalidateAfterAIRequest(queryClient),
  });
}
