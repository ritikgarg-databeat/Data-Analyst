import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreateResumeRequest,
  CreateResumeVersionRequest,
  Resume,
  ResumeEvidence,
  ResumeGapAnalysisResponse,
  ResumeReview,
  ResumeVersion,
  UpdateResumeRequest,
} from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";
import { useToast } from "@/components/shared/toast-provider";

function errorToastFromMutation(error: unknown) {
  return {
    title: "Couldn't save this resume version",
    description: error instanceof ApiError ? error.message : "An unexpected error occurred.",
    variant: "error" as const,
  };
}

/**
 * Resume Intelligence (Phase 11) data layer — mirrors
 * features/interview/use-interview.ts's shape. `Resume` list items only carry
 * a version summary (no raw_text/evidence/reviews) — full version detail is
 * fetched and cached separately via `resumeVersionQueryKey`.
 */

export const resumesQueryKey = ["resumes"] as const;
export const resumeVersionQueryKey = (versionId: string | undefined) => ["resume-version", versionId ?? null] as const;
export const resumeGapAnalysisQueryKey = (versionId: string | undefined, targetRoleId: string | undefined) =>
  ["resume-gap-analysis", versionId ?? null, targetRoleId ?? null] as const;

// --- Resumes ---------------------------------------------------------------------

export function useResumes() {
  return useQuery({
    queryKey: resumesQueryKey,
    queryFn: () => apiClient.get<Resume[]>("/resume"),
  });
}

export function useCreateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateResumeRequest) => apiClient.post<Resume>("/resume", payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: resumesQueryKey }),
  });
}

export function useUpdateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdateResumeRequest) =>
      apiClient.patch<Resume>(`/resume/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: resumesQueryKey }),
  });
}

export function useDeleteResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/resume/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: resumesQueryKey }),
  });
}

// --- Resume versions ---------------------------------------------------------------

export function useCreateResumeVersion(resumeId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  return useMutation({
    mutationFn: (payload: CreateResumeVersionRequest) =>
      apiClient.post<ResumeVersion>(`/resume/${resumeId}/versions`, payload),
    onSuccess: (version) => {
      queryClient.setQueryData(resumeVersionQueryKey(version.id), version);
      void queryClient.invalidateQueries({ queryKey: resumesQueryKey });
    },
    onError: (error) => toast(errorToastFromMutation(error)),
  });
}

/**
 * Uploads a real file (.txt/.md/.docx/.pdf) — the server extracts genuine
 * text (see app/core/file_extraction.py) rather than the browser reading
 * `file.text()`, which silently produced garbage (even a save-breaking NUL
 * byte) for any non-plain-text file.
 */
export function useUploadResumeVersion(resumeId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  return useMutation({
    mutationFn: (file: File) =>
      apiClient.postFile<ResumeVersion>(`/resume/${resumeId}/versions/upload`, file),
    onSuccess: (version) => {
      queryClient.setQueryData(resumeVersionQueryKey(version.id), version);
      void queryClient.invalidateQueries({ queryKey: resumesQueryKey });
    },
    onError: (error) => toast(errorToastFromMutation(error)),
  });
}

export function useResumeVersion(versionId: string | undefined) {
  return useQuery({
    queryKey: resumeVersionQueryKey(versionId),
    queryFn: () => apiClient.get<ResumeVersion>(`/resume/versions/${versionId}`),
    enabled: Boolean(versionId),
  });
}

export function useExtractResumeEvidence(versionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<ResumeEvidence[]>(`/resume/versions/${versionId}/extract-evidence`),
    onSuccess: (evidence) => {
      queryClient.setQueryData<ResumeVersion | undefined>(resumeVersionQueryKey(versionId), (prev) =>
        prev ? { ...prev, evidence } : prev,
      );
    },
  });
}

export function useReviewResumeVersion(versionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetRoleTitle?: string) => {
      const qs = targetRoleTitle ? `?target_role_title=${encodeURIComponent(targetRoleTitle)}` : "";
      return apiClient.post<ResumeReview>(`/resume/versions/${versionId}/review${qs}`);
    },
    onSuccess: (review) => {
      queryClient.setQueryData<ResumeVersion | undefined>(resumeVersionQueryKey(versionId), (prev) =>
        prev ? { ...prev, reviews: [review, ...prev.reviews] } : prev,
      );
    },
  });
}

export function useResumeGapAnalysis(versionId: string | undefined, targetRoleId: string | undefined) {
  return useQuery({
    queryKey: resumeGapAnalysisQueryKey(versionId, targetRoleId),
    queryFn: () =>
      apiClient.get<ResumeGapAnalysisResponse>(
        `/resume/versions/${versionId}/gap-analysis?target_role_id=${targetRoleId}`,
      ),
    enabled: Boolean(versionId) && Boolean(targetRoleId),
  });
}
