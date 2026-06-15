import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.test_result import TestResult
    from aitester.db.models.test_run import TestRun


class TestCase(TimestampMixin, Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="FUNCTIONAL, EDGE, AI, SECURITY"
    )
    endpoint: Mapped[str] = mapped_column(String(512), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)

    # Request Details
    headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    query_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Expected Outcomes
    expected_status_code: Mapped[int | None] = mapped_column(nullable=True)
    expected_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="test_cases")
    test_results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="test_case", cascade="all, delete-orphan"
    )
