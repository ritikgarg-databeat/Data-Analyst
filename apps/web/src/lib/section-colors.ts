import type { SectionColor } from "@data-analyst-lab/shared";

/**
 * Tailwind can't construct class names from interpolated strings at build
 * time (it scans source for literal class-name substrings), so each
 * SectionColor maps to a fully-literal set of classes here rather than a
 * template like `bg-section-${color}`. Keep every literal class name
 * spelled out in full so Tailwind's scanner picks it up.
 */
interface SectionColorClasses {
  /** Icon chip background + icon color. */
  chip: string;
  /** Plain text color. */
  text: string;
  /** Solid background (e.g. active nav indicator bar). */
  solid: string;
  /** Border color, low opacity. */
  border: string;
  /** Gradient pair for hero/header accents. */
  gradient: string;
}

const SECTION_COLOR_CLASSES: Record<SectionColor, SectionColorClasses> = {
  violet: {
    chip: "bg-section-violet/12 text-section-violet dark:bg-section-violet/20",
    text: "text-section-violet",
    solid: "bg-section-violet",
    border: "border-section-violet/30",
    gradient: "from-section-violet to-section-purple",
  },
  blue: {
    chip: "bg-section-blue/12 text-section-blue dark:bg-section-blue/20",
    text: "text-section-blue",
    solid: "bg-section-blue",
    border: "border-section-blue/30",
    gradient: "from-section-blue to-section-teal",
  },
  purple: {
    chip: "bg-section-purple/12 text-section-purple dark:bg-section-purple/20",
    text: "text-section-purple",
    solid: "bg-section-purple",
    border: "border-section-purple/30",
    gradient: "from-section-purple to-section-pink",
  },
  teal: {
    chip: "bg-section-teal/12 text-section-teal dark:bg-section-teal/20",
    text: "text-section-teal",
    solid: "bg-section-teal",
    border: "border-section-teal/30",
    gradient: "from-section-teal to-section-emerald",
  },
  amber: {
    chip: "bg-section-amber/14 text-section-amber dark:bg-section-amber/22",
    text: "text-section-amber",
    solid: "bg-section-amber",
    border: "border-section-amber/30",
    gradient: "from-section-amber to-section-gold",
  },
  rose: {
    chip: "bg-section-rose/12 text-section-rose dark:bg-section-rose/20",
    text: "text-section-rose",
    solid: "bg-section-rose",
    border: "border-section-rose/30",
    gradient: "from-section-rose to-section-pink",
  },
  pink: {
    chip: "bg-section-pink/12 text-section-pink dark:bg-section-pink/20",
    text: "text-section-pink",
    solid: "bg-section-pink",
    border: "border-section-pink/30",
    gradient: "from-section-pink to-section-purple",
  },
  emerald: {
    chip: "bg-section-emerald/12 text-section-emerald dark:bg-section-emerald/20",
    text: "text-section-emerald",
    solid: "bg-section-emerald",
    border: "border-section-emerald/30",
    gradient: "from-section-emerald to-section-teal",
  },
  gold: {
    chip: "bg-section-gold/16 text-section-gold dark:bg-section-gold/24",
    text: "text-section-gold",
    solid: "bg-section-gold",
    border: "border-section-gold/30",
    gradient: "from-section-gold to-section-amber",
  },
  slate: {
    chip: "bg-section-slate/12 text-section-slate dark:bg-section-slate/20",
    text: "text-section-slate",
    solid: "bg-section-slate",
    border: "border-section-slate/30",
    gradient: "from-section-slate to-section-blue",
  },
};

export function sectionColorClasses(color: SectionColor): SectionColorClasses {
  return SECTION_COLOR_CLASSES[color];
}
