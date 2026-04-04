from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CandidateStatus(BaseModel):
    id: UUID
    status: str
    needs_review: bool
    progress_pct: Optional[int] = None
    current_step: Optional[str] = None
    error: Optional[str] = None


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    needs_review: bool
    original_filename: str
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    structured_cv_path: Optional[str] = None
    final_cv_path: Optional[str] = None
    extraction_provider: Optional[str] = None
    extraction_model: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    approved_by: Optional[str] = None


class CandidateCreate(BaseModel):
    job_profile_id: Optional[UUID] = None
    recruiter_notes: Optional[str] = None
