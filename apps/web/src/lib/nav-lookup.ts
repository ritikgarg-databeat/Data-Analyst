import { NAV_SECTIONS, sectionColor, type SectionColor } from "@data-analyst-lab/shared";

import { getLucideIcon } from "@/lib/icons";

interface NavMatch {
  icon: ReturnType<typeof getLucideIcon>;
  color: SectionColor;
}

const FLATTENED = NAV_SECTIONS.flatMap((section) =>
  section.items.map((item) => ({ ...item, color: sectionColor(section.label) })),
);

/**
 * Finds the nav item whose href best matches a given pathname (exact match,
 * or the longest href that's a real path-segment prefix — e.g. `/career/
 * resume/abc123` matches `/career/resume`, not the shorter `/career`), so a
 * dynamic sub-route (a specific case attempt, a specific job description)
 * can still inherit its section's icon/color without an explicit prop.
 */
export function findNavMatch(pathname: string | null): NavMatch | null {
  if (!pathname) return null;
  let best: (typeof FLATTENED)[number] | null = null;
  for (const item of FLATTENED) {
    const matches = pathname === item.href || pathname.startsWith(`${item.href}/`);
    if (matches && (!best || item.href.length > best.href.length)) {
      best = item;
    }
  }
  if (!best) return null;
  return { icon: getLucideIcon(best.icon), color: best.color };
}
