"use client";

import { useState } from "react";
import { Bookmark, Check, Pencil, Plus, Trash2, X } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateSqlSavedQuery,
  useDeleteSqlSavedQuery,
  useSqlSavedQueries,
  useUpdateSqlSavedQuery,
} from "@/features/sql/use-sql-saved-queries";
import { cn } from "@/lib/utils";
import type { SqlSavedQuerySchema } from "@data-analyst-lab/shared";

interface SavedQueriesPanelProps {
  engine: string;
  database: string;
  /** The query currently in the editor — what "Save current query" persists. */
  currentQuery: string;
  workspaceId?: string;
  onSelect: (query: string, engine: string, database: string) => void;
  className?: string;
}

/** List + create/rename/delete for saved queries, scoped to the current engine/database. */
export function SavedQueriesPanel({
  engine,
  database,
  currentQuery,
  workspaceId,
  onSelect,
  className,
}: SavedQueriesPanelProps) {
  const savedQuery = useSqlSavedQueries(workspaceId);
  const createSaved = useCreateSqlSavedQuery();
  const updateSaved = useUpdateSqlSavedQuery();
  const deleteSaved = useDeleteSqlSavedQuery();

  const [showSaveForm, setShowSaveForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  function handleSave() {
    if (!title.trim() || !currentQuery.trim()) return;
    createSaved.mutate(
      {
        title: title.trim(),
        description: description.trim() || undefined,
        query: currentQuery,
        engine,
        database,
        workspace_id: workspaceId,
      },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
          setShowSaveForm(false);
        },
      },
    );
  }

  function startRename(item: SqlSavedQuerySchema) {
    setEditingId(item.id);
    setEditTitle(item.title);
  }

  function commitRename(id: string) {
    if (!editTitle.trim()) return;
    updateSaved.mutate({ id, body: { title: editTitle.trim() } }, { onSuccess: () => setEditingId(null) });
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">{savedQuery.data?.length ?? 0} saved</p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setShowSaveForm((v) => !v)}
          disabled={!currentQuery.trim()}
        >
          <Plus className="size-3.5" aria-hidden="true" />
          Save current query
        </Button>
      </div>

      {showSaveForm ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            handleSave();
          }}
          className="space-y-2 rounded-lg border border-border p-3"
        >
          <div className="space-y-1">
            <Label htmlFor="saved-query-title">Title</Label>
            <Input
              id="saved-query-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Top customers by revenue"
              autoFocus
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="saved-query-description">Description (optional)</Label>
            <Textarea
              id="saved-query-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={2}
            />
          </div>
          <div className="flex items-center gap-2">
            <Button type="submit" size="sm" disabled={!title.trim() || createSaved.isPending}>
              {createSaved.isPending ? "Saving..." : "Save"}
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setShowSaveForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : null}

      {savedQuery.isLoading ? (
        <LoadingState count={3} itemClassName="h-12" />
      ) : savedQuery.isError ? (
        <ErrorState
          title="Unable to load saved queries"
          message="We couldn't reach the API to load your saved queries."
          retry={() => void savedQuery.refetch()}
        />
      ) : (savedQuery.data ?? []).length === 0 ? (
        <EmptyState
          icon={Bookmark}
          title="No saved queries"
          description="Save a query from the editor to build up your personal library."
        />
      ) : (
        <ul className="divide-y divide-border">
          {(savedQuery.data ?? []).map((item) => (
            <li key={item.id} className="group px-1 py-2">
              {editingId === item.id ? (
                <div className="flex items-center gap-1.5">
                  <Input
                    value={editTitle}
                    onChange={(event) => setEditTitle(event.target.value)}
                    className="h-7 text-sm"
                    autoFocus
                    onKeyDown={(event) => {
                      if (event.key === "Enter") commitRename(item.id);
                      if (event.key === "Escape") setEditingId(null);
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="size-7 shrink-0"
                    aria-label="Confirm rename"
                    onClick={() => commitRename(item.id)}
                  >
                    <Check className="size-3.5" aria-hidden="true" />
                  </Button>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="size-7 shrink-0"
                    aria-label="Cancel rename"
                    onClick={() => setEditingId(null)}
                  >
                    <X className="size-3.5" aria-hidden="true" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-start gap-2">
                  <button
                    type="button"
                    onClick={() => onSelect(item.query, item.engine, item.database)}
                    className="min-w-0 flex-1 rounded-md px-1.5 py-1 text-left hover:bg-muted/50"
                  >
                    <p className="truncate text-sm font-medium text-foreground">{item.title}</p>
                    {item.description ? (
                      <p className="truncate text-xs text-muted-foreground">{item.description}</p>
                    ) : (
                      <p className="truncate font-mono text-xs text-muted-foreground">
                        {item.query.trim().split("\n")[0]}
                      </p>
                    )}
                  </button>
                  <div className="flex shrink-0 items-center opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="size-7"
                      aria-label={`Rename ${item.title}`}
                      onClick={() => startRename(item)}
                    >
                      <Pencil className="size-3.5" aria-hidden="true" />
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="size-7"
                      aria-label={`Delete ${item.title}`}
                      onClick={() => deleteSaved.mutate(item.id)}
                    >
                      <Trash2 className="size-3.5" aria-hidden="true" />
                    </Button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
