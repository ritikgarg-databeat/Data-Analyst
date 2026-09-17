from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_domain_service, get_module_service
from app.schemas.domain import CreateDomainRequest, Domain, UpdateDomainRequest
from app.schemas.module import Module
from app.services.domain_service import DomainService
from app.services.module_service import ModuleService

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[Domain])
def list_domains(
    user_id: CurrentUserId, service: Annotated[DomainService, Depends(get_domain_service)]
) -> list[Domain]:
    return service.list_domains(user_id)


@router.post("", response_model=Domain, status_code=201)
def create_domain(
    payload: CreateDomainRequest, service: Annotated[DomainService, Depends(get_domain_service)]
) -> Domain:
    return service.create(payload)


@router.get("/{slug}", response_model=Domain)
def get_domain(
    slug: str, user_id: CurrentUserId, service: Annotated[DomainService, Depends(get_domain_service)]
) -> Domain:
    return service.get_by_slug(slug, user_id)


@router.patch("/{domain_id}", response_model=Domain)
def update_domain(
    domain_id: str,
    payload: UpdateDomainRequest,
    service: Annotated[DomainService, Depends(get_domain_service)],
) -> Domain:
    return service.update(domain_id, payload)


@router.get("/{slug}/modules", response_model=list[Module])
def list_domain_modules(
    slug: str, user_id: CurrentUserId, service: Annotated[ModuleService, Depends(get_module_service)]
) -> list[Module]:
    return service.list_by_domain_slug(slug, user_id)
