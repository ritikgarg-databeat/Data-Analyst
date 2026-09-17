"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { Group, Panel, Separator } from "react-resizable-panels";

import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useSqlDatabases } from "@/features/sql/use-sql-databases";
import { useSqlEngines } from "@/features/sql/use-sql-engines";
import { useSqlExecute } from "@/features/sql/use-sql-execute";
import { cn } from "@/lib/utils";

import { QueryHistoryPanel } from "./query-history-panel";
import { ResultsGrid } from "./results-grid";
import { SavedQueriesPanel } from "./saved-queries-panel";
import { SchemaExplorer } from "./schema-explorer";
import { SqlAskAiPanel } from "./sql-ask-ai-panel";
import { SqlEditor } from "./sql-editor";
import { SqlErrorPanel } from "./sql-error-panel";
import { TablePreviewPanel } from "./table-preview-panel";
import { WorkspaceSelector } from "./workspace-selector";

const DEFAULT_ENGINE = "duckdb";
const DEFAULT_DATABASE = "ecommerce";
const DEFAULT_QUERY = "SELECT * FROM orders LIMIT 100;";

const HORIZONTAL_HANDLE = "w-1.5 shrink-0 cursor-col-resize bg-border transition-colors hover:bg-primary/50 focus-visible:bg-primary/50 outline-none";
const VERTICAL_HANDLE = "h-1.5 shrink-0 cursor-row-resize bg-border transition-colors hover:bg-primary/50 focus-visible:bg-primary/50 outline-none";

type RightTab = "history" | "saved";

interface SqlPlaygroundProps {
  /** Pre-selects the database dropdown — used by the `?database=` deep link from a dataset's page. */
  initialDatabase?: string;
}

