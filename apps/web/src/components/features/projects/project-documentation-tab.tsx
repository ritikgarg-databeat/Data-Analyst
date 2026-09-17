"use client";

import { useState } from "react";
import type { Project } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateProjectDocumentation } from "@/features/projects/use-projects";

import { DOCUMENTATION_SECTIONS } from "./project-format";

/**
 * Documentation editor (spec section 34) — 9 fixed sections saved as a single
 * `Record<string,string>` object; the API has no per-section endpoint, so
 * each field's blur PATCHes the whole object merged with its latest value.
 * Local, controlled state (not read from `project` at blur time) so tabbing
 * through several sections quickly doesn't lose an earlier section's edit to
 * a race with its own still-in-flight save.
 */
export function ProjectDocumentationTab({ project }: { project: Project }) {
  const updateDocumentation = useUpdateProjectDocumentation(project.id);
  // Local, controlled state — initialized once per mount (the Project
  // Workspace remounts per project via routing, so there's no need to
  // re-sync this on every refetch, which would risk clobbering an
  // in-flight local edit).
  const [documentation, setDocumentation] = useState<Record<string, string>>(project.documentation);

  function handleBlur(key: string, value: string) {
    setDocumentation((prev) => {
      const next = { ...prev, [key]: value };
      updateDocumentation.mutate({ documentation: next });
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {DOCUMENTATION_SECTIONS.map((section) => (
        <Card key={section.key}>
          <CardHeader>
            <CardTitle>{section.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={documentation[section.key] ?? ""}
              onChange={(event) =>
                setDocumentation((prev) => ({ ...prev, [section.key]: event.target.value }))
              }
              onBlur={(event) => handleBlur(section.key, event.target.value)}
              rows={4}
              placeholder={`Write the ${section.label.toLowerCase()} section...`}
            />
          </CardContent>
        </Card>
      ))}
      {updateDocumentation.isError ? (
        <p className="text-xs text-destructive">Couldn&apos;t save — check your connection and try again.</p>
      ) : null}
    </div>
  );
}
