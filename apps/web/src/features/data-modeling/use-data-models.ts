import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreateDataModelRequest,
  DataModelKind,
  DataModelSchema,
  DataModelSummarySchema,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function dataModelsQueryKey(modelKind?: DataModelKind) {
  return ["data-models", modelKind ?? "all"] as const;
}

/** Lists saved graphs of one kind — the Data Modeler (DIMENSIONAL), Architecture Diagram Builder
 * (ARCHITECTURE), or Pipeline Playground (PIPELINE) all share this same list endpoint. */
export function useDataModels(modelKind: DataModelKind) {
  return useQuery({
    queryKey: dataModelsQueryKey(modelKind),
    queryFn: () => apiClient.get<DataModelSummarySchema[]>(`/modeling/models?model_kind=${modelKind}`),
    staleTime: 10 * 1000,
  });
}

export function useCreateDataModel(modelKind: DataModelKind) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: Omit<CreateDataModelRequest, "model_kind">) =>
      apiClient.post<DataModelSchema>("/modeling/models", { ...body, model_kind: modelKind }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: dataModelsQueryKey(modelKind) });
    },
  });
}

export function useDeleteDataModel(modelKind: DataModelKind) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (modelId: string) => apiClient.delete<void>(`/modeling/models/${modelId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: dataModelsQueryKey(modelKind) });
    },
  });
}
