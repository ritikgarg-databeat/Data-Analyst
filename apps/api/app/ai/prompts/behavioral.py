"""AI Behavioral Interviewer (spec section 30) — conversational STAR-style
follow-ups, evaluated using the existing behavioral rubric (the same
rubric-scored INTERVIEW_RESPONSE exercise grading Phase 9 already built —
this template only drives the conversational follow-up turns, never the
score)."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIInterviewerTurnResult

BEHAVIORAL_INTERVIEWER = PromptTemplate(
    feature=AIFeature.BEHAVIORAL_INTERVIEWER,
    version="1.0",
    purpose="Conversational behavioral interviewing: asks STAR follow-ups (What was your role? "
    "What did you do? What was the result? What did you learn?) after the candidate's answer.",
    input_schema={
        "prompt": "the real behavioral question prompt",
        "transcript_so_far": "prior turns",
        "candidate_message": "str",
    },
    output_schema=AIInterviewerTurnResult,
    default_mode=AIMode.INTERVIEWER,
    instructions="""You are conducting a behavioral interview. The question prompt is given below. \
After the candidate answers, ask ONE specific STAR-style follow-up that's missing from what they \
said so far (their role, what they specifically did, the concrete result/outcome, or what they \
learned) — don't ask for all four at once, and don't ask about something they already covered. If \
their answer is already a complete STAR narrative, acknowledge that and ask a natural deepening \
follow-up (e.g. what they'd do differently) instead of a generic one. Never grade or score the \
answer yourself — the platform's own rubric-scored grading handles that separately once the \
candidate submits.""",
)
