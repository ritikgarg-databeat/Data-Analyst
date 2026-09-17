"use client";

import { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { useDbtDocs } from "@/features/dbt/use-dbt-docs";
import { cn } from "@/lib/utils";

/** Generated documentation: every model/seed/snapshot's real columns (types from catalog.json, descriptions from manifest.json). */
export function DbtDocsPanel() {
  const docsQuery = useDbtDocs();
  const [expanded, setExpanded] = useState<string | null>(null);

  if (docsQuery.isLoading) return <LoadingState count={4} itemClassName="h-10" />;
  if (docsQuery.isError || !docsQuery.data) {
    return (
      <EmptyState
        icon={BookOpen}
        title="No docs yet"
        description="Run the dbt Lab at least once to generate documentation for the project's models."
      />
    );
  }
  if (docsQuery.data.length === 0) {
    return <EmptyState icon={BookOpen} title="No models yet" description="This dbt project has no models yet." />;
  }

  return (
    <ul className="divide-y divide-border rounded-lg border border-border">
      {docsQuery.data.map((doc) => {
        const isOpen = expanded === doc.unique_id;
        return (
          <li key={doc.unique_id}>
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : doc.unique_id)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-accent/40"
            >
              {isOpen ? (
                <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
              ) : (
                <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
              )}
              <span className="font-mono text-sm text-foreground">{doc.name}</span>
              <Badge variant="outline" className="ml-1">
                {doc.resource_type}
              </Badge>
              {doc.materialized ? <Badge variant="secondary">{doc.materialized}</Badge> : null}
              <span className="ml-auto text-xs text-muted-foreground">{doc.columns.length} columns</span>
            </button>
            {isOpen ? (
              <div className={cn("px-3 pb-3", doc.description && "space-y-2")}>
                {doc.description ? <p className="text-sm text-muted-foreground">{doc.description}</p> : null}
                <div className="overflow-x-auto rounded-md border border-border">
                  <table className="w-full min-w-max border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/50 text-left text-muted-foreground uppercase">
                        <th className="px-3 py-1.5">Column</th>
                        <th className="px-3 py-1.5">Type</th>
                        <th className="px-3 py-1.5">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {doc.columns.map((col) => (
                        <tr key={col.name} className="border-b border-border last:border-0">
                          <td className="px-3 py-1.5 font-mono text-foreground">{col.name}</td>
                          <td className="px-3 py-1.5 text-muted-foreground">{col.data_type ?? "—"}</td>
                          <td className="px-3 py-1.5 text-muted-foreground">{col.description || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
