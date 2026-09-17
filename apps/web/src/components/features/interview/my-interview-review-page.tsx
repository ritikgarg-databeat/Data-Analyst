"use client";

import Link from "next/link";
import { Bookmark, NotebookPen, RotateCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import {
  useDeleteInterviewBookmark,
  useInterviewBookmarks,
  useInterviewNotes,
  useInterviewReviewQueue,
} from "@/features/interview/use-interview";

/** "My Interview Review" (spec section 52/55) — bookmarked questions, notes,
 * and the spaced-review queue (spec section 53) all in one place. */
export function MyInterviewReviewPage() {
  const bookmarksQuery = useInterviewBookmarks();
  const notesQuery = useInterviewNotes();
  const reviewQueueQuery = useInterviewReviewQueue();
  const deleteBookmark = useDeleteInterviewBookmark();

  const isLoading = bookmarksQuery.isLoading || notesQuery.isLoading || reviewQueueQuery.isLoading;
  const isError = bookmarksQuery.isError || notesQuery.isError || reviewQueueQuery.isError;

  if (isLoading) return <LoadingState count={3} itemClassName="h-32" />;
  if (isError) {
    return (
      <ErrorState
        message="We couldn't load your interview review data."
        retry={() => {
          void bookmarksQuery.refetch();
          void notesQuery.refetch();
          void reviewQueueQuery.refetch();
        }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <RotateCcw className="size-4" aria-hidden="true" />
            Due for Review
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(reviewQueueQuery.data ?? []).length === 0 ? (
            <EmptyState icon={RotateCcw} title="Nothing due right now" description="Questions reappear here once their rest interval elapses." />
          ) : (
            <ul className="flex flex-col gap-2">
              {(reviewQueueQuery.data ?? []).map((item) => (
                <li key={item.question_id} className="flex items-center justify-between gap-2 rounded-lg border border-border p-3 text-sm">
                  <div>
                    <Link href={`/interview/questions/${item.slug}`} className="font-medium text-foreground hover:underline">
                      {item.title}
                    </Link>
                    <p className="text-xs text-muted-foreground">{item.reason}</p>
                  </div>
                  <Badge variant="outline">
                    {INTERVIEW_SECTION_TYPE_LABELS[item.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? item.interview_type}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <Bookmark className="size-4" aria-hidden="true" />
            Bookmarked
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(bookmarksQuery.data ?? []).length === 0 ? (
            <EmptyState icon={Bookmark} title="No bookmarks yet" description="Bookmark a question from the catalog to save it here." />
          ) : (
            <ul className="flex flex-col gap-2">
              {(bookmarksQuery.data ?? []).map((b) => (
                <li key={b.id} className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-foreground">
                    {b.target_type}: {b.target_id}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => deleteBookmark.mutate(b.id)}>
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <NotebookPen className="size-4" aria-hidden="true" />
            My Notes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(notesQuery.data ?? []).length === 0 ? (
            <EmptyState icon={NotebookPen} title="No notes yet" description="Add notes from a question's detail page." />
          ) : (
            <ul className="flex flex-col gap-2">
              {(notesQuery.data ?? []).map((n) => (
                <li key={n.id} className="rounded-lg bg-muted/30 p-2 text-sm text-foreground">
                  {n.note}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
