from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from app.database import get_db
from app.services.candidate_service import CandidateService
from app.schemas.candidate import CandidateRead

router = APIRouter()


@router.post("/candidates/upload", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    job_profile_id: Optional[str] = Form(None),
    recruiter_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files allowed")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    service = CandidateService(db)
    candidate = await service.create_candidate(
        filename=file.filename,
        content=content,
        job_profile_id=job_profile_id,
        recruiter_notes=recruiter_notes
    )
    return candidate


@router.get("/candidates", response_model=List[CandidateRead])
async def list_candidates(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    from app.models.candidate import Candidate
    result = await db.execute(
        select(Candidate).order_by(Candidate.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/candidates/{candidate_id}", response_model=CandidateRead)
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.delete("/candidates/{candidate_id}", status_code=204)
async def delete_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.candidate import Candidate
    from app.storage.local import LocalStorage
    from app.config import settings
    import shutil, os

    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Not found")

    await db.delete(candidate)
    await db.commit()

    # Clean up storage
    storage_path = f"{settings.STORAGE_ROOT}/candidates/{candidate_id}"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path, ignore_errors=True)
