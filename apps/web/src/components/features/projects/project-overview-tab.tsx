import type { Project, ProjectTemplate } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProjectOverviewTabProps {
  project: Project;
  template: ProjectTemplate | undefined;
}

export function ProjectOverviewTab({ project, template }: ProjectOverviewTabProps) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm text-foreground">
          {project.description ? <p>{project.description}</p> : null}
          {project.objective ? (
            <div>
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Objective</p>
              <p className="mt-1 whitespace-pre-line">{project.objective}</p>
            </div>
          ) : null}
          {project.business_context ? (
            <div>
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Business context</p>
              <p className="mt-1 whitespace-pre-line">{project.business_context}</p>
            </div>
          ) : null}
          {!project.description && !project.objective && !project.business_context ? (
            <p className="text-muted-foreground">No description yet.</p>
          ) : null}
        </CardContent>
      </Card>

      {project.requirements.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Requirements</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5 text-sm text-foreground">
              {project.requirements.map((requirement, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-0.5 text-muted-foreground">•</span>
                  <span>{requirement}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      {template ? (
        <Card>
          <CardHeader>
            <CardTitle>Source template</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-foreground">
            <p className="font-medium">{template.title}</p>
            <p className="mt-1 whitespace-pre-line text-muted-foreground">{template.objective}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
