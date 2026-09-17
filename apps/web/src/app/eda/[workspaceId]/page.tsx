"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { EdaWorkspace } from "@/components/features/eda/eda-workspace";

export default function EdaWorkspacePage() {
  const params = useParams<{ workspaceId: string }>();

  return (
    <div>
      <nav className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link href="/eda" className="hover:text-foreground hover:underline">
          EDA
        </Link>
        <ChevronRight className="size-3.5" aria-hidden="true" />
        <span className="text-foreground">Workspace</span>
      </nav>
      <EdaWorkspace workspaceId={params.workspaceId} />
    </div>
  );
}
