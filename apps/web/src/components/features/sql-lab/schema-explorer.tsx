"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Eye, Search, Table2 } from "lucide-react";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useSqlTables } from "@/features/sql/use-sql-tables";
import { useSqlTableSchema } from "@/features/sql/use-sql-table-schema";
import type { SqlTableSummary } from "@data-analyst-lab/shared";

interface SchemaTableNodeProps {
  database: string;
  engine: string;
  table: SqlTableSummary;
  query: string;
  expanded: boolean;
  onToggle: () => void;
  onPreview?: (tableName: string) => void;
}

function SchemaTableNode({ database, engine, table, query, expanded, onToggle, onPreview }: SchemaTableNodeProps) {
  const schemaQuery = useSqlTableSchema(database, table.table_name, engine, { enabled: expanded });
  const q = query.trim().toLowerCase();
  const columns = schemaQuery.data?.columns ?? [];
  const filteredColumns = q ? columns.filter((c) => c.name.toLowerCase().includes(q)) : columns;

  return (
    <li>
      <div className="group flex items-center gap-1 rounded-md px-1.5 py-1.5 hover:bg-muted/50">
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={expanded}
          className="flex min-w-0 flex-1 items-center gap-1.5 text-left text-sm outline-none"
        >
          {expanded ? (
            <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          ) : (
            <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          )}
          <Table2 className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          <span className="truncate font-medium text-foreground">{table.table_name}</span>
          {table.row_count != null ? (
            <span className="ml-auto shrink-0 pl-2 text-xs whitespace-nowrap text-muted-foreground">
              {table.row_count.toLocaleString()} rows
            </span>
          ) : null}
        </button>
        {onPreview ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="size-6 shrink-0"
                onClick={() => onPreview(table.table_name)}
                aria-label={`Preview ${table.table_name}`}
              >
                <Eye className="size-3.5" aria-hidden="true" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Preview sample rows</TooltipContent>
          </Tooltip>
        ) : null}
      </div>

      {expanded ? (
        <div className="mb-1 ml-4 border-l border-border py-1 pl-3">
          {schemaQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-5" className="gap-1" />
          ) : schemaQuery.isError ? (
            <p className="py-1 text-xs text-destructive">Couldn&apos;t load columns.</p>
          ) : filteredColumns.length === 0 ? (
            <p className="py-1 text-xs text-muted-foreground">No matching columns.</p>
          ) : (
            <ul className="space-y-1">
              {filteredColumns.map((column) => (
                <li key={column.name} className="flex items-center gap-2 text-xs">
                  <span className="truncate font-mono text-foreground">{column.name}</span>
                  <span className="shrink-0 text-muted-foreground">{column.type}</span>
                  {column.nullable ? (
                    <Badge variant="outline" className="shrink-0 px-1 py-0 text-[10px]">
                      nullable
                    </Badge>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </li>
  );
}

interface SchemaExplorerProps {
  database: string;
  engine: string;
  /** Omit to hide the per-table preview affordance (used for the read-only exercise view). */
  onPreview?: (tableName: string) => void;
  className?: string;
}

/** Searchable, lazily-expandable tree of a database's tables and their columns. */
export function SchemaExplorer({ database, engine, onPreview, className }: SchemaExplorerProps) {
  const tablesQuery = useSqlTables(database, engine);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const query = search.trim().toLowerCase();
  const visibleTables = useMemo(() => {
    const tables = tablesQuery.data ?? [];
    if (!query) return tables;
    return tables.filter((table) => table.table_name.toLowerCase().includes(query) || expanded[table.table_name]);
  }, [tablesQuery.data, query, expanded]);

  function toggle(tableName: string) {
    setExpanded((prev) => ({ ...prev, [tableName]: !prev[tableName] }));
  }

  return (
    <div className={className}>
      <div className="relative mb-2">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search tables & columns"
          aria-label="Search tables and columns"
          className="h-8 pl-8 text-sm"
        />
      </div>

      {tablesQuery.isLoading ? (
        <LoadingState count={4} itemClassName="h-7" />
      ) : tablesQuery.isError ? (
        <ErrorState
          title="Unable to load tables"
          message="We couldn't reach the API to load this database's tables."
          retry={() => void tablesQuery.refetch()}
        />
      ) : visibleTables.length === 0 ? (
        <p className="px-1.5 py-2 text-xs text-muted-foreground">No tables match &quot;{search}&quot;.</p>
      ) : (
        <ul className="space-y-0.5">
          {visibleTables.map((table) => (
            <SchemaTableNode
              key={table.table_name}
              database={database}
              engine={engine}
              table={table}
              query={search}
              expanded={Boolean(expanded[table.table_name])}
              onToggle={() => toggle(table.table_name)}
              onPreview={onPreview}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
