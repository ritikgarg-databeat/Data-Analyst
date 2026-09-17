import { ShieldAlert } from "lucide-react";
import type { WeakArea } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { Progress } from "@/components/ui/progress";

interface WeakAreasSectionProps {
  items: WeakArea[];
}

export function WeakAreasSection({ items }: WeakAreasSectionProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="No weak areas identified yet"
        description="Keep practicing exercises — this surfaces skills worth extra attention once you've attempted a few."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <div key={item.skill.id} className="rounded-xl border border-border bg-card px-4 py-3">
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">{item.skill.name}</span>
            <span className="text-xs text-muted-foreground">{Math.round(item.mastery_score)}/100</span>
          </div>
          <Progress value={item.mastery_score} className="mb-2 h-1.5" />
          <p className="text-xs text-muted-foreground">{item.reason}</p>
        </div>
      ))}
    </div>
  );
}
