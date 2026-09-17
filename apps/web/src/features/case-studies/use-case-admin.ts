import { useQuery } from "@tanstack/react-query";
import type { CaseAdminListItem } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const caseAdminQueryKey = ["cases", "admin"] as const;

/** Fetches every case (active + inactive) for the Content Admin "Cases" tab. */
export function useCaseAdminList() {
  return useQuery({
    queryKey: caseAdminQueryKey,
    queryFn: () => apiClient.get<CaseAdminListItem[]>("/cases/admin"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}
