"use client";

import type { MetricDefinition } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</p>
      {children}
    </div>
  );
}

export function MetricDetailSheet({
  metric,
  onOpenChange,
}: {
  metric: MetricDefinition | null;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={Boolean(metric)} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:w-[28rem]">
        {metric ? (
          <>
            <SheetHeader>
              <SheetTitle>{metric.name}</SheetTitle>
              <Badge variant="outline" className="w-fit capitalize">
                {metric.category}
              </Badge>
            </SheetHeader>
            <div className="flex flex-col gap-4 overflow-y-auto px-4 pb-4">
              <Section title="Definition">
                <p className="text-sm text-foreground">{metric.definition}</p>
              </Section>
              {metric.formula ? (
                <Section title="Formula">
                  <p className="rounded-md bg-muted/50 px-3 py-2 font-mono text-xs text-foreground">{metric.formula}</p>
                </Section>
              ) : null}
              {metric.examples.length > 0 ? (
                <Section title="Examples">
                  <ul className="list-inside list-disc text-sm text-foreground">
                    {metric.examples.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </Section>
              ) : null}
              {metric.sql_example ? (
                <Section title="SQL">
                  <pre className="overflow-x-auto rounded-md bg-muted/50 px-3 py-2 text-xs">
                    <code>{metric.sql_example}</code>
                  </pre>
                </Section>
              ) : null}
              {metric.python_example ? (
                <Section title="Python">
                  <pre className="overflow-x-auto rounded-md bg-muted/50 px-3 py-2 text-xs">
                    <code>{metric.python_example}</code>
                  </pre>
                </Section>
              ) : null}
              {metric.common_mistakes.length > 0 ? (
                <Section title="Common mistakes">
                  <ul className="list-inside list-disc text-sm text-muted-foreground">
                    {metric.common_mistakes.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </Section>
              ) : null}
              {metric.business_questions.length > 0 ? (
                <Section title="Business questions this answers">
                  <ul className="list-inside list-disc text-sm text-muted-foreground">
                    {metric.business_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </Section>
              ) : null}
              {metric.related_metrics.length > 0 ? (
                <Section title="Related metrics">
                  <div className="flex flex-wrap gap-1">
                    {metric.related_metrics.map((slug) => (
                      <Badge key={slug} variant="secondary">
                        {slug}
                      </Badge>
                    ))}
                  </div>
                </Section>
              ) : null}
              {metric.interview_questions.length > 0 ? (
                <Section title="Interview questions">
                  <ul className="flex flex-col gap-2 text-sm">
                    {metric.interview_questions.map((qa, i) => (
                      <li key={i} className="rounded-md border border-border p-2">
                        <p className="font-medium text-foreground">Q: {qa.question}</p>
                        <p className="mt-1 text-muted-foreground">A: {qa.answer}</p>
                      </li>
                    ))}
                  </ul>
                </Section>
              ) : null}
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
