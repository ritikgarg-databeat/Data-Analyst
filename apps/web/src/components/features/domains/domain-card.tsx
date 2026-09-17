import { BookOpen } from "lucide-react";
import type { Domain } from "@data-analyst-lab/shared";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { DynamicIcon } from "@/lib/icons";

interface DomainCardProps {
  domain: Domain;
  /** Progress percent (0-100). Defaults to 0 — real progress ships in a later phase. */
  progressPercent?: number;
}

export function DomainCard({ domain, progressPercent = 0 }: DomainCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="flex-row items-start gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <DynamicIcon iconName={domain.icon} fallback={BookOpen} className="size-5" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <CardTitle className="text-base">{domain.name}</CardTitle>
          <CardDescription>
            {domain.module_count} {domain.module_count === 1 ? "module" : "modules"}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {domain.description ? (
          <p className="line-clamp-2 text-sm text-muted-foreground">{domain.description}</p>
        ) : null}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
          <Progress value={progressPercent} aria-label={`${domain.name} progress: ${Math.round(progressPercent)}%`} />
        </div>
      </CardContent>
    </Card>
  );
}
