"""AI Interview Debrief (spec sections 29, 60) — narrates the ALREADY-
COMPUTED deterministic Interview.score/InterviewQuestionReviewSchema data;
never a second scoring system. "Use the deterministic interview score where
available and AI as a supplementary evaluator" (section 29)."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIDebriefResult

INTERVIEW_DEBRIEF = PromptTemplate(
    feature=AIFeature.INTERVIEW_DEBRIEF,
    version="1.0",
    purpose="Post-interview analysis (spec sections 29, 60): technical mistakes, reasoning gaps, "
    "weak explanations, missed follow-ups, time management, business thinking — supplementary to, "
    "never a replacement for, the real computed score.",
    input_schema={
        "interview_score": "real InterviewScoreSchema (overall + 6 dimensions)",
        "question_reviews": "real InterviewQuestionReviewSchema list "
        "(per-question score/pass/over_time/prompt)",
    },
    output_schema=AIDebriefResult,
    default_mode=AIMode.REVIEWER,
    instructions="""Debrief this completed mock interview. You are given the REAL, already- \
computed overall score, per-dimension scores, and per-question results (including which were over \
time, which passed/failed, and their prompts). Do not restate or reinterpret the numeric scores as \
different numbers — use them as the basis for qualitative analysis: which specific questions show \
a pattern (e.g. two SQL rounds both over time suggests a pacing issue, not a knowledge gap), what \
technical mistakes the given data reveals, and what to practice next. Ground every strength/ \
weakness in a SPECIFIC question from the given list, never a generic interview-skills comment.""",
)
