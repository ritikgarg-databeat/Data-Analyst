from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.services import get_search_service
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.search import ALL_KINDS, SearchKind, SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    service: Annotated[SearchService, Depends(get_search_service)],
    q: str = Query(default="", max_length=200),
    kind: list[SearchKind] | None = Query(default=None),
) -> SearchResponse:
    kinds = tuple(kind) if kind else ALL_KINDS
    results = service.search(q, kinds=kinds)
    return SearchResponse(
        query=q,
        results=[
            SearchResultItem(
                kind=r.kind,
                id=r.id,
                slug=r.slug,
                title=r.title,
                description=r.description,
                url_path=r.url_path,
            )
            for r in results
        ],
    )
