"""Ask the Knowledge Base (spec sections 61-64) — a lightweight local RAG
answer, grounded in retrieved lesson/metric-definition content
(`app/ai/retrieval.py`), never model memory alone. Citations point back to
real lesson slugs the frontend can link to."""

from app.ai.prompts.base import PromptTemplate
from app.models.enums import AIFeature, AIMode
from app.schemas.ai import AIKnowledgeAnswerResult

KNOWLEDGE_SEARCH = PromptTemplate(
    feature=AIFeature.KNOWLEDGE_SEARCH,
    version="1.0",
    purpose="Retrieval-grounded Q&A over the platform's own lesson/metric-definition content "
    "(spec section 61), with citations (section 63) and an explicit 'don't know' when retrieval "
    "found nothing relevant (section 64).",
    input_schema={"query": "str", "retrieved_passages": "top-K real lesson/metric excerpts with slugs"},
    output_schema=AIKnowledgeAnswerResult,
    default_mode=AIMode.EXPLAINER,
    instructions="""Answer the learner's question using ONLY the retrieved passages given below — \
each is a real excerpt from this platform's own lessons or metric definitions, with its lesson/ \
module slug. Cite every passage you actually used in `sources`. If the retrieved passages don't \
actually contain an answer to the question, set `insufficient_knowledge=true` and say plainly that \
the platform's content doesn't cover this yet, rather than answering from general knowledge — this \
feature is explicitly about the platform's own content, not a general-purpose Q&A.""",
)
