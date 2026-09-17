"use client";

import { useState } from "react";
import Link from "next/link";
import { FileBadge, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useCreateResume, useDeleteResume, useResumes, useUpdateResume } from "@/features/career/use-resume";

export function ResumePage() {
  const resumesQuery = useResumes();
  const createResume = useCreateResume();
  const deleteResume = useDeleteResume();
  const updateResume = useUpdateResume();
  const [title, setTitle] = useState("");

  if (resumesQuery.isLoading) return <LoadingState count={3} itemClassName="h-20" />;
  if (resumesQuery.isError) {
    return <ErrorState message="We couldn't reach the API to load your resumes." retry={() => void resumesQuery.refetch()} />;
  }

  const resumes = resumesQuery.data ?? [];

  function handleCreate() {
    if (!title.trim()) return;
    createResume.mutate({ title: title.trim() }, { onSuccess: () => setTitle("") });
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Your Resumes</CardTitle>
        </CardHeader>
        <CardContent>
          {resumes.length === 0 ? (
            <EmptyState icon={FileBadge} title="No resumes yet" description="Create a resume below, then add a version to analyze." />
          ) : (
            <ul className="flex flex-col gap-2">
              {resumes.map((resume) => (
                <li
                  key={resume.id}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <Link href={`/career/resume/${resume.id}`} className="font-medium text-foreground hover:underline">
                        {resume.title}
                      </Link>
                      {resume.is_primary ? <Badge>Primary</Badge> : null}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {resume.versions.length} version{resume.versions.length === 1 ? "" : "s"}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {!resume.is_primary ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => updateResume.mutate({ id: resume.id, is_primary: true })}
                        disabled={updateResume.isPending}
                      >
                        Set Primary
                      </Button>
                    ) : null}
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/career/resume/${resume.id}`}>Open</Link>
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteResume.mutate(resume.id)}
                      disabled={deleteResume.isPending}
                      aria-label={`Delete ${resume.title}`}
                    >
                      <Trash2 className="size-3.5" aria-hidden="true" />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create a New Resume</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. Data Analyst Resume 2026"
            aria-label="Resume title"
          />
          <Button onClick={handleCreate} disabled={createResume.isPending || !title.trim()}>
            Create
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
