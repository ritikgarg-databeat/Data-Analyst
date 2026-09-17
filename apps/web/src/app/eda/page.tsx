"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EdaLauncher } from "@/components/features/eda/eda-launcher";
import { useDatasets } from "@/features/datasets/use-datasets";
import { useCreateEdaWorkspace, useEdaWorkspaces } from "@/features/eda/use-eda";

/** Handles the "Open EDA" deep link from a dataset's page (`/eda?dataset=<id>`) —
 * reuses an existing workspace for that dataset if one exists, otherwise creates one. */
function DatasetDeepLink({ datasetId }: { datasetId: string }) {
  const router = useRouter();
  const workspacesQuery = useEdaWorkspaces();
  const datasetQuery = useDatasets();
  const createWorkspace = useCreateEdaWorkspace();
  const started = useRef(false);

  useEffect(() => {
    if (started.current || !workspacesQuery.data) return;
    const existing = workspacesQuery.data.find((w) => w.dataset_id === datasetId);
    if (existing) {
      started.current = true;
      router.replace(`/eda/${existing.id}`);
      return;
    }
    const dataset = datasetQuery.data?.find((d) => d.id === datasetId);
    if (!dataset) return;
    started.current = true;
    createWorkspace.mutate(
      { dataset_id: dataset.id, name: `${dataset.name} exploration` },
      { onSuccess: (workspace) => router.replace(`/eda/${workspace.id}`) },
    );
  }, [workspacesQuery.data, datasetQuery.data, datasetId, router, createWorkspace]);

  return <LoadingState count={1} itemClassName="h-96" />;
}

function EdaLandingContent() {
  const searchParams = useSearchParams();
  const datasetId = searchParams.get("dataset");
  return datasetId ? <DatasetDeepLink datasetId={datasetId} /> : <EdaLauncher />;
}

export default function EdaLandingPage() {
  return (
    <div>
      <PageHeader
        title="EDA Workspace"
        subtitle="Combine schema, statistics, charts, notes, and findings for a dataset in one place."
      />
      <Suspense fallback={<LoadingState count={1} itemClassName="h-96" />}>
        <EdaLandingContent />
      </Suspense>
    </div>
  );
}
