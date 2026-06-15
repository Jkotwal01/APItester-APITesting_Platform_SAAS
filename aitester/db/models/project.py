import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.test_run import TestRun


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    openapi_spec: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="Parsed OpenAPI Spec as JSON"
    )

    test_runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )
