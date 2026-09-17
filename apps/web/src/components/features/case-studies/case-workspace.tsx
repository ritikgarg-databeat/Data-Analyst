"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Bot } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { useCaseAttempt, useCases } from "@/features/case-studies/use-case-studies";
import { cn } from "@/lib/utils";

import { CaseAnalyzeTab } from "./case-analyze-tab";
import { CaseAskMentorPanel } from "./case-ask-mentor-panel";
import { CaseClarifyTab } from "./case-clarify-tab";
import { CaseFrameTab } from "./case-frame-tab";
import { CaseRecommendTab } from "./case-recommend-tab";
import { CaseSidebar } from "./case-sidebar";
import { CaseSubmitTab } from "./case-submit-tab";

type TabKey = "clarify" | "frame" | "analyze" | "recommend" | "submit";

const TABS: { key: TabKey; label: string }[] = [
  { key: "clarify", label: "Clarify" },
  { key: "frame", label: "Frame" },
  { key: "analyze", label: "Analyze" },
  { key: "recommend", label: "Recommend" },
  { key: "submit", label: "Communicate & Submit" },
];

const STATUS_VARIANT: Record<string, "outline" | "warning" | "success" | "secondary" | "default"> = {
  NOT_STARTED: "outline",
  IN_PROGRESS: "warning",
  PAUSED: "secondary",
  SUBMITTED: "default",
  UNDER_REVIEW: "warning",
  COMPLETED: "success",
};

/**
 * The Case Workspace (spec section 13) — a CASE sidebar (context, objective,
 * data, deliverables, progress, hints) plus a WORKSPACE main area organized
 * into tabs. There's no `GET /cases/by-id/{id}` endpoint, only by slug, so
 * the Case is resolved from the already-fetched, small `useCases()` catalog
 * by `case.id === attempt.case_id` rather than adding a new endpoint.
 */
export function CaseWorkspace({ attemptId }: { attemptId: string }) {
  const attemptQuery = useCaseAttempt(attemptId);
  const casesQuery = useCases();
  const [tab, setTab] = useState<TabKey>("clarify");
  const [mentorOpen, setMentorOpen] = useState(false);

  if (attemptQuery.isLoading || casesQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-96" />;
  }

  if (attemptQuery.isError || !attemptQuery.data) {
    return (
      <ErrorState
        title="Unable to load this case attempt"
        message="We couldn't reach the API, or this attempt doesn't exist."
        retry={() => void attemptQuery.refetch()}
      />
    );
  }

  const attempt = attemptQuery.data;
  const caseData = casesQuery.data?.find((item) => item.case.id === attempt.case_id)?.case;

  if (!caseData) {
    return (
      <ErrorState title="Unable to load this case" message="The case behind this attempt could not be found." />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title={caseData.title}
        subtitle={caseData.objective}
        action={
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_VARIANT[attempt.status]}>{attempt.status.replace(/_/g, " ")}</Badge>
            <Button variant="outline" size="sm" onClick={() => setMentorOpen(true)}>
              <Bot className="size-4" aria-hidden="true" />
              Ask Mentor
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/case-studies">
                <ArrowLeft className="size-4" aria-hidden="true" />
                All Cases
              </Link>
            </Button>
          </div>
        }
      />

      <CaseAskMentorPanel open={mentorOpen} onOpenChange={setMentorOpen} attemptId={attemptId} />

      <div className="flex flex-col gap-5 lg:flex-row">
        <CaseSidebar caseData={caseData} attempt={attempt} />

        <div className="flex min-w-0 flex-1 flex-col gap-4">
          <div className="flex flex-wrap gap-1.5 border-b border-border" role="tablist" aria-label="Case workspace sections">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={cn(
                  "rounded-t-md px-3 py-2 text-sm font-medium transition-colors",
                  tab === t.key
                    ? "border-b-2 border-primary text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div role="tabpanel">
            {tab === "clarify" ? <CaseClarifyTab attempt={attempt} /> : null}
            {tab === "frame" ? <CaseFrameTab attempt={attempt} /> : null}
            {tab === "analyze" ? <CaseAnalyzeTab caseData={caseData} attempt={attempt} /> : null}
            {tab === "recommend" ? <CaseRecommendTab attempt={attempt} /> : null}
            {tab === "submit" ? <CaseSubmitTab caseData={caseData} attempt={attempt} /> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
