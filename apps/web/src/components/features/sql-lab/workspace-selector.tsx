"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useCreateSqlWorkspace, useSqlWorkspaces } from "@/features/sql/use-sql-workspaces";

interface WorkspaceSelectorProps {
  engine: string;
  database: string;
  workspaceId: string | undefined;
  onChange: (workspaceId: string | undefined) => void;
}

/**
 * Optional named grouping for saved queries under one engine+database
 * pairing ("SQL Workspaces") — the backend (SqlWorkspaceService, already
 * threaded through SavedQueriesPanel/useSqlSavedQueries via `workspace_id`)
 * had no picker to actually create or select one, so `workspaceId` was
 * always undefined in practice. Scoped to whichever engine/database is
 * currently selected, matching a workspace's own engine+database pairing.
 */
export function WorkspaceSelector({ engine, database, workspaceId, onChange }: WorkspaceSelectorProps) {
  const workspacesQuery = useSqlWorkspaces();
  const createWorkspace = useCreateSqlWorkspace();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");

  const workspaces = (workspacesQuery.data ?? []).filter((w) => w.engine === engine && w.database === database);

  function handleCreate() {
    if (!name.trim()) return;
    createWorkspace.mutate(
      { name: name.trim(), engine, database },
      {
        onSuccess: (workspace) => {
          onChange(workspace.id);
          setName("");
          setShowCreate(false);
        },
      },
    );
  }

  return (
    <div className="flex w-full flex-col gap-1 sm:w-auto">
      <Label htmlFor="sql-lab-workspace">Workspace</Label>
      <div className="flex items-center gap-1.5">
        <Select
          id="sql-lab-workspace"
          value={workspaceId ?? ""}
          onChange={(event) => onChange(event.target.value || undefined)}
          className="min-w-0 flex-1 sm:w-40 sm:flex-none"
        >
          <option value="">No workspace</option>
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </Select>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="size-9 shrink-0"
          aria-label="New workspace"
          onClick={() => setShowCreate((v) => !v)}
        >
          <Plus className="size-4" aria-hidden="true" />
        </Button>
      </div>
      {workspacesQuery.isError ? (
        <p className="text-xs text-destructive">Couldn&apos;t load workspaces.</p>
      ) : null}
      {showCreate ? (
        <div className="flex items-center gap-1.5">
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Workspace name"
            className="h-8 min-w-0 flex-1 text-sm sm:w-40 sm:flex-none"
            autoFocus
            onKeyDown={(event) => {
              if (event.key === "Enter") handleCreate();
              if (event.key === "Escape") setShowCreate(false);
            }}
          />
          <Button
            type="button"
            size="sm"
            disabled={!name.trim() || createWorkspace.isPending}
            onClick={handleCreate}
          >
            {createWorkspace.isPending ? "Creating..." : "Create"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
