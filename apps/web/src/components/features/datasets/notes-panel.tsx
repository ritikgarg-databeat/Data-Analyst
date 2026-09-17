"use client";

import { useState } from "react";
import { NotebookPen, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Textarea } from "@/components/ui/textarea";
import { useAddNote, useDatasetNotes, useDeleteNote } from "@/features/datasets/use-dataset-notes";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function NotesPanel({ datasetSlug }: { datasetSlug: string }) {
  const notesQuery = useDatasetNotes(datasetSlug);
  const addMutation = useAddNote(datasetSlug);
  const deleteMutation = useDeleteNote(datasetSlug);
  const [body, setBody] = useState("");

  function handleAdd() {
    if (!body.trim()) return;
    addMutation.mutate({ body: body.trim() }, { onSuccess: () => setBody("") });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder='e.g. "Revenue appears heavily skewed because enterprise customers generate very large orders."'
        />
        <Button size="sm" className="self-end" onClick={handleAdd} disabled={!body.trim() || addMutation.isPending}>
          Add Note
        </Button>
      </div>

      {notesQuery.isLoading ? (
        <LoadingState count={2} itemClassName="h-16" />
      ) : notesQuery.isError ? (
        <ErrorState
          title="Unable to load notes"
          message="We couldn't reach the API to load your notes for this dataset."
          retry={() => void notesQuery.refetch()}
        />
      ) : !notesQuery.data || notesQuery.data.length === 0 ? (
        <EmptyState icon={NotebookPen} title="No notes yet" description="Personal notes stay local to you and this dataset." />
      ) : (
        <ul className="flex flex-col gap-2">
          {notesQuery.data.map((note) => (
            <li key={note.id} className="rounded-lg border border-border p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-foreground">{note.body}</p>
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(note.id)}
                  aria-label="Delete note"
                  className="shrink-0 rounded p-1 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {note.table_name ? `${note.table_name}${note.column_name ? `.${note.column_name}` : ""} · ` : ""}
                {formatDate(note.created_at)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
