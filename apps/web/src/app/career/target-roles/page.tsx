"use client";

import { PageHeader } from "@/components/shared/page-header";
import { TargetRolesPage } from "@/components/features/career/target-roles-page";

export default function CareerTargetRolesPage() {
  return (
    <div>
      <PageHeader
        title="Target Roles"
        subtitle="Pick the roles you're aiming for — from a template or a custom title — and mark one as primary."
      />
      <TargetRolesPage />
    </div>
  );
}
