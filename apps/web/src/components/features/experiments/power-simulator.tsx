"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useSimulateABTest } from "@/features/experiments/use-experiments";

/** A deterministic-seed A/B test simulator (spec sections 20 & 24) — makes statistical
 * power intuitive by actually running many simulated experiments, not just a formula. */
export function PowerSimulator() {
  const [controlRate, setControlRate] = useState(0.1);
  const [treatmentRate, setTreatmentRate] = useState(0.12);
  const [sampleSize, setSampleSize] = useState(2000);
  const [numSimulations, setNumSimulations] = useState(500);
  const [seed, setSeed] = useState(42);
  const mutation = useSimulateABTest();

  function handleRun() {
    mutation.mutate({
      control_rate: controlRate,
      treatment_rate: treatmentRate,
      sample_size_per_variant: sampleSize,
      num_simulations: numSimulations,
      seed,
    });
  }

  const result = mutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Power Simulator</p>
        <p className="text-xs text-muted-foreground">
          Runs many simulated experiments under a fixed, known true effect, and reports what share actually came
          back statistically significant — a hands-on way to see why underpowered tests give inconsistent results.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <Label>True control rate</Label>
            <Input type="number" step={0.01} value={controlRate} onChange={(e) => setControlRate(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label>True treatment rate</Label>
            <Input
              type="number"
              step={0.01}
              value={treatmentRate}
              onChange={(e) => setTreatmentRate(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Sample size / variant</Label>
            <Input type="number" value={sampleSize} onChange={(e) => setSampleSize(Number(e.target.value))} />
          </div>
          <div className="flex flex-col gap-1">
            <Label># Simulations</Label>
            <Input
              type="number"
              min={1}
              max={5000}
              value={numSimulations}
              onChange={(e) => setNumSimulations(Number(e.target.value))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label>Seed</Label>
            <Input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
          </div>
        </div>
        <Button onClick={handleRun} disabled={mutation.isPending}>
          {mutation.isPending ? "Simulating…" : "Run Simulation"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Simulation failed."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Empirical power</p>
          <p className="text-3xl font-semibold text-foreground">{(result.empirical_power * 100).toFixed(0)}%</p>
          <Progress value={result.empirical_power * 100} />
          <p className="text-sm text-muted-foreground">
            {result.significant_count} of {result.num_simulations} simulated experiments were statistically
            significant at alpha={result.alpha}.
          </p>
          <p className="text-sm text-foreground">{result.interpretation}</p>
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Fill in the inputs and click Run Simulation.
        </div>
      )}
    </div>
  );
}
