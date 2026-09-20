"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, Code2, Lightbulb, Microscope, Terminal } from "lucide-react";
import type { Case, CaseAttempt, CaseStage } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CASE_STAGE_LABELS } from "@/features/case-studies/constants";
import {
  useRecordStageTime,
  useRevealHint,
  useSaveDatasetSelection,
  useUpdateCaseStage,
} from "@/features/case-studies/use-case-studies";
import { labDeepLinks, titleizeSlug } from "@/features/case-studies/utils";
import { cn } from "@/lib/utils";

/**
 * The CASE sidebar (spec section 13) — Context/Objective/Data/Deliverables/
 * Progress, plus hints. This is a reference panel: the actual editable work
 * (clarification, framing, findings, recommendation, executive summary)
 * lives in the WORKSPACE main area's tabs, not duplicated here.
 */
export function CaseSidebar({ caseData, attempt }: { caseData: Case; attempt: CaseAttempt }) {
  const saveDatasets = useSaveDatasetSelection(attempt.id);
  const updateStage = useUpdateCaseStage(attempt.id);
  const recordStageTime = useRecordStageTime(attempt.id);
  const revealHint = useRevealHint(attempt.id);
  const [revealedHints, setRevealedHints] = useState<string[]>([]);
  const [hintError, setHintError] = useState<string | null>(null);

  // Tracks time spent on the current stage by recording elapsed seconds in
  // this effect's cleanup, which fires right before `current_stage` changes
  // (or on unmount) — an effect lifecycle boundary, not render, so the
  // Date.now() timestamps here are on the correct side of React's purity
  // rules (see the assessment page's handleStart/handleSubmit for the
  // equivalent event-handler-timing pattern used elsewhere in this app).
  useEffect(() => {
    const enteredAt = Date.now();
    const stage = attempt.current_stage;
    return () => {
      if (!stage) return;
      const seconds = Math.round((Date.now() - enteredAt) / 1000);
      if (seconds > 0) recordStageTime.mutate({ stage, seconds });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- recordStageTime is stable per attemptId; only current_stage should retrigger this.
  }, [attempt.current_stage]);

  function toggleDataset(slug: string, checked: boolean) {
    const next = checked
      ? [...attempt.selected_dataset_slugs, slug]
      : attempt.selected_dataset_slugs.filter((s) => s !== slug);
    saveDatasets.mutate(next);
  }

  function jumpToStage(stage: CaseStage) {
    updateStage.mutate(stage);
  }

  function handleHint() {
    setHintError(null);
    revealHint.mutate(undefined, {
      onSuccess: (result) => setRevealedHints((prev) => [...prev, result.hint]),
      onError: () => setHintError("No more hints available for this case."),
    });
  }

  return (
    <aside className="flex w-full flex-shrink-0 flex-col gap-4 text-sm lg:max-w-xs">
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Context</p>
        <p className="mt-1 font-medium text-foreground">
          {caseData.stakeholder_name}, {caseData.stakeholder_role}
        </p>
        <blockquote className="mt-1 border-l-2 border-primary/40 pl-3 text-xs text-muted-foreground italic">
          &ldquo;{caseData.problem_statement}&rdquo;
        </blockquote>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Objective</p>
        <p className="mt-1 text-foreground">{caseData.objective}</p>
      </div>

      {caseData.available_datasets.length > 0 ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Data</p>
          <ul className="mt-2 flex flex-col gap-2">
            {caseData.available_datasets.map((slug) => {
              const selected = attempt.selected_dataset_slugs.includes(slug);
              const links = labDeepLinks(slug);
              return (
                <li key={slug} className="flex flex-col gap-1">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      className="size-4"
                      checked={selected}
                      onChange={(event) => toggleDataset(slug, event.target.checked)}
                    />
                    <span className="text-foreground">{titleizeSlug(slug)}</span>
                  </label>
                  {selected ? (
                    <div className="flex flex-wrap gap-1 pl-6">
                      <Button variant="outline" size="sm" className="h-6 px-1.5 text-[11px]" asChild>
                        <Link href={links.sql} target="_blank" rel="noopener noreferrer">
                          <Terminal className="size-3" aria-hidden="true" />
                          SQL
                        </Link>
                      </Button>
                      <Button variant="outline" size="sm" className="h-6 px-1.5 text-[11px]" asChild>
                        <Link href={links.eda} target="_blank" rel="noopener noreferrer">
                          <Microscope className="size-3" aria-hidden="true" />
                          EDA
                        </Link>
                      </Button>
                      <Button variant="outline" size="sm" className="h-6 px-1.5 text-[11px]" asChild>
                        <Link href={links.python} target="_blank" rel="noopener noreferrer">
                          <Code2 className="size-3" aria-hidden="true" />
                          Python
                        </Link>
                      </Button>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {caseData.expected_deliverables.length > 0 ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Deliverables</p>
          <ul className="mt-2 flex flex-col gap-1 text-foreground">
            {caseData.expected_deliverables.map((deliverable, index) => (
              <li key={index} className="flex items-start gap-1.5">
                <span className="mt-0.5 text-muted-foreground">•</span>
                <span>{deliverable}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {caseData.stages.length > 0 ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Progress</p>
          <ul className="flex flex-col gap-1">
            {caseData.stages.map((stage) => {
              const active = attempt.current_stage === stage;
              return (
                <li key={stage}>
                  <button
                    type="button"
                    onClick={() => jumpToStage(stage)}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-md px-2 py-1 text-left transition-colors",
                      active ? "bg-primary/10 font-medium text-primary" : "text-muted-foreground hover:bg-accent",
                    )}
                  >
                    {active ? <Check className="size-3.5" aria-hidden="true" /> : <span className="size-3.5" />}
                    {CASE_STAGE_LABELS[stage]}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Hints</p>
          <Badge variant="outline">{attempt.hints_used}</Badge>
        </div>
        <Button variant="outline" size="sm" className="mt-2" onClick={handleHint} disabled={revealHint.isPending}>
          <Lightbulb className="size-4" aria-hidden="true" />
          Get a hint
        </Button>
        {hintError ? <p className="mt-1 text-xs text-destructive">{hintError}</p> : null}
        {revealedHints.length > 0 ? (
          <ul className="mt-2 flex flex-col gap-1.5">
            {revealedHints.map((hint, index) => (
              <li key={index} className="rounded-md bg-accent/40 p-2 text-xs text-foreground">
                {hint}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </aside>
  );
}
