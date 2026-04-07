import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.candidate_service import CandidateService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_extraction_bg(candidate_id: str):
    """Run extraction as a FastAPI background task (shares no session with request)."""
    from app.database import AsyncSessionLocal
    from app.services.extraction_service import ExtractionService
    print(f"[BGTASK] Starting extraction for {candidate_id}...")
    async with AsyncSessionLocal() as db:
        service = ExtractionService(db)
        try:
            await service.extract_and_process(candidate_id)
            print(f"[BGTASK] Completed successfully for {candidate_id}")
        except Exception as e:
            print(f"[BGTASK] FAILED for {candidate_id}: {e}")
            logger.error(f"Background extraction failed for {candidate_id}: {e}")


@router.post("/candidates/{candidate_id}/extract")
async def trigger_extraction(
    candidate_id: str,
    instructions: str = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    print("BACKEND_EXTRACTION_HIT", f"Candidate ID: {candidate_id}, Instructions: {instructions}")
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status not in ["UPLOADED", "FAILED", "EXTRACTED", "PENDING_REVIEW", "APPROVED"]:
        raise HTTPException(status_code=400, detail=f"Cannot extract from status: {candidate.status}")

    # Reset status if re-extracting
    if candidate.status != "UPLOADED":
        from sqlalchemy import update
        from app.models.candidate import Candidate
        await db.execute(
            update(Candidate)
            .where(Candidate.id == candidate_id)
            .values(status="UPLOADED", error_log=None)
        )
        await db.commit()

    # Fire extraction as a FastAPI BackgroundTask (runs in same event loop, error logged)
    background_tasks.add_task(_run_extraction_bg, candidate_id)
    return {"task_id": f"bg-{candidate_id}", "candidate_id": candidate_id, "status": "queued"}


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
        "extraction_model": candidate.extraction_model,
        # Surface backend error so frontend can display it on FAILED
        "error": candidate.error_log.get("error") if isinstance(candidate.error_log, dict) else None,
    }


def _calculate_progress(status: str) -> int:
    return {
        "UPLOADED": 10, "EXTRACTING": 40, "EXTRACTED": 60,
        "PENDING_REVIEW": 70, "APPROVED": 80,
        "GENERATING_STAGE2": 90, "COMPLETED": 100
    }.get(status, 0)
