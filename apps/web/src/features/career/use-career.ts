import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import type {
  Achievement,
  BehavioralStory,
  BehavioralStoryCoverageResponse,
  CareerAssessment,
  CareerCoachRequest,
  CareerDashboardResponse,
  CareerGoal,
  CareerMilestone,
  CareerNote,
  CareerProfile,
  CareerReportSchema,
  CareerSkillMatrixEntry,
  CareerWeeklyReviewResponse,
  ComputeCareerAssessmentRequest,
  CreateBehavioralStoryRequest,
  CreateCareerGoalRequest,
  CreateCareerNoteRequest,
  CreateTargetRoleRequest,
  AIChatResponse,
  RoleTemplate,
  TargetRole,
  UpdateBehavioralStoryRequest,
  UpdateCareerGoalRequest,
  UpdateCareerNoteRequest,
  UpdateCareerProfileRequest,
  UserAchievement,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Career Readiness, Portfolio & Job Preparation (Phase 11) data layer —
 * mirrors features/interview/use-interview.ts's shape: query-key
 * constants/factories, and mutations that write the full updated resource
 * straight into the cache (singletons via `setQueryData`, lists via
 * invalidation) rather than only invalidating everywhere, so the UI updates
 * instantly without an extra round trip.
 */

// --- Profile / dashboard / weekly review / report -----------------------------

export const careerProfileQueryKey = ["career-profile"] as const;
export const careerDashboardQueryKey = ["career-dashboard"] as const;
export const careerWeeklyReviewQueryKey = ["career-weekly-review"] as const;
export const careerReportQueryKey = ["career-report"] as const;

export function useCareerProfile() {
  return useQuery({
    queryKey: careerProfileQueryKey,
    queryFn: () => apiClient.get<CareerProfile>("/career/profile"),
  });
}

export function useUpdateCareerProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateCareerProfileRequest) => apiClient.patch<CareerProfile>("/career/profile", payload),
    onSuccess: (profile) => {
      queryClient.setQueryData(careerProfileQueryKey, profile);
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

export function useCareerDashboard() {
  return useQuery({
    queryKey: careerDashboardQueryKey,
    queryFn: () => apiClient.get<CareerDashboardResponse>("/career/dashboard"),
    staleTime: 15 * 1000,
  });
}

export function useCareerWeeklyReview() {
  return useQuery({
    queryKey: careerWeeklyReviewQueryKey,
    queryFn: () => apiClient.get<CareerWeeklyReviewResponse>("/career/weekly-review"),
    staleTime: 60 * 1000,
  });
}

/** Fetched on demand from the "Open Career Report" button, not on page load. */
export function useCareerReport(enabled: boolean) {
  return useQuery({
    queryKey: careerReportQueryKey,
    queryFn: () => apiClient.get<CareerReportSchema>("/career/report"),
    enabled,
  });
}

// --- Role templates / target roles --------------------------------------------

export const roleTemplatesQueryKey = ["career-role-templates"] as const;
export const targetRolesQueryKey = ["career-target-roles"] as const;

export function useRoleTemplates() {
  return useQuery({
    queryKey: roleTemplatesQueryKey,
    queryFn: () => apiClient.get<RoleTemplate[]>("/career/role-templates"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useTargetRoles() {
  return useQuery({
    queryKey: targetRolesQueryKey,
    queryFn: () => apiClient.get<TargetRole[]>("/career/target-roles"),
  });
}

export function useCreateTargetRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTargetRoleRequest) => apiClient.post<TargetRole>("/career/target-roles", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: targetRolesQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

export function useDeleteTargetRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/career/target-roles/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: targetRolesQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

// --- Readiness assessment / skill matrix --------------------------------------

export const careerAssessmentLatestQueryKey = ["career-assessment-latest"] as const;
export const careerAssessmentHistoryQueryKey = ["career-assessment-history"] as const;
export const careerSkillMatrixQueryKey = ["career-skill-matrix"] as const;

export function useLatestCareerAssessment() {
  return useQuery({
    queryKey: careerAssessmentLatestQueryKey,
    queryFn: () => apiClient.get<CareerAssessment | null>("/career/readiness/latest"),
  });
}

export function useCareerAssessmentHistory() {
  return useQuery({
    queryKey: careerAssessmentHistoryQueryKey,
    queryFn: () => apiClient.get<CareerAssessment[]>("/career/readiness/history"),
  });
}

export function useComputeCareerAssessment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ComputeCareerAssessmentRequest = {}) =>
      apiClient.post<CareerAssessment>("/career/readiness/compute", payload),
    onSuccess: (assessment) => {
      queryClient.setQueryData(careerAssessmentLatestQueryKey, assessment);
      void queryClient.invalidateQueries({ queryKey: careerAssessmentHistoryQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

export function useCareerSkillMatrix() {
  return useQuery({
    queryKey: careerSkillMatrixQueryKey,
    queryFn: () => apiClient.get<CareerSkillMatrixEntry[]>("/career/skill-matrix"),
    staleTime: 30 * 1000,
  });
}

// --- Goals ---------------------------------------------------------------------

export const careerGoalsQueryKey = ["career-goals"] as const;

export function useCareerGoals() {
  return useQuery({
    queryKey: careerGoalsQueryKey,
    queryFn: () => apiClient.get<CareerGoal[]>("/career/goals"),
  });
}

export function useCreateCareerGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCareerGoalRequest) => apiClient.post<CareerGoal>("/career/goals", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: careerGoalsQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

export function useUpdateCareerGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateCareerGoalRequest) =>
      apiClient.patch<CareerGoal>(`/career/goals/${id}`, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: careerGoalsQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

export function useDeleteCareerGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/career/goals/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: careerGoalsQueryKey });
      void queryClient.invalidateQueries({ queryKey: careerDashboardQueryKey });
    },
  });
}

// --- Timeline / achievements -----------------------------------------------------

export const careerTimelineQueryKey = ["career-timeline"] as const;
export const achievementsQueryKey = ["career-achievements"] as const;
export const earnedAchievementsQueryKey = ["career-achievements-earned"] as const;

export function useCareerTimeline() {
  return useQuery({
    queryKey: careerTimelineQueryKey,
    queryFn: () => apiClient.get<CareerMilestone[]>("/career/timeline"),
  });
}

export function useAchievements() {
  return useQuery({
    queryKey: achievementsQueryKey,
    queryFn: () => apiClient.get<Achievement[]>("/career/achievements"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useEarnedAchievements() {
  return useQuery({
    queryKey: earnedAchievementsQueryKey,
    queryFn: () => apiClient.get<UserAchievement[]>("/career/achievements/earned"),
  });
}

// --- Behavioral story bank -----------------------------------------------------

export const behavioralStoriesQueryKey = ["career-behavioral-stories"] as const;
export const behavioralStoryCoverageQueryKey = ["career-behavioral-story-coverage"] as const;

function invalidateBehavioralStories(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: behavioralStoriesQueryKey });
  void queryClient.invalidateQueries({ queryKey: behavioralStoryCoverageQueryKey });
}

export function useBehavioralStories() {
  return useQuery({
    queryKey: behavioralStoriesQueryKey,
    queryFn: () => apiClient.get<BehavioralStory[]>("/career/behavioral-stories"),
  });
}

export function useCreateBehavioralStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateBehavioralStoryRequest) =>
      apiClient.post<BehavioralStory>("/career/behavioral-stories", payload),
    onSuccess: () => invalidateBehavioralStories(queryClient),
  });
}

