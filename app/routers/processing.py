from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.candidate_service import CandidateService
from app.tasks.extraction_tasks import extract_candidate_cv

router = APIRouter()


@router.post("/candidates/{candidate_id}/extract")
async def trigger_extraction(candidate_id: str, db: AsyncSession = Depends(get_db)):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status not in ["UPLOADED", "FAILED"]:
        raise HTTPException(status_code=400, detail=f"Cannot extract from status: {candidate.status}")

    task = extract_candidate_cv.delay(candidate_id)
    return {"task_id": task.id, "candidate_id": candidate_id, "status": "queued"}


@router.get("/candidates/{candidate_id}/status")
async def get_status(candidate_id: str, db: AsyncSession = Depends(get_db)):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "id": str(candidate.id),
        "status": candidate.status,
        "needs_review": candidate.needs_review,
        "progress_pct": _calculate_progress(candidate.status),
        "current_step": candidate.status,
        "extraction_provider": candidate.extraction_provider,
        "extraction_model": candidate.extraction_model
    }


def _calculate_progress(status: str) -> int:
    return {
        "UPLOADED": 10, "EXTRACTING": 40, "EXTRACTED": 60,
        "PENDING_REVIEW": 70, "APPROVED": 80,
        "GENERATING_STAGE2": 90, "COMPLETED": 100
    }.get(status, 0)
