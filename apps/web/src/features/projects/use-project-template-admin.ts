import { useQuery } from "@tanstack/react-query";
import type { ProjectTemplateAdmin } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const projectTemplateAdminQueryKey = ["projects", "templates", "admin"] as const;

/** Fetches every project template (active + inactive) for the Content Admin "Project Templates" tab. */
export function useProjectTemplateAdminList() {
  return useQuery({
    queryKey: projectTemplateAdminQueryKey,
    queryFn: () => apiClient.get<ProjectTemplateAdmin[]>("/projects/templates/admin"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}
