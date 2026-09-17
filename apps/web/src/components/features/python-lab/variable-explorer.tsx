"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Table2, Variable } from "lucide-react";
import type { PythonVariableSchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils";

import { DataFrameViewer } from "./dataframe-viewer";

interface VariableExplorerProps {
  variables: PythonVariableSchema[];
  className?: string;
}

/** Compact right-aligned summary — "125,420 × 14" for a DataFrame's shape, otherwise the value's own preview text. */
function shapeLabel(variable: PythonVariableSchema): string {
  if (variable.shape && variable.shape.length > 0) {
    return variable.shape.map((n) => n.toLocaleString()).join(" × ");
  }
  return variable.preview;
}

/**
 * Lists the variables defined after a Python execution. Non-DataFrame
 * variables just show their preview; clicking a DataFrame-typed variable
 * expands its full DataFrameViewer inline.
 */
export function VariableExplorer({ variables, className }: VariableExplorerProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  if (variables.length === 0) {
    return (
      <EmptyState
        icon={Variable}
        title="No variables yet"
        description="Run a cell to see its variables here."
        className={className}
      />
    );
  }

  return (
    <ul className={cn("divide-y divide-border", className)}>
      {variables.map((variable) => {
        const isDataFrame = Boolean(variable.dataframe);
        const isExpanded = Boolean(expanded[variable.name]);
        return (
          <li key={variable.name} className="py-1.5">
            <button
              type="button"
              onClick={() =>
                isDataFrame && setExpanded((prev) => ({ ...prev, [variable.name]: !prev[variable.name] }))
              }
              aria-expanded={isDataFrame ? isExpanded : undefined}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-sm outline-none",
                isDataFrame && "hover:bg-muted/50",
              )}
            >
              {isDataFrame ? (
                isExpanded ? (
                  <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                ) : (
                  <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                )
              ) : (
                <span className="size-3.5 shrink-0" aria-hidden="true" />
              )}
              {isDataFrame ? (
                <Table2 className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
              ) : (
                <Variable className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
              )}
              <span className="truncate font-mono font-medium text-foreground">{variable.name}</span>
              <span className="shrink-0 text-xs text-muted-foreground">{variable.type_name}</span>
              <span className="ml-auto min-w-0 truncate pl-2 text-right text-xs text-muted-foreground">
                {shapeLabel(variable)}
              </span>
            </button>

            {isDataFrame && isExpanded && variable.dataframe ? (
              <div className="mt-2 border-l border-border pl-4">
                <DataFrameViewer dataframe={variable.dataframe} name={variable.name} />
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
