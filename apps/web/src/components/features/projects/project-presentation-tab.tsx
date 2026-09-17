"use client";

import { useState } from "react";
import type { Project } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateProjectPresentation } from "@/features/projects/use-projects";

import { PRESENTATION_SLIDES } from "./project-format";

type Slide = Record<string, string>;

function initialSlides(project: Project): Slide[] {
  if (project.presentation.length > 0) {
    return project.presentation.map((s) => ({ slide: s.slide ?? "", content: s.content ?? "" }));
  }
  return PRESENTATION_SLIDES.map((slide) => ({ slide, content: "" }));
}

/**
 * Final Presentation / storyboard editor (spec section 40) — a structured,
 * fixed 9-slide storyboard, NOT a full slide-deck builder. Stored as
 * `presentation: Array<{slide, content}>`; saved as a whole array on each
 * slide's blur (no per-slide endpoint). Local, controlled state (not
 * recomputed from `project` at blur time) so editing several slides quickly
 * doesn't lose an earlier slide's edit to a race with its own still-in-flight
 * save.
 */
export function ProjectPresentationTab({ project }: { project: Project }) {
  const updatePresentation = useUpdateProjectPresentation(project.id);
  // Local, controlled state — see ProjectDocumentationTab's docstring for
  // why there's no reset-on-prop-change effect.
  const [slides, setSlides] = useState<Slide[]>(() => initialSlides(project));

  function handleBlur(index: number, content: string) {
    setSlides((prev) => {
      const next = prev.map((s, i) => (i === index ? { ...s, content } : s));
      updatePresentation.mutate({ presentation: next });
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        A structured storyboard for the final presentation — 9 fixed slide blocks, not a full slide-deck editor.
      </p>
      {slides.map((slide, index) => (
        <Card key={slide.slide || index}>
          <CardHeader>
            <CardTitle>
              {index + 1}. {slide.slide}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={slide.content}
              onChange={(event) =>
                setSlides((prev) => prev.map((s, i) => (i === index ? { ...s, content: event.target.value } : s)))
              }
              onBlur={(event) => handleBlur(index, event.target.value)}
              rows={4}
              placeholder={`Write the "${slide.slide}" slide's content...`}
            />
          </CardContent>
        </Card>
      ))}
      {updatePresentation.isError ? (
        <p className="text-xs text-destructive">Couldn&apos;t save — check your connection and try again.</p>
      ) : null}
    </div>
  );
}
