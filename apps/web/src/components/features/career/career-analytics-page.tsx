"use client";

import { useState } from "react";
import { Download, FileText, Search, Trash2, Trophy } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { CAREER_MILESTONE_TYPE_LABELS, CAREER_READINESS_LEVEL_LABELS, READINESS_DISCLAIMER } from "@/features/career/constants";
import {
  useAchievements,
  useCareerAssessmentHistory,
  useCareerNotes,
  useCareerReport,
  useCareerTimeline,
  useCareerWeeklyReview,
  useCreateCareerNote,
  useDeleteCareerNote,
  useEarnedAchievements,
  useUpdateCareerNote,
} from "@/features/career/use-career";

function downloadText(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function CareerAnalyticsPage() {
  const historyQuery = useCareerAssessmentHistory();
  const weeklyReviewQuery = useCareerWeeklyReview();
  const timelineQuery = useCareerTimeline();
  const achievementsQuery = useAchievements();
  const earnedAchievementsQuery = useEarnedAchievements();

  const [noteSearch, setNoteSearch] = useState("");
  const notesQuery = useCareerNotes(noteSearch || undefined);
  const createNote = useCreateCareerNote();
  const updateNote = useUpdateCareerNote();
  const deleteNote = useDeleteCareerNote();
  const [noteTopic, setNoteTopic] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);

  const [reportOpen, setReportOpen] = useState(false);
  const reportQuery = useCareerReport(reportOpen);

  const earnedSlugs = new Set((earnedAchievementsQuery.data ?? []).map((ua) => ua.achievement.slug));

  function handleSaveNote() {
    if (!noteBody.trim()) return;
    if (editingNoteId) {
      updateNote.mutate(
        { id: editingNoteId, topic: noteTopic || undefined, body: noteBody },
        { onSuccess: () => { setEditingNoteId(null); setNoteTopic(""); setNoteBody(""); } },
      );
    } else {
      createNote.mutate(
        { topic: noteTopic || undefined, body: noteBody },
        { onSuccess: () => { setNoteTopic(""); setNoteBody(""); } },
      );
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Readiness History</CardTitle>
        </CardHeader>
        <CardContent>
          {historyQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : historyQuery.isError ? (
            <ErrorState message="We couldn't load your readiness history." retry={() => void historyQuery.refetch()} />
          ) : (historyQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No assessments computed yet. Compute one from the Career Overview page.</p>
          ) : (
            <>
              <ul className="flex flex-col gap-2">
                {(historyQuery.data ?? []).map((assessment) => (
                  <li key={assessment.id} className="flex items-center justify-between gap-2 rounded-md border border-border bg-card p-2 text-sm">
                    <span className="text-muted-foreground">{new Date(assessment.computed_at).toLocaleDateString()}</span>
                    <span className="font-medium text-foreground">{assessment.overall_score.toFixed(0)}%</span>
                    <Badge variant="outline">{CAREER_READINESS_LEVEL_LABELS[assessment.overall_readiness_level]}</Badge>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[11px] text-muted-foreground">{READINESS_DISCLAIMER}</p>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Weekly Review</CardTitle>
        </CardHeader>
        <CardContent>
          {weeklyReviewQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-16" />
          ) : weeklyReviewQuery.isError ? (
            <ErrorState
              title="Unable to load your weekly review"
              message="We couldn't reach the API to load this week's activity."
              retry={() => void weeklyReviewQuery.refetch()}
            />
          ) : weeklyReviewQuery.data ? (
            <div className="flex flex-col gap-2 text-sm">
              <p className="text-muted-foreground">
                {new Date(weeklyReviewQuery.data.period_start).toLocaleDateString()} –{" "}
                {new Date(weeklyReviewQuery.data.period_end).toLocaleDateString()}
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                <div><p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.exercises_attempted}</p><p className="text-xs text-muted-foreground">Attempted</p></div>
                <div><p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.exercises_passed}</p><p className="text-xs text-muted-foreground">Passed</p></div>
                <div><p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.cases_completed}</p><p className="text-xs text-muted-foreground">Cases</p></div>
                <div><p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.projects_completed}</p><p className="text-xs text-muted-foreground">Projects</p></div>
                <div><p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.interviews_completed}</p><p className="text-xs text-muted-foreground">Interviews</p></div>
              </div>
              {weeklyReviewQuery.data.weak_skill_slugs.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {weeklyReviewQuery.data.weak_skill_slugs.map((slug) => (
                    <Badge key={slug} variant="destructive">{slug}</Badge>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Career Progress Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {timelineQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : timelineQuery.isError ? (
            <ErrorState message="We couldn't load your timeline." retry={() => void timelineQuery.refetch()} />
          ) : (timelineQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No milestones yet.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {(timelineQuery.data ?? []).map((milestone) => (
                <li key={milestone.id} className="flex items-center justify-between gap-2 text-sm">
                  <div>
                    <p className="text-foreground">{milestone.title}</p>
                    {milestone.detail ? <p className="text-xs text-muted-foreground">{milestone.detail}</p> : null}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant="outline">{CAREER_MILESTONE_TYPE_LABELS[milestone.milestone_type]}</Badge>
                    <span className="text-xs text-muted-foreground">{new Date(milestone.achieved_at).toLocaleDateString()}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5">
            <Trophy className="size-4 text-primary" aria-hidden="true" />
            Achievements
          </CardTitle>
        </CardHeader>
        <CardContent>
          {achievementsQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : achievementsQuery.isError ? (
            <ErrorState message="We couldn't load achievements." retry={() => void achievementsQuery.refetch()} />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {(achievementsQuery.data ?? []).map((achievement) => {
                const earned = earnedSlugs.has(achievement.slug);
                return (
                  <div
                    key={achievement.id}
                    className={`rounded-xl border p-3 ${earned ? "border-primary bg-primary/5" : "border-border bg-card opacity-60"}`}
                  >
                    <p className="font-medium text-foreground">{achievement.title}</p>
                    <p className="text-xs text-muted-foreground">{achievement.description}</p>
                    {earned ? <Badge className="mt-2">Earned</Badge> : <Badge variant="outline" className="mt-2">Not yet earned</Badge>}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Career Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input value={noteSearch} onChange={(event) => setNoteSearch(event.target.value)} placeholder="Search notes..." className="pl-8" aria-label="Search notes" />
          </div>

          {notesQuery.isLoading ? (
            <LoadingState count={2} itemClassName="h-16" />
          ) : notesQuery.isError ? (
            <ErrorState message="We couldn't load your notes." retry={() => void notesQuery.refetch()} />
          ) : (notesQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No notes yet.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {(notesQuery.data ?? []).map((note) => (
                <li key={note.id} className="rounded-md border border-border bg-card p-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    {note.topic ? <Badge variant="outline">{note.topic}</Badge> : <span />}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditingNoteId(note.id);
                          setNoteTopic(note.topic ?? "");
                          setNoteBody(note.body);
                        }}
                      >
                        Edit
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => deleteNote.mutate(note.id)} disabled={deleteNote.isPending} aria-label="Delete note">
                        <Trash2 className="size-3.5" aria-hidden="true" />
                      </Button>
                    </div>
                  </div>
                  <p className="mt-1 whitespace-pre-wrap text-foreground">{note.body}</p>
                </li>
              ))}
            </ul>
          )}

          <div className="flex flex-col gap-2 rounded-md border border-border p-3">
            <Input value={noteTopic} onChange={(event) => setNoteTopic(event.target.value)} placeholder="Topic (optional)" aria-label="Note topic" />
            <Textarea value={noteBody} onChange={(event) => setNoteBody(event.target.value)} placeholder="Note..." rows={2} aria-label="Note body" />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveNote} disabled={!noteBody.trim() || createNote.isPending || updateNote.isPending}>
                {editingNoteId ? "Save Changes" : "Add Note"}
              </Button>
              {editingNoteId ? (
                <Button size="sm" variant="outline" onClick={() => { setEditingNoteId(null); setNoteTopic(""); setNoteBody(""); }}>
                  Cancel
                </Button>
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-1.5">
              <FileText className="size-4 text-primary" aria-hidden="true" />
              Career Report
            </CardTitle>
            {!reportOpen ? (
              <Button size="sm" onClick={() => setReportOpen(true)}>
                Open Career Report
              </Button>
            ) : null}
          </div>
        </CardHeader>
        {reportOpen ? (
          <CardContent className="flex flex-col gap-3">
            {reportQuery.isLoading ? (
              <LoadingState count={1} itemClassName="h-32" />
            ) : reportQuery.isError || !reportQuery.data ? (
              <ErrorState message="We couldn't generate your career report." retry={() => void reportQuery.refetch()} />
            ) : (
              <>
                <p className="text-xs text-muted-foreground">
                  Generated {new Date(reportQuery.data.generated_at).toLocaleString()}
                </p>
                <p className="text-sm text-foreground">
                  {reportQuery.data.target_roles.length} target role(s) · {reportQuery.data.active_goals.length} active goal(s) ·{" "}
                  {reportQuery.data.achievement_count} achievement(s)
                </p>
                {reportQuery.data.latest_assessment ? (
                  <p className="text-sm text-foreground">
                    Latest readiness: {reportQuery.data.latest_assessment.overall_score.toFixed(0)}% (
                    {CAREER_READINESS_LEVEL_LABELS[reportQuery.data.latest_assessment.overall_readiness_level]})
                  </p>
                ) : null}
                {reportQuery.data.top_skill_gaps.length > 0 ? (
                  <div>
                    <p className="text-xs font-medium text-foreground">Top skill gaps</p>
                    <div className="flex flex-wrap gap-1.5">
                      {reportQuery.data.top_skill_gaps.map((gap) => (
                        <Badge key={gap.skill_slug} variant="destructive">{gap.name}</Badge>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => downloadText("career-report.json", JSON.stringify(reportQuery.data, null, 2), "application/json")}
                  >
                    <Download className="size-3.5" aria-hidden="true" />
                    Download JSON
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      downloadText(
                        "career-report.txt",
                        [
                          `Career Report — generated ${reportQuery.data.generated_at}`,
                          `Target roles: ${reportQuery.data.target_roles.map((r) => r.custom_title ?? r.role_template?.title ?? "Untitled").join(", ") || "none"}`,
                          `Latest readiness: ${reportQuery.data.latest_assessment ? `${reportQuery.data.latest_assessment.overall_score.toFixed(0)}%` : "not computed"}`,
                          `Top skill gaps: ${reportQuery.data.top_skill_gaps.map((g) => g.name).join(", ") || "none"}`,
                          `Active goals: ${reportQuery.data.active_goals.map((g) => g.title).join(", ") || "none"}`,
                          `Achievements: ${reportQuery.data.achievement_count}`,
                          "",
                          "This report reflects platform-estimated readiness and is not a hiring guarantee.",
                        ].join("\n"),
                        "text/plain",
                      )
                    }
                  >
                    <Download className="size-3.5" aria-hidden="true" />
                    Download Text
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        ) : null}
      </Card>
    </div>
  );
}
