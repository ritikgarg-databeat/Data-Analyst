"use client";

import { CheckCircle2, ClipboardCheck, XCircle } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { useDbtTestResults } from "@/features/dbt/use-dbt-test-results";

/** Results from the most recent `dbt test`/`dbt build` — reads run_results.json for real, never simulated. */
export function DbtTestResultsPanel() {
  const testsQuery = useDbtTestResults();

  if (testsQuery.isLoading) return <LoadingState count={3} itemClassName="h-8" />;
  if (testsQuery.isError || !testsQuery.data || testsQuery.data.length === 0) {
    return (
      <EmptyState
        icon={ClipboardCheck}
        title="No test results yet"
        description='Run "Test" or "Build" to see real pass/fail results here.'
      />
    );
  }

  const passed = testsQuery.data.filter((t) => t.status === "pass").length;

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        {passed} / {testsQuery.data.length} passed
      </p>
      <ul className="divide-y divide-border rounded-lg border border-border">
        {testsQuery.data.map((test) => (
          <li key={test.unique_id} className="flex items-start gap-2 px-3 py-2 text-sm">
            {test.status === "pass" ? (
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
            ) : (
              <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-xs text-foreground">{test.name}</p>
              {test.message ? <p className="mt-0.5 text-xs text-muted-foreground">{test.message}</p> : null}
            </div>
            {test.failures != null ? (
              <Badge variant="outline" className="shrink-0">
                {test.failures} failing
              </Badge>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
