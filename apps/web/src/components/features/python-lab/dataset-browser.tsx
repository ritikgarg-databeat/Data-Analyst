"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Database, FileCode, Search } from "lucide-react";
import type { PythonDatasetFileSchema } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { usePythonDatasets } from "@/features/python/use-python-datasets";
import { cn } from "@/lib/utils";

interface DatasetGroup {
  slug: string;
  dataset_name: string;
  files: PythonDatasetFileSchema[];
}

interface DatasetBrowserProps {
  /** Inserts a file's ready-to-run `pd.read_csv(...)`-style snippet into the active cell editor. */
  onInsertCode: (code: string) => void;
  className?: string;
}

/**
 * Tree of every dataset file the Python Lab sandbox can read (mounted
 * read-only at `container_path`), grouped by dataset, with a one-click
 * "Insert" for its ready-made load snippet — the Python Lab analogue of
 * sql-lab/schema-explorer.tsx.
 */
export function DatasetBrowser({ onInsertCode, className }: DatasetBrowserProps) {
  const datasetsQuery = usePythonDatasets();
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const groups = useMemo<DatasetGroup[]>(() => {
    const files = datasetsQuery.data ?? [];
    const query = search.trim().toLowerCase();
    const filtered = query
      ? files.filter((f) => f.label.toLowerCase().includes(query) || f.dataset_name.toLowerCase().includes(query))
      : files;

    const byDataset = new Map<string, DatasetGroup>();
    for (const file of filtered) {
      const entry = byDataset.get(file.dataset_slug) ?? {
        slug: file.dataset_slug,
        dataset_name: file.dataset_name,
        files: [],
      };
      entry.files.push(file);
      byDataset.set(file.dataset_slug, entry);
    }
    return Array.from(byDataset.values());
  }, [datasetsQuery.data, search]);

  function toggle(slug: string) {
    setExpanded((prev) => ({ ...prev, [slug]: !prev[slug] }));
  }

  if (datasetsQuery.isLoading) {
    return <LoadingState count={4} itemClassName="h-7" className={className} />;
  }
  if (datasetsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load datasets"
        message="We couldn't reach the API to load the Python Lab datasets."
        retry={() => void datasetsQuery.refetch()}
        className={className}
      />
    );
  }

  return (
    <div className={cn(className)}>
      <div className="relative mb-2">
        <Search
          className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search datasets & files"
          aria-label="Search datasets and files"
          className="h-8 pl-8 text-sm"
        />
      </div>

      {groups.length === 0 ? (
        <p className="px-1.5 py-2 text-xs text-muted-foreground">No datasets match &quot;{search}&quot;.</p>
      ) : (
        <ul className="space-y-0.5">
          {groups.map((group) => {
            const isExpanded = Boolean(expanded[group.slug]) || Boolean(search.trim());
            return (
              <li key={group.slug}>
                <button
                  type="button"
                  onClick={() => toggle(group.slug)}
                  aria-expanded={isExpanded}
                  className="flex w-full items-center gap-1.5 rounded-md px-1.5 py-1.5 text-left text-sm hover:bg-muted/50"
                >
                  {isExpanded ? (
                    <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                  ) : (
                    <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                  )}
                  <Database className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <span className="truncate font-medium text-foreground">{group.dataset_name}</span>
                  <span className="ml-auto shrink-0 pl-2 text-xs text-muted-foreground">{group.files.length}</span>
                </button>

                {isExpanded ? (
                  <ul className="mb-1 ml-4 space-y-1 border-l border-border py-1 pl-3">
                    {group.files.map((file) => (
                      <li
                        key={file.container_path}
                        className="group flex items-start gap-1.5 rounded-md px-1 py-1 hover:bg-muted/40"
                      >
                        <FileCode className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs font-medium text-foreground">{file.label}</p>
                          <p className="truncate text-[10px] text-muted-foreground">
                            {file.grain ?? "—"}
                            {file.row_count != null ? ` · ${file.row_count.toLocaleString()} rows` : ""}
                            {file.column_count != null ? ` · ${file.column_count} cols` : ""}
                          </p>
                        </div>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          className="h-6 shrink-0 px-2 text-xs opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                          aria-label={`Insert ${file.label}`}
                          onClick={() => onInsertCode(file.suggested_code)}
                        >
                          Insert
                        </Button>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