export function useUpdateBehavioralStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateBehavioralStoryRequest) =>
      apiClient.patch<BehavioralStory>(`/career/behavioral-stories/${id}`, body),
    onSuccess: () => invalidateBehavioralStories(queryClient),
  });
}

export function useDeleteBehavioralStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/career/behavioral-stories/${id}`),
    onSuccess: () => invalidateBehavioralStories(queryClient),
  });
}

export function usePracticeBehavioralStory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<BehavioralStory>(`/career/behavioral-stories/${id}/practice`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: behavioralStoriesQueryKey }),
  });
}

export function useBehavioralStoryCoverage() {
  return useQuery({
    queryKey: behavioralStoryCoverageQueryKey,
    queryFn: () => apiClient.get<BehavioralStoryCoverageResponse>("/career/behavioral-stories/coverage"),
  });
}

// --- Career knowledge base notes -----------------------------------------------

export const careerNotesQueryKey = (q?: string) => ["career-notes", q ?? null] as const;

export function useCareerNotes(q?: string) {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  return useQuery({
    queryKey: careerNotesQueryKey(q),
    queryFn: () => apiClient.get<CareerNote[]>(`/career/notes${qs}`),
  });
}

export function useCreateCareerNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCareerNoteRequest) => apiClient.post<CareerNote>("/career/notes", payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["career-notes"] }),
  });
}

export function useUpdateCareerNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateCareerNoteRequest) =>
      apiClient.patch<CareerNote>(`/career/notes/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["career-notes"] }),
  });
}

export function useDeleteCareerNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/career/notes/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["career-notes"] }),
  });
}

// --- AI Career Coach -------------------------------------------------------------

/** Thin chat mutation — the panel keeps its own local message list rather than
 * a server-fetched conversation history (no `GET /career/coach` list exists). */
export function useCareerCoach() {
  return useMutation({
    mutationFn: (payload: CareerCoachRequest) => apiClient.post<AIChatResponse>("/career/coach", payload),
  });
}
