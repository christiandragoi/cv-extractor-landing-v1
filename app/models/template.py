from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Boolean, DateTime, Float, func
from app.db_types import PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Template(Base):
    __tablename__ = "templates"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    template_type: Mapped[str] = mapped_column(String(50), default="lebenslauf")  # lebenslauf, anschreiben, zeugnis
    file_path: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    fields: Mapped[List[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
