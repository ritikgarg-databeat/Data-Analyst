"""A lightweight, local RAG retriever (spec sections 61-64) — plain TF-IDF +
cosine similarity over the platform's own lesson content and metric
definitions, computed in-process with `numpy` (already a core dependency
since Phase 6). No vector database, no embedding API call, no external
service: "Start with semantic/vector search if infrastructure already
exists... a lightweight local solution is acceptable" — this repo's own
`app/services/search.py` already does plain `.ilike()` substring matching for
general search; this module is the same philosophy applied to Q&A retrieval,
one step up (term-frequency relevance instead of pure substring match),
without introducing new infrastructure.

The corpus is two real, already-authored/seeded sources — lesson content
(`app/content/loader.py`, YAML-authored) and the Metrics Library
(`MetricDefinition`, DB-seeded) — never model-generated text. A query that
doesn't match anything above a minimum relevance threshold returns no
sources, and the caller (see `app/ai/prompts/knowledge.py`) is instructed to
say so rather than answer from general knowledge."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from app.content import loader as content_loader

_TOKEN_RE = re.compile(r"[a-z0-9]+")
MIN_RELEVANCE_SCORE = 0.05


@dataclass(frozen=True)
class RetrievedPassage:
    doc_id: str
    kind: str  # "lesson" | "metric"
    title: str
    lesson_slug: str | None
    module_slug: str | None
    domain_slug: str | None
    text: str
    score: float


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) > 2]


def _module_to_domain_slug(db: Session) -> dict[str, str]:
    from app.models.domain import Domain
    from app.models.module import Module

    rows = db.query(Module.slug, Domain.slug).join(Domain, Module.domain_id == Domain.id).all()
    return dict(rows)


def _lesson_documents(db: Session) -> list[dict]:
    result = content_loader.load_all()
    module_domains = _module_to_domain_slug(db)
    docs = []
    for lesson in result.lessons:
        block_text = " ".join(
            str(getattr(block, "body", "") or getattr(block, "title", "") or "") for block in lesson.blocks
        )
        text = " ".join(
            [
                lesson.title,
                " ".join(lesson.objectives),
                " ".join(lesson.key_takeaways),
                block_text,
            ]
        )
        docs.append(
            {
                "doc_id": f"lesson:{lesson.slug}",
                "kind": "lesson",
                "title": lesson.title,
                "lesson_slug": lesson.slug,
                "domain_slug": module_domains.get(lesson.module_slug),
                "module_slug": lesson.module_slug,
                "text": text,
            }
        )
    return docs


def _metric_documents(db: Session) -> list[dict]:
    from app.models.metric import MetricDefinition

    rows = db.query(MetricDefinition).all()
    docs = []
    for metric in rows:
        text = " ".join(
            [
                metric.name,
                metric.definition,
                metric.formula or "",
                " ".join(metric.business_questions or []),
                " ".join(metric.common_mistakes or []),
            ]
        )
        docs.append(
            {
                "doc_id": f"metric:{metric.slug}",
                "kind": "metric",
                "title": metric.name,
                "lesson_slug": None,
                "domain_slug": None,
                "module_slug": None,
                "text": text,
            }
        )
    return docs


def _tfidf_matrix(documents: list[list[str]]) -> tuple[np.ndarray, dict[str, int]]:
    vocab: dict[str, int] = {}
    for tokens in documents:
        for token in tokens:
            vocab.setdefault(token, len(vocab))

    n_docs = len(documents)
    n_terms = len(vocab)
    tf = np.zeros((n_docs, n_terms), dtype=np.float64)
    for row, tokens in enumerate(documents):
        for token in tokens:
            tf[row, vocab[token]] += 1.0
        if tokens:
            tf[row] /= len(tokens)

    doc_freq = (tf > 0).sum(axis=0)
    idf = np.log((n_docs + 1) / (doc_freq + 1)) + 1.0
    return tf * idf, vocab


def search(query: str, *, db: Session, limit: int = 5) -> list[RetrievedPassage]:
    """Retriever step of the RAG pipeline (spec section 62): User Question ->
    Retriever -> Relevant Lessons/Docs. Pure TF-IDF cosine similarity over the
    combined lesson+metric corpus, rebuilt fresh per call — the corpus is
    small enough (a few hundred lessons, tens of metrics) that this is fast
    without needing a persisted index."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    documents = _lesson_documents(db) + _metric_documents(db)
    if not documents:
        return []

    tokenized_docs = [_tokenize(d["text"]) for d in documents]
    matrix, vocab = _tfidf_matrix([*tokenized_docs, query_tokens])
    doc_vectors, query_vector = matrix[:-1], matrix[-1]

    doc_norms = np.linalg.norm(doc_vectors, axis=1)
    query_norm = np.linalg.norm(query_vector)
    if query_norm == 0:
        return []
    similarities = np.divide(
        doc_vectors @ query_vector,
        doc_norms * query_norm,
        out=np.zeros(len(documents)),
        where=(doc_norms * query_norm) != 0,
    )

    ranked = sorted(range(len(documents)), key=lambda i: similarities[i], reverse=True)
    passages = []
    for i in ranked[:limit]:
        score = float(similarities[i])
        if score < MIN_RELEVANCE_SCORE or math.isnan(score):
            continue
        doc = documents[i]
        passages.append(
            RetrievedPassage(
                doc_id=doc["doc_id"],
                kind=doc["kind"],
                title=doc["title"],
                lesson_slug=doc["lesson_slug"],
                module_slug=doc["module_slug"],
                domain_slug=doc["domain_slug"],
                text=doc["text"][:1500],
                score=score,
            )
        )
    return passages
