"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import type { AIDebugResult, AIReviewResult, SqlErrorInfo } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { useDebugSql, useOptimizeSql, useReviewSql } from "@/features/ai/use-ai";

type Mode = "review" | "debug" | "optimize";

interface SqlAskAiPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  query: string;
  engine: string;
  database: string;
  error: SqlErrorInfo | null;
  executionTimeMs?: number;
  initialMode?: Mode;
}

/**
 * SQL AI Tutor / Review Query / SQL Debugging / SQL Optimization Coach (spec
 * sections 9-12) — one panel, three deterministic-authority-respecting
 * actions plus a free-text question, all sharing the query/schema/result
 * context. Never auto-replaces the user's query (section 9) — this panel has
 * no "apply" action, only explanation/review text.
 */
export function SqlAskAiPanel({
  open,
  onOpenChange,
  query,
  engine,
  database,
  error,
  executionTimeMs,
  initialMode,
}: SqlAskAiPanelProps) {
  const [mode, setMode] = useState<Mode>(initialMode ?? (error ? "debug" : "review"));
  const [question, setQuestion] = useState("");

  const review = useReviewSql();
  const debug = useDebugSql();
  const optimize = useOptimizeSql();

  const activeMutation = mode === "debug" ? debug : mode === "optimize" ? optimize : review;

  function handleAsk() {
    if (mode === "debug") {
      if (!error) return;
      debug.mutate({ query, error_message: error.message, engine, database });
    } else if (mode === "optimize") {
      optimize.mutate({ query, engine, database, execution_time_ms: executionTimeMs ?? null });
    } else {
      review.mutate({ query, question: question.trim() || null, engine, database });
    }
  }

  const response = activeMutation.data;
  const structuredReview = response?.structured as AIReviewResult | undefined;
  const structuredDebug = mode === "debug" ? (response?.structured as AIDebugResult | undefined) : undefined;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-xl flex-col gap-4 sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="size-5" aria-hidden="true" />
            Ask AI about this query
          </SheetTitle>
          <SheetDescription>
            This sends your query, its schema, and (if run) its result/error to the configured AI provider.
          </SheetDescription>
        </SheetHeader>

        <div role="tablist" className="flex gap-1 border-b border-border">
          {(["review", "debug", "optimize"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={mode === m}
              disabled={m === "debug" && !error}
              onClick={() => setMode(m)}
              className={
                mode === m
                  ? "border-b-2 border-primary px-3 py-2 text-sm font-medium text-foreground"
                  : "border-b-2 border-transparent px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
              }
            >
              {m === "review" ? "Review Query" : m === "debug" ? "Debug Error" : "Optimize"}
            </button>
          ))}
        </div>

        {mode === "review" ? (
          <Textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Optional: a specific question about this query..."
            rows={2}
          />
        ) : null}

        <Button onClick={handleAsk} disabled={activeMutation.isPending || (mode === "debug" && !error)}>
          {activeMutation.isPending ? "Thinking..." : `Ask AI to ${mode === "review" ? "review" : mode}`}
        </Button>

        {response ? (
          <div className="flex-1 overflow-y-auto rounded-md border border-border p-3 text-sm">
            {structuredDebug ? (
              <dl className="flex flex-col gap-3">
                {(
                  [
                    ["What happened", structuredDebug.what_happened],
                    ["Why it likely happened", structuredDebug.why_it_likely_happened],
                    ["Where", structuredDebug.where],
                    ["How to investigate", structuredDebug.how_to_investigate],
                    ["Suggested fix", structuredDebug.suggested_fix],
                  ] as const
                ).map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{label}</dt>
                    <dd className="mt-0.5 text-foreground">{value}</dd>
                  </div>
                ))}
              </dl>
            ) : structuredReview ? (
              <div className="flex flex-col gap-3">
                <p className="text-foreground">{structuredReview.summary}</p>
                {structuredReview.strengths.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Strengths</p>
                    <ul className="list-inside list-disc text-foreground">
                      {structuredReview.strengths.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {structuredReview.issues.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Issues</p>
                    <ul className="list-inside list-disc text-foreground">
                      {structuredReview.issues.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {structuredReview.suggestions.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Suggestions</p>
                    <ul className="list-inside list-disc text-foreground">
                      {structuredReview.suggestions.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="whitespace-pre-wrap text-foreground">{response.raw_text}</p>
            )}
            {response.provider === "local" ? (
              <p className="mt-3 border-t border-border pt-2 text-xs text-muted-foreground">
                No AI provider is configured — this is a local placeholder response.
              </p>
            ) : null}
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
