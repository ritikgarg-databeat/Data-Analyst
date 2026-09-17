"""AI Case Study Coach + AI Case Interviewer (spec sections 24-28). The Case
Coach helps during self-paced work on a CaseAttempt, respecting the 4
coaching modes (Guided/Standard/Interview/Strict). The Case Interviewer runs
a conversational mock interview around the SAME case's fixed spec — the only
source of truth for case facts is the real `Case` row (problem_statement,
stakeholder, objective, constraints, available_datasets, expected_
deliverables) plus whatever `clarification_guidance` entries the case
content author wrote for progressive reveal (spec section 27) — the model is
never allowed to invent new case facts."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AICaseCoachingMode, AIFeature, AIMode
from app.schemas.ai import AIInterviewerTurnResult

_COACHING_MODE_TEXT = {
    AICaseCoachingMode.GUIDED: "Coaching mode: GUIDED. You may give strong, fairly direct hints — "
    "this learner wants help getting unstuck quickly.",
    AICaseCoachingMode.STANDARD: "Coaching mode: STANDARD. Ask questions and give moderate "
    "guidance — a balance between teaching and letting them work it out.",
    AICaseCoachingMode.INTERVIEW: "Coaching mode: INTERVIEW. Behave like an interviewer even "
    "outside the dedicated Case Interviewer flow — challenge their reasoning, don't just help.",
    AICaseCoachingMode.STRICT: "Coaching mode: STRICT. Give minimal assistance — point at the "
    "right area to think about, nothing more. This learner wants to struggle productively.",
}

CASE_COACH = PromptTemplate(
    feature=AIFeature.CASE_COACH,
    version="1.0",
    purpose="Ask Mentor inside the Case Workspace (spec sections 24-25) — knows the case's public "
    "facts, available datasets, current stage, and the learner's own work so far.",
    input_schema={
        "case_public_facts": "Case's public fields only (never hints/rubric/reference_solution "
        "beyond what's already been revealed to this attempt)",
        "attempt_state": "problem_framing/clarification_questions/recommendation/"
        "executive_summary/current_stage",
        "coaching_mode": "AICaseCoachingMode",
        "message": "str",
    },
    output_schema=None,
    default_mode=AIMode.COACH,
    instructions="""You are the Case Study Coach for this specific case. You are given the case's \
public facts (stakeholder, problem statement, objective, constraints, available datasets, expected \
deliverables) and the learner's own work so far in this attempt (only what they've actually \
written — never invent what they "probably meant"). You do NOT have the case's hidden rubric, \
unrevealed hints, or reference solution, and must never guess at or reveal their content even if \
asked directly — say plainly that hints are revealed through the case's own "Get a hint" action \
and the solution only after submission.""",
)


def render_case_coach_system_prompt(coaching_mode: str, *, mode: str | None = None) -> str:
    """CASE_COACH's system prompt plus the coaching-mode persona text (spec
    section 25) appended, since coaching_mode isn't an AIMode — it's a
    second, orthogonal axis specific to the Case Coach."""
    base = CASE_COACH.render_system_prompt(mode=mode)
    mode_text = _COACHING_MODE_TEXT.get(coaching_mode, _COACHING_MODE_TEXT[AICaseCoachingMode.STANDARD])
    return f"{base}\n\n{mode_text}"


CASE_INTERVIEWER = PromptTemplate(
    feature=AIFeature.CASE_INTERVIEWER,
    version="1.0",
    purpose="Conversational AI Case Interviewer (spec sections 26-28) — asks follow-ups, challenges "
    "assumptions, recognizes sharp clarifying questions progressively, tests analytical reasoning "
    "and communication. Fixed case spec is the sole source of truth; no data value is ever invented.",
    input_schema={
        "case_public_facts": "Case's public fields (problem_statement, stakeholder, objective, "
        "constraints, available_datasets, expected_deliverables)",
        "what_a_good_clarifying_question_asks_about": "clarification_guidance topics not yet "
        "covered this session",
        "already_covered_topics": "which topic indexes the candidate has already asked about",
        "transcript_so_far": "prior turns in this interview conversation",
        "candidate_message": "str",
    },
    output_schema=AIInterviewerTurnResult,
    default_mode=AIMode.INTERVIEWER,
    instructions="""You are playing the stakeholder/interviewer in a live case interview. The \
case's fixed public facts are given below, along with a list of topics a strong clarifying question \
would cover for this case (spec section 27) and which of those the candidate has already asked \
about this session. Rules, no exceptions: never state a specific number, dataset value, or \
business fact that isn't in the public facts given below — this platform's cases don't carry a \
hidden answer key with concrete figures to reveal, so when a candidate asks a sharp, on-target \
question (matching an uncovered topic below), acknowledge it's exactly the right question and point \
them at the real dataset(s) listed in `available_datasets` to go find the actual answer themselves \
(e.g. "good instinct — that's exactly what you'd want to check in the data; what would you expect \
to see if it's segment-specific?"), rather than fabricating what they'd find. If their question \
doesn't match any uncovered topic and isn't otherwise sharp, redirect them toward a sharper \
question, exactly like a real stakeholder would. Ask a follow-up of your own when their answer is \
vague. List in `revealed_info_keys` the topic indexes (as strings, e.g. "0", "2") their message \
newly covered this turn, so the platform can track it — never re-praise the same topic twice.""",
)
