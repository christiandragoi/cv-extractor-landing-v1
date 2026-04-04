from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.candidate import Candidate
from app.models.employment import EmploymentRecord

router = APIRouter()


@router.get("/candidates/{candidate_id}/review")
async def get_review_data(candidate_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Not found")

    needs_review_count = sum(1 for emp in candidate.employment_history if emp.needs_review)
    needs_review_count += sum(1 for skill in candidate.skill_records if skill.needs_review)

    return {
        "candidate": {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "date_of_birth": candidate.date_of_birth.isoformat() if candidate.date_of_birth else None,
            "nationality": candidate.nationality,
            "needs_review": candidate.needs_review,
            "status": candidate.status,
        },
        "employment_history": [
            {
                "id": str(emp.id),
                "company_name": emp.company_name,
                "job_title": emp.job_title,
                "start_date": emp.start_date.isoformat() if emp.start_date else None,
                "end_date": emp.end_date.isoformat() if emp.end_date else None,
                "is_current": emp.is_current,
                "is_gap_record": emp.is_gap_record,
                "gap_type": emp.gap_type,
                "gap_note": emp.gap_note,
                "inferred": emp.inferred,
                "needs_review": emp.needs_review,
            } for emp in sorted(candidate.employment_history, key=lambda e: e.start_date or __import__('datetime').date.min, reverse=True)
        ],
        "skills": [
            {
                "id": str(skill.id),
                "skill_name": skill.skill_name,
                "level": skill.level,
                "category": skill.category,
                "inferred": skill.inferred,
                "needs_review": skill.needs_review,
            } for skill in candidate.skill_records
        ],
        "languages": [
            {
                "id": str(lang.id),
                "language": lang.language,
                "level_normalized": lang.level_normalized,
                "level_raw": lang.level_raw,
            } for lang in candidate.language_records
        ],
        "needs_review_count": needs_review_count
    }


@router.patch("/candidates/{candidate_id}/review")
async def update_review(candidate_id: str, updates: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Not found")

    if "full_name" in updates:
        candidate.full_name = updates["full_name"]
    if "nationality" in updates:
        candidate.nationality = updates["nationality"]

    for emp_update in updates.get("employment_updates", []):
        emp = await db.get(EmploymentRecord, emp_update["id"])
        if emp and str(emp.candidate_id) == candidate_id:
            for field in ["gap_type", "gap_note", "needs_review", "company_name", "job_title"]:
                if field in emp_update:
                    setattr(emp, field, emp_update[field])

    await db.commit()
    return {"status": "updated"}


@router.post("/candidates/{candidate_id}/approve")
async def approve_candidate(candidate_id: str, approved_by: str = "recruiter", db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Not found")
    if candidate.status != "EXTRACTED":
        raise HTTPException(status_code=400, detail="Can only approve EXTRACTED candidates")

    unreviewed = sum(1 for emp in candidate.employment_history if emp.needs_review)
    unreviewed += sum(1 for skill in candidate.skill_records if skill.needs_review)
    if unreviewed > 0:
        raise HTTPException(status_code=400, detail=f"{unreviewed} items still need review")

    candidate.status = "APPROVED"
    candidate.approval_timestamp = datetime.utcnow()
    candidate.approved_by = approved_by
    candidate.needs_review = False
    await db.commit()
    return {"status": "approved", "approved_by": approved_by}
