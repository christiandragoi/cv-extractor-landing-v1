from datetime import datetime
from typing import Optional, Dict
import uuid
from uuid import UUID
from sqlalchemy import String, DateTime, ForeignKey, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[UUID] = mapped_column(PGUUID(), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="audit_logs")
