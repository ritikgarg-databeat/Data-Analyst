"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ClipboardList, FileText, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { JD_REQUIREMENT_PRIORITY_LABELS, JOB_PREP_STATUS_ORDER, JOB_PREP_STATUS_LABELS } from "@/features/career/constants";
import {
  useAnalyzeJD,
  useCreateJobWorkspace,
  useExtractJDRequirements,
  useJDAnalysis,
  useJDInterviewPlan,
  useJDPreparationPlan,
  useJDSkillGaps,
  useJobDescription,
  useJobWorkspaces,
  useUpdateJobWorkspace,
} from "@/features/career/use-jobs";
import type { JobPrepChecklistItem, JobPrepStatus } from "@data-analyst-lab/shared";

export function JobDescriptionDetail({ jobDescriptionId }: { jobDescriptionId: string }) {
  const jdQuery = useJobDescription(jobDescriptionId);
  const extract = useExtractJDRequirements(jobDescriptionId);
  const skillGapsQuery = useJDSkillGaps(jobDescriptionId);
  const analysisQuery = useJDAnalysis(jobDescriptionId);
  const analyze = useAnalyzeJD(jobDescriptionId);
  const prepPlanQuery = useJDPreparationPlan(jobDescriptionId);
  const interviewPlanQuery = useJDInterviewPlan(jobDescriptionId);
  const workspacesQuery = useJobWorkspaces();
  const createWorkspace = useCreateJobWorkspace();
  const updateWorkspace = useUpdateJobWorkspace();

  const [mustHaveWeight, setMustHaveWeight] = useState(3);
  const [preferredWeight, setPreferredWeight] = useState(2);
  const [niceWeight, setNiceWeight] = useState(1);
  const [checklistDraft, setChecklistDraft] = useState("");

  const workspace = useMemo(
    () => (workspacesQuery.data ?? []).find((w) => w.job_description_id === jobDescriptionId) ?? null,
    [workspacesQuery.data, jobDescriptionId],
  );

  if (jdQuery.isLoading) return <LoadingState count={3} itemClassName="h-32" />;
  if (jdQuery.isError || !jdQuery.data) {
    return <ErrorState message="We couldn't load this job description." retry={() => void jdQuery.refetch()} />;
  }

  const jd = jdQuery.data;

  function toggleChecklistItem(index: number) {
    if (!workspace) return;
    const nextChecklist = workspace.checklist.map((item, i) => (i === index ? { ...item, is_done: !item.is_done } : item));
    updateWorkspace.mutate({ id: workspace.id, checklist: nextChecklist });
  }

  function addChecklistItem() {
    if (!workspace || !checklistDraft.trim()) return;
    const nextChecklist: JobPrepChecklistItem[] = [...workspace.checklist, { label: checklistDraft.trim(), is_done: false }];
    updateWorkspace.mutate({ id: workspace.id, checklist: nextChecklist }, { onSuccess: () => setChecklistDraft("") });
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-4 text-primary" aria-hidden="true" />
            {jd.title}
            {jd.company ? <span className="font-normal text-muted-foreground">· {jd.company}</span> : null}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {jd.location ? <p className="text-sm text-muted-foreground">{jd.location}</p> : null}
          {jd.notes ? <p className="text-sm text-muted-foreground">{jd.notes}</p> : null}
          <Textarea value={jd.raw_text} readOnly rows={8} className="font-mono text-xs" aria-label="Job description text" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Requirements</CardTitle>
            <Button size="sm" onClick={() => extract.mutate()} disabled={extract.isPending}>
              <Sparkles className="size-4" aria-hidden="true" />
              {extract.isPending ? "Extracting..." : "Extract Requirements"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {jd.requirements.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="No requirements extracted yet"
              description="Click Extract Requirements to parse this posting's skills, tools, and expectations."
            />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-max border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                    <th className="px-4 py-2.5">Text</th>
                    <th className="px-4 py-2.5">Kind</th>
                    <th className="px-4 py-2.5">Priority</th>
                    <th className="px-4 py-2.5">Matched Skill</th>
                  </tr>
                </thead>
                <tbody>
                  {jd.requirements.map((req) => (
                    <tr key={req.id} className="border-b border-border last:border-0">
                      <td className="px-4 py-2 text-foreground">{req.raw_text}</td>
                      <td className="px-4 py-2 text-muted-foreground">{req.kind.replace(/_/g, " ")}</td>
                      <td className="px-4 py-2">
                        <Badge variant={req.priority === "MUST_HAVE" ? "default" : "outline"}>
                          {JD_REQUIREMENT_PRIORITY_LABELS[req.priority]}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{req.matched_skill_slug ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Skill Gaps</CardTitle>
        </CardHeader>
        <CardContent>
          {skillGapsQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : skillGapsQuery.isError || !skillGapsQuery.data ? (
            <p className="text-sm text-muted-foreground">Extract requirements first to see skill gaps.</p>
          ) : skillGapsQuery.data.gaps.length === 0 ? (
            <EmptyState icon={ClipboardList} title="No gaps found" description="Your mastery covers every matched requirement so far." />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-max border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                    <th className="px-4 py-2.5">Skill</th>
                    <th className="px-4 py-2.5">Priority</th>
                    <th className="px-4 py-2.5">Current Mastery</th>
                    <th className="px-4 py-2.5">Gap Size</th>
                  </tr>
                </thead>
                <tbody>
                  {skillGapsQuery.data.gaps.map((gap) => (
                    <tr key={gap.id} className="border-b border-border last:border-0">
                      <td className="px-4 py-2 text-foreground">{gap.skill_slug}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {gap.priority ? JD_REQUIREMENT_PRIORITY_LABELS[gap.priority] : "—"}
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{gap.current_mastery_score.toFixed(0)}%</td>
                      <td className="px-4 py-2 text-muted-foreground">{gap.gap_size.toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Readiness Analysis</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-muted-foreground" htmlFor="weight-must">Must-have weight</label>
              <Input id="weight-must" type="number" value={mustHaveWeight} onChange={(e) => setMustHaveWeight(Number(e.target.value))} className="w-24" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground" htmlFor="weight-preferred">Preferred weight</label>
              <Input id="weight-preferred" type="number" value={preferredWeight} onChange={(e) => setPreferredWeight(Number(e.target.value))} className="w-24" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground" htmlFor="weight-nice">Nice-to-have weight</label>
              <Input id="weight-nice" type="number" value={niceWeight} onChange={(e) => setNiceWeight(Number(e.target.value))} className="w-24" />
            </div>
            <Button
              onClick={() =>
                analyze.mutate({
                  weights: { MUST_HAVE: mustHaveWeight, STRONGLY_PREFERRED: preferredWeight, NICE_TO_HAVE: niceWeight },
                })
              }
              disabled={analyze.isPending}
            >
              {analyze.isPending ? "Analyzing..." : "Analyze"}
            </Button>
          </div>
          {analysisQuery.data ? (
            <div className="rounded-xl border border-border bg-card p-4">
              <p className="text-2xl font-semibold text-foreground">{analysisQuery.data.readiness_score.toFixed(0)}%</p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                A platform estimate based on your mastery against this posting&apos;s weighted requirements — not a hiring guarantee.
              </p>
              {analysisQuery.data.summary ? <p className="mt-2 text-sm text-foreground">{analysisQuery.data.summary}</p> : null}
              {analysisQuery.data.ai_explanation ? (
                <p className="mt-2 rounded-md border border-border bg-muted/40 p-2 text-xs text-foreground">
                  {analysisQuery.data.ai_explanation}
                </p>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Run an analysis to see your readiness score for this posting.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preparation Plan</CardTitle>
        </CardHeader>
        <CardContent>
          {prepPlanQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : !prepPlanQuery.data || prepPlanQuery.data.tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No preparation tasks yet — extract requirements first.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {prepPlanQuery.data.tasks.map((task) => (
                <li key={task.skill_slug} className="rounded-xl border border-border bg-card p-3">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-foreground">{task.skill_slug}</p>
                    {task.priority ? <Badge variant="outline">{JD_REQUIREMENT_PRIORITY_LABELS[task.priority]}</Badge> : null}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
                    {task.recommended_exercise_slugs.map((slug) => (
                      <Link key={slug} href={`/practice/${slug}`} className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                        Exercise: {slug}
                      </Link>
                    ))}
                    {task.recommended_case_slugs.map((slug) => (
                      <Link key={slug} href={`/case-studies/${slug}`} className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                        Case: {slug}
                      </Link>
                    ))}
                    {task.recommended_project_slugs.map((slug) => (
                      <Link key={slug} href="/projects" className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                        Project: {slug}
                      </Link>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Interview Plan</CardTitle>
        </CardHeader>
        <CardContent>
          {interviewPlanQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : !interviewPlanQuery.data ? (
            <p className="text-sm text-muted-foreground">No interview plan yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-1.5">
                {interviewPlanQuery.data.focus_interview_types.map((type) => (
                  <Badge key={type} variant="outline">{type.replace(/_/g, " ")}</Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">{interviewPlanQuery.data.note}</p>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {interviewPlanQuery.data.suggested_question_slugs.map((slug) => (
                  <Link key={slug} href={`/interview/questions/${slug}`} className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                    {slug}
                  </Link>
                ))}
                {interviewPlanQuery.data.suggested_case_slugs.map((slug) => (
                  <Link key={slug} href={`/case-studies/${slug}`} className="rounded-md border border-border px-2 py-1 text-primary hover:underline">
                    {slug}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preparation Workspace</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {!workspace ? (
            <Button
              className="self-start"
              onClick={() => createWorkspace.mutate({ job_description_id: jobDescriptionId })}
              disabled={createWorkspace.isPending}
            >
              Prepare for This Job
            </Button>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <label className="text-xs text-muted-foreground" htmlFor="workspace-status">Status</label>
                <Select
                  id="workspace-status"
                  value={workspace.status}
                  onChange={(event) =>
                    updateWorkspace.mutate({ id: workspace.id, status: event.target.value as JobPrepStatus })
                  }
                  className="w-40"
                >
                  {JOB_PREP_STATUS_ORDER.map((status) => (
                    <option key={status} value={status}>{JOB_PREP_STATUS_LABELS[status]}</option>
                  ))}
                </Select>
              </div>
              <Textarea
                defaultValue={workspace.notes ?? ""}
                placeholder="Notes on how you're preparing for this job..."
                rows={3}
                aria-label="Preparation notes"
                onBlur={(event) => updateWorkspace.mutate({ id: workspace.id, notes: event.target.value })}
              />
              <div className="flex flex-col gap-1.5">
                {workspace.checklist.map((item, index) => (
                  <label key={`${item.label}-${index}`} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={item.is_done} onChange={() => toggleChecklistItem(index)} />
                    <span className={item.is_done ? "text-muted-foreground line-through" : "text-foreground"}>{item.label}</span>
                  </label>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={checklistDraft}
                  onChange={(event) => setChecklistDraft(event.target.value)}
                  placeholder="Add a checklist item..."
                  aria-label="New checklist item"
                />
                <Button variant="outline" onClick={addChecklistItem} disabled={!checklistDraft.trim() || updateWorkspace.isPending}>
                  Add
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
