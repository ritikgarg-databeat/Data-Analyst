"use client";

import { useState } from "react";
import type { ColumnProfileSchema } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useDatasetOutliers } from "@/features/datasets/use-dataset-drilldown";

function Stat({ label, value }: { label: string; value: string | number | null }) {
  if (value === null || value === undefined) return null;
  return (
    <div className="flex items-center justify-between border-b border-border/60 py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium tabular-nums text-foreground">{value}</span>
    </div>
  );
}

interface ColumnDetailSheetProps {
  datasetSlug: string;
  tableName: string;
  column: ColumnProfileSchema | null;
  onOpenChange: (open: boolean) => void;
}

/** Section 13 of the Phase 5 spec: type/nulls/uniqueness/min/max/mean/median/stddev/quantiles/samples/frequencies. */
export function ColumnDetailSheet({ datasetSlug, tableName, column, onOpenChange }: ColumnDetailSheetProps) {
  const [inspectOutliers, setInspectOutliers] = useState(false);
  const outliersQuery = useDatasetOutliers(datasetSlug, tableName, column?.column_name, inspectOutliers);

  return (
    <Sheet open={Boolean(column)} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:w-96">
        {column ? (
          <>
            <SheetHeader>
              <SheetTitle>{column.column_name}</SheetTitle>
              <div className="flex items-center gap-1.5">
                <Badge variant="outline">{column.data_type}</Badge>
                <span className="text-xs text-muted-foreground">{column.inferred_sql_type}</span>
              </div>
            </SheetHeader>

            <div className="flex flex-col gap-4 overflow-y-auto px-4 pb-4">
              <div>
                <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Completeness &amp; uniqueness
                </p>
                <Stat label="Null count" value={column.null_count} />
                <Stat label="Null %" value={`${column.null_percentage.toFixed(1)}%`} />
                <Stat label="Unique count" value={column.unique_count} />
                <Stat label="Unique %" value={`${column.unique_percentage.toFixed(1)}%`} />
              </div>

              {column.data_type === "numeric" ? (
                <div>
                  <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    Statistics
                  </p>
                  <Stat label="Min" value={column.min_value} />
                  <Stat label="Max" value={column.max_value} />
                  <Stat label="Mean" value={column.mean?.toFixed(2) ?? null} />
                  <Stat label="Median" value={column.median?.toFixed(2) ?? null} />
                  <Stat label="Std dev" value={column.std_dev?.toFixed(2) ?? null} />
                  <Stat label="P25" value={column.quantiles?.p25?.toFixed(2) ?? null} />
                  <Stat label="P75" value={column.quantiles?.p75?.toFixed(2) ?? null} />
                  <Stat label="Zero values" value={column.zero_count} />
                  <Stat label="Negative values" value={column.negative_count} />
                </div>
              ) : null}

              {(column.data_type === "text" || column.data_type === "categorical") &&
              (column.min_length !== null || column.max_length !== null) ? (
                <div>
                  <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    Length distribution
                  </p>
                  <Stat label="Min length" value={column.min_length} />
                  <Stat label="Max length" value={column.max_length} />
                  <Stat label="Avg length" value={column.avg_length?.toFixed(1) ?? null} />
                </div>
              ) : null}

              {column.outlier_count ? (
                <div>
                  <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    Outliers
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {column.outlier_count.toLocaleString()} potential outlier(s) by the {column.outlier_method}{" "}
                    method. These may be legitimate business observations, not errors.
                  </p>
                  {!inspectOutliers ? (
                    <Button variant="outline" size="sm" className="mt-2" onClick={() => setInspectOutliers(true)}>
                      Inspect
                    </Button>
                  ) : outliersQuery.data ? (
                    <div className="mt-2 overflow-x-auto rounded-md border border-border">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-border bg-muted/50">
                            {outliersQuery.data.columns.map((c) => (
                              <th key={c} className="px-2 py-1 text-left font-medium">
                                {c}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {outliersQuery.data.sample_rows.map((row, i) => (
                            <tr key={i} className="border-b border-border/60 last:border-0">
                              {row.map((cell, j) => (
                                <td key={j} className="px-2 py-1 tabular-nums">
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

              {column.top_values && column.top_values.length > 0 ? (
                <div>
                  <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    Frequency distribution
                  </p>
                  <div className="flex flex-col gap-1">
                    {column.top_values.map((tv) => (
                      <div key={tv.value} className="flex items-center gap-2 text-xs">
                        <span className="w-20 truncate text-foreground">{tv.value}</span>
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                          <div className="h-full bg-primary" style={{ width: `${tv.percentage}%` }} />
                        </div>
                        <span className="w-14 shrink-0 text-right text-muted-foreground">
                          {tv.count.toLocaleString()} ({tv.percentage.toFixed(1)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {column.sample_values && column.sample_values.length > 0 ? (
                <div>
                  <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    Sample values
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {column.sample_values.map((value, i) => (
                      <Badge key={i} variant="outline">
                        {String(value)}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
