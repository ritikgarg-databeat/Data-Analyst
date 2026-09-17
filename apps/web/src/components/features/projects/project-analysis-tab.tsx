import Link from "next/link";
import { Code2, Microscope, Terminal } from "lucide-react";
import type { Project } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Section } from "@/components/shared/section";
import { FindingsPanel } from "@/components/features/findings/findings-panel";
import { HypothesisTracker } from "@/components/features/findings/hypothesis-tracker";
import { useDatasets } from "@/features/datasets/use-datasets";

/** Analysis / Findings — the shared Findings + Hypothesis Tracker (built for
 * both the Case Workspace and the Project Workspace via `owner`), plus deep
 * links out to the actual analysis tools (SQL Lab / Python Lab / EDA), which
 * live in their own parts of the app. */
export function ProjectAnalysisTab({ project }: { project: Project }) {
  const datasetsQuery = useDatasets();
  const firstProjectDataset = project.project_datasets[0];
  const linkedDataset = firstProjectDataset
    ? datasetsQuery.data?.find((d) => d.id === firstProjectDataset.dataset_id)
    : undefined;

  return (
    <div className="flex flex-col gap-6">
      <Section title="Analysis Tools" description="Open a tool in a new tab — your work there is saved independently and referenced back here as an artifact.">
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link
              href={linkedDataset ? `/sql-lab?database=${linkedDataset.slug}` : "/sql-lab"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Terminal className="size-4" aria-hidden="true" />
              SQL Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href="/python-lab" target="_blank" rel="noopener noreferrer">
              <Code2 className="size-4" aria-hidden="true" />
              Python Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link
              href={linkedDataset ? `/eda?dataset=${linkedDataset.id}` : "/eda"}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Microscope className="size-4" aria-hidden="true" />
              EDA Workspace
            </Link>
          </Button>
        </div>
      </Section>

      <Section title="Findings">
        <FindingsPanel owner={{ projectId: project.id }} />
      </Section>

      <Section title="Hypothesis Tracker">
        <HypothesisTracker owner={{ projectId: project.id }} />
      </Section>
    </div>
  );
}
