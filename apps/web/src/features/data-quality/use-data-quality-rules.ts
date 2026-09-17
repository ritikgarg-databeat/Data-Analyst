import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateDataQualityRuleRequest, DataQualityRuleSchema, DataQualityRunSchema } from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";
import { useToast } from "@/components/shared/toast-provider";

export function dataQualityRulesQueryKey(datasetId?: string) {
  return ["data-quality", "rules", datasetId ?? "all"] as const;
}

export function useDataQualityRules(datasetId?: string) {
  return useQuery({
    queryKey: dataQualityRulesQueryKey(datasetId),
    queryFn: () =>
      apiClient.get<DataQualityRuleSchema[]>(
        `/data-quality/rules${datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : ""}`,
      ),
    staleTime: 10 * 1000,
  });
}

export function useCreateDataQualityRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CreateDataQualityRuleRequest) =>
      apiClient.post<DataQualityRuleSchema>("/data-quality/rules", body),
    onSuccess: (rule) => {
      void queryClient.invalidateQueries({ queryKey: dataQualityRulesQueryKey(rule.dataset_id) });
      void queryClient.invalidateQueries({ queryKey: dataQualityRulesQueryKey() });
    },
  });
}

export function useDeleteDataQualityRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ruleId: string) => apiClient.delete<void>(`/data-quality/rules/${ruleId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["data-quality", "rules"] });
    },
  });
}

export function dataQualityRunsQueryKey(ruleId: string) {
  return ["data-quality", "rules", ruleId, "runs"] as const;
}

export function useDataQualityRuns(ruleId: string) {
  return useQuery({
    queryKey: dataQualityRunsQueryKey(ruleId),
    queryFn: () => apiClient.get<DataQualityRunSchema[]>(`/data-quality/rules/${ruleId}/runs`),
    staleTime: 5 * 1000,
    enabled: Boolean(ruleId),
  });
}

export function useRunDataQualityRule() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (ruleId: string) => apiClient.post<DataQualityRunSchema>(`/data-quality/rules/${ruleId}/run`),
    onSuccess: (_run, ruleId) => {
      void queryClient.invalidateQueries({ queryKey: dataQualityRunsQueryKey(ruleId) });
    },
    // A request-level failure is distinct from a rule that ran and FAILED/
    // ERRORed (that's a normal DataQualityRun, shown in the run history) —
    // without this, a failed request left the Run button simply re-enabled
    // with no indication anything went wrong.
    onError: (error) =>
      toast({
        title: "Couldn't run this rule",
        description: error instanceof ApiError ? error.message : "An unexpected error occurred.",
        variant: "error",
      }),
  });
}
