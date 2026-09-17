import { AlertTriangle, Lightbulb } from "lucide-react";
import type { PythonErrorSchema } from "@data-analyst-lab/shared";

interface PythonErrorPanelProps {
  error: PythonErrorSchema | null;
  className?: string;
}

/**
 * Renders a Python execution error — the real error type/message/traceback
 * from the sandbox — plus its derived hint if present. Modeled directly on
 * sql-lab/sql-error-panel.tsx; never fabricates wording beyond what the API
 * returned.
 */
export function PythonErrorPanel({ error, className }: PythonErrorPanelProps) {
  if (!error) return null;

  return (
    <div role="alert" className={className}>
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-destructive">
          <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
          {error.error_type}
          {error.line != null ? (
            <span className="text-xs font-normal text-destructive/80">on line {error.line}</span>
          ) : null}
        </div>
        <p className="mt-1 text-sm text-destructive">{error.message}</p>
        {error.traceback_text ? (
          <pre className="mt-2 overflow-x-auto rounded-md bg-destructive/10 px-3 py-2 font-mono text-xs whitespace-pre-wrap text-destructive">
            {error.traceback_text}
          </pre>
        ) : null}
      </div>

      {error.hint ? (
        <div className="mt-2 flex gap-2.5 rounded-xl border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-warning-foreground" aria-hidden="true" />
          <div>
            <p className="text-xs font-semibold tracking-wide uppercase text-warning-foreground/80">Hint</p>
            <p className="text-foreground">{error.hint}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
