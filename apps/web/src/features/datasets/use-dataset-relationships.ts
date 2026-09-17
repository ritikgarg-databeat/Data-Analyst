import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateRelationshipRequest, DatasetRelationshipSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

function relationshipsQueryKey(idOrSlug: string | undefined) {
  return ["datasets", "detail", idOrSlug, "relationships"] as const;
}

export function useDatasetRelationships(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: relationshipsQueryKey(idOrSlug),
    queryFn: () =>
      apiClient.get<DatasetRelationshipSchema[]>(`/datasets/${encodeURIComponent(idOrSlug!)}/relationships`),
    enabled: Boolean(idOrSlug),
    staleTime: 60 * 1000,
  });
}

export function useAddRelationship(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateRelationshipRequest) =>
      apiClient.post<DatasetRelationshipSchema>(`/datasets/${idOrSlug}/relationships`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: relationshipsQueryKey(idOrSlug) });
    },
  });
}

export function useDeleteRelationship(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (relationshipId: string) =>
      apiClient.delete<void>(`/datasets/${idOrSlug}/relationships/${relationshipId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: relationshipsQueryKey(idOrSlug) });
    },
  });
}
