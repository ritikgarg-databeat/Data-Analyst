"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import type { AIEdaResult } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEdaAssist, useExploreWithAI } from "@/features/ai/use-ai";

const SECTIONS: { key: keyof AIEdaResult; label: string }[] = [
  { key: "observed_issues", label: "Observed issues (from this dataset's own profile)" },
  { key: "what_to_inspect", label: "What to inspect first" },
  { key: "important_variables", label: "Important variables" },
  { key: "suggested_visualizations", label: "Suggested visualizations" },
  { key: "suggested_investigations", label: "Suggested investigations (not yet verified)" },
  { key: "suggested_questions", label: "Questions to explore" },
  { key: "potential_hypotheses", label: "Potential hypotheses" },
];

/**
 * AI EDA Assistant / Explore with AI (spec sections 22-23) — grounds
 * suggestions in this workspace's own already-computed dataset profile
 * (never a claim of an already-verified finding; `observed_issues` is kept
 * separate from `suggested_investigations` the same way AIEdaResult itself
 * separates them, matching sql-ask-ai-panel.tsx's structured/raw_text
 * fallback and local-provider disclaimer conventions).
 */
export function EdaAssistPanel({ datasetId, tableName }: { datasetId: string; tableName?: string }) {
  const [goal, setGoal] = useState("");
  const [activeMode, setActiveMode] = useState<"assist" | "explore" | null>(null);
  const assist = useEdaAssist();
  const explore = useExploreWithAI();
  // Tracked explicitly (not derived from `.data`/`.isPending`) so the panel
  // always shows whichever action was clicked MOST RECENTLY — react-query
  // keeps a mutation's `data` cached indefinitely, so an "assist" result
  // would otherwise never be replaced by a later "explore" click.
  const activeMutation = activeMode === "explore" ? explore : assist;

  const response = activeMutation.data;
  const structured = response?.structured as AIEdaResult | undefined;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-foreground">
        <Sparkles className="size-4" aria-hidden="true" />
        Ask AI to help explore this dataset
      </p>
      <p className="mb-3 text-xs text-muted-foreground">
        Sends this dataset&apos;s real, already-computed profile (column types, null %, distributions,
        correlations, outliers) to the configured AI provider.
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setActiveMode("assist");
            assist.mutate({ dataset_id: datasetId, table_name: tableName });
          }}
          disabled={assist.isPending}
        >
          {assist.isPending ? "Thinking…" : "Assist with this profile"}
        </Button>
        <Input
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          placeholder='Optional goal, e.g. "find drivers of churn"'
          className="w-full sm:w-64"
        />
        <Button
          size="sm"
          onClick={() => {
            setActiveMode("explore");
            explore.mutate({ dataset_id: datasetId, table_name: tableName, user_goal: goal.trim() || undefined });
          }}
          disabled={explore.isPending}
        >
          {explore.isPending ? "Thinking…" : "Explore with AI"}
        </Button>
      </div>

      {activeMutation.isError ? (
        <p role="alert" className="mt-3 text-sm text-destructive">
          Couldn&apos;t reach the AI provider. Try again in a moment.
        </p>
      ) : null}

      {response ? (
        <div className="mt-4 flex flex-col gap-3 border-t border-border pt-3 text-sm">
          {structured ? (
            SECTIONS.map(({ key, label }) => {
              const items = structured[key] as string[];
              if (!items || items.length === 0) return null;
              return (
                <div key={key}>
                  <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{label}</p>
                  <ul className="mt-0.5 list-inside list-disc text-foreground">
                    {items.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              );
            })
          ) : (
            <p className="whitespace-pre-wrap text-foreground">{response.raw_text}</p>
          )}
          {response.provider === "local" ? (
            <p className="border-t border-border pt-2 text-xs text-muted-foreground">
              No AI provider is configured — this is a local placeholder response.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
