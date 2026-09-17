"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { CaseAdminListItem, UpdateCaseAdminRequest } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { caseAdminQueryKey, useCaseAdminList } from "@/features/case-studies/use-case-admin";
import { apiClient } from "@/lib/api-client";

export function CaseAdminPanel() {
  const { data: cases, isLoading, isError, refetch } = useCaseAdminList();
  const queryClient = useQueryClient();

  const updateCase = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateCaseAdminRequest }) =>
      apiClient.patch<CaseAdminListItem>(`/cases/admin/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: caseAdminQueryKey }),
  });

  if (isLoading) return <LoadingState count={4} itemClassName="h-12" />;
  if (isError) {
    return <ErrorState title="Unable to load cases" message="We couldn't reach the API." retry={() => void refetch()} />;
  }

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        Case content is authored in <code>content/cases/</code> files — edit those and run the seed/sync script to
        change the problem, rubric, or reference solution. Here you can only activate or deactivate a case.
      </p>

      <div className="divide-y divide-border rounded-lg border border-border">
        {(cases ?? []).map((item) => (
          <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {item.title} <span className="text-xs text-muted-foreground">({item.slug})</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {item.category} · {item.difficulty}
              </p>
            </div>
            <div className="flex items-center gap-1">
              <Badge variant={item.is_active ? "success" : "outline"}>
                {item.is_active ? "Active" : "Inactive"}
              </Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => updateCase.mutate({ id: item.id, body: { is_active: !item.is_active } })}
              >
                {item.is_active ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
