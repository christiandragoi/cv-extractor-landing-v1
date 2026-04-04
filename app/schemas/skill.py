from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SkillRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_name: str
    category: str
    level: str
    years_of_experience: Optional[float] = None
    evidence: Optional[str] = None
    inferred: bool
    needs_review: bool
    is_verified: bool
