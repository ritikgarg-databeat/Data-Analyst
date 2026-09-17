/**
 * Shared static constants used by the frontend (and mirrored by backend seed data).
 * Source of truth for seed data lives in apps/api/app/db/seed_data.py — keep in sync.
 */
import type { SkillCategory } from "./types";

export const APP_NAME = "Ritik's Personal Data Analyst Lab";
export const APP_TAGLINE =
  "Ritik's end-to-end environment for becoming a modern Data Analyst.";

export const DOMAIN_SLUGS = [
  "data-analyst-foundations",
  "sql",
  "python",
  "excel",
  "statistics",
  "data-visualization",
  "business-analytics",
  "product-analytics",
  "data-engineering",
  "data-warehousing",
  "data-modeling",
  "machine-learning",
  "modern-data-stack",
  "case-studies",
  "projects",
  "interview-preparation",
  "experimentation",
] as const;

export const SKILL_CATEGORY_LABELS: Record<SkillCategory, string> = {
  SQL: "SQL",
  PYTHON: "Python",
  STATISTICS: "Statistics",
  EXCEL: "Excel",
  DATA_VISUALIZATION: "Data Visualization",
  BUSINESS_ANALYTICS: "Business Analytics",
  PRODUCT_ANALYTICS: "Product Analytics",
  DATA_ENGINEERING: "Data Engineering",
  DATA_WAREHOUSING: "Data Warehousing",
  DATA_MODELING: "Data Modeling",
  MACHINE_LEARNING: "Machine Learning",
  INTERVIEW_READINESS: "Interview Readiness",
};

export const SKILL_CATEGORY_ORDER: SkillCategory[] = [
  "SQL",
  "PYTHON",
  "STATISTICS",
  "EXCEL",
  "DATA_VISUALIZATION",
  "BUSINESS_ANALYTICS",
  "PRODUCT_ANALYTICS",
  "DATA_ENGINEERING",
  "DATA_WAREHOUSING",
  "DATA_MODELING",
  "MACHINE_LEARNING",
  "INTERVIEW_READINESS",
];

export interface NavItem {
  label: string;
  href: string;
  icon: string; // lucide-react icon name
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    label: "Main",
    items: [{ label: "Dashboard", href: "/", icon: "LayoutDashboard" }],
  },
  {
    label: "Learn",
    items: [
      { label: "Curriculum", href: "/learn", icon: "GraduationCap" },
      { label: "Skills", href: "/skills", icon: "Sparkles" },
      { label: "Practice", href: "/practice", icon: "Dumbbell" },
      { label: "Review", href: "/review", icon: "RotateCcw" },
    ],
  },
  {
    label: "Analyze",
    items: [
      { label: "SQL Lab", href: "/sql-lab", icon: "Terminal" },
      { label: "Python Lab", href: "/python-lab", icon: "Code2" },
      { label: "Datasets", href: "/datasets", icon: "Database" },
      { label: "EDA", href: "/eda", icon: "Microscope" },
      { label: "Visualization", href: "/visualization", icon: "PieChart" },
      { label: "Statistics", href: "/statistics", icon: "Sigma" },
      { label: "Experiments", href: "/experiments", icon: "FlaskConical" },
      { label: "Product Analytics", href: "/product-analytics", icon: "Rocket" },
      { label: "Analytics Cases", href: "/analytics-cases", icon: "FileSearch" },
    ],
  },
  {
    label: "Data Stack",
    items: [
      { label: "dbt Lab", href: "/dbt-lab", icon: "GitBranch" },
      { label: "Data Modeler", href: "/data-modeler", icon: "Boxes" },
      { label: "Architecture", href: "/architecture", icon: "Network" },
      { label: "Pipeline Playground", href: "/pipeline", icon: "Workflow" },
      { label: "Data Quality", href: "/data-quality", icon: "BadgeCheck" },
    ],
  },
  {
    label: "Cases & Projects",
    items: [
      { label: "Case Studies", href: "/case-studies", icon: "Briefcase" },
      { label: "Projects", href: "/projects", icon: "FolderKanban" },
      { label: "Portfolio", href: "/career/portfolio", icon: "LayoutGrid" },
    ],
  },
  {
    label: "Interview",
    items: [
      { label: "Overview", href: "/interview", icon: "MessagesSquare" },
      { label: "Question Practice", href: "/interview/questions", icon: "ListChecks" },
      { label: "Templates", href: "/interview/templates", icon: "ClipboardList" },
      { label: "Readiness", href: "/interview/readiness", icon: "Gauge" },
      { label: "My Review", href: "/interview/review", icon: "RotateCcw" },
    ],
  },
  {
    label: "AI",
    items: [
      { label: "AI Mentor", href: "/ai/mentor", icon: "Bot" },
      { label: "Ask the Knowledge Base", href: "/ai/knowledge", icon: "MessageCircleQuestion" },
    ],
  },
  {
    label: "Career",
    items: [
      { label: "Overview", href: "/career", icon: "Compass" },
      { label: "Target Roles", href: "/career/target-roles", icon: "Crosshair" },
      { label: "Job Descriptions", href: "/career/job-descriptions", icon: "FileText" },
      { label: "Skill Gaps", href: "/career/skill-gaps", icon: "Puzzle" },
      { label: "Resume", href: "/career/resume", icon: "FileBadge" },
      { label: "Interview Prep", href: "/career/interview-prep", icon: "Mic" },
      { label: "Behavioral Stories", href: "/career/behavioral-stories", icon: "BookMarked" },
      { label: "Career Analytics", href: "/career/analytics", icon: "LineChart" },
    ],
  },
  {
    label: "Knowledge",
    items: [
      { label: "Metrics Library", href: "/metrics", icon: "BarChart3" },
      { label: "Notes", href: "/notes", icon: "NotebookPen" },
      { label: "Resources", href: "/resources", icon: "Library" },
      { label: "Search", href: "/search", icon: "Search" },
    ],
  },
  {
    label: "Settings",
    items: [
      { label: "Settings", href: "/settings", icon: "Settings" },
      { label: "Content Admin", href: "/admin/content", icon: "ShieldCheck" },
    ],
  },
];
