import { Check } from "lucide-react";
import type { Project } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { Progress } from "@/components/ui/progress";
import { useUpdateMilestone } from "@/features/projects/use-projects";
import { cn } from "@/lib/utils";

/** Milestones checklist — `project.milestones[]` comes pre-ordered by
 * `display_order` from the API; toggling one PATCHes it and refreshes the
 * whole project (so the progress bar below updates immediately). */
export function ProjectMilestonesTab({ project }: { project: Project }) {
  const updateMilestone = useUpdateMilestone(project.id);
  const milestones = project.milestones;
  const completed = milestones.filter((m) => m.is_completed).length;
  const total = milestones.length;
  const pct = total > 0 ? (completed / total) * 100 : 0;

  if (total === 0) {
    return (
      <EmptyState
        icon={Check}
        title="No milestones"
        description="This project has no milestones — free-form projects started from a dataset don't seed any; template-based projects do."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-foreground">Progress</span>
          <span className="text-muted-foreground">
            {completed} / {total} completed
          </span>
        </div>
        <Progress value={pct} />
      </div>

      <ul className="flex flex-col gap-2">
        {milestones.map((milestone) => (
          <li key={milestone.id} className="rounded-xl border border-border bg-card p-4">
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                className="mt-1 size-4"
                checked={milestone.is_completed}
                disabled={updateMilestone.isPending}
                onChange={(event) =>
                  updateMilestone.mutate({
                    milestoneId: milestone.id,
                    payload: { is_completed: event.target.checked },
                  })
                }
              />
              <div>
                <p className={cn("text-sm font-medium text-foreground", milestone.is_completed && "line-through opacity-70")}>
                  {milestone.title}
                </p>
                {milestone.description ? (
                  <p className="mt-0.5 text-sm text-muted-foreground">{milestone.description}</p>
                ) : null}
              </div>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
