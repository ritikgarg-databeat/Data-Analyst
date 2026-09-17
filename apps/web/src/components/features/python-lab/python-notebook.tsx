"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Download, ListRestart, Play, Plus, RotateCcw, Sparkles } from "lucide-react";
import type { PythonCellSchema, PythonExecutionResultSchema } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import {
  useAddPythonCell,
  useDeletePythonCell,
  usePythonCells,
  useRecordPythonCellResult,
  useUpdatePythonCell,
} from "@/features/python/use-python-cells";
import { usePythonExecute } from "@/features/python/use-python-execute";
import { useCreatePythonRuntime } from "@/features/python/use-python-runtimes";
import { useDestroyPythonRuntime } from "@/features/python/use-python-destroy-runtime";
import { useRestartPythonRuntime } from "@/features/python/use-python-restart-runtime";
import { cn } from "@/lib/utils";

import { PythonAskAiPanel } from "./python-ask-ai-panel";
import { PythonCellEditor } from "./python-cell-editor";
import { PythonOutputPanel } from "./python-output-panel";

function downloadBlob(content: string, mimeType: string, filename: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

interface PythonNotebookProps {
  workspaceId: string;
  /** Exposed so a sibling panel (the dataset browser) can insert a code snippet into the currently focused cell. */
  onInsertCodeRef?: (insert: (code: string) => void) => void;
  /** Called after every cell run (and on restart, with `null`) with the runtime's current variable listing, for a sibling Variable Explorer panel. */
  onLatestResult?: (result: PythonExecutionResultSchema | null) => void;
  className?: string;
}

/**
 * The multi-cell orchestrator: an ordered, numbered list of cells (each a
 * PythonCellEditor + its PythonOutputPanel), notebook-level controls (Run
 * All, Clear Outputs, Restart Runtime, Export .py), and the lazily-created
 * PythonRuntime backing every execution in this workspace. Cells and their
 * last results are persisted server-side (apps/api's
 * /python/workspaces/{id}/cells) so reloading the page restores them.
 */
export function PythonNotebook({ workspaceId, onInsertCodeRef, onLatestResult, className }: PythonNotebookProps) {
  const cellsQuery = usePythonCells(workspaceId);
  const addCell = useAddPythonCell();
  const updateCell = useUpdatePythonCell();
  const deleteCell = useDeletePythonCell();
  const recordResult = useRecordPythonCellResult();
  const createRuntime = useCreatePythonRuntime();
  const restartRuntime = useRestartPythonRuntime();
  const destroyRuntime = useDestroyPythonRuntime();
  const executeMutation = usePythonExecute();

  const [runtimeId, setRuntimeId] = useState<string | null>(null);
  const [codeByCellId, setCodeByCellId] = useState<Record<string, string>>({});
  const [clearedCellIds, setClearedCellIds] = useState<Set<string>>(new Set());
  const [focusedCellId, setFocusedCellId] = useState<string | null>(null);
  const [runningCellId, setRunningCellId] = useState<string | null>(null);
  const [isRunningAll, setIsRunningAll] = useState(false);
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [askAiCellId, setAskAiCellId] = useState<string | null>(null);

  const sortedCells = useMemo(
    () => [...(cellsQuery.data ?? [])].sort((a, b) => a.display_order - b.display_order),
    [cellsQuery.data],
  );
  // The "active" cell (target for dataset-browser/history inserts) defaults to the last cell
  // until the user explicitly focuses a different one — derived directly rather than mirrored
  // into state-via-effect, since `sortedCells` is already available during render.
  const activeCellId = focusedCellId ?? sortedCells[sortedCells.length - 1]?.id ?? null;

  // Reset the held runtime whenever the caller switches workspaces — React's documented
  // "adjust state during rendering" pattern (no effect needed: this runs synchronously as part
  // of this render, before it commits, rather than causing an extra render pass).
  const [runtimeWorkspaceId, setRuntimeWorkspaceId] = useState(workspaceId);
  if (runtimeWorkspaceId !== workspaceId) {
    setRuntimeWorkspaceId(workspaceId);
    setRuntimeId(null);
    setRuntimeError(null);
  }

  // Keep a ref mirror of `runtimeId` so the cleanup below (destroying the runtime that belonged
  // to the previous workspace, or on unmount) always sees the latest value rather than the one
  // captured when the effect last ran.
  const runtimeIdRef = useRef<string | null>(null);
  useEffect(() => {
    runtimeIdRef.current = runtimeId;
  }, [runtimeId]);

  useEffect(() => {
    return () => {
      if (runtimeIdRef.current) destroyRuntime.mutate(runtimeIdRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  function insertCodeIntoActiveCell(code: string) {
    const targetId = activeCellId;
    if (!targetId) return;
    setCodeByCellId((prev) => {
      const current = prev[targetId] ?? "";
      return { ...prev, [targetId]: current ? `${current}\n${code}` : code };
    });
    setFocusedCellId(targetId);
  }
  onInsertCodeRef?.(insertCodeIntoActiveCell);

  async function ensureRuntime(): Promise<string> {
    if (runtimeId) return runtimeId;
    const runtime = await createRuntime.mutateAsync(workspaceId);
    setRuntimeId(runtime.id);
    return runtime.id;
  }

  async function runCell(cell: PythonCellSchema) {
    const code = codeByCellId[cell.id] ?? cell.code;
    setRunningCellId(cell.id);
    setRuntimeError(null);
    try {
      const rtId = await ensureRuntime();
      await updateCell.mutateAsync({ workspaceId, cellId: cell.id, body: { code } });
      const result = await executeMutation.mutateAsync({
        runtimeId: rtId,
        body: { code, workspace_id: workspaceId },
      });
      await recordResult.mutateAsync({ workspaceId, cellId: cell.id, result });
      setClearedCellIds((prev) => {
        if (!prev.has(cell.id)) return prev;
        const next = new Set(prev);
        next.delete(cell.id);
        return next;
      });
      onLatestResult?.(result);
    } catch (error) {
      setRuntimeError(errorMessage(error));
    } finally {
      setRunningCellId(null);
    }
  }

  async function handleRunAll() {
    setIsRunningAll(true);
    try {
      for (const cell of sortedCells) {
        await runCell(cell);
      }
    } finally {
      setIsRunningAll(false);
    }
  }

  function handleAddCell() {
    addCell.mutate(
      { workspaceId, body: { code: "" } },
      { onSuccess: (cell) => setCodeByCellId((prev) => ({ ...prev, [cell.id]: cell.code })) },
    );
  }

  function handleDeleteCell(cellId: string) {
    deleteCell.mutate({ workspaceId, cellId });
    setCodeByCellId((prev) => {
      if (!(cellId in prev)) return prev;
      const next = { ...prev };
      delete next[cellId];
      return next;
    });
    setFocusedCellId((prev) => (prev === cellId ? null : prev));
  }

  function handleMove(cellId: string, direction: "up" | "down") {
    const index = sortedCells.findIndex((c) => c.id === cellId);
    const swapIndex = direction === "up" ? index - 1 : index + 1;
    if (index < 0 || swapIndex < 0 || swapIndex >= sortedCells.length) return;
    const a = sortedCells[index];
    const b = sortedCells[swapIndex];
    updateCell.mutate({ workspaceId, cellId: a.id, body: { display_order: b.display_order } });
    updateCell.mutate({ workspaceId, cellId: b.id, body: { display_order: a.display_order } });
  }

  function handleClearOutputs() {
    setClearedCellIds(new Set(sortedCells.map((c) => c.id)));
  }

  async function handleRestartRuntime() {
    if (!runtimeId) return;
    setRuntimeError(null);
    try {
      await restartRuntime.mutateAsync(runtimeId);
      setClearedCellIds(new Set(sortedCells.map((c) => c.id)));
      onLatestResult?.(null);
    } catch (error) {
      setRuntimeError(errorMessage(error));
    }
  }

  function handleExportPy() {
    const content = sortedCells
      .map((cell, index) => `# [${index + 1}]\n${codeByCellId[cell.id] ?? cell.code}`)
      .join("\n\n");
    downloadBlob(content, "text/x-python;charset=utf-8;", "python-lab-notebook.py");
  }

  if (cellsQuery.isLoading) {
    return <LoadingState count={2} itemClassName="h-64" className={className} />;
  }
  if (cellsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load this workspace"
        message="We couldn't reach the API to load this workspace's cells."
        retry={() => void cellsQuery.refetch()}
        className={className}
      />
    );
  }

  const isBusy = runningCellId !== null || isRunningAll;

  return (
    <div className={cn("flex h-full flex-col gap-3", className)}>
      <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-2">
        <Button type="button" size="sm" variant="outline" onClick={handleAddCell} disabled={addCell.isPending}>
          <Plus className="size-3.5" aria-hidden="true" />
          Add Cell
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={() => void handleRunAll()} disabled={isBusy || sortedCells.length === 0}>
          <Play className="size-3.5" aria-hidden="true" />
          {isRunningAll ? "Running all..." : "Run All"}
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={handleClearOutputs} disabled={sortedCells.length === 0}>
          <ListRestart className="size-3.5" aria-hidden="true" />
          Clear Outputs
        </Button>
        <Button type="button" size="sm" variant="outline" onClick={handleExportPy} disabled={sortedCells.length === 0}>
          <Download className="size-3.5" aria-hidden="true" />
          Export .py
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setAskAiCellId(activeCellId)}
          disabled={!activeCellId}
        >
          <Sparkles className="size-3.5" aria-hidden="true" />
          Ask AI
        </Button>
        <Button
          type="button"
          size="sm"
          variant="destructive"
          className="ml-auto"
          onClick={() => void handleRestartRuntime()}
          disabled={!runtimeId || restartRuntime.isPending}
        >
          <RotateCcw className="size-3.5" aria-hidden="true" />
          {restartRuntime.isPending ? "Restarting..." : "Restart Runtime"}
        </Button>
      </div>

      {runtimeError ? (
        <div role="alert" className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
          <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          {runtimeError}
        </div>
      ) : null}

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pb-2">
        {sortedCells.map((cell, index) => (
          <div key={cell.id} onFocus={() => setFocusedCellId(cell.id)} className="space-y-2">
            <PythonCellEditor
              value={codeByCellId[cell.id] ?? cell.code}
              onChange={(next) => setCodeByCellId((prev) => ({ ...prev, [cell.id]: next }))}
              onRun={() => void runCell(cell)}
              isRunning={runningCellId === cell.id || isRunningAll}
              readOnly={isRunningAll && runningCellId !== cell.id}
              cellNumber={index + 1}
              onDelete={sortedCells.length > 1 ? () => handleDeleteCell(cell.id) : undefined}
              onMoveUp={() => handleMove(cell.id, "up")}
              onMoveDown={() => handleMove(cell.id, "down")}
              canMoveUp={index > 0}
              canMoveDown={index < sortedCells.length - 1}
              className="h-64"
              ariaLabel={`Python cell ${index + 1} editor`}
            />
            {cell.last_result && !clearedCellIds.has(cell.id) ? (
              <>
                <PythonOutputPanel result={cell.last_result} className="rounded-xl border border-border bg-card p-3" />
                {cell.last_result.error ? (
                  <Button variant="outline" size="sm" onClick={() => setAskAiCellId(cell.id)}>
                    <Sparkles className="size-3.5" aria-hidden="true" />
                    Ask AI about this error
                  </Button>
                ) : null}
              </>
            ) : null}
          </div>
        ))}
      </div>

      <PythonAskAiPanel
        key={askAiCellId ?? "none"}
        open={askAiCellId !== null}
        onOpenChange={(open) => {
          if (!open) setAskAiCellId(null);
        }}
        code={askAiCellId ? codeByCellId[askAiCellId] ?? sortedCells.find((c) => c.id === askAiCellId)?.code ?? "" : ""}
        error={
          askAiCellId
            ? (sortedCells.find((c) => c.id === askAiCellId)?.last_result?.error ?? null)
            : null
        }
      />
    </div>
  );
}