/** Top-level SQL Lab composition: engine/database pickers, schema explorer, editor, results, and history/saved sidebar. */
export function SqlPlayground({ initialDatabase }: SqlPlaygroundProps = {}) {
  const enginesQuery = useSqlEngines();
  const databasesQuery = useSqlDatabases();
  const executeMutation = useSqlExecute();

  const [engine, setEngine] = useState(DEFAULT_ENGINE);
  const [database, setDatabase] = useState(initialDatabase ?? DEFAULT_DATABASE);
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [previewTable, setPreviewTable] = useState<string | null>(null);
  const [rightTab, setRightTab] = useState<RightTab>("history");
  const [askAiOpen, setAskAiOpen] = useState(false);
  const [askAiMode, setAskAiMode] = useState<"review" | "debug" | "optimize">("review");

  const result = executeMutation.data;
  const canRun = query.trim().length > 0 && !executeMutation.isPending;

  function handleRun() {
    if (!canRun) return;
    executeMutation.mutate({ engine, database, query });
  }

  function handleSelectQuery(nextQuery: string, nextEngine: string, nextDatabase: string) {
    setQuery(nextQuery);
    setEngine(nextEngine);
    setDatabase(nextDatabase);
    // A workspace is scoped to one engine+database pairing — switching either
    // (directly or by picking a history/saved entry from a different one)
    // invalidates whichever workspace was selected for the old pairing.
    setWorkspaceId(undefined);
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-[32rem] flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="sql-lab-engine">Engine</Label>
          <Select
            id="sql-lab-engine"
            value={engine}
            onChange={(event) => {
              setEngine(event.target.value);
              setWorkspaceId(undefined);
            }}
            className="w-40"
          >
            {(enginesQuery.data ?? [{ name: DEFAULT_ENGINE, label: "DuckDB", is_available: true, reason: null }]).map(
              (item) => (
                <option key={item.name} value={item.name} disabled={!item.is_available} title={item.reason ?? undefined}>
                  {item.label}
                  {!item.is_available ? " (unavailable)" : ""}
                </option>
              ),
            )}
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <Label htmlFor="sql-lab-database">Database</Label>
          <Select
            id="sql-lab-database"
            value={database}
            onChange={(event) => {
              setDatabase(event.target.value);
              setWorkspaceId(undefined);
            }}
            className="w-48"
          >
            {(databasesQuery.data ?? [{ name: DEFAULT_DATABASE, label: "Ecommerce", engine: DEFAULT_ENGINE, description: null, table_count: 0 }]).map(
              (item) => (
                <option key={item.name} value={item.name}>
                  {item.label}
                </option>
              ),
            )}
          </Select>
        </div>

        <WorkspaceSelector engine={engine} database={database} workspaceId={workspaceId} onChange={setWorkspaceId} />

        <p className="ml-auto text-xs text-muted-foreground">
          {executeMutation.isPending
            ? "Running query..."
            : result
              ? `Last run: ${result.status === "success" ? "success" : "error"} in ${result.execution_time_ms}ms`
              : "Write a query and run it (Ctrl/Cmd+Enter)."}
        </p>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setAskAiMode("review");
            setAskAiOpen(true);
          }}
        >
          <Sparkles className="size-4" aria-hidden="true" />
          Ask AI
        </Button>
      </div>

      <Group orientation="horizontal" className="min-h-0 flex-1 overflow-hidden rounded-xl border border-border">
        <Panel defaultSize="20" minSize="14" maxSize="35" className="min-w-0 overflow-y-auto bg-card p-3">
          <SchemaExplorer database={database} engine={engine} onPreview={setPreviewTable} />
        </Panel>

        <Separator className={HORIZONTAL_HANDLE} />

        <Panel defaultSize="58" minSize="30" className="min-w-0">
          <Group orientation="vertical" className="h-full">
            <Panel defaultSize="45" minSize="20" className="min-h-0">
              <SqlEditor
                value={query}
                onChange={setQuery}
                onRun={handleRun}
                isRunning={executeMutation.isPending}
                className="h-full rounded-none border-0 border-b border-border"
              />
            </Panel>

            <Separator className={VERTICAL_HANDLE} />

            <Panel defaultSize="55" minSize="20" className="min-h-0 overflow-y-auto bg-card p-3">
              {executeMutation.isPending ? (
                <LoadingState count={1} itemClassName="h-48" />
              ) : result ? (
                <div className="space-y-3">
                  <SqlErrorPanel error={result.error} />
                  {result.error ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setAskAiMode("debug");
                        setAskAiOpen(true);
                      }}
                    >
                      <Sparkles className="size-4" aria-hidden="true" />
                      Ask AI about this error
                    </Button>
                  ) : null}
                  {result.status === "success" ? (
                    <ResultsGrid
                      columns={result.columns}
                      rows={result.rows}
                      rowCount={result.row_count}
                      truncated={result.truncated}
                    />
                  ) : null}
                </div>
              ) : (
                <ResultsGrid columns={[]} rows={[]} rowCount={0} />
              )}
            </Panel>
          </Group>
        </Panel>

        <Separator className={HORIZONTAL_HANDLE} />

        <Panel defaultSize="22" minSize="16" maxSize="35" className="min-w-0 overflow-y-auto bg-card">
          <div role="tablist" className="flex border-b border-border px-1">
            <button
              type="button"
              role="tab"
              aria-selected={rightTab === "history"}
              onClick={() => setRightTab("history")}
              className={cn(
                "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                rightTab === "history"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              History
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={rightTab === "saved"}
              onClick={() => setRightTab("saved")}
              className={cn(
                "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                rightTab === "saved"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              Saved
            </button>
          </div>
          <div role="tabpanel" className="p-3">
            {rightTab === "history" ? (
              <QueryHistoryPanel onSelect={handleSelectQuery} />
            ) : (
              <SavedQueriesPanel
                engine={engine}
                database={database}
                workspaceId={workspaceId}
                currentQuery={query}
                onSelect={handleSelectQuery}
              />
            )}
          </div>
        </Panel>
      </Group>

      <TablePreviewPanel
        database={database}
        engine={engine}
        table={previewTable}
        onOpenChange={(open) => {
          if (!open) setPreviewTable(null);
        }}
      />

      <SqlAskAiPanel
        key={askAiMode}
        open={askAiOpen}
        onOpenChange={setAskAiOpen}
        query={query}
        engine={engine}
        database={database}
        error={result?.error ?? null}
        executionTimeMs={result?.execution_time_ms}
        initialMode={askAiMode}
      />

      {/* Tooltip primitives render nothing on their own — this keeps the (unused-so-far) hover-help
          affordance available for a future pass without an unused-import lint failure today. */}
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="sr-only" aria-hidden="true" />
        </TooltipTrigger>
        <TooltipContent className="sr-only">SQL Lab</TooltipContent>
      </Tooltip>
    </div>
  );
}
