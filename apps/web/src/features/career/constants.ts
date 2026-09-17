import type {
  BehavioralStoryCategory,
  CareerGoalStatus,
  CareerGoalType,
  CareerMilestoneType,
  CareerReadinessLevel,
  CareerRubricDimension,
  CareerSkillEvidenceLevel,
  JDRequirementKind,
  JDRequirementPriority,
  JobPrepStatus,
  PortfolioItemType,
  PrivacyLevel,
  TargetRoleCategory,
} from "@data-analyst-lab/shared";

/** Canonical order + human labels for the 7 target role categories. */
export const TARGET_ROLE_CATEGORY_ORDER: TargetRoleCategory[] = [
  "DATA_ANALYST",
  "PRODUCT_ANALYST",
  "BUSINESS_ANALYST",
  "BI_ANALYST",
  "MARKETING_ANALYST",
  "ANALYTICS_ENGINEER_ENTRY",
  "ANALYTICS_ENGINEER_INTERMEDIATE",
];

export const TARGET_ROLE_CATEGORY_LABELS: Record<TargetRoleCategory, string> = {
  DATA_ANALYST: "Data Analyst",
  PRODUCT_ANALYST: "Product Analyst",
  BUSINESS_ANALYST: "Business Analyst",
  BI_ANALYST: "BI Analyst",
  MARKETING_ANALYST: "Marketing Analyst",
  ANALYTICS_ENGINEER_ENTRY: "Analytics Engineer (Entry)",
  ANALYTICS_ENGINEER_INTERMEDIATE: "Analytics Engineer (Intermediate)",
};

export const JD_REQUIREMENT_KIND_LABELS: Record<JDRequirementKind, string> = {
  SKILL: "Skill",
  TOOL: "Tool",
  RESPONSIBILITY: "Responsibility",
  EXPERIENCE: "Experience",
  EDUCATION: "Education",
  DOMAIN_KNOWLEDGE: "Domain Knowledge",
  SOFT_SKILL: "Soft Skill",
  BUSINESS_EXPECTATION: "Business Expectation",
};

export const JD_REQUIREMENT_PRIORITY_ORDER: JDRequirementPriority[] = [
  "MUST_HAVE",
  "STRONGLY_PREFERRED",
  "NICE_TO_HAVE",
];

export const JD_REQUIREMENT_PRIORITY_LABELS: Record<JDRequirementPriority, string> = {
  MUST_HAVE: "Must Have",
  STRONGLY_PREFERRED: "Strongly Preferred",
  NICE_TO_HAVE: "Nice to Have",
};

export const PORTFOLIO_ITEM_TYPE_LABELS: Record<PortfolioItemType, string> = {
  PROJECT: "Project",
  CASE_STUDY: "Case Study",
  CERTIFICATION: "Certification",
  ACHIEVEMENT: "Achievement",
  SKILL_HIGHLIGHT: "Skill Highlight",
};

export const PORTFOLIO_ITEM_TYPE_ORDER: PortfolioItemType[] = [
  "PROJECT",
  "CASE_STUDY",
  "CERTIFICATION",
  "ACHIEVEMENT",
  "SKILL_HIGHLIGHT",
];

/** Always defaults to PRIVATE server-side when omitted from a request. */
export const PRIVACY_LEVEL_LABELS: Record<PrivacyLevel, string> = {
  PRIVATE: "Private",
  PORTFOLIO: "Portfolio Only",
  PUBLIC_READY: "Public Ready",
};

export const PRIVACY_LEVEL_ORDER: PrivacyLevel[] = ["PRIVATE", "PORTFOLIO", "PUBLIC_READY"];

export const CAREER_GOAL_TYPE_LABELS: Record<CareerGoalType, string> = {
  TARGET_ROLE: "Target Role",
  SKILL_MASTERY: "Skill Mastery",
  READINESS_LEVEL: "Readiness Level",
  PORTFOLIO_COMPLETION: "Portfolio Completion",
  INTERVIEW_PREP: "Interview Prep",
  CUSTOM: "Custom",
};

export const CAREER_GOAL_TYPE_ORDER: CareerGoalType[] = [
  "TARGET_ROLE",
  "SKILL_MASTERY",
  "READINESS_LEVEL",
  "PORTFOLIO_COMPLETION",
  "INTERVIEW_PREP",
  "CUSTOM",
];

export const CAREER_GOAL_STATUS_LABELS: Record<CareerGoalStatus, string> = {
  ACTIVE: "Active",
  COMPLETED: "Completed",
  ABANDONED: "Abandoned",
};

