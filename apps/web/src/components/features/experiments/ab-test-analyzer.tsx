"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAnalyzeABTest } from "@/features/experiments/use-experiments";

const VERDICT_STYLE: Record<string, string> = {
  "Ship-worthy evidence": "bg-success/15 text-success",
  "Statistically significant but too small to matter": "bg-warning/15 text-warning",
  "Practically meaningful but not statistically confirmed": "bg-warning/15 text-warning",
  Inconclusive: "bg-muted text-muted-foreground",
};

/** The A/B Test Analyzer (spec section 21) — never reduces the decision to "p < 0.05 = ship". */
export function ABTestAnalyzer() {
  const [controlUsers, setControlUsers] = useState(10000);
  const [controlConversions, setControlConversions] = useState(1000);
  const [treatmentUsers, setTreatmentUsers] = useState(10000);
  const [treatmentConversions, setTreatmentConversions] = useState(1080);
  const [alpha, setAlpha] = useState(0.05);
  const [minEffect, setMinEffect] = useState("");
  const mutation = useAnalyzeABTest();

  function handleAnalyze() {
    mutation.mutate({
      control_users: controlUsers,
      control_conversions: controlConversions,
      treatment_users: treatmentUsers,
      treatment_conversions: treatmentConversions,
      alpha,
      minimum_practical_effect: minEffect ? Number(minEffect) : undefined,
    });
  }

  const result = mutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">A/B Test Analyzer</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <Label>Control users</Label>
            <Input type="number" value={controlUsers} onChange={(e) => setControlUsers(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Control conversions</Label>
            <Input
              type="number"
              value={controlConversions}
              onChange={(e) => setControlConversions(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Treatment users</Label>
            <Input type="number" value={treatmentUsers} onChange={(e) => setTreatmentUsers(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Treatment conversions</Label>
            <Input
              type="number"
              value={treatmentConversions}
              onChange={(e) => setTreatmentConversions(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Alpha</Label>
            <Input type="number" step={0.01} value={alpha} onChange={(e) => setAlpha(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Min. practical effect (optional)</Label>
            <Input
              type="number"
              step={0.001}
              placeholder="e.g. 0.01"
              value={minEffect}
              onChange={(e) => setMinEffect(e.target.value)}
            />
          </div>
        </div>
        <Button onClick={handleAnalyze} disabled={mutation.isPending}>
          {mutation.isPending ? "Analyzing…" : "Analyze"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Failed to analyze."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground">Result</p>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${VERDICT_STYLE[result.verdict] ?? "bg-muted"}`}>
              {result.verdict}
            </span>
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">Control rate</dt>
              <dd className="font-medium tabular-nums text-foreground">{(result.control_rate * 100).toFixed(2)}%</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Treatment rate</dt>
              <dd className="font-medium tabular-nums text-foreground">{(result.treatment_rate * 100).toFixed(2)}%</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Relative uplift</dt>
              <dd className="font-medium tabular-nums text-foreground">
                {result.relative_uplift !== null ? `${(result.relative_uplift * 100).toFixed(1)}%` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">p-value</dt>
              <dd className="font-medium tabular-nums text-foreground">
                {result.p_value !== null ? result.p_value.toFixed(4) : "—"}
              </dd>
            </div>
            <div className="col-span-2">
              <dt className="text-xs text-muted-foreground">95% CI for the difference</dt>
              <dd className="font-medium tabular-nums text-foreground">
                [{(result.confidence_interval_95[0] * 100).toFixed(2)}%, {(result.confidence_interval_95[1] * 100).toFixed(2)}%]
              </dd>
            </div>
          </dl>
          <p className="text-sm text-foreground">{result.interpretation}</p>
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Fill in the inputs and click Analyze.
        </div>
      )}
    </div>
  );
}
