import { useQuery } from "@tanstack/react-query";
import type { PythonDatasetFileSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonDatasetsQueryKey() {
  return ["python", "datasets"] as const;
}

/** Lists every dataset file the Python Lab sandbox can read (with a ready-to-insert `pd.read_csv(...)` snippet each). */
export function usePythonDatasets() {
  return useQuery({
    queryKey: pythonDatasetsQueryKey(),
    queryFn: () => apiClient.get<PythonDatasetFileSchema[]>("/python/datasets"),
    staleTime: 5 * 60 * 1000,
  });
}
