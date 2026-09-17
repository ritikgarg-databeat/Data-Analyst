from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMSchema(BaseModel):
    """Base for schemas that are built from SQLAlchemy ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    timestamp: datetime
