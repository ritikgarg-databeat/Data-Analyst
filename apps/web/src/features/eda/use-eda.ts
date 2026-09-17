import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreateEdaWorkspaceRequest,
  CreateFindingRequest,
  EdaFindingSchema,
  EdaOverview,
  EdaQuestion,
  EdaWorkspaceSchema,
  UpdateEdaWorkspaceRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

const workspacesKey = ["eda-workspaces"] as const;
const workspaceKey = (id: string | undefined) => ["eda-workspaces", id] as const;

export function useEdaWorkspaces() {
  return useQuery({
    queryKey: workspacesKey,
    queryFn: () => apiClient.get<EdaWorkspaceSchema[]>("/eda-workspaces"),
    staleTime: 30 * 1000,
  });
}

export function useEdaWorkspace(id: string | undefined) {
  return useQuery({
    queryKey: workspaceKey(id),
    queryFn: () => apiClient.get<EdaWorkspaceSchema>(`/eda-workspaces/${id}`),
    enabled: Boolean(id),
    staleTime: 15 * 1000,
  });
}

export function useCreateEdaWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateEdaWorkspaceRequest) =>
      apiClient.post<EdaWorkspaceSchema>("/eda-workspaces", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}

export function useUpdateEdaWorkspace(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateEdaWorkspaceRequest) =>
      apiClient.patch<EdaWorkspaceSchema>(`/eda-workspaces/${id}`, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(workspaceKey(id), updated);
      void queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}

export function useDeleteEdaWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/eda-workspaces/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspacesKey });
    },
  });
}

/** Runs the deterministic "Generate EDA Overview" action and persists it on the workspace. */
export function useGenerateOverview(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<EdaOverview>(`/eda-workspaces/${id}/overview`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKey(id) });
    },
  });
}

export function useWorkspaceQuestions(id: string | undefined) {
  return useQuery({
    queryKey: ["eda-workspaces", id, "questions"],
    queryFn: () => apiClient.get<EdaQuestion[]>(`/eda-workspaces/${id}/questions`),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useAddFinding(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateFindingRequest) =>
      apiClient.post<EdaFindingSchema>(`/eda-workspaces/${workspaceId}/findings`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKey(workspaceId) });
    },
  });
}

export function useDeleteFinding(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (findingId: string) =>
      apiClient.delete<void>(`/eda-workspaces/${workspaceId}/findings/${findingId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKey(workspaceId) });
    },
  });
}

/** Dataset-level convenience — the automatic overview/questions without a saved workspace. */
export function useDatasetEdaOverview(datasetId: string | undefined, table: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["eda", datasetId, "overview", table],
    queryFn: () =>
      apiClient.get<EdaOverview>(`/eda/${datasetId}${table ? `?table=${encodeURIComponent(table)}` : ""}`),
    enabled: Boolean(datasetId) && enabled,
    staleTime: 30 * 1000,
  });
}
