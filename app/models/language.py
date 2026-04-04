from typing import Optional
from uuid import UUID
from sqlalchemy import String, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LanguageRecord(Base):
    __tablename__ = "language_records"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    candidate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)

    language: Mapped[str] = mapped_column(String(100), nullable=False)
    level_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    level_normalized: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    inferred: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="language_records")
