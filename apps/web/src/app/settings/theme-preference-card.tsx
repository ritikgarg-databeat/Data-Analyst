"use client";

import { Moon, SunMedium, SunMoon } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMounted } from "@/lib/use-mounted";
import { cn } from "@/lib/utils";

const OPTIONS = [
  { value: "light", label: "Light", icon: SunMedium },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: SunMoon },
] as const;

export function ThemePreferenceCard() {
  const { theme, setTheme } = useTheme();
  const mounted = useMounted();

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>Choose how Personal Data Analyst Lab looks on this device.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Theme preference">
          {OPTIONS.map((option) => {
            const isActive = mounted && theme === option.value;
            return (
              <Button
                key={option.value}
                type="button"
                variant={isActive ? "default" : "outline"}
                size="sm"
                role="radio"
                aria-checked={isActive}
                className={cn("gap-2")}
                onClick={() => setTheme(option.value)}
              >
                <option.icon className="size-4" />
                {option.label}
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
