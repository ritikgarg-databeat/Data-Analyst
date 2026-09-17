"use client";

import { forwardRef, useImperativeHandle, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { NumberListInput, parseNumberList } from "@/components/shared/number-list-input";
import { Select } from "@/components/ui/select";
import { useRunCorrelationTest } from "@/features/statistics/use-statistics";

export interface CorrelationToolHandle {
  setMethod: (method: "pearson" | "spearman") => void;
}

export const CorrelationTool = forwardRef<CorrelationToolHandle>(function CorrelationTool(_props, ref) {
  const [x, setX] = useState("");
  const [y, setY] = useState("");
  const [method, setMethod] = useState<"pearson" | "spearman">("pearson");
  const mutation = useRunCorrelationTest();

  useImperativeHandle(ref, () => ({ setMethod }));

  function handleRun() {
    const xValues = parseNumberList(x);
    const yValues = parseNumberList(y);
    if (xValues.length < 3 || xValues.length !== yValues.length) return;
    mutation.mutate({ x: xValues, y: yValues, method });
  }

  const result = mutation.data;
  const xValues = parseNumberList(x);
  const yValues = parseNumberList(y);
  const canRun = xValues.length >= 3 && xValues.length === yValues.length;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Correlation</p>
        <div className="flex flex-col gap-1">
          <Label htmlFor="corr-method">Method</Label>
          <Select id="corr-method" value={method} onChange={(e) => setMethod(e.target.value as "pearson" | "spearman")}>
            <option value="pearson">Pearson</option>
            <option value="spearman">Spearman</option>
          </Select>
        </div>
        <NumberListInput label="X values" value={x} onChange={setX} />
        <NumberListInput label="Y values" value={y} onChange={setY} />
        {xValues.length !== yValues.length ? (
          <p className="text-xs text-destructive">X and Y must have the same number of values.</p>
        ) : null}
        <Button onClick={handleRun} disabled={!canRun || mutation.isPending}>
          {mutation.isPending ? "Computing…" : "Compute Correlation"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Failed to compute correlation."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <p className="text-sm font-semibold text-foreground">{result.test_name}</p>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Coefficient (r)</dt>
              <dd className="font-medium tabular-nums text-foreground">
                {result.statistic !== null ? result.statistic.toFixed(4) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">p-value</dt>
              <dd className="font-medium tabular-nums text-foreground">
                {result.p_value !== null ? result.p_value.toFixed(4) : "—"}
              </dd>
            </div>
          </dl>
          <p className="text-sm text-foreground">{result.interpretation}</p>
          <p className="rounded-md bg-warning/10 px-3 py-2 text-xs text-foreground">
            Correlation does not imply causation.
          </p>
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Paste at least 3 paired X/Y values and click Compute.
        </div>
      )}
    </div>
  );
});
