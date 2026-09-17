/**
 * Maps each top-level nav section (packages/shared/src/constants.ts's
 * NAV_SECTIONS) to one of the ten "--section-*" accent colors defined in
 * apps/web/src/app/globals.css, so the sidebar, page headers, and stat
 * tiles can all color-code by section consistently from one place.
 */
export type SectionColor =
  | "violet"
  | "blue"
  | "purple"
  | "teal"
  | "amber"
  | "rose"
  | "pink"
  | "emerald"
  | "gold"
  | "slate";

export const SECTION_COLOR_BY_LABEL: Record<string, SectionColor> = {
  Main: "violet",
  Learn: "blue",
  Analyze: "purple",
  "Data Stack": "teal",
  "Cases & Projects": "amber",
  Interview: "rose",
  AI: "pink",
  Career: "emerald",
  Knowledge: "gold",
  Settings: "slate",
};

export function sectionColor(label: string | null | undefined): SectionColor {
  if (!label) return "violet";
  return SECTION_COLOR_BY_LABEL[label] ?? "violet";
}
