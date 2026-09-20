"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { AlertTriangle } from "lucide-react";
import type { PythonExecutionResultSchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useCreatePythonWorkspace, usePythonWorkspaces } from "@/features/python/use-python-workspaces";
import { usePythonAvailability } from "@/features/python/use-python-availability";
import { cn } from "@/lib/utils";
import { useMediaQuery } from "@/lib/use-media-query";

import { DatasetBrowser } from "./dataset-browser";
import { PythonHistoryPanel } from "./python-history-panel";
import { PythonNotebook } from "./python-notebook";
import { PythonWorkspacesPanel } from "./python-workspaces-panel";
import { VariableExplorer } from "./variable-explorer";

const HORIZONTAL_HANDLE =
  "w-1.5 shrink-0 cursor-col-resize bg-border transition-colors hover:bg-primary/50 focus-visible:bg-primary/50 outline-none";

type RightTab = "workspaces" | "history";

/**
 * Top-level Python Lab composition: dataset browser | notebook (cells +
 * variable explorer) | workspaces/history sidebar — the same resizable-panel
 * layout philosophy as sql-lab/sql-playground.tsx. Gated up front by
 * `usePythonAvailability`: if the whole Docker sandbox is unreachable, this
 * shows a clear message instead of the editor (unlike SQL Lab, where only
 * one *engine option* can be unavailable — here the entire feature can be).
 */
