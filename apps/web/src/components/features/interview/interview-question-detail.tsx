"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bookmark, BookmarkCheck, NotebookPen, Play } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_QUESTION_TYPE_LABELS } from "@/features/interview/constants";
import {
  useCreateInterview,
  useCreateInterviewBookmark,
  useCreateInterviewNote,
  useDeleteInterviewBookmark,
  useInterviewBookmarks,
  useInterviewNotes,
  useInterviewQuestion,
} from "@/features/interview/use-interview";

export function InterviewQuestionDetailView({ slug }: { slug: string }) {
  const questionQuery = useInterviewQuestion(slug);
  const bookmarksQuery = useInterviewBookmarks();
  const createBookmark = useCreateInterviewBookmark();
  const deleteBookmark = useDeleteInterviewBookmark();
  const createInterview = useCreateInterview();
  const router = useRouter();

  const question = questionQuery.data;
  const notesQuery = useInterviewNotes(question?.id);
  const createNote = useCreateInterviewNote();
  const [noteDraft, setNoteDraft] = useState("");

  if (questionQuery.isLoading) return <LoadingState count={2} itemClassName="h-40" />;
  if (questionQuery.isError || !question) {
    return <ErrorState message="We couldn't load this question." retry={() => void questionQuery.refetch()} />;
  }

  const existingBookmark = (bookmarksQuery.data ?? []).find((b) => b.target_type === "QUESTION" && b.target_id === question.id);

  const questionId = question.id;

  function handlePractice() {
    createInterview.mutate(
      { mode: "PRACTICE", question_id: questionId },
      { onSuccess: (interview) => router.push(`/interview/session/${interview.id}`) },
    );
  }

  function handleSaveNote() {
    if (!noteDraft.trim()) return;
    createNote.mutate(
      { target_type: "QUESTION", target_id: questionId, note: noteDraft.trim() },
      { onSuccess: () => setNoteDraft("") },
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline">{INTERVIEW_QUESTION_TYPE_LABELS[question.interview_type]}</Badge>
          <Badge variant="secondary">{question.difficulty}</Badge>
          {question.company_archetypes.map((archetype) => (
            <Badge key={archetype} variant="outline">
              {archetype.replace(/_/g, " ")}
            </Badge>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              existingBookmark
                ? deleteBookmark.mutate(existingBookmark.id)
                : createBookmark.mutate({ target_type: "QUESTION", target_id: question.id })
            }
          >
            {existingBookmark ? (
              <>
                <BookmarkCheck className="size-4 text-primary" aria-hidden="true" />
                Bookmarked
              </>
            ) : (
              <>
                <Bookmark className="size-4" aria-hidden="true" />
                Bookmark
              </>
            )}
          </Button>
          <Button onClick={handlePractice} disabled={createInterview.isPending}>
            <Play className="size-4" aria-hidden="true" />
            Practice This Question
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{question.title}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {question.business_context ? (
            <p className="rounded-lg bg-muted/30 p-3 text-sm text-muted-foreground">{question.business_context}</p>
          ) : null}
          <p className="text-sm text-foreground whitespace-pre-line">{question.prompt}</p>
          {question.constraints.length > 0 ? (
            <div>
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Constraints</p>
              <ul className="mt-1 list-inside list-disc text-sm text-muted-foreground">
                {question.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {question.rubric.length > 0 ? (
            <div>
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Evaluation rubric</p>
              <ul className="mt-1 flex flex-col gap-1 text-sm text-muted-foreground">
                {question.rubric.map((c) => (
                  <li key={c.criterion}>
                    {c.criterion} <span className="text-xs">({c.points} pts)</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-4 pt-2 text-xs text-muted-foreground">
            <span>{question.time_limit_seconds ? `${Math.round(question.time_limit_seconds / 60)} min suggested` : "Untimed"}</span>
            <span>{question.hint_count} hint{question.hint_count === 1 ? "" : "s"} available</span>
            <span>Attempted {question.attempt_count}x{question.best_score != null ? ` · best ${question.best_score.toFixed(0)}%` : ""}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <NotebookPen className="size-4" aria-hidden="true" />
            My Notes
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {(notesQuery.data ?? []).map((note) => (
            <p key={note.id} className="rounded-lg bg-muted/30 p-2 text-sm text-foreground">
              {note.note}
            </p>
          ))}
          <div className="flex items-start gap-2">
            <Textarea
              value={noteDraft}
              onChange={(e) => setNoteDraft(e.target.value)}
              placeholder="Add a note for next time you see this question..."
              rows={2}
              className="flex-1"
            />
            <Button size="sm" onClick={handleSaveNote} disabled={createNote.isPending || !noteDraft.trim()}>
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
