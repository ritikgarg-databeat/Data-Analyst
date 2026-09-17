"use client";

import { useMemo, useState } from "react";
import type { Data, Layout } from "plotly.js";

import { Button } from "@/components/ui/button";
import { PlotlyView } from "@/components/shared/plotly-view";
import { NumberListInput, parseNumberList } from "@/components/shared/number-list-input";
import { useComputeSummary } from "@/features/statistics/use-statistics";

export function SummaryStatsTool() {
  const [raw, setRaw] = useState("");
  const [chartValues, setChartValues] = useState<number[]>([]);
  const mutation = useComputeSummary();

  function handleCompute() {
    const values = parseNumberList(raw);
    if (values.length < 2) return;
    setChartValues(values);
    mutation.mutate({ values });
  }

  const result = mutation.data;

  // A histogram of the same values (spec section 54: reuse the Phase 5
  // visualization system rather than building a second chart pipeline).
  const histogramTraces = useMemo<Data[]>(
    () => (chartValues.length ? [{ type: "histogram", x: chartValues, marker: { color: "#2563eb" } } as Data] : []),
    [chartValues],
  );
  const histogramLayout: Partial<Layout> = { margin: { t: 8, r: 16, b: 32, l: 40 } };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Descriptive Statistics</p>
        <NumberListInput label="Values" value={raw} onChange={setRaw} />
        <Button onClick={handleCompute} disabled={parseNumberList(raw).length < 2 || mutation.isPending}>
          {mutation.isPending ? "Computing…" : "Compute"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Failed to compute statistics."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <p className="text-sm font-semibold text-foreground">Results</p>
          <dl className="grid grid-cols-3 gap-3 text-sm">
            {[
              ["Count", result.count],
              ["Mean", result.mean.toFixed(3)],
              ["Median", result.median.toFixed(3)],
              ["Std Dev", result.std_dev.toFixed(3)],
              ["Variance", result.variance.toFixed(3)],
              ["CV", result.coefficient_of_variation !== null ? result.coefficient_of_variation.toFixed(3) : "—"],
              ["Min", result.min.toFixed(3)],
              ["Q1", result.q1.toFixed(3)],
              ["Median (p50)", result.percentiles["50"]?.toFixed(3) ?? "—"],
              ["Q3", result.q3.toFixed(3)],
              ["Max", result.max.toFixed(3)],
              ["IQR", result.iqr.toFixed(3)],
              ["Skewness", result.skewness.toFixed(3)],
              ["Outliers", result.outlier_count],
              ["Mode", result.mode.length ? result.mode.map((m) => m.toFixed(2)).join(", ") : "—"],
            ].map(([label, value]) => (
              <div key={label as string}>
                <dt className="text-xs text-muted-foreground">{label}</dt>
                <dd className="font-medium tabular-nums text-foreground">{value}</dd>
              </div>
            ))}
          </dl>
          <div className="rounded-md bg-accent/40 px-3 py-2 text-xs text-foreground">
            95% CI for the mean: [{result.mean_confidence_interval.lower.toFixed(3)},{" "}
            {result.mean_confidence_interval.upper.toFixed(3)}] (margin of error ±
            {result.mean_confidence_interval.margin_of_error.toFixed(3)})
          </div>
          <p className="text-xs text-muted-foreground">{result.methodology}</p>
          <PlotlyView data={histogramTraces} layout={histogramLayout} style={{ width: "100%", height: "200px" }} />
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Paste at least 2 values and click Compute.
        </div>
      )}
    </div>
  );
}
