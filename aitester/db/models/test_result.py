import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.test_case import TestCase
    from aitester.db.models.test_run import TestRun


class TestResult(TimestampMixin, Base):
    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False
    )

    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Actual Response Data
    actual_status_code: Mapped[int | None] = mapped_column(nullable=True)
    actual_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # AI Failure Analysis
    ai_failure_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Structured failure reason from Gemini"
    )

    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="test_results")
    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="test_results")
