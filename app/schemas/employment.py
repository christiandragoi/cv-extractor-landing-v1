from datetime import date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EmploymentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_name: str
    job_title: str
    job_title_original: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    location: Optional[str] = None
    description: List[str]
    is_gap_record: bool
    gap_type: Optional[str] = None
    gap_note: Optional[str] = None
    inferred: bool
    needs_review: bool


class EmploymentRecordUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gap_type: Optional[str] = None
    gap_note: Optional[str] = None
    needs_review: Optional[bool] = None
