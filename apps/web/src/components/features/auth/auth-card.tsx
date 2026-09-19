import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function AuthCard({ title, description, children, footer }: {
  title: string; description: string; children: React.ReactNode; footer?: React.ReactNode;
}) {
  return <main className="grid min-h-svh place-items-center bg-muted/30 p-4">
    <Card className="w-full max-w-md">
      <CardHeader><Link href="/" className="mb-3 text-sm font-semibold text-primary">Data Lab</Link>
        <CardTitle className="text-xl">{title}</CardTitle><CardDescription>{description}</CardDescription>
      </CardHeader><CardContent>{children}{footer ? <div className="mt-5 text-center text-sm text-muted-foreground">{footer}</div> : null}</CardContent>
    </Card>
  </main>;
}
