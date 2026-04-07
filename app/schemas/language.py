from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LanguageRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    language: str
    level_raw: Optional[str] = None
    level_normalized: str
    evidence: Optional[str] = None
    inferred: bool
    needs_review: bool


class LanguageRecordUpdate(BaseModel):
    language: Optional[str] = None
    level_raw: Optional[str] = None
    level_normalized: Optional[str] = None
    needs_review: Optional[bool] = None
