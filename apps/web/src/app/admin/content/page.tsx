"use client";

import { useState } from "react";

import { CaseAdminPanel } from "@/components/features/admin/case-admin-panel";
import { DomainAdminPanel } from "@/components/features/admin/domain-admin-panel";
import { ExerciseAdminPanel } from "@/components/features/admin/exercise-admin-panel";
import { InterviewQuestionAdminPanel } from "@/components/features/admin/interview-question-admin-panel";
import { InterviewTemplateAdminPanel } from "@/components/features/admin/interview-template-admin-panel";
import { LessonAdminPanel } from "@/components/features/admin/lesson-admin-panel";
import { ModuleAdminPanel } from "@/components/features/admin/module-admin-panel";
import { ProjectTemplateAdminPanel } from "@/components/features/admin/project-template-admin-panel";
import { SkillAdminPanel } from "@/components/features/admin/skill-admin-panel";
import { TagAdminPanel } from "@/components/features/admin/tag-admin-panel";
import { PageHeader } from "@/components/shared/page-header";
import { cn } from "@/lib/utils";

const TABS = [
  { value: "domains", label: "Domains" },
  { value: "modules", label: "Modules" },
  { value: "lessons", label: "Lessons" },
  { value: "exercises", label: "Exercises" },
  { value: "skills", label: "Skills" },
  { value: "tags", label: "Tags" },
  { value: "cases", label: "Cases" },
  { value: "project-templates", label: "Project Templates" },
  { value: "interview-questions", label: "Interview Questions" },
  { value: "interview-templates", label: "Interview Templates" },
] as const;

type Tab = (typeof TABS)[number]["value"];

export default function ContentAdminPage() {
  const [tab, setTab] = useState<Tab>("domains");

  return (
    <div>
      <PageHeader
        title="Content Admin"
        subtitle="Manage the structural taxonomy (domains, modules, skills, tags) and reorder/activate lessons and exercises. Lesson and exercise content itself is authored as files in content/ — see the note in each tab."
      />

      <div role="tablist" aria-label="Content admin sections" className="mb-6 flex flex-wrap gap-1.5 border-b border-border pb-3">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            role="tab"
            aria-selected={tab === t.value}
            onClick={() => setTab(t.value)}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === t.value
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "domains" ? <DomainAdminPanel /> : null}
      {tab === "modules" ? <ModuleAdminPanel /> : null}
      {tab === "lessons" ? <LessonAdminPanel /> : null}
      {tab === "exercises" ? <ExerciseAdminPanel /> : null}
      {tab === "skills" ? <SkillAdminPanel /> : null}
      {tab === "tags" ? <TagAdminPanel /> : null}
      {tab === "cases" ? <CaseAdminPanel /> : null}
      {tab === "project-templates" ? <ProjectTemplateAdminPanel /> : null}
      {tab === "interview-questions" ? <InterviewQuestionAdminPanel /> : null}
      {tab === "interview-templates" ? <InterviewTemplateAdminPanel /> : null}
    </div>
  );
}
