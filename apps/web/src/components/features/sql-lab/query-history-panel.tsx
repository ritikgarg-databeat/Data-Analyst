"use client";

import { CheckCircle2, History, Trash2, XCircle } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { useDeleteSqlHistoryEntry, useSqlHistory } from "@/features/sql/use-sql-history";
import { cn } from "@/lib/utils";

function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const seconds = Math.floor((Date.now() - then) / 1000);
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

interface QueryHistoryPanelProps {
  onSelect: (query: string, engine: string, database: string) => void;
  className?: string;
}

/** Recent SQL Lab executions — click a row to reload that query, or delete it. */
export function QueryHistoryPanel({ onSelect, className }: QueryHistoryPanelProps) {
  const historyQuery = useSqlHistory({ limit: 50 });
  const deleteEntry = useDeleteSqlHistoryEntry();

  if (historyQuery.isLoading) {
    return <LoadingState count={4} itemClassName="h-12" className={className} />;
  }
  if (historyQuery.isError) {
    return (
      <ErrorState
        title="Unable to load history"
        message="We couldn't reach the API to load your query history."
        retry={() => void historyQuery.refetch()}
        className={className}
      />
    );
  }
  const items = historyQuery.data ?? [];
  if (items.length === 0) {
    return (
      <EmptyState
        icon={History}
        title="No queries yet"
        description="Run a query and it'll show up here so you can revisit it later."
        className={className}
      />
    );
  }

  return (
    <ul className={cn("divide-y divide-border", className)}>
      {items.map((item) => (
        <li key={item.id} className="group flex items-start gap-2 px-1 py-2">
          <button
            type="button"
            onClick={() => onSelect(item.query, item.engine, item.database)}
            className="min-w-0 flex-1 rounded-md px-1.5 py-1 text-left hover:bg-muted/50"
          >
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              {item.status === "success" ? (
                <CheckCircle2 className="size-3.5 shrink-0 text-success" aria-hidden="true" />
              ) : (
                <XCircle className="size-3.5 shrink-0 text-destructive" aria-hidden="true" />
              )}
              <span className="truncate">{item.database}</span>
              <span aria-hidden="true">·</span>
              <span className="shrink-0">{formatRelativeTime(item.executed_at)}</span>
            </div>
            <p className="mt-1 truncate font-mono text-xs text-foreground">{item.query.trim().split("\n")[0]}</p>
          </button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="size-7 shrink-0 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
            aria-label="Delete history entry"
            onClick={() => deleteEntry.mutate(item.id)}
            disabled={deleteEntry.isPending}
          >
            <Trash2 className="size-3.5" aria-hidden="true" />
          </Button>
        </li>
      ))}
    </ul>
  );
}
