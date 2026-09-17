import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  DataModelSchema,
  SaveDataModelGraphRequest,
  UpdateDataModelRequest,
  ValidationResultSchema,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function dataModelQueryKey(modelId: string) {
  return ["data-models", "detail", modelId] as const;
}

export function useDataModel(modelId: string) {
  return useQuery({
    queryKey: dataModelQueryKey(modelId),
    queryFn: () => apiClient.get<DataModelSchema>(`/modeling/models/${modelId}`),
    staleTime: 5 * 1000,
    enabled: Boolean(modelId),
  });
}

export function useUpdateDataModel(modelId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: UpdateDataModelRequest) =>
      apiClient.patch<DataModelSchema>(`/modeling/models/${modelId}`, body),
    onSuccess: (data) => queryClient.setQueryData(dataModelQueryKey(modelId), data),
  });
}

/** Wholesale-replaces the model's tables/relationships — the natural "save" unit for a canvas editor. */
export function useSaveDataModelGraph(modelId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SaveDataModelGraphRequest) =>
      apiClient.put<DataModelSchema>(`/modeling/models/${modelId}/graph`, body),
    onSuccess: (data) => queryClient.setQueryData(dataModelQueryKey(modelId), data),
  });
}

export function useValidateDataModel(modelId: string) {
  return useMutation({
    mutationFn: () => apiClient.post<ValidationResultSchema>(`/modeling/models/${modelId}/validate`),
  });
}
