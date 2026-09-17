# Career Layer

See [README.md](../README.md#career-layer) for a one-paragraph summary and [`docs/roadmap.md`](roadmap.md)'s
Phase 11 entry for the full feature list. This page covers the parts a developer extending the Career
layer needs: the readiness rubric's exact mapping, the gating rule, and how it composes (never
duplicates) every earlier phase's own engines.

## Every number here comes from somewhere real

The Career layer computes nothing from scratch — it reads:

- `UserSkill.mastery_score` (the real, deterministic `MasteryService` output) for every skill-based
  dimension.
- `InterviewReadinessService.get_readiness()` (Phase 9's real mock-interview readiness score) for the
  `INTERVIEW` dimension, blended with the `INTERVIEW_READINESS`-category skills (`interview-sql`,
  `analytics-case-studies`, `product-cases`, `behavioral-interviewing`) — a Phase 12 audit found this
  category fed into nothing until this blend was added; see `career_readiness_service.py::
  _interview_score`.
- Real `Portfolio`/`PortfolioItem` completeness/description/visibility for the `PORTFOLIO` dimension.

## The 8-dimension rubric → `SkillCategory` mapping

| Rubric dimension | Source |
|---|---|
| `TECHNICAL` | Average mastery across SQL, PYTHON, EXCEL, DATA_VISUALIZATION |
| `ANALYTICAL` | Average mastery across STATISTICS, MACHINE_LEARNING |
| `BUSINESS` | Average mastery of BUSINESS_ANALYTICS |
| `PRODUCT` | Average mastery of PRODUCT_ANALYTICS |
| `DATA_ENGINEERING_AWARENESS` | Average mastery across DATA_ENGINEERING, DATA_WAREHOUSING, DATA_MODELING |
| `COMMUNICATION` | Mastery of the single `communication` skill |
| `INTERVIEW` | 70% `InterviewReadinessService` score + 30% INTERVIEW_READINESS-category mastery |
| `PORTFOLIO` | Deterministic completeness/description/visibility heuristic |

This is deliberately **not** the same 12-value `SkillCategory` enum — seven rubric dimensions map from
one or more `SkillCategory` values, and `INTERVIEW`/`PORTFOLIO` don't come from `SkillCategory` at all.

## Gating — why a high score doesn't always mean a high level

A single strong dimension must never hide a real weakness elsewhere. Every dimension must clear a
minimum (40/100 by default) before `INTERVIEW_READY`/`STRONG_CANDIDATE`/`EXCEPTIONAL` is reachable —
regardless of the weighted overall score. A profile that scores 89 overall but has one dimension at 10
is capped at `INTERMEDIATE`, with `gating_passed: false` and an explanation naming which dimension(s)
fell short. This is tested directly (`tests/test_career_readiness_and_e2e.py::TestReadinessGating`) by
constructing exactly that scenario.

Every `CareerAssessment` carries a per-dimension `explanation` (spec's explainability requirement) and
an explicit disclaimer: this is the platform's own estimate of preparation, never a guarantee of any
real employer's hiring decision.

## Data model

21 tables (one migration, `4d9c395b6197`): `CareerProfile`, `RoleTemplate`, `TargetRole`,
`JobDescription`, `JDRequirement`, `JDAnalysis`, `SkillGap`, `Resume`, `ResumeVersion`, `ResumeEvidence`,
`ResumeReview`, `Portfolio`, `PortfolioItem`, `CareerGoal`, `CareerMilestone`, `CareerAssessment`,
`BehavioralStory`, `JobPreparationWorkspace`, `Achievement`, `UserAchievement`, `CareerNote`.

## AI extension points

`JD_EXTRACTION`, `RESUME_REVIEW`, `CAREER_COACH`, `PORTFOLIO_REVIEW` — all optional, all degrade
gracefully under the local provider, and none of them ever computes a score: JD extraction's suggested
skill slugs are re-validated against the real skill taxonomy before being trusted (never invented);
resume quality/clarity/impact scores are deterministic heuristics, AI only adds qualitative issues/
suggestions on top.

## Next Best Action (Phase 12)

`app/services/next_best_action_service.py` composes five independent signal sources (interview
weakness detection, active-JD skill gaps, lesson recommendations, portfolio gap detection, career
goals) into a small, capped, ranked list — it never recomputes any of their scoring, it only picks the
single highest-signal item from each and returns the top few. See `GET /api/v1/platform/next-best-actions`.
