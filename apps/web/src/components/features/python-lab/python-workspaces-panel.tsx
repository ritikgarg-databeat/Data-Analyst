"use client";

import { useState } from "react";
import { Check, FolderOpen, Pencil, Plus, Trash2, X } from "lucide-react";
import type { PythonWorkspaceSchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useCreatePythonWorkspace,
  useDeletePythonWorkspace,
  usePythonWorkspaces,
  useUpdatePythonWorkspace,
} from "@/features/python/use-python-workspaces";
import { cn } from "@/lib/utils";

interface PythonWorkspacesPanelProps {
  activeWorkspaceId: string | null;
  onSelect: (workspaceId: string) => void;
  className?: string;
}

/** Workspace switcher: list/create/rename/delete — the Python Lab analogue of sql-lab/saved-queries-panel.tsx. */
export function PythonWorkspacesPanel({ activeWorkspaceId, onSelect, className }: PythonWorkspacesPanelProps) {
  const workspacesQuery = usePythonWorkspaces();
  const createWorkspace = useCreatePythonWorkspace();
  const updateWorkspace = useUpdatePythonWorkspace();
  const deleteWorkspace = useDeletePythonWorkspace();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [name, setName] = useState("");

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  function handleCreate() {
    if (!name.trim()) return;
    createWorkspace.mutate(
      { name: name.trim() },
      {
        onSuccess: (workspace) => {
          setName("");
          setShowCreateForm(false);
          onSelect(workspace.id);
        },
      },
    );
  }

  function startRename(item: PythonWorkspaceSchema) {
    setEditingId(item.id);
    setEditName(item.name);
  }

  function commitRename(id: string) {
    if (!editName.trim()) return;
    updateWorkspace.mutate({ id, body: { name: editName.trim() } }, { onSuccess: () => setEditingId(null) });
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">{workspacesQuery.data?.length ?? 0} workspaces</p>
        <Button type="button" size="sm" variant="outline" onClick={() => setShowCreateForm((v) => !v)}>
          <Plus className="size-3.5" aria-hidden="true" />
          New workspace
        </Button>
      </div>

      {showCreateForm ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            handleCreate();
          }}
          className="space-y-2 rounded-lg border border-border p-3"
        >
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Cohort analysis"
            aria-label="Workspace name"
            autoFocus
          />
          <div className="flex items-center gap-2">
            <Button type="submit" size="sm" disabled={!name.trim() || createWorkspace.isPending}>
              {createWorkspace.isPending ? "Creating..." : "Create"}
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setShowCreateForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : null}

      {workspacesQuery.isLoading ? (
        <LoadingState count={3} itemClassName="h-10" />
      ) : workspacesQuery.isError ? (
        <ErrorState
          title="Unable to load workspaces"
          message="We couldn't reach the API to load your Python Lab workspaces."
          retry={() => void workspacesQuery.refetch()}
        />
      ) : (workspacesQuery.data ?? []).length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title="No workspaces yet"
          description="Create a workspace to save a notebook of cells you can come back to."
        />
      ) : (
        <ul className="divide-y divide-border">
          {(workspacesQuery.data ?? []).map((item) => (
            <li key={item.id} className="group px-1 py-2">
              {editingId === item.id ? (
                <div className="flex items-center gap-1.5">
                  <Input
                    value={editName}
                    onChange={(event) => setEditName(event.target.value)}
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
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => onSelect(item.id)}
                    aria-current={activeWorkspaceId === item.id ? "true" : undefined}
                    className={cn(
                      "min-w-0 flex-1 rounded-md px-1.5 py-1 text-left text-sm hover:bg-muted/50",
                      activeWorkspaceId === item.id && "bg-accent/40 font-medium text-foreground",
                    )}
                  >
                    <span className="truncate">{item.name}</span>
                  </button>
                  <div className="flex shrink-0 items-center opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="size-7"
                      aria-label={`Rename ${item.name}`}
                      onClick={() => startRename(item)}
                    >
                      <Pencil className="size-3.5" aria-hidden="true" />
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="size-7"
                      aria-label={`Delete ${item.name}`}
                      onClick={() => deleteWorkspace.mutate(item.id)}
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
