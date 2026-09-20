"use client";

import { useState } from "react";
import Link from "next/link";
import { FileText, GitCompare, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import {
  useCreateJobDescription,
  useDeleteJobDescription,
  useJobDescriptions,
  useUploadJobDescription,
} from "@/features/career/use-jobs";

export function JobDescriptionsPage() {
  const jobDescriptionsQuery = useJobDescriptions();
  const createJobDescription = useCreateJobDescription();
  const uploadJobDescription = useUploadJobDescription();
  const deleteJobDescription = useDeleteJobDescription();

  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [rawText, setRawText] = useState("");
  const [source, setSource] = useState<"PASTED" | "UPLOADED">("PASTED");

  if (jobDescriptionsQuery.isLoading) return <LoadingState count={4} itemClassName="h-20" />;
  if (jobDescriptionsQuery.isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your saved job descriptions."
        retry={() => void jobDescriptionsQuery.refetch()}
      />
    );
  }

  const jobDescriptions = jobDescriptionsQuery.data ?? [];

  function handleCreate() {
    if (!title.trim() || !rawText.trim()) return;
    createJobDescription.mutate(
      {
        title: title.trim(),
        company: company.trim() || undefined,
        location: location.trim() || undefined,
        notes: notes.trim() || undefined,
        raw_text: rawText.trim(),
        source,
      },
      {
        onSuccess: () => {
          setTitle("");
          setCompany("");
          setLocation("");
          setNotes("");
          setRawText("");
        },
      },
    );
  }

  function handleJdFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file
    if (!file || !title.trim()) return;
    // Uploaded straight to the server, which extracts real text
    // (.txt/.md/.docx/.pdf) — never read client-side via `file.text()`,
    // which silently produces garbage (even a save-breaking NUL byte) for
    // any non-plain-text file.
    uploadJobDescription.mutate(
      {
        file,
        title: title.trim(),
        company: company.trim() || undefined,
        location: location.trim() || undefined,
        notes: notes.trim() || undefined,
      },
      {
        onSuccess: () => {
          setTitle("");
          setCompany("");
          setLocation("");
          setNotes("");
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex justify-end">
        <Button variant="outline" asChild>
          <Link href="/career/job-descriptions/compare">
            <GitCompare className="size-4" aria-hidden="true" />
            Compare Saved JDs
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Saved Job Descriptions</CardTitle>
        </CardHeader>
        <CardContent>
          {jobDescriptions.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No job descriptions yet"
              description="Paste one below to extract requirements, find skill gaps, and build a prep plan."
            />
          ) : (
            <ul className="flex flex-col gap-2">
              {jobDescriptions.map((jd) => (
                <li
                  key={jd.id}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <Link href={`/career/job-descriptions/${jd.id}`} className="font-medium text-foreground hover:underline">
                      {jd.title}
                    </Link>
                    <p className="text-sm text-muted-foreground">
                      {jd.company ?? "Unknown company"}
                      {jd.location ? ` · ${jd.location}` : ""}
                    </p>
                    <Badge variant="outline" className="mt-1">
                      {jd.requirements.length} requirement{jd.requirements.length === 1 ? "" : "s"} extracted
                    </Badge>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/career/job-descriptions/${jd.id}`}>Open</Link>
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteJobDescription.mutate(jd.id)}
                      disabled={deleteJobDescription.isPending}
                      aria-label={`Delete ${jd.title}`}
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
          <CardTitle>Paste a New Job Description</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Job title"
              aria-label="Job title"
            />
            <Input
              value={company}
              onChange={(event) => setCompany(event.target.value)}
              placeholder="Company (optional)"
              aria-label="Company"
            />
            <Input
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              placeholder="Location (optional)"
              aria-label="Location"
            />
          </div>
          <Select
            value={source}
            onChange={(event) => {
              setSource(event.target.value as "PASTED" | "UPLOADED");
              setRawText("");
            }}
            className="w-full sm:w-48"
            aria-label="Source"
          >
            <option value="PASTED">Pasted</option>
            <option value="UPLOADED">Uploaded</option>
          </Select>
          {source === "UPLOADED" ? (
            <div className="flex flex-col gap-2">
              <input
                type="file"
                accept=".txt,.md,.docx,.pdf"
                onChange={handleJdFileChange}
                disabled={uploadJobDescription.isPending || !title.trim()}
                aria-label="Job description file"
                className="text-sm text-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1.5 file:text-sm file:font-medium disabled:opacity-50"
              />
              <p className="text-xs text-muted-foreground">
                {uploadJobDescription.isPending
                  ? "Uploading and extracting text..."
                  : !title.trim()
                    ? "Enter a job title above first, then choose a .txt, .md, .docx, or .pdf file."
                    : "Choose a file — it uploads and saves this job description immediately."}
              </p>
            </div>
          ) : (
            <Textarea
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste the full job description text here..."
              rows={8}
              aria-label="Job description text"
            />
          )}
          <Textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Notes (optional)"
            rows={2}
            aria-label="Notes"
          />
          {source === "PASTED" ? (
            <Button
              className="self-start"
              onClick={handleCreate}
              disabled={createJobDescription.isPending || !title.trim() || !rawText.trim()}
            >
              Save Job Description
            </Button>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
