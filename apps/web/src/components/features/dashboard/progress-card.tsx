import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import type { SectionColor } from "@data-analyst-lab/shared";
import { motion } from "framer-motion";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { sectionColorClasses } from "@/lib/section-colors";
import { cn } from "@/lib/utils";

interface ProgressCardProps {
  icon: LucideIcon;
  label: string;
  value: ReactNode;
  hint?: string;
  color?: SectionColor;
  className?: string;
}

/** Single stat card used in the dashboard's top progress row. */
export function ProgressCard({ icon: Icon, label, value, hint, color = "violet", className }: ProgressCardProps) {
  const classes = sectionColorClasses(color);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <Card className={cn("card-hover", className)}>
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
          <div className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg", classes.chip)}>
            <Icon className="size-4.5" aria-hidden="true" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold tracking-tight text-foreground">{value}</div>
          {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}
