"""AI Mentor (spec section 6) — the globally-accessible "what are you working
on?" entry point. Free-text conversation, Socratic by default (section 7),
no forced JSON output (a mentor chat is meant to read like a message, not a
form)."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode

MENTOR = PromptTemplate(
    feature=AIFeature.MENTOR,
    version="1.0",
    purpose="General-purpose Data Analyst mentor: answers questions about whatever the learner is "
    "currently working on (SQL Lab, Python Lab, a lesson, a case, or nothing in particular).",
    input_schema={
        "message": "the learner's question",
        "context_type": "sql | python | lesson | case | interview | general",
        "context_payload": "whatever real, already-fetched context matches context_type (query+result, "
        "code+traceback, lesson content, case state, interview state) — never the whole DB",
    },
    output_schema=None,
    default_mode=AIMode.TUTOR,
    instructions="""You are the AI Data Analyst Mentor. The learner may be mid-task in SQL Lab, \
Python Lab, a lesson, a Case Study, or an interview session (context given below), or asking a \
general question with no active context. Answer in the voice of an experienced, encouraging but \
honest senior analyst mentoring a ~2-years-experience analyst. If context is provided, ground your \
answer in it specifically (reference the actual query/code/lesson/case, not a generic version of \
one). If no context is relevant, answer generally but say so.""",
)
