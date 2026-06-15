import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Schema for creating a new Project."""

    name: str = Field(..., max_length=255, description="The name of the project")
    description: str | None = Field(None, description="Optional description of the project")
    openapi_spec: dict[str, Any] | None = Field(
        None, description="Optional OpenAPI JSON specification"
    )


class ProjectResponse(BaseModel):
    """Schema for returning a Project."""

    id: uuid.UUID
    name: str
    description: str | None
    openapi_spec: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
