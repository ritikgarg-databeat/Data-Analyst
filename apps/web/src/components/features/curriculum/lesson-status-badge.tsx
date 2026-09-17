import { CheckCircle2, Circle, PlayCircle } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { LessonProgressStatus } from "@data-analyst-lab/shared";

import { Badge, type BadgeProps } from "@/components/ui/badge";

const STATUS_CONFIG: Record<
  LessonProgressStatus,
  { label: string; variant: BadgeProps["variant"]; icon: LucideIcon }
> = {
  NOT_STARTED: { label: "Not Started", variant: "outline", icon: Circle },
  IN_PROGRESS: { label: "In Progress", variant: "warning", icon: PlayCircle },
  COMPLETED: { label: "Completed", variant: "success", icon: CheckCircle2 },
};

interface LessonStatusBadgeProps {
  status: LessonProgressStatus;
  className?: string;
}

export function LessonStatusBadge({ status, className }: LessonStatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className={className}>
      <Icon aria-hidden="true" />
      {config.label}
    </Badge>
  );
}
