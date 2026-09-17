import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreatePythonCellRequest,
  PythonCellSchema,
  PythonExecutionResultSchema,
  UpdatePythonCellRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonCellsQueryKey(workspaceId: string) {
  return ["python", "workspaces", workspaceId, "cells"] as const;
}

/** Lists a workspace's cells, in `display_order`. */
export function usePythonCells(workspaceId: string | null) {
  return useQuery({
    queryKey: pythonCellsQueryKey(workspaceId ?? ""),
    queryFn: () => apiClient.get<PythonCellSchema[]>(`/python/workspaces/${workspaceId}/cells`),
    enabled: Boolean(workspaceId),
    staleTime: 10 * 1000,
  });
}

/** Appends a new (usually empty) cell to a workspace. */
export function useAddPythonCell() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, body = {} }: { workspaceId: string; body?: CreatePythonCellRequest }) =>
      apiClient.post<PythonCellSchema>(`/python/workspaces/${workspaceId}/cells`, body),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: pythonCellsQueryKey(variables.workspaceId) });
    },
  });
}

/** Edits a cell's code and/or reorders it (`display_order`). */
export function useUpdatePythonCell() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      cellId,
      body,
    }: {
      workspaceId: string;
      cellId: string;
      body: UpdatePythonCellRequest;
    }) => apiClient.patch<PythonCellSchema>(`/python/workspaces/${workspaceId}/cells/${cellId}`, body),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: pythonCellsQueryKey(variables.workspaceId) });
    },
  });
}

/** Persists a cell's last execution result (so reloading the workspace shows the same output). */
export function useRecordPythonCellResult() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      cellId,
      result,
    }: {
      workspaceId: string;
      cellId: string;
      result: PythonExecutionResultSchema;
    }) => apiClient.post<PythonCellSchema>(`/python/workspaces/${workspaceId}/cells/${cellId}/result`, { result }),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: pythonCellsQueryKey(variables.workspaceId) });
    },
  });
}

/** Deletes a cell. */
export function useDeletePythonCell() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, cellId }: { workspaceId: string; cellId: string }) =>
      apiClient.delete<void>(`/python/workspaces/${workspaceId}/cells/${cellId}`),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: pythonCellsQueryKey(variables.workspaceId) });
    },
  });
}
