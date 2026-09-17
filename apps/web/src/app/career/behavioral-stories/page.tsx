"use client";

import { PageHeader } from "@/components/shared/page-header";
import { BehavioralStoriesPage } from "@/components/features/career/behavioral-stories-page";

export default function CareerBehavioralStoriesPage() {
  return (
    <div>
      <PageHeader
        title="Behavioral Stories"
        subtitle="Keep STAR-format stories ready across the 12 real behavioral interview categories, and track which ones you still need."
      />
      <BehavioralStoriesPage />
    </div>
  );
}
