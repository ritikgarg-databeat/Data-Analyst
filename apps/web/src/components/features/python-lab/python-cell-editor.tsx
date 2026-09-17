"use client";

import { useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { ChevronDown, ChevronUp, Play, Trash2 } from "lucide-react";
import type { OnMount } from "@monaco-editor/react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Monaco touches `window` while loading its worker bundles, so it must never
// run during SSR — load it lazily, client-side only. Mirrors sql-editor.tsx.
const MonacoEditor = dynamic(() => import("@monaco-editor/react").then((mod) => mod.default), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-40 items-center justify-center text-sm text-muted-foreground">
      Loading editor…
    </div>
  ),
});

interface PythonCellEditorProps {
  value: string;
  onChange: (value: string) => void;
  /** Called on the toolbar "Run" button and on Ctrl/Cmd+Enter inside the editor. Omit to hide the button. */
  onRun?: () => void;
  isRunning?: boolean;
  readOnly?: boolean;
  height?: string | number;
  className?: string;
  ariaLabel?: string;
  /** 1-based cell index in a notebook — shown as `[n]` instead of the generic "PYTHON" label. */
  cellNumber?: number;
  onDelete?: () => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  canMoveUp?: boolean;
  canMoveDown?: boolean;
}

/**
 * A Monaco-based Python editor with a "Run" affordance, sized to fill its
 * container. Modeled directly on sql-lab/sql-editor.tsx (same Ctrl/Cmd+Enter
 * keybinding pattern), with optional notebook-cell chrome (numbering,
 * delete, reorder) so the same component serves both the multi-cell
 * notebook and the single-editor exercise workspace.
 */
export function PythonCellEditor({
  value,
  onChange,
  onRun,
  isRunning = false,
  readOnly = false,
  height = "100%",
  className,
  ariaLabel = "Python code editor",
  cellNumber,
  onDelete,
  onMoveUp,
  onMoveDown,
  canMoveUp = true,
  canMoveDown = true,
}: PythonCellEditorProps) {
  // Keep the latest onRun in a ref so the Monaco keybinding (registered once
  // on mount) always calls the current handler rather than a stale closure.
  const onRunRef = useRef(onRun);
  useEffect(() => {
    onRunRef.current = onRun;
  }, [onRun]);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onRunRef.current?.();
    });
  }, []);

  const hasCellChrome = Boolean(onDelete || onMoveUp || onMoveDown);

  return (
    <div
      className={cn(
        "flex h-full min-h-64 flex-col overflow-hidden rounded-xl border border-border bg-card",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-border bg-muted/40 px-3 py-1.5">
        <span className="font-mono text-xs font-medium tracking-wide text-muted-foreground">
          {cellNumber != null ? `[${cellNumber}]` : "PYTHON"}
        </span>
        <div className="flex items-center gap-1">
          {hasCellChrome ? (
            <>
              {onMoveUp ? (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-7"
                  aria-label="Move cell up"
                  onClick={onMoveUp}
                  disabled={!canMoveUp}
                >
                  <ChevronUp className="size-3.5" aria-hidden="true" />
                </Button>
              ) : null}
              {onMoveDown ? (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-7"
                  aria-label="Move cell down"
                  onClick={onMoveDown}
                  disabled={!canMoveDown}
                >
                  <ChevronDown className="size-3.5" aria-hidden="true" />
                </Button>
              ) : null}
              {onDelete ? (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-7"
                  aria-label="Delete cell"
                  onClick={onDelete}
                >
                  <Trash2 className="size-3.5" aria-hidden="true" />
                </Button>
              ) : null}
            </>
          ) : null}
          {onRun ? (
            <Button type="button" size="sm" onClick={onRun} disabled={isRunning || readOnly}>
              <Play className="size-3.5" aria-hidden="true" />
              {isRunning ? "Running..." : "Run"}
              <span className="ml-1 hidden text-[10px] font-normal opacity-70 sm:inline">Ctrl/Cmd+Enter</span>
            </Button>
          ) : null}
        </div>
      </div>
      <div className="min-h-0 flex-1" role="group" aria-label={ariaLabel}>
        <MonacoEditor
          height={height}
          defaultLanguage="python"
          language="python"
          value={value}
          onChange={(next) => onChange(next ?? "")}
          onMount={handleMount}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbersMinChars: 3,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            wordWrap: "on",
          }}
        />
      </div>
    </div>
  );
}
