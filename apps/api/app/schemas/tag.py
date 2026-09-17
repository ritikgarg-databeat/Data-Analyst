from app.schemas.common import ORMSchema


class Tag(ORMSchema):
    id: str
    slug: str
    name: str


class CreateTagRequest(ORMSchema):
    slug: str
    name: str


class UpdateTagRequest(ORMSchema):
    slug: str | None = None
    name: str | None = None
