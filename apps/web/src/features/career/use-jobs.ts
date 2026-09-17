import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import type {
  AnalyzeJDRequest,
  CreateJobDescriptionRequest,
  CreateJobWorkspaceRequest,
  JDAnalysis,
  JDComparisonResponse,
  JDInterviewPlanResponse,
  JDPreparationPlanResponse,
  JDRequirement,
  JobDescription,
  JobPreparationWorkspace,
  SkillGapsResponse,
  UpdateJobDescriptionRequest,
  UpdateJobWorkspaceRequest,
} from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";
import { useToast } from "@/components/shared/toast-provider";

function errorToastFromMutation(error: unknown) {
  return {
    title: "Couldn't save this job description",
    description: error instanceof ApiError ? error.message : "An unexpected error occurred.",
    variant: "error" as const,
  };
}

/**
 * Job Description Intelligence & Preparation (Phase 11) data layer — mirrors
 * features/interview/use-interview.ts's shape: every mutation that returns
 * the full updated `JobDescription` writes it straight into
 * `jobDescriptionQueryKey(id)`'s cache rather than only invalidating.
 */

export const jobDescriptionsQueryKey = ["job-descriptions"] as const;
export const jobDescriptionQueryKey = (id: string | undefined) => ["job-description", id ?? null] as const;
export const jobDescriptionCompareQueryKey = (ids: string[]) => ["job-descriptions-compare", [...ids].sort()] as const;
export const jdSkillGapsQueryKey = (id: string | undefined) => ["job-description-skill-gaps", id ?? null] as const;
export const jdAnalysisQueryKey = (id: string | undefined) => ["job-description-analysis", id ?? null] as const;
export const jdPreparationPlanQueryKey = (id: string | undefined) =>
  ["job-description-preparation-plan", id ?? null] as const;
export const jdInterviewPlanQueryKey = (id: string | undefined) =>
  ["job-description-interview-plan", id ?? null] as const;
export const jobWorkspacesQueryKey = ["job-workspaces"] as const;

function writeJobDescriptionCache(queryClient: QueryClient, jd: JobDescription) {
  queryClient.setQueryData(jobDescriptionQueryKey(jd.id), jd);
  void queryClient.invalidateQueries({ queryKey: jobDescriptionsQueryKey });
}

// --- Job descriptions ------------------------------------------------------------

export function useJobDescriptions() {
  return useQuery({
    queryKey: jobDescriptionsQueryKey,
    queryFn: () => apiClient.get<JobDescription[]>("/jobs/descriptions"),
  });
}

export function useJobDescription(id: string | undefined) {
  return useQuery({
    queryKey: jobDescriptionQueryKey(id),
    queryFn: () => apiClient.get<JobDescription>(`/jobs/descriptions/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateJobDescription() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  return useMutation({
    mutationFn: (payload: CreateJobDescriptionRequest) =>
      apiClient.post<JobDescription>("/jobs/descriptions", payload),
    onSuccess: (jd) => writeJobDescriptionCache(queryClient, jd),
    onError: (error) => toast(errorToastFromMutation(error)),
  });
}

/**
 * Uploads a real file (.txt/.md/.docx/.pdf) — the server extracts genuine
 * text (see app/core/file_extraction.py) rather than the browser reading
 * `file.text()`, which silently produced garbage (even a save-breaking NUL
 * byte) for any non-plain-text file.
 */
interface UploadJobDescriptionInput {
  file: File;
  title: string;
  company?: string;
  location?: string;
  notes?: string;
}

export function useUploadJobDescription() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  return useMutation({
    mutationFn: ({ file, title, company, location, notes }: UploadJobDescriptionInput) =>
      apiClient.postFile<JobDescription>("/jobs/descriptions/upload", file, {
        title,
        ...(company ? { company } : {}),
        ...(location ? { location } : {}),
        ...(notes ? { notes } : {}),
      }),
    onSuccess: (jd) => writeJobDescriptionCache(queryClient, jd),
    onError: (error) => toast(errorToastFromMutation(error)),
  });
}

export function useUpdateJobDescription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateJobDescriptionRequest) =>
      apiClient.patch<JobDescription>(`/jobs/descriptions/${id}`, body),
    onSuccess: (jd) => writeJobDescriptionCache(queryClient, jd),
  });
}

export function useDeleteJobDescription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/jobs/descriptions/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: jobDescriptionsQueryKey }),
  });
}

export function useCompareJobDescriptions(ids: string[]) {
  const qs = [...ids].sort().join(",");
  return useQuery({
    queryKey: jobDescriptionCompareQueryKey(ids),
    queryFn: () => apiClient.get<JDComparisonResponse>(`/jobs/descriptions/compare?jd_ids=${qs}`),
    enabled: ids.length >= 2,
  });
}

// --- Extraction / gaps / analysis / plans --------------------------------------

export function useExtractJDRequirements(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<JDRequirement[]>(`/jobs/descriptions/${id}/extract`),
    onSuccess: (requirements) => {
      queryClient.setQueryData<JobDescription | undefined>(jobDescriptionQueryKey(id), (prev) =>
        prev ? { ...prev, requirements } : prev,
      );
      void queryClient.invalidateQueries({ queryKey: jdSkillGapsQueryKey(id) });
    },
  });
}

export function useJDSkillGaps(id: string | undefined) {
  return useQuery({
    queryKey: jdSkillGapsQueryKey(id),
    queryFn: () => apiClient.get<SkillGapsResponse>(`/jobs/descriptions/${id}/skill-gaps`),
    enabled: Boolean(id),
    staleTime: 0, // always recomputed fresh server-side
  });
}

export function useAnalyzeJD(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AnalyzeJDRequest = {}) => apiClient.post<JDAnalysis>(`/jobs/descriptions/${id}/analyze`, payload),
    onSuccess: (analysis) => queryClient.setQueryData(jdAnalysisQueryKey(id), analysis),
  });
}

export function useJDAnalysis(id: string | undefined) {
  return useQuery({
    queryKey: jdAnalysisQueryKey(id),
    queryFn: () => apiClient.get<JDAnalysis | null>(`/jobs/descriptions/${id}/analysis`),
    enabled: Boolean(id),
  });
}

export function useJDPreparationPlan(id: string | undefined) {
  return useQuery({
    queryKey: jdPreparationPlanQueryKey(id),
    queryFn: () => apiClient.get<JDPreparationPlanResponse>(`/jobs/descriptions/${id}/preparation-plan`),
    enabled: Boolean(id),
  });
}

export function useJDInterviewPlan(id: string | undefined) {
  return useQuery({
    queryKey: jdInterviewPlanQueryKey(id),
    queryFn: () => apiClient.get<JDInterviewPlanResponse>(`/jobs/descriptions/${id}/interview-plan`),
    enabled: Boolean(id),
  });
}

// --- Job preparation workspaces --------------------------------------------------

export function useJobWorkspaces() {
  return useQuery({
    queryKey: jobWorkspacesQueryKey,
    queryFn: () => apiClient.get<JobPreparationWorkspace[]>("/jobs/workspaces"),
  });
}

export function useCreateJobWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateJobWorkspaceRequest) =>
      apiClient.post<JobPreparationWorkspace>("/jobs/workspaces", payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: jobWorkspacesQueryKey }),
  });
}

export function useUpdateJobWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateJobWorkspaceRequest) =>
      apiClient.patch<JobPreparationWorkspace>(`/jobs/workspaces/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: jobWorkspacesQueryKey }),
  });
}
