"use client";

import { useRouter } from "next/navigation";
import { Lightbulb } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { CASE_CATEGORY_LABELS, CASE_DIFFICULTY_LABELS } from "@/features/case-studies/constants";
import { useCaseBySlug, useStartCase } from "@/features/case-studies/use-case-studies";

/**
 * Case detail (pre-start) — every field here is intentionally what the
 * stakeholder would actually tell you before you started: the ambiguous
 * problem, the objective, constraints, and what's expected — never the
 * rubric's answer text, hints' text, or the reference solution (the API's
 * public `Case` shape never sends those at all — see app/schemas/case.py).
 */
export function CaseDetail({ slug }: { slug: string }) {
  const caseQuery = useCaseBySlug(slug);
  const startCase = useStartCase();
  const router = useRouter();

  if (caseQuery.isLoading) return <LoadingState count={1} itemClassName="h-96" />;
  if (caseQuery.isError || !caseQuery.data) {
    return (
      <ErrorState
        title="Unable to load this case"
        message="We couldn't reach the API, or this case doesn't exist."
        retry={() => void caseQuery.refetch()}
      />
    );
  }

  const c = caseQuery.data;

  function handleStart() {
    startCase.mutate(slug, {
      onSuccess: (attempt) => router.push(`/case-studies/attempts/${attempt.id}`),
    });
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-1.5">
          <Badge variant="outline">{CASE_CATEGORY_LABELS[c.category]}</Badge>
          <Badge variant="secondary">{CASE_DIFFICULTY_LABELS[c.difficulty]}</Badge>
          <span className="text-xs text-muted-foreground">{c.estimated_minutes} min</span>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{c.title}</h1>
        {c.company_context ? <p className="mt-2 text-sm text-muted-foreground">{c.company_context}</p> : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {c.stakeholder_name}, {c.stakeholder_role}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <blockquote className="border-l-2 border-primary/40 pl-4 text-sm text-foreground italic">
            &ldquo;{c.problem_statement}&rdquo;
          </blockquote>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Objective</CardTitle>
          </CardHeader>
          <CardContent className="text-sm whitespace-pre-line text-foreground">{c.objective}</CardContent>
        </Card>

        {c.business_context ? (
          <Card>
            <CardHeader>
              <CardTitle>Business Context</CardTitle>
            </CardHeader>
            <CardContent className="text-sm whitespace-pre-line text-foreground">{c.business_context}</CardContent>
          </Card>
        ) : null}

        {c.constraints.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Constraints</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-1.5 text-sm text-foreground">
                {c.constraints.map((constraint, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="mt-0.5 text-muted-foreground">•</span>
                    <span>{constraint}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ) : null}

        {c.expected_deliverables.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Expected Deliverables</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col gap-1.5 text-sm text-foreground">
                {c.expected_deliverables.map((deliverable, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="mt-0.5 text-muted-foreground">•</span>
                    <span>{deliverable}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Learning Objectives</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-1.5 text-sm text-foreground">
            {c.learning_objectives.map((objective, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="mt-0.5 text-muted-foreground">•</span>
                <span>{objective}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        {c.skills.map((skill) => (
          <Badge key={skill} variant="outline">
            {skill}
          </Badge>
        ))}
      </div>

      <div className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <Lightbulb className="size-4" aria-hidden="true" />
          {c.hint_count > 0 ? `${c.hint_count} hint${c.hint_count === 1 ? "" : "s"} available if you get stuck` : "No hints for this case"}
        </p>
        <Button onClick={handleStart} disabled={startCase.isPending}>
          {startCase.isPending ? "Starting..." : "Start Case"}
        </Button>
      </div>
      {startCase.isError ? <p className="text-xs text-destructive">Couldn&apos;t start this case. Try again.</p> : null}
    </div>
  );
}
