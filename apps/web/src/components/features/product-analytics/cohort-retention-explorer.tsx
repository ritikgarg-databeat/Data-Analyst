"use client";

import { useState } from "react";
import type { RawColumnSchema } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import { useDatasetCohortRetention } from "@/features/datasets/use-dataset-analysis";

interface CohortRetentionExplorerProps {
  datasetId: string;
  tableName: string;
  columns: RawColumnSchema[];
}

function cellColor(pct: number | null): string {
  if (pct === null) return "transparent";
  const alpha = Math.max(0.08, Math.min(0.9, pct / 100));
  return `rgba(37, 99, 235, ${alpha})`;
}

/** The interactive cohort retention explorer (spec section 37). */
export function CohortRetentionExplorer({ datasetId, tableName, columns }: CohortRetentionExplorerProps) {
  const [userCol, setUserCol] = useState(columns.find((c) => /user/i.test(c.column_name))?.column_name ?? columns[0]?.column_name ?? "");
  const [cohortCol, setCohortCol] = useState(
    columns.find((c) => /signup|cohort|created/i.test(c.column_name))?.column_name ?? columns[0]?.column_name ?? "",
  );
  const [activityCol, setActivityCol] = useState(
    columns.find((c) => /event_timestamp|activity/i.test(c.column_name))?.column_name ?? columns[0]?.column_name ?? "",
  );
  const [granularity, setGranularity] = useState("month");
  const [periods, setPeriods] = useState(6);
  const [enabled, setEnabled] = useState(true);

  const cohortQuery = useDatasetCohortRetention(datasetId, tableName, userCol, cohortCol, activityCol, granularity, periods, enabled);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="cohort-user-col">User column</Label>
          <Select id="cohort-user-col" value={userCol} onChange={(e) => setUserCol(e.target.value)} className="w-36">
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="cohort-date-col">Cohort date column</Label>
          <Select id="cohort-date-col" value={cohortCol} onChange={(e) => setCohortCol(e.target.value)} className="w-36">
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="activity-date-col">Activity date column</Label>
          <Select id="activity-date-col" value={activityCol} onChange={(e) => setActivityCol(e.target.value)} className="w-36">
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="cohort-granularity">Granularity</Label>
          <Select id="cohort-granularity" value={granularity} onChange={(e) => setGranularity(e.target.value)} className="w-28">
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="cohort-periods">Periods</Label>
          <Input
            id="cohort-periods"
            type="number"
            min={1}
            max={24}
            value={periods}
            onChange={(e) => setPeriods(Number(e.target.value))}
            className="w-20"
          />
        </div>
        <Button
          onClick={() => {
            setEnabled(false);
            requestAnimationFrame(() => setEnabled(true));
          }}
        >
          Build Matrix
        </Button>
      </div>

      {cohortQuery.isLoading ? (
        <LoadingState count={1} itemClassName="h-64" />
      ) : cohortQuery.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Unable to build this cohort matrix — check the column names (cohort date must be denormalized onto every row).
        </p>
      ) : cohortQuery.data && cohortQuery.data.cohorts.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-border bg-card p-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="px-2 py-1.5">Cohort</th>
                <th className="px-2 py-1.5 text-right">Size</th>
                {Array.from({ length: cohortQuery.data.periods }, (_, i) => (
                  <th key={i} className="px-2 py-1.5 text-right">
                    {granularity[0].toUpperCase()}
                    {i}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cohortQuery.data.cohorts.map((row) => (
                <tr key={row.cohort} className="border-t border-border">
                  <td className="px-2 py-1.5 font-mono">{row.cohort.slice(0, 10)}</td>
                  <td className="px-2 py-1.5 text-right tabular-nums">{row.cohort_size}</td>
                  {row.retention_pct.map((pct, i) => (
                    <td
                      key={i}
                      className="px-2 py-1.5 text-right tabular-nums text-foreground"
                      style={{ backgroundColor: cellColor(pct) }}
                    >
                      {pct !== null ? `${pct.toFixed(0)}%` : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No cohorts found for these columns.</p>
      )}
    </div>
  );
}
