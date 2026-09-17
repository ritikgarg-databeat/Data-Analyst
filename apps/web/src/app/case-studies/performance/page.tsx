"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { CasePerformanceDashboard } from "@/components/features/case-studies/case-performance-dashboard";

export default function CasePerformancePage() {
  return (
    <div>
      <nav className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link href="/case-studies" className="hover:text-foreground hover:underline">
          Case Studies
        </Link>
        <ChevronRight className="size-3.5" aria-hidden="true" />
        <span className="text-foreground">My Performance</span>
      </nav>
      <PageHeader
        title="My Case Performance"
        subtitle="Deterministic personal analytics across every case you've attempted — no AI, just your own real history."
      />
      <CasePerformanceDashboard />
    </div>
  );
}
