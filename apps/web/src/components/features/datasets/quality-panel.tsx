"use client";

import { useState } from "react";
import { AlertTriangle, Info, OctagonAlert } from "lucide-react";
import type { QualityReportSchema } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useDatasetDuplicates } from "@/features/datasets/use-dataset-drilldown";

const SEVERITY_ICON = { high: OctagonAlert, medium: AlertTriangle, low: Info } as const;
const SEVERITY_VARIANT = { high: "destructive", medium: "warning", low: "outline" } as const;

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-sm text-muted-foreground">{label}</span>
      <Progress value={value} className="flex-1" />
      <span className="w-12 shrink-0 text-right text-sm font-medium tabular-nums">{value.toFixed(0)}%</span>
    </div>
  );
}

export function QualityPanel({ datasetSlug, report }: { datasetSlug: string; report: QualityReportSchema }) {
  const [inspectDuplicates, setInspectDuplicates] = useState(false);
  const duplicatesQuery = useDatasetDuplicates(datasetSlug, report.table_name, inspectDuplicates);

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Data Quality</p>
            <p className="text-3xl font-semibold text-foreground">{report.overall_score.toFixed(0)}%</p>
          </div>
        </div>
        <div className="flex flex-col gap-2.5">
          <ScoreRow label="Completeness" value={report.completeness_score} />
          <ScoreRow label="Uniqueness" value={report.uniqueness_score} />
          <ScoreRow label="Validity" value={report.validity_score} />
          <ScoreRow label="Consistency" value={report.consistency_score} />
        </div>
        <p className="mt-4 text-xs text-muted-foreground">{report.methodology}</p>
      </div>

      {report.duplicate_row_count > 0 ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-sm font-medium text-foreground">
            Potential duplicate rows: {report.duplicate_row_count.toLocaleString()}
          </p>
          {!inspectDuplicates ? (
            <Button variant="outline" size="sm" className="mt-2" onClick={() => setInspectDuplicates(true)}>
              Inspect
            </Button>
          ) : duplicatesQuery.data ? (
            <div className="mt-2 overflow-x-auto rounded-md border border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    {duplicatesQuery.data.columns.map((c) => (
                      <th key={c} className="px-2 py-1 text-left font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {duplicatesQuery.data.sample_rows.map((row, i) => (
                    <tr key={i} className="border-b border-border/60 last:border-0">
                      {row.map((cell, j) => (
                        <td key={j} className="px-2 py-1">
                          {String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      ) : null}

      <div>
        <p className="mb-2 text-sm font-semibold text-foreground">Issues found</p>
        {report.issues.length === 0 ? (
          <p className="text-sm text-muted-foreground">No notable issues detected.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {report.issues.map((issue, i) => {
              const Icon = SEVERITY_ICON[issue.severity];
              return (
                <li key={i} className="flex items-start gap-2 rounded-lg border border-border p-3">
                  <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={SEVERITY_VARIANT[issue.severity]}>{issue.severity}</Badge>
                      {issue.column ? <span className="text-xs font-medium text-foreground">{issue.column}</span> : null}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{issue.detail}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
