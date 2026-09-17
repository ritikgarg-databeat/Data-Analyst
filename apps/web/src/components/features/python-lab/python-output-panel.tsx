import type { PythonExecutionResultSchema } from "@data-analyst-lab/shared";

import { cn } from "@/lib/utils";

import { ChartOutput } from "./chart-output";
import { DataFrameViewer } from "./dataframe-viewer";
import { PythonErrorPanel } from "./python-error-panel";

interface PythonOutputPanelProps {
  result: PythonExecutionResultSchema;
  className?: string;
}

/**
 * Everything a single Python execution produced, in the order Jupyter-style
 * notebooks conventionally show it: stdout, then the auto-displayed
 * trailing-expression result (a DataFrameViewer if it's a DataFrame,
 * otherwise its preview text), then any charts, then an error if the run
 * failed. Rendered under a cell after running it.
 */
export function PythonOutputPanel({ result, className }: PythonOutputPanelProps) {
  const hasStdout = result.stdout.trim().length > 0;
  const hasAnything = hasStdout || Boolean(result.display_value) || result.charts.length > 0 || Boolean(result.error);

  return (
    <div className={cn("space-y-3", className)}>
      {hasStdout ? (
        <div>
          <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">stdout</p>
          <pre className="overflow-x-auto rounded-lg border border-border bg-muted/30 px-3 py-2 font-mono text-xs whitespace-pre-wrap text-foreground">
            {result.stdout}
          </pre>
          {result.stdout_truncated ? (
            <p className="mt-1 text-xs text-muted-foreground">
              Output truncated — this cell printed more than the display cap allows.
            </p>
          ) : null}
        </div>
      ) : null}

      {result.display_value ? (
        <div>
          <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Result</p>
          {result.display_value.dataframe ? (
            <DataFrameViewer dataframe={result.display_value.dataframe} name={result.display_value.name} />
          ) : (
            <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
              <span className="font-mono text-xs text-muted-foreground">{result.display_value.type_name}</span>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap font-mono text-sm text-foreground">
                {result.display_value.preview}
              </pre>
            </div>
          )}
        </div>
      ) : null}

      {result.charts.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            Chart{result.charts.length === 1 ? "" : "s"}
          </p>
          {result.charts.map((chart, index) => (
            <ChartOutput key={index} chart={chart} />
          ))}
        </div>
      ) : null}

      <PythonErrorPanel error={result.error} />

      {!hasAnything ? <p className="text-sm text-muted-foreground">No output.</p> : null}
    </div>
  );
}
