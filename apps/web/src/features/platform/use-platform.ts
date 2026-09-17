import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  BackupBundle,
  NextBestActionResponse,
  RestoreRequest,
  RestoreResponse,
  RestorePreviewResponse,
  SystemHealthResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Phase 12 cross-cutting platform data layer — Next Best Action, System
 * Health, and Backup/Restore. Mirrors features/interview/use-interview.ts's
 * conventions (query-key constants, apiClient-backed useQuery/useMutation).
 * Backup/restore are one-shot actions rather than cached resources, so they
 * are mutations, not queries.
 */

export const nextBestActionsQueryKey = (limit: number) => ["platform-next-best-actions", limit] as const;
export const systemHealthQueryKey = ["platform-health"] as const;

export function useNextBestActions(limit = 3) {
  return useQuery({
    queryKey: nextBestActionsQueryKey(limit),
    queryFn: () => apiClient.get<NextBestActionResponse>(`/platform/next-best-actions?limit=${limit}`),
    staleTime: 30 * 1000,
    retry: 1,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: systemHealthQueryKey,
    queryFn: () => apiClient.get<SystemHealthResponse>("/platform/health"),
    staleTime: 15 * 1000,
    retry: 1,
  });
}

/** Fetches the downloadable backup bundle — the caller triggers the Blob download on success. */
export function useCreateBackup() {
  return useMutation({
    mutationFn: () => apiClient.get<BackupBundle>("/platform/backup"),
  });
}

/** Always call this before offering to restore — surfaces `issues` for the user to review. */
export function usePreviewRestore() {
  return useMutation({
    mutationFn: (bundle: BackupBundle) => apiClient.post<RestorePreviewResponse>("/platform/restore/preview", bundle),
  });
}

/** Requires an explicit user confirmation upstream — `confirm: true` is enforced by RestoreRequest's type. */
export function useRestore() {
  return useMutation({
    mutationFn: (payload: RestoreRequest) => apiClient.post<RestoreResponse>("/platform/restore", payload),
  });
}
