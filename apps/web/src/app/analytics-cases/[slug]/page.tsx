"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { CaseDetail } from "@/components/features/analytics-cases/case-detail";

export default function AnalyticsCaseDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  return (
    <div>
      <nav className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link href="/analytics-cases" className="hover:text-foreground hover:underline">
          Analytics Cases
        </Link>
        <ChevronRight className="size-3.5" aria-hidden="true" />
        <span className="text-foreground">{slug}</span>
      </nav>

      <CaseDetail slug={slug} />
    </div>
  );
}
