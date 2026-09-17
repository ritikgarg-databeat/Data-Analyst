"use client";

import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { ValidationResultSchema } from "@data-analyst-lab/shared";

interface ValidationPanelProps {
  result: ValidationResultSchema | null;
}

/** Findings from a real validation run (missing PKs, invalid FKs, circular relationships, etc.) —
 * "educational warnings, not absolute rules" per the Data Modeler's own design. */
export function ValidationPanel({ result }: ValidationPanelProps) {
  if (!result) return null;

  if (result.findings.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-success/30 bg-success/5 px-3 py-2 text-sm">
        <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
        <p className="text-foreground">No issues found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {result.error_count} error(s), {result.warning_count} warning(s)
      </p>
      <ul className="space-y-1.5">
        {result.findings.map((finding, index) => (
          <li
            key={index}
            className="flex items-start gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm"
          >
            {finding.severity === "error" ? (
              <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
            ) : (
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" aria-hidden="true" />
            )}
            <div className="min-w-0">
              <p className="text-foreground">{finding.message}</p>
              {finding.table_name ? (
                <p className="mt-0.5 font-mono text-xs text-muted-foreground">{finding.table_name}</p>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
