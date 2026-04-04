from typing import Optional
from uuid import UUID
from sqlalchemy import String, ForeignKey, Float, Boolean, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SkillRecord(Base):
    __tablename__ = "skill_records"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    candidate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)

    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    years_of_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    inferred: Mapped[bool] = mapped_column(Boolean, default=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="skill_records")
