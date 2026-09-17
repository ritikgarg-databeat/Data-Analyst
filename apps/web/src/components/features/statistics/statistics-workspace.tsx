"use client";

import { useRef, useState } from "react";

import { CorrelationTool, type CorrelationToolHandle } from "./correlation-tool";
import { HypothesisTestTool } from "./hypothesis-test-tool";
import { RegressionTool } from "./regression-tool";
import { SummaryStatsTool } from "./summary-stats-tool";

type Tab = "summary" | "test" | "correlation" | "regression";

const TABS: { key: Tab; label: string }[] = [
  { key: "summary", label: "Summary Stats" },
  { key: "test", label: "Hypothesis Test" },
  { key: "correlation", label: "Correlation" },
  { key: "regression", label: "Regression" },
];

export function StatisticsWorkspace() {
  const [tab, setTab] = useState<Tab>("summary");
  const correlationRef = useRef<CorrelationToolHandle>(null);

  function jumpToCorrelation(method: "pearson" | "spearman") {
    setTab("correlation");
    // The ref target only exists once this tab actually mounts.
    requestAnimationFrame(() => correlationRef.current?.setMethod(method));
  }

  return (
    <div className="flex flex-col gap-4">
      <div role="tablist" className="flex flex-wrap gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "summary" ? <SummaryStatsTool /> : null}
        {tab === "test" ? <HypothesisTestTool onJumpToCorrelation={jumpToCorrelation} /> : null}
        {tab === "correlation" ? <CorrelationTool ref={correlationRef} /> : null}
        {tab === "regression" ? <RegressionTool /> : null}
      </div>
    </div>
  );
}
