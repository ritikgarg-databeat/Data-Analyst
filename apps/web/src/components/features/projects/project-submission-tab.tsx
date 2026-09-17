"use client";

import { useState } from "react";
import type { CaseFeedback, Project, ProjectTemplate, ReflectionPayload } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { useSaveProjectReflection, useSubmitProject } from "@/features/projects/use-projects";

interface ProjectSubmissionTabProps {
  project: Project;
  template: ProjectTemplate | undefined;
}

const REFLECTION_FIELDS: Array<{ key: keyof ReflectionPayload; label: string }> = [
  { key: "what_learned", label: "What did you learn?" },
  { key: "what_difficult", label: "What was difficult?" },
  { key: "what_differently", label: "What would you do differently?" },
  { key: "skill_improved", label: "What skill did this improve?" },
  { key: "what_review", label: "What should you review?" },
];

const FEEDBACK_BUCKETS: Array<{ key: keyof CaseFeedback; label: string }> = [
  { key: "what_went_well", label: "What went well" },
  { key: "what_missed", label: "What was missed" },
  { key: "technical_issues", label: "Technical issues" },
  { key: "business_reasoning_issues", label: "Business reasoning" },
  { key: "communication_issues", label: "Communication" },
];

/**
 * Submission (spec sections 41-42) — a rubric self-assessment checklist built
 * from the source `ProjectTemplate.rubric` (only template-based projects can
 * submit; there's no rubric to score a free-form project against). After
 * submission, shows the real computed score/feedback — same shape as a
 * Case's, except here it's nested at `project.score.feedback` rather than a
 * sibling field (see app/services/project_service.py's `submit_project`).
 */
export function ProjectSubmissionTab({ project, template }: ProjectSubmissionTabProps) {
  const submitProject = useSubmitProject(project.id);
  const saveReflection = useSaveProjectReflection(project.id);
  const [selections, setSelections] = useState<Record<string, string[]>>(project.rubric_selections ?? {});
  // Local, controlled state (see the Case Workspace's frame/recommend/submit
  // tabs for why — reading straight from `project` at blur time races
  // against an earlier field's still-in-flight save when tabbing through
  // several fields quickly, silently dropping edits).
  const [reflection, setReflection] = useState<ReflectionPayload>(
    project.reflection ?? {
      what_learned: "",
      what_difficult: "",
      what_differently: "",
      skill_improved: "",
      what_review: "",
    },
  );

  if (!project.template_id) {
    return (
      <Card>
        <CardContent className="py-5 text-sm text-muted-foreground">
          This is a free-form project (not started from a template), so there&apos;s no rubric to submit
          against — rubric-based scoring is only available for template-based projects.
        </CardContent>
      </Card>
    );
  }

  if (!template) {
    return <p className="text-sm text-muted-foreground">Loading rubric...</p>;
  }

  const toggleCriterion = (category: string, criterion: string, checked: boolean) => {
    setSelections((prev) => {
      const current = new Set(prev[category] ?? []);
      if (checked) current.add(criterion);
      else current.delete(criterion);
      return { ...prev, [category]: Array.from(current) };
    });
  };

  const scored = project.status === "COMPLETED" && project.score;

  const handleReflectionBlur = (key: keyof ReflectionPayload, value: string) => {
    setReflection((prev) => {
      const next = { ...prev, [key]: value };
      saveReflection.mutate({ reflection: next });
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-4">
      {!scored ? (
        <>
          {template.rubric.map((category) => (
            <Card key={category.category}>
              <CardHeader>
                <CardTitle>
                  {category.category}{" "}
                  <span className="font-normal text-muted-foreground">({category.weight}%)</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="flex flex-col gap-2">
                  {category.criteria.map((criterion) => (
                    <li key={criterion.criterion}>
                      <label className="flex cursor-pointer items-start gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="mt-0.5 size-4"
                          checked={(selections[category.category] ?? []).includes(criterion.criterion)}
                          onChange={(event) =>
                            toggleCriterion(category.category, criterion.criterion, event.target.checked)
                          }
                        />
                        <span className="text-foreground">{criterion.criterion}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}

          <Button
            onClick={() => submitProject.mutate({ rubric_selections: selections })}
            disabled={submitProject.isPending}
            className="self-start"
          >
            {submitProject.isPending ? "Submitting..." : "Submit project"}
          </Button>
          {submitProject.isError ? (
            <p className="text-xs text-destructive">Couldn&apos;t submit — check your connection and try again.</p>
          ) : null}
        </>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Score: {project.score!.overall.toFixed(1)}%</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-3">
              {project.score!.categories.map((cat) => (
                <div key={cat.category}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-foreground">{cat.category}</span>
                    <span className="text-muted-foreground">{cat.pct.toFixed(0)}%</span>
                  </div>
                  <Progress value={cat.pct} />
                </div>
              ))}
            </div>

            {project.score!.feedback ? (
              <div className="flex flex-col gap-3 text-sm">
                {FEEDBACK_BUCKETS.map(({ key, label }) => {
                  const items = project.score!.feedback![key];
                  if (!items || items.length === 0) return null;
                  return (
                    <div key={key}>
                      <p className="font-medium text-foreground">{label}</p>
                      <ul className="list-inside list-disc text-muted-foreground">
                        {items.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Reflection</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {REFLECTION_FIELDS.map((field) => (
            <div key={field.key} className="flex flex-col gap-1">
              <Label htmlFor={`project-reflection-${field.key}`}>{field.label}</Label>
              <Textarea
                id={`project-reflection-${field.key}`}
                value={reflection[field.key]}
                onChange={(event) => setReflection((prev) => ({ ...prev, [field.key]: event.target.value }))}
                onBlur={(event) => handleReflectionBlur(field.key, event.target.value)}
                rows={2}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
