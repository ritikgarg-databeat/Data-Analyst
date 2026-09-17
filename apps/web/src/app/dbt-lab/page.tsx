"use client";

import { PageHeader } from "@/components/shared/page-header";
import { DbtLabWorkspace } from "@/components/features/dbt-lab/dbt-lab-workspace";

export default function DbtLabPage() {
  return (
    <div>
      <PageHeader
        title="dbt Lab"
        subtitle="A real, local dbt Core project running against DuckDB — run, test, and explore the actual project at dbt/."
      />
      <DbtLabWorkspace />
    </div>
  );
}
