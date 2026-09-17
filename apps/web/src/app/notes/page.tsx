import { NotebookPen } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { PhasePlaceholder } from "@/components/shared/phase-placeholder";

export default function NotesPage() {
  return (
    <div>
      <PageHeader title="Notes" subtitle="Your own notes, linked to lessons, skills, and exercises." />
      <PhasePlaceholder
        icon={NotebookPen}
        title="Personal notes are on the way"
        description="Freeform notes attached to any lesson or skill, searchable across the whole curriculum."
        phase={2}
      />
    </div>
  );
}
