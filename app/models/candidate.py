from datetime import date, datetime
from typing import Optional, List
import uuid
from uuid import UUID
from sqlalchemy import String, Date, DateTime, Text, ForeignKey, Boolean, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(PGUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOADED")

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    structured_cv_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    final_cv_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    job_profile_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(), ForeignKey("job_profiles.id"), nullable=True)
    recruiter_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extraction_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extraction_duration_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    error_log: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    approval_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)

    employment_history: Mapped[List["EmploymentRecord"]] = relationship(
        "EmploymentRecord", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    education_records: Mapped[List["EducationRecord"]] = relationship(
        "EducationRecord", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    language_records: Mapped[List["LanguageRecord"]] = relationship(
        "LanguageRecord", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    skill_records: Mapped[List["SkillRecord"]] = relationship(
        "SkillRecord", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    identity_documents: Mapped[List["IdentityDocument"]] = relationship(
        "IdentityDocument", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
