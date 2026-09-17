import Link from "next/link";
import type { ContinueLearningItem } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface ContinueLearningSectionProps {
  items: ContinueLearningItem[];
}

export function ContinueLearningSection({ items }: ContinueLearningSectionProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-card/50 px-6 py-14 text-center">
        <p className="text-sm font-medium text-foreground">Your learning journey starts here.</p>
        <Button asChild size="sm" variant="outline">
          <Link href="/learn">Browse the curriculum</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <Card key={item.lesson.id}>
          <CardContent className="space-y-2">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              {item.domain_name} · {item.module_title}
            </p>
            <p className="text-sm font-semibold text-foreground">{item.lesson.title}</p>
            <Progress
              value={item.progress_percent}
              aria-label={`${item.lesson.title} progress: ${Math.round(item.progress_percent)}%`}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
