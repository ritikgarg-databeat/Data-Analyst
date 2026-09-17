"use client";

import Link from "next/link";
import { Code2, Microscope, Terminal } from "lucide-react";
import type { Case, CaseAttempt } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Section } from "@/components/shared/section";
import { FindingsPanel } from "@/components/features/findings/findings-panel";
import { HypothesisTracker } from "@/components/features/findings/hypothesis-tracker";
import { labDeepLinks } from "@/features/case-studies/utils";

/** Analyze (spec sections 15-17) — the shared Findings + Hypothesis Tracker,
 * plus deep links into the real analysis tools for whichever dataset(s) the
 * learner selected in the sidebar. */
export function CaseAnalyzeTab({ caseData, attempt }: { caseData: Case; attempt: CaseAttempt }) {
  const datasetSlug = attempt.selected_dataset_slugs[0] ?? caseData.available_datasets[0];
  const links = datasetSlug ? labDeepLinks(datasetSlug) : null;

  return (
    <div className="flex flex-col gap-6">
      <Section
        title="Analysis Tools"
        description="Open a tool in a new tab — your work there is saved independently; bring the results back here as evidence."
      >
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={links?.sql ?? "/sql-lab"} target="_blank" rel="noopener noreferrer">
              <Terminal className="size-4" aria-hidden="true" />
              SQL Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={links?.python ?? "/python-lab"} target="_blank" rel="noopener noreferrer">
              <Code2 className="size-4" aria-hidden="true" />
              Python Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={links?.eda ?? "/eda"} target="_blank" rel="noopener noreferrer">
              <Microscope className="size-4" aria-hidden="true" />
              EDA Workspace
            </Link>
          </Button>
        </div>
      </Section>

      <Section title="Findings" description="Observation, evidence, impact, and confidence — link evidence back to a real query, chart, or stat.">
        <FindingsPanel owner={{ caseAttemptId: attempt.id }} />
      </Section>

      <Section title="Hypothesis Tracker">
        <HypothesisTracker owner={{ caseAttemptId: attempt.id }} />
      </Section>
    </div>
  );
}
