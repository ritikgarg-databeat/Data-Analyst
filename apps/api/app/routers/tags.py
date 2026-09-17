from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.services import get_tag_service
from app.schemas.tag import CreateTagRequest, Tag, UpdateTagRequest
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[Tag])
def list_tags(service: Annotated[TagService, Depends(get_tag_service)]) -> list[Tag]:
    return service.list_tags()


@router.post("", response_model=Tag, status_code=201)
def create_tag(payload: CreateTagRequest, service: Annotated[TagService, Depends(get_tag_service)]) -> Tag:
    return service.create(payload)


@router.patch("/{tag_id}", response_model=Tag)
def update_tag(
    tag_id: str, payload: UpdateTagRequest, service: Annotated[TagService, Depends(get_tag_service)]
) -> Tag:
    return service.update(tag_id, payload)


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: str, service: Annotated[TagService, Depends(get_tag_service)]) -> None:
    service.delete(tag_id)
