import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.project import Project
    from aitester.db.models.report import Report
    from aitester.db.models.test_case import TestCase
    from aitester.db.models.test_result import TestResult


class TestRun(TimestampMixin, Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="test_runs")
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase", back_populates="test_run", cascade="all, delete-orphan"
    )
    test_results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="test_run", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="test_run", cascade="all, delete-orphan"
    )
