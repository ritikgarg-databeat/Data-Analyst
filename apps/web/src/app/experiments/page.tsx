"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ExperimentsWorkspace } from "@/components/features/experiments/experiments-workspace";

export default function ExperimentsPage() {
  return (
    <div>
      <PageHeader
        title="Experimentation"
        subtitle="Plan sample size, analyze A/B test results, and see statistical power made intuitive through simulation."
      />
      <ExperimentsWorkspace />
    </div>
  );
}
