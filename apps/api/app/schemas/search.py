from typing import Literal

from pydantic import BaseModel

SearchResultKind = Literal[
    "domain", "module", "lesson", "skill", "exercise", "case", "project", "interview_question", "metric"
]


class SearchResultItem(BaseModel):
    kind: SearchResultKind
    id: str
    slug: str
    title: str
    description: str | None
    url_path: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
