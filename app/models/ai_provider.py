from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, DateTime, Integer, Boolean, LargeBinary, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AIProvider(Base):
    __tablename__ = "ai_providers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    api_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    api_key_hint: Mapped[str] = mapped_column(String(10), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_selected: Mapped[str] = mapped_column(String(100), nullable=False)
    models_available: Mapped[List[str]] = mapped_column(JSONB, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_last_attempt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)

    circuit_breaker_failures: Mapped[int] = mapped_column(Integer, default=0)
    circuit_breaker_last_failure: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    circuit_breaker_state: Mapped[str] = mapped_column(String(20), default="CLOSED")
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
