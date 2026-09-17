"use client";

import { useMemo, useState } from "react";
import { Wand2 } from "lucide-react";
import type { StatTestType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";

type Comparison =
  | "one_sample"
  | "two_independent"
  | "paired"
  | "two_proportions"
  | "more_than_two_groups"
  | "two_categorical"
  | "two_numeric";

const COMPARISON_OPTIONS: { value: Comparison; label: string }[] = [
  { value: "one_sample", label: "One sample vs. a known/target value" },
  { value: "two_independent", label: "Two independent groups" },
  { value: "paired", label: "Two paired/matched samples (before vs. after)" },
  { value: "two_proportions", label: "Two proportions (e.g. conversion rates)" },
  { value: "more_than_two_groups", label: "More than two groups" },
  { value: "two_categorical", label: "Two categorical variables (independence)" },
  { value: "two_numeric", label: "Two numeric variables (association)" },
];

type Suggestion =
  | { kind: "test"; testType: StatTestType; testName: string; reason: string }
  | { kind: "correlation"; method: "pearson" | "spearman"; testName: string; reason: string };

interface TestSelectionAssistantProps {
  onUseTest: (testType: StatTestType) => void;
  onUseCorrelation: (method: "pearson" | "spearman") => void;
}

/** A deterministic, educational decision-tree helper (spec section 12) — NOT a substitute
 * for real statistical judgment, and it says so. Purely client-side logic, no backend call. */
export function TestSelectionAssistant({ onUseTest, onUseCorrelation }: TestSelectionAssistantProps) {
  const [comparison, setComparison] = useState<Comparison | "">("");
  const [normal, setNormal] = useState<"yes" | "no" | "unsure" | "">("");

  const needsNormalityQuestion = comparison === "two_independent" || comparison === "two_numeric";

  const suggestion: Suggestion | null = useMemo(() => {
    if (!comparison) return null;
    switch (comparison) {
      case "one_sample":
        return {
          kind: "test",
          testType: "one_sample_t",
          testName: "One-sample t-test",
          reason: "You're comparing a single sample's mean against one known or target value.",
        };
      case "paired":
        return {
          kind: "test",
          testType: "paired_t",
          testName: "Paired t-test",
          reason: "The same subjects were measured twice (e.g. before/after) — a paired test uses the within-subject differences, which is more powerful than treating the two sets as independent.",
        };
      case "two_proportions":
        return {
          kind: "test",
          testType: "two_proportion_z",
          testName: "Two-proportion z-test",
          reason: "You're comparing conversion-style rates between two independent groups — the standard choice for A/B test analysis.",
        };
      case "more_than_two_groups":
        return {
          kind: "test",
          testType: "anova",
          testName: "One-way ANOVA",
          reason: "You have more than two groups to compare on a continuous outcome — ANOVA tests whether at least one group differs (a significant result still needs a post-hoc test to say which).",
        };
      case "two_categorical":
        return {
          kind: "test",
          testType: "chi_square",
          testName: "Chi-square test of independence",
          reason: "You're checking whether two categorical variables are associated — chi-square compares observed vs. expected counts in a contingency table.",
        };
      case "two_numeric":
        if (normal === "") return null;
        return normal === "no"
          ? {
              kind: "correlation",
              method: "spearman",
              testName: "Spearman rank correlation",
              reason: "The relationship isn't clearly linear/normal, so a rank-based (non-parametric) correlation is safer than Pearson.",
            }
          : {
              kind: "correlation",
              method: "pearson",
              testName: "Pearson correlation",
              reason: "Both variables are roughly normal with a plausibly linear relationship — Pearson measures linear association directly.",
            };
      case "two_independent":
        if (normal === "") return null;
        return normal === "no"
          ? {
              kind: "test",
              testType: "mann_whitney",
              testName: "Mann-Whitney U test",
              reason: "The data isn't clearly normal (or has outliers/is ordinal) — Mann-Whitney compares distributions using ranks instead of means, so it doesn't need a normality assumption.",
            }
          : {
              kind: "test",
              testType: "independent_t",
              testName: "Independent two-sample t-test (Welch's)",
              reason: "Two independent groups, roughly normal — Welch's t-test compares their means without assuming equal variances.",
            };
      default:
        return null;
    }
  }, [comparison, normal]);

  function reset() {
    setComparison("");
    setNormal("");
  }

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-1.5">
        <Wand2 className="size-4 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm font-semibold text-foreground">Test Selection Assistant</p>
      </div>
      <p className="text-xs text-muted-foreground">
        An educational guide, not a substitute for statistical judgment — always sanity-check assumptions
        against your actual data.
      </p>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-muted-foreground">What are you comparing?</label>
        <div className="flex flex-wrap gap-1.5">
          {COMPARISON_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => {
                setComparison(opt.value);
                setNormal("");
              }}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                comparison === opt.value
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border text-muted-foreground hover:bg-accent/60 hover:text-foreground"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {needsNormalityQuestion ? (
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">
            {comparison === "two_numeric"
              ? "Is the relationship roughly linear, with both variables roughly normal?"
              : "Is each group's data roughly normally distributed (no major outliers/skew)?"}
          </label>
          <div className="flex gap-1.5">
            {(["yes", "no", "unsure"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setNormal(v)}
                className={`rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors ${
                  normal === v
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {suggestion ? (
        <div className="rounded-lg bg-accent/40 p-3">
          <p className="text-sm text-foreground">
            Suggested: <strong>{suggestion.testName}</strong>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{suggestion.reason}</p>
          <Button
            size="sm"
            variant="outline"
            className="mt-2"
            onClick={() => (suggestion.kind === "test" ? onUseTest(suggestion.testType) : onUseCorrelation(suggestion.method))}
          >
            Use this test
          </Button>
        </div>
      ) : null}

      {comparison ? (
        <Button variant="ghost" size="sm" className="self-start" onClick={reset}>
          Start over
        </Button>
      ) : null}
    </div>
  );
}
