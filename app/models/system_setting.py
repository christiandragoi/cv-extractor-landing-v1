from datetime import datetime
from typing import Optional
import uuid
from uuid import UUID
from sqlalchemy import String, DateTime, Boolean, LargeBinary, func
from app.db_types import PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[UUID] = mapped_column(PGUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    key_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    value_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    value_hint: Mapped[str] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
