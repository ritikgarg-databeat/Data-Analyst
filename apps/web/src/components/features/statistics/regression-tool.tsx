"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NumberListInput, parseNumberList } from "@/components/shared/number-list-input";
import { useRunRegression } from "@/features/statistics/use-statistics";

export function RegressionTool() {
  const [x1, setX1] = useState("");
  const [x1Name, setX1Name] = useState("x1");
  const [x2, setX2] = useState("");
  const [x2Name, setX2Name] = useState("x2");
  const [y, setY] = useState("");
  const [yName, setYName] = useState("y");
  const mutation = useRunRegression();

  const x1Values = parseNumberList(x1);
  const x2Values = parseNumberList(x2);
  const yValues = parseNumberList(y);
  const usingX2 = x2Values.length > 0;
  const canRun = x1Values.length >= 3 && x1Values.length === yValues.length && (!usingX2 || x2Values.length === yValues.length);

  function handleRun() {
    if (!canRun) return;
    const features: Record<string, number[]> = { [x1Name || "x1"]: x1Values };
    if (usingX2) features[x2Name || "x2"] = x2Values;
    mutation.mutate({ features, y: yValues, y_name: yName || "y" });
  }

  const result = mutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Regression</p>
        <p className="text-xs text-muted-foreground">
          Add a second predictor to run a multiple regression, or leave it blank for simple linear regression.
        </p>
        <div className="grid grid-cols-[1fr_5rem] gap-2">
          <NumberListInput label="Predictor 1 (x1)" value={x1} onChange={setX1} />
          <div className="flex flex-col gap-1">
            <Label htmlFor="x1-name">Name</Label>
            <Input id="x1-name" value={x1Name} onChange={(e) => setX1Name(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-[1fr_5rem] gap-2">
          <NumberListInput label="Predictor 2 (x2, optional)" value={x2} onChange={setX2} />
          <div className="flex flex-col gap-1">
            <Label htmlFor="x2-name">Name</Label>
            <Input id="x2-name" value={x2Name} onChange={(e) => setX2Name(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-[1fr_5rem] gap-2">
          <NumberListInput label="Outcome (y)" value={y} onChange={setY} />
          <div className="flex flex-col gap-1">
            <Label htmlFor="y-name">Name</Label>
            <Input id="y-name" value={yName} onChange={(e) => setYName(e.target.value)} />
          </div>
        </div>
        <Button onClick={handleRun} disabled={!canRun || mutation.isPending}>
          {mutation.isPending ? "Fitting…" : "Fit Regression"}
        </Button>
        {mutation.isError ? (
          <p role="alert" className="text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : "Failed to fit regression."}
          </p>
        ) : null}
      </div>

      {result ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <p className="text-sm font-semibold text-foreground">{result.formula_description}</p>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-muted-foreground">R²</dt>
              <dd className="font-medium tabular-nums text-foreground">{result.r_squared.toFixed(4)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Adjusted R²</dt>
              <dd className="font-medium tabular-nums text-foreground">{result.adjusted_r_squared.toFixed(4)}</dd>
            </div>
          </dl>
          <div className="overflow-x-auto rounded-md border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-2 py-1.5 text-left">Term</th>
                  <th className="px-2 py-1.5 text-right">Coef</th>
                  <th className="px-2 py-1.5 text-right">p-value</th>
                  <th className="px-2 py-1.5 text-right">Sig.</th>
                </tr>
              </thead>
              <tbody>
                {[result.intercept, ...result.coefficients].map((c) => (
                  <tr key={c.name} className="border-b border-border last:border-0">
                    <td className="px-2 py-1.5 font-mono">{c.name}</td>
                    <td className="px-2 py-1.5 text-right tabular-nums">{c.value.toFixed(4)}</td>
                    <td className="px-2 py-1.5 text-right tabular-nums">{c.p_value.toFixed(4)}</td>
                    <td className="px-2 py-1.5 text-right">{c.significant ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-sm text-foreground">{result.interpretation}</p>
          {result.multicollinearity_warning ? (
            <p className="rounded-md bg-warning/10 px-3 py-2 text-xs text-foreground">
              {result.multicollinearity_warning}
            </p>
          ) : null}
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
          Paste at least 3 rows and click Fit Regression.
        </div>
      )}
    </div>
  );
}
