from datetime import date
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Date, Integer, ForeignKey, Boolean, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EmploymentRecord(Base):
    __tablename__ = "employment_records"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    candidate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title_original: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[List[str]] = mapped_column(JSONB, default=list)

    is_gap_record: Mapped[bool] = mapped_column(Boolean, default=False)
    gap_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gap_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    technologies: Mapped[List[str]] = mapped_column(JSONB, default=list)

    inferred: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="employment_history")
