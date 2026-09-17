"use client";

import { useState } from "react";
import { CheckCircle2, History, XCircle } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { useDbtRuns } from "@/features/dbt/use-dbt-runs";
import { cn } from "@/lib/utils";

/** Every real `dbt <command>` invocation this session has made, most recent first. */
export function DbtRunHistoryPanel() {
  const runsQuery = useDbtRuns();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (runsQuery.isLoading) return <LoadingState count={3} itemClassName="h-10" />;
  if (runsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load run history"
        message="We couldn't reach the API to load past dbt runs."
        retry={() => void runsQuery.refetch()}
      />
    );
  }
  if (!runsQuery.data || runsQuery.data.length === 0) {
    return (
      <EmptyState icon={History} title="No runs yet" description="Use the buttons above to run the dbt project." />
    );
  }

  return (
    <ul className="divide-y divide-border rounded-lg border border-border">
      {runsQuery.data.map((run) => {
        const isOpen = expandedId === run.id;
        return (
          <li key={run.id}>
            <button
              type="button"
              onClick={() => setExpandedId(isOpen ? null : run.id)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-accent/40"
            >
              {run.status === "SUCCESS" ? (
                <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
              ) : (
                <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
              )}
              <span className="font-mono text-sm text-foreground">dbt {run.command}</span>
              {run.selector ? <Badge variant="outline">--select {run.selector}</Badge> : null}
              <span className="ml-auto text-xs text-muted-foreground">
                {new Date(run.started_at).toLocaleTimeString()}
              </span>
            </button>
            {isOpen ? (
              <div className="space-y-2 px-3 pb-3">
                {run.summary.node_count != null ? (
                  <p className="text-xs text-muted-foreground">
                    {run.summary.node_count as number} node(s) ·{" "}
                    {run.summary.result_counts
                      ? Object.entries(run.summary.result_counts as Record<string, number>)
                          .map(([status, count]) => `${count} ${status}`)
                          .join(", ")
                      : null}
                  </p>
                ) : null}
                {run.log ? (
                  <pre
                    className={cn(
                      "max-h-64 overflow-auto rounded-md bg-muted/50 p-2 font-mono text-[11px] whitespace-pre-wrap text-muted-foreground",
                    )}
                  >
                    {run.log}
                  </pre>
                ) : null}
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
