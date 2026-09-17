import Link from "next/link";
import { ClipboardCheck } from "lucide-react";
import type { Module } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

import { DifficultyBadge } from "./difficulty-badge";

interface ModuleCardProps {
  module: Module;
  domainSlug: string;
  orderNumber: number;
}

export function ModuleCard({ module, domainSlug, orderNumber }: ModuleCardProps) {
  const rounded = Math.round(module.progress_percent);

  return (
    <Link
      href={`/learn/${domainSlug}/${module.slug}`}
      className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardHeader className="flex-row items-start gap-3">
          <div
            className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-sm font-semibold text-accent-foreground"
            aria-hidden="true"
          >
            {orderNumber}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="text-base">{module.title}</CardTitle>
              <DifficultyBadge difficulty={module.difficulty} />
              {module.has_assessment ? (
                <Badge variant="secondary" className="gap-1">
                  <ClipboardCheck aria-hidden="true" />
                  Assessment available
                </Badge>
              ) : null}
            </div>
            <CardDescription className="mt-1">
              {module.lesson_count} {module.lesson_count === 1 ? "lesson" : "lessons"} · {module.estimated_minutes} min
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-1.5">
          {module.description ? (
            <p className="line-clamp-2 text-sm text-muted-foreground">{module.description}</p>
          ) : null}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{rounded}%</span>
          </div>
          <Progress value={rounded} aria-label={`${module.title} progress: ${rounded}%`} />
        </CardContent>
      </Card>
    </Link>
  );
}
