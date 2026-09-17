"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { SqlPlayground } from "@/components/features/sql-lab/sql-playground";

function SqlLabContent() {
  // "Open in SQL Lab" from a dataset's page (section 32 of the Phase 5 spec)
  // deep-links here as `?database=<slug>` to pre-select it.
  const searchParams = useSearchParams();
  return <SqlPlayground initialDatabase={searchParams.get("database") ?? undefined} />;
}

export default function SqlLabPage() {
  return (
    <div>
      <PageHeader
        title="SQL Lab"
        subtitle="Run real queries against practice databases — explore the schema, execute, and save your work."
      />
      <Suspense fallback={<LoadingState count={1} itemClassName="h-96" />}>
        <SqlLabContent />
      </Suspense>
    </div>
  );
}
