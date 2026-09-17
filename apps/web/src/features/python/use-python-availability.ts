import { useQuery } from "@tanstack/react-query";
import type { PythonAvailabilitySchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonAvailabilityQueryKey() {
  return ["python", "availability"] as const;
}

/** Whether the Python Lab Docker sandbox is available right now (and why not, if not). */
export function usePythonAvailability() {
  return useQuery({
    queryKey: pythonAvailabilityQueryKey(),
    queryFn: () => apiClient.get<PythonAvailabilitySchema>("/python/availability"),
    staleTime: 60 * 1000,
  });
}
