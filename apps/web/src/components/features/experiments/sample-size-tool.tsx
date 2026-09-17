"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useComputeSampleSize } from "@/features/experiments/use-experiments";

/** The Sample Size Calculator (spec section 19). */
export function SampleSizeTool() {
  const [baseline, setBaseline] = useState(0.1);
  const [uplift, setUplift] = useState(0.2);
  const [alpha, setAlpha] = useState(0.05);
  const [power, setPower] = useState(0.8);
  const mutation = useComputeSampleSize();

  function handleCompute() {
    mutation.mutate({ baseline_conversion: baseline, expected_uplift_relative: uplift, alpha, power });
  }

  const result = mutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Sample Size Calculator</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <Label htmlFor="ss-baseline">Baseline conversion</Label>
            <Input
              id="ss-baseline"
              type="number"
              step={0.01}
              min={0.001}
              max={0.999}
              value={baseline}
              onChange={(e) => setBaseline(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="ss-uplift">Expected relative uplift</Label>
            <Input
              id="ss-uplift"
              type="number"
              step={0.01}
              value={uplift}
              onChange={(e) => setUplift(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="ss-alpha">Alpha</Label>
            <Input
              id="ss-alpha"
              type="number"
              step={0.01}
              min={0.001}
              max={0.5}
              value={alpha}
              onChange={(e) => setAlpha(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="ss-power">Power</Label>
            <Input
              id="ss-power"
              type="number"
              step={0.01}
              min={0.5}
              max={0.99}
              value={power}
              onChange={(e) => setPower(Number(e.target.value))}
            />
          </div>
        </div>
        <Button onClick={handleCompute} disabled={mutation.isPending}>
          {mutation.isPending ? "Computing…" : "Calculate Sample Size"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Failed to calculate sample size."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Recommended sample size</p>
          <p className="text-3xl font-semibold text-foreground">
            {result.sample_size_per_variant.toLocaleString()} <span className="text-base font-normal text-muted-foreground">per variant</span>
          </p>
          <p className="text-sm text-muted-foreground">
            {result.total_sample_size.toLocaleString()} total across both variants — detecting an absolute effect of{" "}
            {(result.absolute_mde * 100).toFixed(2)} points ({(result.baseline_conversion * 100).toFixed(1)}% →{" "}
            {((result.baseline_conversion * (1 + result.expected_uplift)) * 100).toFixed(1)}%).
          </p>
          <p className="text-xs text-muted-foreground">{result.assumptions}</p>
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Fill in the inputs and click Calculate.
        </div>
      )}
    </div>
  );
}
