import * as React from "react";
import {
  BadgeCheck,
  BarChart3,
  BookMarked,
  Bot,
  Boxes,
  BrainCircuit,
  Briefcase,
  ClipboardList,
  Code2,
  Compass,
  Crosshair,
  Database,
  Dumbbell,
  FileBadge,
  FileSearch,
  FileText,
  FlaskConical,
  FolderKanban,
  Gauge,
  GitBranch,
  GraduationCap,
  HelpCircle,
  Layers,
  LayoutDashboard,
  LayoutGrid,
  Library,
  LineChart,
  ListChecks,
  MessageCircleQuestion,
  MessagesSquare,
  Mic,
  Microscope,
  Network,
  NotebookPen,
  PieChart,
  Puzzle,
  Rocket,
  RotateCcw,
  Search,
  Settings,
  ShieldCheck,
  Sigma,
  Sparkles,
  Table2,
  Terminal,
  Warehouse,
  Workflow,
} from "lucide-react";
import type { LucideIcon, LucideProps } from "lucide-react";

// Keep this explicit: a namespace import pulls every Lucide glyph into the
// client bundle and makes the sidebar expensive on every authenticated page.
const iconMap: Record<string, LucideIcon> = {
  BadgeCheck,
  BarChart3,
  BookMarked,
  Bot,
  Boxes,
  BrainCircuit,
  Briefcase,
  ClipboardList,
  Code2,
  Compass,
  Crosshair,
  Database,
  Dumbbell,
  FileBadge,
  FileSearch,
  FileText,
  FlaskConical,
  FolderKanban,
  Gauge,
  GitBranch,
  GraduationCap,
  HelpCircle,
  Layers,
  LayoutDashboard,
  LayoutGrid,
  Library,
  LineChart,
  ListChecks,
  MessageCircleQuestion,
  MessagesSquare,
  Mic,
  Microscope,
  Network,
  NotebookPen,
  PieChart,
  Puzzle,
  Rocket,
  RotateCcw,
  Search,
  Settings,
  ShieldCheck,
  Sigma,
  Sparkles,
  Table2,
  Terminal,
  Warehouse,
  Workflow,
};

/**
 * Resolve a Lucide icon by its export name (as used in NAV_SECTIONS / domain
 * `icon` fields, which are plain strings coming from data, not code).
 * Falls back to a generic icon so unexpected/missing names never crash render.
 */
export function getLucideIcon(name: string | null | undefined, fallback: LucideIcon = HelpCircle): LucideIcon {
  if (!name) return fallback;
  return iconMap[name] ?? fallback;
}

interface DynamicIconProps extends Omit<LucideProps, "name"> {
  /** Lucide export name from data (e.g. a domain's `icon` field). */
  iconName: string | null | undefined;
  fallback?: LucideIcon;
}

/** Renders a Lucide icon looked up by name at data-fetch time, not import time. */
export function DynamicIcon({ iconName, fallback = HelpCircle, ...props }: DynamicIconProps) {
  return React.createElement(getLucideIcon(iconName, fallback), props);
}
