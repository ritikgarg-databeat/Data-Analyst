"use client";

import Link from "next/link";
import { BookMarked, FileText, MessagesSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useJobDescriptions } from "@/features/career/use-jobs";

export function InterviewPrepPage() {
  const jobDescriptionsQuery = useJobDescriptions();

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessagesSquare className="size-4 text-primary" aria-hidden="true" />
            Practice Interview Rounds
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="text-sm text-muted-foreground">
            Actual timed practice, mock interviews, and the question bank live in the main Interview section — this
            page is the career-specific view on top of it.
          </p>
          <Button variant="outline" className="self-start" asChild>
            <Link href="/interview">
              <MessagesSquare className="size-4" aria-hidden="true" />
              Go to Interview Prep
            </Link>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 text-primary" aria-hidden="true" />
            Job-Specific Interview Plans
          </CardTitle>
        </CardHeader>
        <CardContent>
          {jobDescriptionsQuery.isLoading ? (
            <LoadingState count={3} itemClassName="h-14" />
          ) : jobDescriptionsQuery.isError ? (
            <ErrorState message="We couldn't load your saved job descriptions." retry={() => void jobDescriptionsQuery.refetch()} />
          ) : (jobDescriptionsQuery.data ?? []).length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No saved job descriptions"
              description="Save a job description to get a focus-area interview plan tailored to it."
              action={{ label: "Add a Job Description", href: "/career/job-descriptions" }}
            />
          ) : (
            <ul className="flex flex-col gap-2">
              {(jobDescriptionsQuery.data ?? []).map((jd) => (
                <li key={jd.id} className="flex items-center justify-between gap-2 rounded-xl border border-border bg-card p-3 text-sm">
                  <div>
                    <p className="font-medium text-foreground">{jd.title}</p>
                    {jd.company ? <p className="text-xs text-muted-foreground">{jd.company}</p> : null}
                  </div>
                  <Button size="sm" variant="outline" asChild>
                    <Link href={`/career/job-descriptions/${jd.id}`}>View Interview Plan</Link>
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookMarked className="size-4 text-primary" aria-hidden="true" />
            Behavioral Stories
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="text-sm text-muted-foreground">
            Keep a bank of STAR-format stories ready for behavioral rounds, organized by the 12 real interview
            categories.
          </p>
          <Button variant="outline" className="self-start" asChild>
            <Link href="/career/behavioral-stories">
              <BookMarked className="size-4" aria-hidden="true" />
              Open Behavioral Story Bank
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
