"use client";

import { PageHeader } from "@/components/shared/page-header";
import { PortfolioPage } from "@/components/features/career/portfolio-page";

export default function CareerPortfolioPage() {
  return (
    <div>
      <PageHeader
        title="Portfolio"
        subtitle="Build a portfolio of projects, cases, and certifications — every item defaults to Private until you choose otherwise."
      />
      <PortfolioPage />
    </div>
  );
}