export const CAREER_MILESTONE_TYPE_LABELS: Record<CareerMilestoneType, string> = {
  SKILL_LEVEL_UP: "Skill Level Up",
  PROJECT_COMPLETED: "Project Completed",
  CASE_COMPLETED: "Case Completed",
  INTERVIEW_COMPLETED: "Interview Completed",
  ASSESSMENT_PASSED: "Assessment Passed",
  GOAL_COMPLETED: "Goal Completed",
  READINESS_LEVEL_UP: "Readiness Level Up",
  ACHIEVEMENT_EARNED: "Achievement Earned",
};

export const CAREER_READINESS_LEVEL_ORDER: CareerReadinessLevel[] = [
  "FOUNDATION",
  "DEVELOPING",
  "INTERMEDIATE",
  "INTERVIEW_READY",
  "STRONG_CANDIDATE",
  "EXCEPTIONAL",
];

export const CAREER_READINESS_LEVEL_LABELS: Record<CareerReadinessLevel, string> = {
  FOUNDATION: "Foundation",
  DEVELOPING: "Developing",
  INTERMEDIATE: "Intermediate",
  INTERVIEW_READY: "Interview Ready",
  STRONG_CANDIDATE: "Strong Candidate",
  EXCEPTIONAL: "Exceptional",
};

export const CAREER_RUBRIC_DIMENSION_ORDER: CareerRubricDimension[] = [
  "TECHNICAL",
  "ANALYTICAL",
  "BUSINESS",
  "PRODUCT",
  "DATA_ENGINEERING_AWARENESS",
  "COMMUNICATION",
  "INTERVIEW",
  "PORTFOLIO",
];

export const CAREER_RUBRIC_DIMENSION_LABELS: Record<CareerRubricDimension, string> = {
  TECHNICAL: "Technical",
  ANALYTICAL: "Analytical",
  BUSINESS: "Business",
  PRODUCT: "Product",
  DATA_ENGINEERING_AWARENESS: "Data Engineering Awareness",
  COMMUNICATION: "Communication",
  INTERVIEW: "Interview",
  PORTFOLIO: "Portfolio",
};

export const CAREER_SKILL_EVIDENCE_LEVEL_LABELS: Record<CareerSkillEvidenceLevel, string> = {
  LEARNED: "Learned",
  PRACTICED: "Practiced",
  APPLIED: "Applied",
  INTERVIEW_READY: "Interview Ready",
  DEMONSTRATED: "Demonstrated",
};

/** The real 12 behavioral story categories — matches the Phase 9 behavioral-exercise tags. */
export const BEHAVIORAL_STORY_CATEGORY_ORDER: BehavioralStoryCategory[] = [
  "AMBIGUITY",
  "COMMUNICATION",
  "CONFLICT",
  "DEADLINES",
  "DISAGREEMENT",
  "WORKING_WITH_ENGINEERS",
  "FAILURE",
  "INCOMPLETE_DATA",
  "INFLUENCING",
  "OWNERSHIP",
  "PRIORITIZATION",
  "STAKEHOLDER_MANAGEMENT",
];

export const BEHAVIORAL_STORY_CATEGORY_LABELS: Record<BehavioralStoryCategory, string> = {
  AMBIGUITY: "Ambiguity",
  COMMUNICATION: "Communication",
  CONFLICT: "Conflict",
  DEADLINES: "Deadlines",
  DISAGREEMENT: "Disagreement",
  WORKING_WITH_ENGINEERS: "Working with Engineers",
  FAILURE: "Failure",
  INCOMPLETE_DATA: "Incomplete Data",
  INFLUENCING: "Influencing",
  OWNERSHIP: "Ownership",
  PRIORITIZATION: "Prioritization",
  STAKEHOLDER_MANAGEMENT: "Stakeholder Management",
};

export const JOB_PREP_STATUS_ORDER: JobPrepStatus[] = ["SAVED", "IN_PROGRESS", "READY", "ARCHIVED"];

export const JOB_PREP_STATUS_LABELS: Record<JobPrepStatus, string> = {
  SAVED: "Saved",
  IN_PROGRESS: "In Progress",
  READY: "Ready",
  ARCHIVED: "Archived",
};

/** Platform-estimate disclaimer shown next to every readiness/score number this phase produces. */
export const READINESS_DISCLAIMER =
  "This is a platform estimate based on your practice history, not a guarantee of hiring outcomes.";
