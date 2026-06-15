import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.test_run import TestRun


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )

    # Summary Metrics
    total_tests: Mapped[int] = mapped_column(default=0)
    passed_tests: Mapped[int] = mapped_column(default=0)
    failed_tests: Mapped[int] = mapped_column(default=0)

    # Generated Output Paths
    html_report_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    json_report_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Overall Scores
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_executive_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="AI-generated high-level summary of the run"
    )

    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="reports")
