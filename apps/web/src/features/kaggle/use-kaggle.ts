import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  Dataset,
  KaggleFilesResponse,
  KaggleImportRequest,
  KaggleSearchResponse,
  KaggleStatusResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Whether Kaggle credentials are configured — gate the whole Kaggle UI behind this. */
export function useKaggleStatus() {
  return useQuery({
    queryKey: ["kaggle", "status"],
    queryFn: () => apiClient.get<KaggleStatusResponse>("/kaggle/status"),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

/** Searches Kaggle datasets — only enabled once a non-empty query is entered. */
export function useKaggleSearch(query: string, page: number) {
  return useQuery({
    queryKey: ["kaggle", "search", query, page],
    queryFn: () =>
      apiClient.get<KaggleSearchResponse>(`/kaggle/search?q=${encodeURIComponent(query)}&page=${page}`),
    enabled: query.trim().length > 0,
    staleTime: 60 * 1000,
  });
}

/** Lists the files inside one Kaggle dataset — fetched once a dataset is selected for inspection. */
export function useKaggleFiles(ref: string | null) {
  return useQuery({
    queryKey: ["kaggle", "files", ref],
    queryFn: () => apiClient.get<KaggleFilesResponse>(`/kaggle/datasets/${ref}/files`),
    enabled: Boolean(ref),
    staleTime: 60 * 1000,
  });
}

/** Downloads the selected files from a Kaggle dataset and registers it in the catalog. */
export function useKaggleImport(ref: string | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: KaggleImportRequest) =>
      apiClient.post<Dataset>(`/kaggle/datasets/${ref}/import`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
