import Link from "next/link";
import { ChevronRight } from "lucide-react";

interface LessonBreadcrumbProps {
  domainSlug: string;
  domainName: string;
  moduleSlug: string;
  moduleTitle: string;
  lessonTitle: string;
}

/** Four-level breadcrumb used only by the lesson reader (Learn > Domain > Module > Lesson). */
export function LessonBreadcrumb({
  domainSlug,
  domainName,
  moduleSlug,
  moduleTitle,
  lessonTitle,
}: LessonBreadcrumbProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="mb-4 flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground"
    >
      <Link href="/learn" className="hover:text-foreground hover:underline">
        Learn
      </Link>
      <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
      <Link href={`/learn/${domainSlug}`} className="hover:text-foreground hover:underline">
        {domainName}
      </Link>
      <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
      <Link href={`/learn/${domainSlug}/${moduleSlug}`} className="hover:text-foreground hover:underline">
        {moduleTitle}
      </Link>
      <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />
      <span aria-current="page" className="font-medium text-foreground">
        {lessonTitle}
      </span>
    </nav>
  );
}
