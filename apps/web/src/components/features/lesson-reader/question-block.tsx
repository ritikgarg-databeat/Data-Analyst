"use client";

import { useState } from "react";
import { CheckCircle2, HelpCircle, XCircle } from "lucide-react";
import type { QuestionBlock } from "@data-analyst-lab/shared";

import { cn } from "@/lib/utils";

/**
 * Inline knowledge-check question. Graded entirely client-side against
 * `correct_index` — this is NOT a graded Exercise and never touches the API.
 */
export function QuestionBlockView({ block }: { block: QuestionBlock }) {
  const [selected, setSelected] = useState<number | null>(null);
  const answered = selected !== null;
  const isCorrect = answered && selected === block.correct_index;

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-4">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        <HelpCircle className="size-3.5" aria-hidden="true" />
        Knowledge Check
      </div>
      <p className="mb-3 text-sm font-medium text-foreground">{block.prompt}</p>
      <div role="radiogroup" aria-label={block.prompt} className="space-y-2">
        {block.choices.map((choice, index) => {
          const isSelected = selected === index;
          const isRightAnswer = index === block.correct_index;
          return (
            <button
              key={index}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={answered}
              onClick={() => setSelected(index)}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                !answered && "border-border hover:border-primary/50 hover:bg-accent/40",
                answered && isRightAnswer && "border-success bg-success/10",
                answered && isSelected && !isRightAnswer && "border-destructive bg-destructive/10",
                answered && !isSelected && !isRightAnswer && "border-border opacity-60",
              )}
            >
              {answered && isRightAnswer ? (
                <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
              ) : answered && isSelected ? (
                <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
              ) : (
                <span className="size-4 shrink-0 rounded-full border border-muted-foreground" aria-hidden="true" />
              )}
              <span className="text-foreground">{choice}</span>
            </button>
          );
        })}
      </div>
      {answered ? (
        <div
          role="status"
          className={cn(
            "mt-3 rounded-lg border px-3 py-2.5 text-sm",
            isCorrect ? "border-success/30 bg-success/5 text-foreground" : "border-destructive/30 bg-destructive/5 text-foreground",
          )}
        >
          <p className="font-semibold">{isCorrect ? "Correct!" : "Not quite."}</p>
          <p className="mt-1 text-muted-foreground">{block.explanation}</p>
        </div>
      ) : null}
    </div>
  );
}
