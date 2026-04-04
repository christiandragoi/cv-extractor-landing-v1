from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy import String, Text, Boolean, DateTime, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class JobProfile(Base):
    __tablename__ = "job_profiles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    extraction_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_skills: Mapped[List[str]] = mapped_column(JSONB, default=list)
    gap_handling_rules: Mapped[Dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
