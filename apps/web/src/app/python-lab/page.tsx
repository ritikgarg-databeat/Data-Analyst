"use client";

import { PageHeader } from "@/components/shared/page-header";
import { PythonLabPage } from "@/components/features/python-lab/python-lab-page";

export default function PythonLabRoutePage() {
  return (
    <div>
      <PageHeader
        title="Python Lab"
        subtitle="Run real Python against practice datasets in a Docker-sandboxed notebook — explore data, plot charts, and save your work."
      />
      <PythonLabPage />
    </div>
  );
}
