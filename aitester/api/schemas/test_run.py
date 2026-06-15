import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TestRunCreate(BaseModel):
    spec_path: str
    base_url: str
    types: list[Literal["functional", "edge", "security", "ai"]] = ["functional"]
    enable_ai: bool = False


class TestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    base_url: str


class TestRunStatusResponse(BaseModel):
    status: str
    total_cases: int | None = None
    completed_cases: int | None = None
