import type { LucideIcon } from "lucide-react";

import { EmptyState } from "./empty-state";

interface PhasePlaceholderProps {
  icon: LucideIcon;
  title: string;
  description: string;
  /** Roadmap phase (or phase range, e.g. "3-4") that will implement this surface. */
  phase: number | string;
}

/**
 * Full-page "not built yet" state for routes that are scoped to a later
 * phase of the 12-phase roadmap. Intentionally premium-looking, not a stub.
 */
export function PhasePlaceholder({ icon, title, description, phase }: PhasePlaceholderProps) {
  return (
    <EmptyState
      icon={icon}
      title={title}
      description={`${description} This arrives in Phase ${phase} of the roadmap.`}
      className="min-h-[55vh]"
      action={{ label: `Planned for Phase ${phase}`, disabled: true }}
    />
  );
}
