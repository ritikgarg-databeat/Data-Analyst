"use client";

import { Sparkles } from "lucide-react";
import type { AIDebriefResult } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useInterviewDebrief } from "@/features/ai/use-ai";

const SECTIONS: { key: keyof AIDebriefResult; label: string }[] = [
  { key: "strengths", label: "Strengths" },
  { key: "weaknesses", label: "Weaknesses" },
  { key: "missed_opportunities", label: "Missed Opportunities" },
  { key: "suggested_practice", label: "Suggested Practice" },
];

/**
 * AI Interview Debrief (spec sections 29, 60) — narrates the ALREADY-
 * COMPUTED deterministic score/per-question review; the real score above
 * this card remains authoritative (spec section 50), this is a
 * supplementary qualitative layer generated on request.
 */
export function AIInterviewDebrief({ interviewId }: { interviewId: string }) {
  const debrief = useInterviewDebrief(interviewId);
  const structured = debrief.data?.structured as AIDebriefResult | undefined;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4" aria-hidden="true" />
          AI Interview Debrief
        </CardTitle>
        <Button variant="outline" size="sm" onClick={() => debrief.mutate()} disabled={debrief.isPending}>
          {debrief.isPending ? "Generating..." : debrief.data ? "Regenerate" : "Generate Debrief"}
        </Button>
      </CardHeader>
      {debrief.data ? (
        <CardContent className="flex flex-col gap-4">
          {structured ? (
            SECTIONS.map((section) => {
              const items = structured[section.key] as string[];
              if (!items || items.length === 0) return null;
              return (
                <div key={section.key}>
                  <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{section.label}</p>
                  <ul className="mt-1 list-inside list-disc text-sm text-foreground">
                    {items.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              );
            })
          ) : (
            <p className="text-sm whitespace-pre-wrap text-foreground">{debrief.data.raw_text}</p>
          )}
          {debrief.data.provider === "local" ? (
            <p className="border-t border-border pt-2 text-xs text-muted-foreground">
              No AI provider is configured — this is a local placeholder response.
            </p>
          ) : null}
        </CardContent>
      ) : (
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Generate a qualitative debrief on top of your real score above — strengths, weaknesses, missed
            opportunities, and what to practice next.
          </p>
        </CardContent>
      )}
    </Card>
  );
}
