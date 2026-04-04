from datetime import date, datetime
from typing import Optional, Dict
from uuid import UUID
from sqlalchemy import String, Date, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class IdentityDocument(Base):
    __tablename__ = "identity_documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    candidate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path_front: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_path_back: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    generated_docx_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    surname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    given_names: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    place_of_birth: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    confidence_scores: Mapped[Dict] = mapped_column(JSONB, default=dict)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=True)
    recruiter_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="UPLOADED")

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="identity_documents")
