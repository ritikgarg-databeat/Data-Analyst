"use client";

import { useState } from "react";

import { ABTestAnalyzer } from "./ab-test-analyzer";
import { PowerSimulator } from "./power-simulator";
import { SampleSizeTool } from "./sample-size-tool";

type Tab = "sample-size" | "analyzer" | "simulator";

const TABS: { key: Tab; label: string }[] = [
  { key: "sample-size", label: "Sample Size Calculator" },
  { key: "analyzer", label: "A/B Test Analyzer" },
  { key: "simulator", label: "Power Simulator" },
];

export function ExperimentsWorkspace() {
  const [tab, setTab] = useState<Tab>("sample-size");

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
        {tab === "sample-size" ? <SampleSizeTool /> : null}
        {tab === "analyzer" ? <ABTestAnalyzer /> : null}
        {tab === "simulator" ? <PowerSimulator /> : null}
      </div>
    </div>
  );
}
