"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import type { AIReviewResult, PythonErrorSchema } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { useReviewPython } from "@/features/ai/use-ai";

interface PythonAskAiPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  code: string;
  error: PythonErrorSchema | null;
}

/**
 * Python AI Tutor / Code Review (spec sections 13-14) — code + real
 * error/traceback (when present) as context, free-text question optional.
 * Never auto-replaces the cell's code (no "apply" action here).
 */
export function PythonAskAiPanel({ open, onOpenChange, code, error }: PythonAskAiPanelProps) {
  const [question, setQuestion] = useState("");
  const review = useReviewPython();

  function handleAsk() {
    review.mutate({
      code,
      question: question.trim() || null,
      error_type: error?.error_type ?? null,
      error_message: error?.message ?? null,
      traceback_text: error?.traceback_text ?? null,
    });
  }

  const response = review.data;
  const structured = response?.structured as AIReviewResult | undefined;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-xl flex-col gap-4 sm:max-w-xl">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="size-5" aria-hidden="true" />
            Ask AI about this code
          </SheetTitle>
          <SheetDescription>
            This sends your code{error ? " and its error/traceback" : ""} to the configured AI provider.
          </SheetDescription>
        </SheetHeader>

        {error ? (
          <p className="rounded-md border border-destructive/30 bg-destructive/5 p-2 text-xs text-destructive">
            Reviewing with the real error: {error.error_type} — {error.message}
          </p>
        ) : null}

        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Optional: a specific question about this code..."
          rows={3}
        />

        <Button onClick={handleAsk} disabled={review.isPending}>
          {review.isPending ? "Thinking..." : "Ask AI"}
        </Button>

        {response ? (
          <div className="flex-1 overflow-y-auto rounded-md border border-border p-3 text-sm">
            {structured ? (
              <div className="flex flex-col gap-3">
                <p className="text-foreground">{structured.summary}</p>
                {(["strengths", "issues", "suggestions"] as const).map((key) =>
                  structured[key].length > 0 ? (
                    <div key={key}>
                      <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{key}</p>
                      <ul className="list-inside list-disc text-foreground">
                        {structured[key].map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null,
                )}
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
