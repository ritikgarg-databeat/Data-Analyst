"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Quote, Sparkles, XCircle } from "lucide-react";
import type { ResumeSource } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useTargetRoles } from "@/features/career/use-career";
import {
  useCreateResumeVersion,
  useExtractResumeEvidence,
  useResumeGapAnalysis,
  useResumeVersion,
  useResumes,
  useReviewResumeVersion,
  useUploadResumeVersion,
} from "@/features/career/use-resume";

export function ResumeDetail({ resumeId }: { resumeId: string }) {
  const resumesQuery = useResumes();
  const targetRolesQuery = useTargetRoles();
  const createVersion = useCreateResumeVersion(resumeId);
  const uploadVersion = useUploadResumeVersion(resumeId);
  const [selectedVersionId, setSelectedVersionId] = useState<string | undefined>(undefined);
  const [newVersionText, setNewVersionText] = useState("");
  const [newVersionSource, setNewVersionSource] = useState<ResumeSource>("PASTED");
  const [targetRoleTitle, setTargetRoleTitle] = useState("");
  const [gapTargetRoleId, setGapTargetRoleId] = useState("");

  const resume = useMemo(() => (resumesQuery.data ?? []).find((r) => r.id === resumeId), [resumesQuery.data, resumeId]);

  const currentVersionId =
    selectedVersionId ?? resume?.versions.find((v) => v.is_current)?.id ?? resume?.versions[0]?.id;

  const versionQuery = useResumeVersion(currentVersionId);
  const extractEvidence = useExtractResumeEvidence(currentVersionId ?? "");
  const review = useReviewResumeVersion(currentVersionId ?? "");
  const gapAnalysisQuery = useResumeGapAnalysis(currentVersionId, gapTargetRoleId || undefined);

  if (resumesQuery.isLoading) return <LoadingState count={3} itemClassName="h-24" />;
  if (resumesQuery.isError || !resume) {
    return <ErrorState message="We couldn't load this resume." retry={() => void resumesQuery.refetch()} />;
  }

  function handleAddVersion() {
    if (!newVersionText.trim()) return;
    createVersion.mutate(
      { source: newVersionSource, raw_text: newVersionText.trim(), file_name: undefined },
      {
        onSuccess: (version) => {
          setSelectedVersionId(version.id);
          setNewVersionText("");
        },
      },
    );
  }

  function handleResumeFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file
    if (!file) return;
    // Uploaded straight to the server, which extracts real text
    // (.txt/.md/.docx/.pdf) — never read client-side via `file.text()`,
    // which silently produces garbage (even a save-breaking NUL byte) for
    // any non-plain-text file.
    uploadVersion.mutate(file, {
      onSuccess: (version) => setSelectedVersionId(version.id),
    });
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>{resume.title} — Version History</CardTitle>
        </CardHeader>
        <CardContent>
          {resume.versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No versions yet — add one below.</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {resume.versions.map((version) => (
                <li key={version.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedVersionId(version.id)}
                    className={`flex w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-sm ${
                      version.id === currentVersionId ? "border-primary bg-primary/5" : "border-border hover:bg-accent"
                    }`}
                  >
                    <span className="text-foreground">Version {version.version_number}</span>
                    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      {version.is_current ? <Badge variant="outline">Current</Badge> : null}
                      {version.source}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a Version</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Select
            value={newVersionSource}
            onChange={(event) => {
              setNewVersionSource(event.target.value as ResumeSource);
              setNewVersionText("");
            }}
            className="w-full sm:w-48"
            aria-label="Source"
          >
            <option value="PASTED">Pasted</option>
            <option value="UPLOADED">Uploaded</option>
          </Select>
          {newVersionSource === "UPLOADED" ? (
            <div className="flex flex-col gap-2">
              <input
                type="file"
                accept=".txt,.md,.docx,.pdf"
                onChange={handleResumeFileChange}
                disabled={uploadVersion.isPending}
                aria-label="Resume file"
                className="text-sm text-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1.5 file:text-sm file:font-medium disabled:opacity-50"
              />
              <p className="text-xs text-muted-foreground">
                {uploadVersion.isPending
                  ? "Uploading and extracting text..."
                  : "Choose a .txt, .md, .docx, or .pdf file — it uploads and creates a version immediately."}
              </p>
            </div>
          ) : (
            <>
              <Textarea
                value={newVersionText}
                onChange={(event) => setNewVersionText(event.target.value)}
                placeholder="Paste your resume text here..."
                rows={8}
                aria-label="Resume text"
              />
              <Button
                className="self-start"
                onClick={handleAddVersion}
                disabled={createVersion.isPending || !newVersionText.trim()}
              >
                Add Version
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {currentVersionId ? (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle>Evidence</CardTitle>
                <Button size="sm" onClick={() => extractEvidence.mutate()} disabled={extractEvidence.isPending}>
                  <Sparkles className="size-4" aria-hidden="true" />
                  {extractEvidence.isPending ? "Extracting..." : "Extract Evidence"}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {versionQuery.isLoading ? (
                <LoadingState count={1} itemClassName="h-16" />
              ) : !versionQuery.data || versionQuery.data.evidence.length === 0 ? (
                <p className="text-sm text-muted-foreground">No evidence extracted yet.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {versionQuery.data.evidence.map((item) => (
                    <li key={item.id} className="rounded-md border border-border bg-card p-3 text-sm">
                      <div className="flex items-center gap-1.5">
                        <Badge variant="outline">{item.skill_slug}</Badge>
                      </div>
                      <p className="mt-1 flex items-start gap-1.5 text-foreground italic">
                        <Quote className="mt-0.5 size-3 shrink-0 text-muted-foreground" aria-hidden="true" />
                        {item.evidence_text}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Review</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <div className="flex gap-2">
                <Input
                  value={targetRoleTitle}
                  onChange={(event) => setTargetRoleTitle(event.target.value)}
                  placeholder="Target role title (optional)"
                  aria-label="Target role title"
                />
                <Button onClick={() => review.mutate(targetRoleTitle.trim() || undefined)} disabled={review.isPending}>
                  {review.isPending ? "Reviewing..." : "Review"}
                </Button>
              </div>
              {!versionQuery.data || versionQuery.data.reviews.length === 0 ? (
                <p className="text-sm text-muted-foreground">No reviews yet.</p>
              ) : (
                <ul className="flex flex-col gap-3">
                  {versionQuery.data.reviews.map((r) => (
                    <li key={r.id} className="rounded-md border border-border bg-card p-3">
                      <div className="flex flex-wrap gap-3 text-sm">
                        <span>
                          <span className="font-medium text-foreground">{r.quality_score.toFixed(0)}</span>{" "}
                          <span className="text-muted-foreground">quality</span>
                        </span>
                        {r.clarity_score != null ? (
                          <span>
                            <span className="font-medium text-foreground">{r.clarity_score.toFixed(0)}</span>{" "}
                            <span className="text-muted-foreground">clarity</span>
                          </span>
                        ) : null}
                        {r.impact_score != null ? (
                          <span>
                            <span className="font-medium text-foreground">{r.impact_score.toFixed(0)}</span>{" "}
                            <span className="text-muted-foreground">impact</span>
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        Scores are deterministic. {r.ai_generated ? "Issues/suggestions below are AI suggestions." : ""}
                      </p>
                      {r.issues.length > 0 || r.suggestions.length > 0 ? (
                        <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
                          <div>
                            <p className="text-xs font-medium text-foreground">Issues</p>
                            <ul className="list-inside list-disc text-xs text-muted-foreground">
                              {r.issues.map((issue, i) => (
                                <li key={i}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-foreground">Suggestions</p>
                            <ul className="list-inside list-disc text-xs text-muted-foreground">
                              {r.suggestions.map((suggestion, i) => (
                                <li key={i}>{suggestion}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ) : (
                        <p className="mt-2 text-xs text-muted-foreground">
                          No AI suggestions available right now (AI may be unconfigured in local mode).
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Gap Analysis</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Select
                value={gapTargetRoleId}
                onChange={(event) => setGapTargetRoleId(event.target.value)}
                className="w-full sm:w-64"
                aria-label="Target role for gap analysis"
              >
                <option value="">Choose a target role...</option>
                {(targetRolesQuery.data ?? []).map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.custom_title ?? role.role_template?.title ?? "Untitled role"}
                  </option>
                ))}
              </Select>
              {!gapTargetRoleId ? (
                <p className="text-sm text-muted-foreground">Pick a target role to see which of its skills your resume lacks evidence for.</p>
              ) : gapAnalysisQuery.isLoading ? (
                <LoadingState count={1} itemClassName="h-24" />
              ) : gapAnalysisQuery.isError || !gapAnalysisQuery.data ? (
                <p className="text-sm text-muted-foreground">Couldn&apos;t load gap analysis.</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {gapAnalysisQuery.data.gaps.map((gap) => (
                    <li key={gap.skill_slug} className="flex items-center gap-2 text-sm">
                      {gap.has_evidence ? (
                        <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                      ) : (
                        <XCircle className="size-4 text-rose-600 dark:text-rose-400" aria-hidden="true" />
                      )}
                      <span className="text-foreground">{gap.skill_slug}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
