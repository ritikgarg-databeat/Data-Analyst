import { Library } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { PhasePlaceholder } from "@/components/shared/phase-placeholder";

export default function ResourcesPage() {
  return (
    <div>
      <PageHeader title="Resources" subtitle="Curated external references, cheat sheets, and further reading." />
      <PhasePlaceholder
        icon={Library}
        title="The resource library is on the way"
        description="A curated collection of docs, cheat sheets, and reading tied directly into the curriculum."
        phase={2}
      />
    </div>
  );
}
