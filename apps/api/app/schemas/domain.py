from datetime import datetime

from app.schemas.common import ORMSchema


class Domain(ORMSchema):
    id: str
    slug: str
    name: str
    description: str | None = None
    display_order: int
    icon: str | None = None
    is_active: bool
    module_count: int = 0
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime


class CreateDomainRequest(ORMSchema):
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    display_order: int = 0


class UpdateDomainRequest(ORMSchema):
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    display_order: int | None = None
    is_active: bool | None = None
