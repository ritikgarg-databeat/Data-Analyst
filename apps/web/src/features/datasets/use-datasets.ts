import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Dataset, LocalImportForm } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export interface DatasetFilters {
  q?: string;
  business_domain?: string;
  source_type?: string;
  status?: string;
  tag?: string;
}

export const datasetsQueryKey = (filters?: DatasetFilters) => ["datasets", filters ?? {}] as const;
export const datasetQueryKey = (idOrSlug: string) => ["datasets", "detail", idOrSlug] as const;

function toSearchParams(filters?: DatasetFilters): string {
  if (!filters) return "";
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

/** Fetches every dataset in the catalog, optionally filtered (search, domain, source, status, tag). */
export function useDatasets(filters?: DatasetFilters) {
  return useQuery({
    queryKey: datasetsQueryKey(filters),
    queryFn: () => apiClient.get<Dataset[]>(`/datasets${toSearchParams(filters)}`),
    staleTime: 30 * 1000,
    retry: 1,
  });
}

/** Fetches one dataset by id or slug — polled while it's still importing/profiling. */
export function useDataset(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: datasetQueryKey(idOrSlug ?? ""),
    queryFn: () => apiClient.get<Dataset>(`/datasets/${encodeURIComponent(idOrSlug!)}`),
    enabled: Boolean(idOrSlug),
    staleTime: 10 * 1000,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "IMPORTING" || status === "PROFILING" ? 1500 : false;
    },
  });
}

/** Starts a local file (or multi-file collection) import — returns immediately with status IMPORTING. */
export function useImportDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ files, form }: { files: File[]; form: LocalImportForm }) =>
      apiClient.postForm<Dataset>("/datasets/import", files, {
        name: form.name,
        ...(form.description ? { description: form.description } : {}),
        ...(form.business_domain ? { business_domain: form.business_domain } : {}),
        ...(form.difficulty ? { difficulty: form.difficulty } : {}),
        tags: (form.tags ?? []).join(","),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

/** Re-imports new file(s) into an existing dataset — bumps its version if the data changed. */
export function useReimportDataset(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => apiClient.postForm<Dataset>(`/datasets/${idOrSlug}/reimport`, files),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

/** Manually re-runs profiling/quality scoring without touching the underlying files. */
export function useTriggerReprofile(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<Dataset>(`/datasets/${idOrSlug}/profile`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
