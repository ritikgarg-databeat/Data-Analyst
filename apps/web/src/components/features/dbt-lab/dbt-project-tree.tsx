"use client";

import { FileCode2 } from "lucide-react";
import type { ProjectTreeItemSchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useDbtProjectTree } from "@/features/dbt/use-dbt-project-tree";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, string> = {
  staging: "Staging",
  intermediate: "Intermediate",
  marts: "Marts",
  seeds: "Seeds",
  snapshots: "Snapshots",
  macros: "Macros",
  tests: "Tests",
  analyses: "Analyses",
};

const CATEGORY_ORDER = ["staging", "intermediate", "marts", "seeds", "snapshots", "macros", "tests", "analyses"];

interface DbtProjectTreeProps {
  selected: string | null;
  onSelect: (item: ProjectTreeItemSchema) => void;
}

/** The real dbt project's own files (models/staging, models/marts, seeds, snapshots, macros, tests, analyses). */
export function DbtProjectTree({ selected, onSelect }: DbtProjectTreeProps) {
  const treeQuery = useDbtProjectTree();

  if (treeQuery.isLoading) return <LoadingState count={3} itemClassName="h-6" />;
  if (treeQuery.isError || !treeQuery.data) {
    return (
      <ErrorState
        title="Unable to load the project tree"
        message="We couldn't reach the API to list the dbt project's files."
        retry={() => void treeQuery.refetch()}
      />
    );
  }
  if (treeQuery.data.length === 0) {
    return <EmptyState icon={FileCode2} title="No files yet" description="The dbt project has no models yet." />;
  }

  const byCategory = new Map<string, ProjectTreeItemSchema[]>();
  for (const item of treeQuery.data) {
    const list = byCategory.get(item.category) ?? [];
    list.push(item);
    byCategory.set(item.category, list);
  }

  return (
    <div className="space-y-4">
      {CATEGORY_ORDER.filter((category) => byCategory.has(category)).map((category) => (
        <div key={category}>
          <p className="mb-1 px-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            {CATEGORY_LABELS[category] ?? category}
          </p>
          <ul className="space-y-0.5">
            {byCategory.get(category)!.map((item) => (
              <li key={item.relative_path}>
                <button
                  type="button"
                  onClick={() => onSelect(item)}
                  className={cn(
                    "flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left font-mono text-xs transition-colors",
                    selected === item.name
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                  )}
                  title={item.relative_path}
                >
                  <FileCode2 className="size-3.5 shrink-0" aria-hidden="true" />
                  <span className="truncate">{item.name}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
