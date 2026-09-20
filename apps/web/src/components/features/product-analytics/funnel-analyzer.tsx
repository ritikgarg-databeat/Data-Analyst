"use client";

import { useMemo, useState } from "react";
import type { Data, Layout } from "plotly.js";

import { PlotlyView } from "@/components/shared/plotly-view";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import type { RawColumnSchema } from "@data-analyst-lab/shared";
import { useDatasetFunnel } from "@/features/datasets/use-dataset-analysis";

interface FunnelAnalyzerProps {
  datasetId: string;
  tableName: string;
  columns: RawColumnSchema[];
}

/** The Funnel Analyzer (spec section 36) — step conversion/drop-off for a chosen event sequence. */
export function FunnelAnalyzer({ datasetId, tableName, columns }: FunnelAnalyzerProps) {
  const [userCol, setUserCol] = useState(columns.find((c) => /user/i.test(c.column_name))?.column_name ?? columns[0]?.column_name ?? "");
  const [eventCol, setEventCol] = useState(
    columns.find((c) => /event/i.test(c.column_name))?.column_name ?? columns[0]?.column_name ?? "",
  );
  const [stepsRaw, setStepsRaw] = useState("signup, activated, engaged, upgraded");
  const [submittedSteps, setSubmittedSteps] = useState<string[]>(["signup", "activated", "engaged", "upgraded"]);

  const funnelQuery = useDatasetFunnel(datasetId, tableName, userCol, eventCol, submittedSteps, true);

  function handleRun() {
    const steps = stepsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    setSubmittedSteps(steps);
  }

  const traces = useMemo<Data[]>(() => {
    if (!funnelQuery.data) return [];
    return [
      {
        type: "bar",
        x: funnelQuery.data.steps.map((s) => s.step),
        y: funnelQuery.data.steps.map((s) => s.users),
        text: funnelQuery.data.steps.map((s) => `${(s.conversion_from_start * 100).toFixed(1)}%`),
        textposition: "outside",
        marker: { color: "#2563eb" },
      } as Data,
    ];
  }, [funnelQuery.data]);

  const layout: Partial<Layout> = { margin: { t: 16, r: 16, b: 40, l: 56 }, yaxis: { title: { text: "Users" } } };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-3">
        <div className="flex w-full flex-col gap-1 sm:w-auto">
          <Label htmlFor="funnel-user-col">User column</Label>
          <Select id="funnel-user-col" value={userCol} onChange={(e) => setUserCol(e.target.value)} className="w-full sm:w-40">
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex w-full flex-col gap-1 sm:w-auto">
          <Label htmlFor="funnel-event-col">Event column</Label>
          <Select id="funnel-event-col" value={eventCol} onChange={(e) => setEventCol(e.target.value)} className="w-full sm:w-40">
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex w-full flex-1 flex-col gap-1 sm:min-w-64">
          <Label htmlFor="funnel-steps">Steps (in order, comma-separated)</Label>
          <Input id="funnel-steps" value={stepsRaw} onChange={(e) => setStepsRaw(e.target.value)} />
        </div>
        <Button onClick={handleRun} disabled={funnelQuery.isFetching}>
          {funnelQuery.isFetching ? "Running…" : "Run Funnel"}
        </Button>
      </div>

      {funnelQuery.isLoading ? (
        <LoadingState count={1} itemClassName="h-72" />
      ) : funnelQuery.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Unable to compute this funnel — check the column names and step names match real event values.
        </p>
      ) : funnelQuery.data ? (
        <div className="rounded-xl border border-border bg-card p-3">
          <PlotlyView data={traces} layout={layout} style={{ width: "100%", height: "340px" }} />
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="py-1.5">Step</th>
                  <th className="py-1.5 text-right">Users</th>
                  <th className="py-1.5 text-right">% of previous</th>
                  <th className="py-1.5 text-right">% of start</th>
                  <th className="py-1.5 text-right">Drop-off</th>
                </tr>
              </thead>
              <tbody>
                {funnelQuery.data.steps.map((s) => (
                  <tr key={s.step} className="border-b border-border last:border-0">
                    <td className="py-1.5 font-medium">{s.step}</td>
                    <td className="py-1.5 text-right tabular-nums">{s.users.toLocaleString()}</td>
                    <td className="py-1.5 text-right tabular-nums">{(s.conversion_from_previous * 100).toFixed(1)}%</td>
                    <td className="py-1.5 text-right tabular-nums">{(s.conversion_from_start * 100).toFixed(1)}%</td>
                    <td className="py-1.5 text-right tabular-nums">{s.drop_off.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{funnelQuery.data.methodology}</p>
        </div>
      ) : null}
    </div>
  );
}
