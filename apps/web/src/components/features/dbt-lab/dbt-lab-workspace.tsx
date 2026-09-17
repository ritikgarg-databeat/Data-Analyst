"use client";

import { useState } from "react";
import type { DbtCommand, ProjectTreeItemSchema } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRunDbtCommand } from "@/features/dbt/use-dbt-runs";
import { cn } from "@/lib/utils";

import { DbtDocsPanel } from "./dbt-docs-panel";
import { DbtLineageGraph } from "./dbt-lineage-graph";
import { DbtProjectTree } from "./dbt-project-tree";
import { DbtRunHistoryPanel } from "./dbt-run-history-panel";
import { DbtTestResultsPanel } from "./dbt-test-results-panel";

const COMMANDS: { command: DbtCommand; label: string }[] = [
  { command: "run", label: "Run" },
  { command: "test", label: "Test" },
  { command: "build", label: "Build" },
  { command: "compile", label: "Compile" },
  { command: "docs generate", label: "Docs Generate" },
];

type Tab = "lineage" | "docs" | "tests" | "history";

const TABS: { id: Tab; label: string }[] = [
  { id: "lineage", label: "Lineage" },
  { id: "docs", label: "Docs" },
  { id: "tests", label: "Test Results" },
  { id: "history", label: "Run History" },
];

/** Top-level dbt Lab composition — a real, local dbt Core project against DuckDB (see dbt/ at the repo root). */
export function DbtLabWorkspace() {
  const runMutation = useRunDbtCommand();
  const [selector, setSelector] = useState("");
  const [tab, setTab] = useState<Tab>("history");

  function handleRun(command: DbtCommand) {
    runMutation.mutate(
      { command, selector: selector.trim() || undefined },
      { onSuccess: () => setTab("history") },
    );
  }

  function handleSelectTreeItem(item: ProjectTreeItemSchema) {
    setSelector(item.name);
  }

  const lastRun = runMutation.data;

  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-[36rem] flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {COMMANDS.map(({ command, label }) => (
            <Button
              key={command}
              size="sm"
              variant={command === "run" || command === "build" ? "default" : "outline"}
              onClick={() => handleRun(command)}
              disabled={runMutation.isPending}
            >
              {runMutation.isPending ? "Running…" : label}
            </Button>
          ))}
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="dbt-selector" className="text-xs font-medium text-muted-foreground">
            --select (optional)
          </label>
          <Input
            id="dbt-selector"
            value={selector}
            onChange={(event) => setSelector(event.target.value)}
            placeholder="e.g. stg_orders"
            className="h-8 w-48 font-mono text-xs"
          />
        </div>

        <p className="ml-auto text-xs text-muted-foreground">
          {runMutation.isPending
            ? "Running dbt for real — this can take a few seconds…"
            : lastRun
              ? `Last run: dbt ${lastRun.command} — ${lastRun.status}`
              : "Pick a command to run the real dbt project."}
        </p>
      </div>

      <div className="flex min-h-0 flex-1 gap-3 overflow-hidden">
        <div className="w-56 shrink-0 overflow-y-auto rounded-xl border border-border bg-card p-3">
          <DbtProjectTree selected={selector || null} onSelect={handleSelectTreeItem} />
        </div>

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-xl border border-border bg-card">
          <div role="tablist" className="flex border-b border-border px-1">
            {TABS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={tab === id}
                onClick={() => setTab(id)}
                className={cn(
                  "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                  tab === id
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                {label}
                {id === "history" && lastRun ? (
                  <Badge variant="outline" className="ml-1.5">
                    {lastRun.status}
                  </Badge>
                ) : null}
              </button>
            ))}
          </div>
          <div role="tabpanel" className="min-h-0 flex-1 overflow-y-auto p-3">
            {tab === "lineage" ? <DbtLineageGraph /> : null}
            {tab === "docs" ? <DbtDocsPanel /> : null}
            {tab === "tests" ? <DbtTestResultsPanel /> : null}
            {tab === "history" ? <DbtRunHistoryPanel /> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
