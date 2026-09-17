"use client";

import { useState } from "react";
import type { StatTestRequest, StatTestType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NumberListInput, parseNumberList } from "@/components/shared/number-list-input";
import { Select } from "@/components/ui/select";
import { useRunStatTest } from "@/features/statistics/use-statistics";

import { TestSelectionAssistant } from "./test-selection-assistant";

const TEST_LABELS: Record<StatTestType, string> = {
  one_sample_t: "One-sample t-test",
  independent_t: "Independent two-sample t-test",
  paired_t: "Paired t-test",
  two_proportion_z: "Two-proportion z-test",
  chi_square: "Chi-square test of independence",
  mann_whitney: "Mann-Whitney U test",
  anova: "One-way ANOVA",
};

const NEEDS_TWO_SAMPLES = new Set<StatTestType>(["independent_t", "paired_t", "mann_whitney"]);

interface HypothesisTestToolProps {
  onJumpToCorrelation: (method: "pearson" | "spearman") => void;
}

export function HypothesisTestTool({ onJumpToCorrelation }: HypothesisTestToolProps) {
  const [testType, setTestType] = useState<StatTestType>("independent_t");
  const [alpha, setAlpha] = useState(0.05);
  const [sampleA, setSampleA] = useState("");
  const [sampleB, setSampleB] = useState("");
  const [populationMean, setPopulationMean] = useState("");
  const [successesA, setSuccessesA] = useState("");
  const [nA, setNA] = useState("");
  const [successesB, setSuccessesB] = useState("");
  const [nB, setNB] = useState("");
  const [contingencyRaw, setContingencyRaw] = useState("30,10\n20,40");
  const [groupsRaw, setGroupsRaw] = useState("");

  const mutation = useRunStatTest();

  function handleRun() {
    const payload: StatTestRequest = { test_type: testType, alpha };
    if (testType === "one_sample_t") {
      payload.sample_a = parseNumberList(sampleA);
      payload.population_mean = Number(populationMean);
    } else if (NEEDS_TWO_SAMPLES.has(testType)) {
      payload.sample_a = parseNumberList(sampleA);
      payload.sample_b = parseNumberList(sampleB);
    } else if (testType === "two_proportion_z") {
      payload.successes_a = Number(successesA);
      payload.n_a = Number(nA);
      payload.successes_b = Number(successesB);
      payload.n_b = Number(nB);
    } else if (testType === "chi_square") {
      payload.contingency_table = contingencyRaw
        .trim()
        .split("\n")
        .map((row) => parseNumberList(row));
    } else if (testType === "anova") {
      payload.groups = groupsRaw
        .trim()
        .split("\n")
        .map((row) => parseNumberList(row))
        .filter((g) => g.length > 0);
    }
    mutation.mutate(payload);
  }

  const result = mutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[18rem_1fr]">
      <TestSelectionAssistant onUseTest={setTestType} onUseCorrelation={onJumpToCorrelation} />

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1">
              <Label htmlFor="test-type">Test</Label>
              <Select id="test-type" value={testType} onChange={(e) => setTestType(e.target.value as StatTestType)}>
                {Object.entries(TEST_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="alpha">Alpha</Label>
              <Input
                id="alpha"
                type="number"
                step={0.01}
                min={0.001}
                max={0.5}
                value={alpha}
                onChange={(e) => setAlpha(Number(e.target.value))}
                className="w-24"
              />
            </div>
          </div>

          {testType === "one_sample_t" ? (
            <>
              <NumberListInput label="Sample" value={sampleA} onChange={setSampleA} />
              <div className="flex flex-col gap-1">
                <Label htmlFor="pop-mean">Population / target mean</Label>
                <Input
                  id="pop-mean"
                  type="number"
                  value={populationMean}
                  onChange={(e) => setPopulationMean(e.target.value)}
                  className="w-40"
                />
              </div>
            </>
          ) : null}

          {NEEDS_TWO_SAMPLES.has(testType) ? (
            <>
              <NumberListInput label="Sample A" value={sampleA} onChange={setSampleA} />
              <NumberListInput label="Sample B" value={sampleB} onChange={setSampleB} />
            </>
          ) : null}

          {testType === "two_proportion_z" ? (
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <Label>Group A successes</Label>
                <Input type="number" value={successesA} onChange={(e) => setSuccessesA(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1">
                <Label>Group A total (n)</Label>
                <Input type="number" value={nA} onChange={(e) => setNA(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1">
                <Label>Group B successes</Label>
                <Input type="number" value={successesB} onChange={(e) => setSuccessesB(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1">
                <Label>Group B total (n)</Label>
                <Input type="number" value={nB} onChange={(e) => setNB(e.target.value)} />
              </div>
            </div>
          ) : null}

          {testType === "chi_square" ? (
            <div className="flex flex-col gap-1">
              <Label>Contingency table (one row per line, comma-separated counts)</Label>
              <NumberListInput
                label=""
                value={contingencyRaw}
                onChange={setContingencyRaw}
                placeholder={"30,10\n20,40"}
              />
            </div>
          ) : null}

          {testType === "anova" ? (
            <div className="flex flex-col gap-1">
              <Label>Groups (one per line, comma-separated values)</Label>
              <NumberListInput label="" value={groupsRaw} onChange={setGroupsRaw} placeholder={"1,2,3\n4,5,6\n7,8,9"} />
            </div>
          ) : null}

          <Button onClick={handleRun} disabled={mutation.isPending} className="self-start">
            {mutation.isPending ? "Running…" : "Run Test"}
          </Button>
          {mutation.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {mutation.error instanceof Error ? mutation.error.message : "Test failed."}
            </p>
          ) : null}
        </div>

        {result ? (
          <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-foreground">{result.test_name}</p>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  result.reject_null ? "bg-success/15 text-success" : "bg-muted text-muted-foreground"
                }`}
              >
                {result.reject_null ? "Reject H₀" : "Fail to reject H₀"}
              </span>
            </div>
            <dl className="grid grid-cols-3 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Statistic</dt>
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
              {result.effect_size !== null ? (
                <div>
                  <dt className="text-xs text-muted-foreground">{result.effect_size_label}</dt>
                  <dd className="font-medium tabular-nums text-foreground">{result.effect_size.toFixed(3)}</dd>
                </div>
              ) : null}
            </dl>
            <p className="text-sm text-foreground">{result.interpretation}</p>
            <div>
              <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Assumptions</p>
              <ul className="list-inside list-disc text-xs text-muted-foreground">
                {result.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
