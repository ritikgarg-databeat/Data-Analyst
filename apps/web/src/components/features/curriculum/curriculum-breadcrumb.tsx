import Link from "next/link";
import { ChevronRight } from "lucide-react";

interface CurriculumBreadcrumbProps {
  domainSlug: string;
  domainName: string;
  /** Omit on the domain page; set to render "Learn > Domain > Module". */
  moduleTitle?: string;
}

/** Simple breadcrumb used by the curriculum browsing pages only (Learn > Domain [> Module]). */
export function CurriculumBreadcrumb({ domainSlug, domainName, moduleTitle }: CurriculumBreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="mb-4 flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
      <Link href="/learn" className="hover:text-foreground hover:underline">
        Learn
      </Link>
      <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
      {moduleTitle ? (
        <Link href={`/learn/${domainSlug}`} className="hover:text-foreground hover:underline">
          {domainName}
        </Link>
      ) : (
        <span aria-current="page" className="font-medium text-foreground">
          {domainName}
        </span>
      )}
      {moduleTitle ? (
        <>
          <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
          <span aria-current="page" className="font-medium text-foreground">
            {moduleTitle}
          </span>
        </>
      ) : null}
    </nav>
  );
}