export function PythonLabPage() {
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const availabilityQuery = usePythonAvailability();
  const workspacesQuery = usePythonWorkspaces();
  const createWorkspace = useCreatePythonWorkspace();

  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [rightTab, setRightTab] = useState<RightTab>("workspaces");
  const [latestResult, setLatestResult] = useState<PythonExecutionResultSchema | null>(null);
  const bootstrapped = useRef(false);

  const insertCodeRef = useRef<((code: string) => void) | null>(null);
  const handleInsertCodeRef = useCallback((insert: (code: string) => void) => {
    insertCodeRef.current = insert;
  }, []);

  // The active workspace defaults to the first one returned, until the user explicitly picks a
  // different one — derived directly during render rather than mirrored into state via an effect.
  const resolvedActiveWorkspaceId = activeWorkspaceId ?? workspacesQuery.data?.[0]?.id ?? null;

  // Auto-create a default workspace the first time this user has none —
  // creating one auto-creates its first starter cell server-side.
  useEffect(() => {
    if (!workspacesQuery.data || bootstrapped.current || workspacesQuery.data.length > 0) return;
    bootstrapped.current = true;
    createWorkspace.mutate({ name: "My Workspace" }, { onSuccess: (workspace) => setActiveWorkspaceId(workspace.id) });
  }, [workspacesQuery.data, createWorkspace]);

  function handleSelectWorkspace(workspaceId: string) {
    setActiveWorkspaceId(workspaceId);
    setLatestResult(null);
  }

  function renderWorkspacePanel() {
    return (
      <>
        <div role="tablist" className="flex overflow-x-auto border-b border-border px-1 scrollbar-thin">
          <button
            type="button"
            role="tab"
            aria-selected={rightTab === "workspaces"}
            onClick={() => setRightTab("workspaces")}
            className={cn(
              "shrink-0 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              rightTab === "workspaces"
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            Workspaces
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={rightTab === "history"}
            onClick={() => setRightTab("history")}
            className={cn(
              "shrink-0 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              rightTab === "history"
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            History
          </button>
        </div>
        <div role="tabpanel" className="p-3">
          {rightTab === "workspaces" ? (
            <PythonWorkspacesPanel activeWorkspaceId={resolvedActiveWorkspaceId} onSelect={handleSelectWorkspace} />
          ) : (
            <PythonHistoryPanel
              workspaceId={resolvedActiveWorkspaceId ?? undefined}
              onSelect={(code) => insertCodeRef.current?.(code)}
            />
          )}
        </div>
      </>
    );
  }

  if (availabilityQuery.isLoading || workspacesQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-[32rem]" />;
  }

  if (availabilityQuery.isError) {
    return (
      <ErrorState
        title="Unable to check Python Lab availability"
        message="We couldn't reach the API to find out whether the Python sandbox is available."
        retry={() => void availabilityQuery.refetch()}
      />
    );
  }

  if (availabilityQuery.data && !availabilityQuery.data.available) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Python Lab requires Docker"
        description={
          availabilityQuery.data.reason ??
          "The Docker-sandboxed Python runtime isn't reachable right now. Make sure Docker is running, then reload this page."
        }
        className="min-h-[32rem]"
      />
    );
  }

  if (workspacesQuery.isError) {
    return (
      <ErrorState
        title="Unable to load your workspaces"
        message="We couldn't reach the API to load your Python Lab workspaces."
        retry={() => void workspacesQuery.refetch()}
      />
    );
  }

  return (
    <div className={cn("flex min-w-0 flex-col gap-3", isDesktop && "h-[calc(100dvh-8rem)] min-h-[32rem]")}>
      {isDesktop ? <Group orientation="horizontal" className="min-h-0 flex-1 overflow-hidden rounded-xl border border-border">
        <Panel defaultSize="18" minSize="14" maxSize="30" className="min-w-0 overflow-y-auto bg-card p-3">
          <DatasetBrowser onInsertCode={(code) => insertCodeRef.current?.(code)} />
        </Panel>

        <Separator className={HORIZONTAL_HANDLE} />

        <Panel defaultSize="58" minSize="35" className="min-w-0">
          {!resolvedActiveWorkspaceId ? (
            <div className="flex h-full items-center justify-center p-6">
              <LoadingState count={1} itemClassName="h-64 w-full" />
            </div>
          ) : (
            <Group orientation="horizontal" className="h-full">
              <Panel defaultSize="72" minSize="40" className="min-w-0 p-3">
                <PythonNotebook
                  workspaceId={resolvedActiveWorkspaceId}
                  onInsertCodeRef={handleInsertCodeRef}
                  onLatestResult={setLatestResult}
                />
              </Panel>

              <Separator className={HORIZONTAL_HANDLE} />

              <Panel defaultSize="28" minSize="18" className="min-w-0 overflow-y-auto bg-card p-3">
                <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Variables</p>
                <VariableExplorer variables={latestResult?.variables ?? []} />
              </Panel>
            </Group>
          )}
        </Panel>

        <Separator className={HORIZONTAL_HANDLE} />

        <Panel defaultSize="24" minSize="16" maxSize="35" className="min-w-0 overflow-y-auto bg-card">
          {renderWorkspacePanel()}
        </Panel>
      </Group> : (
        <div className="flex min-w-0 flex-col gap-3">
          <section className="max-h-72 overflow-y-auto rounded-xl border border-border bg-card p-3" aria-label="Python datasets">
            <DatasetBrowser onInsertCode={(code) => insertCodeRef.current?.(code)} />
          </section>

          <section className="h-[70dvh] min-h-[36rem] min-w-0 overflow-hidden rounded-xl border border-border bg-card p-3" aria-label="Python notebook">
            {!resolvedActiveWorkspaceId ? (
              <div className="flex h-full items-center justify-center p-3">
                <LoadingState count={1} itemClassName="h-64 w-full" />
              </div>
            ) : (
              <PythonNotebook
                workspaceId={resolvedActiveWorkspaceId}
                onInsertCodeRef={handleInsertCodeRef}
                onLatestResult={setLatestResult}
              />
            )}
          </section>

          <section className="max-h-72 overflow-y-auto rounded-xl border border-border bg-card p-3" aria-label="Python variables">
            <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Variables</p>
            <VariableExplorer variables={latestResult?.variables ?? []} />
          </section>

          <section className="min-w-0 overflow-hidden rounded-xl border border-border bg-card" aria-label="Python workspaces and history">
            {renderWorkspacePanel()}
          </section>
        </div>
      )}
    </div>
  );
}
