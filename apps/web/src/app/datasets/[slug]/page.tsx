"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { DatasetDetail } from "@/components/features/datasets/dataset-detail";

export default function DatasetDetailPage() {
  const params = useParams<{ slug: string }>();

  return (
    <div>
      <nav className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link href="/datasets" className="hover:text-foreground hover:underline">
          Datasets
        </Link>
        <ChevronRight className="size-3.5" aria-hidden="true" />
        <span className="text-foreground">{params.slug}</span>
      </nav>
      <DatasetDetail slug={params.slug} />
    </div>
  );
}
