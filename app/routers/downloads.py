from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.candidate import Candidate
from app.models.identity_document import IdentityDocument
from app.models.audit_log import AuditLog
from app.storage.local import LocalStorage
from app.config import settings

router = APIRouter()


@router.get("/candidates/{candidate_id}/download/structured-cv")
async def download_structured_cv(candidate_id: str, db: AsyncSession = Depends(get_db)):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate or not candidate.structured_cv_path:
        raise HTTPException(status_code=404, detail="Structured CV not found")

    storage = LocalStorage(settings.STORAGE_ROOT)
    if not storage.exists(candidate.structured_cv_path):
        raise HTTPException(status_code=404, detail="File not found on storage")

    return FileResponse(
        path=str(storage._full_path(candidate.structured_cv_path)),
        filename=f"{candidate.full_name or 'candidate'}_structured.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/candidates/{candidate_id}/download/final-cv")
async def download_final_cv(candidate_id: str, db: AsyncSession = Depends(get_db)):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Final CV only available after Stage 2 completion")
    if not candidate.final_cv_path:
        raise HTTPException(status_code=404, detail="Final CV not generated")

    storage = LocalStorage(settings.STORAGE_ROOT)
    return FileResponse(
        path=str(storage._full_path(candidate.final_cv_path)),
        filename=f"{candidate.full_name or 'candidate'}_final.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.post("/identcheck/{document_id}/confirm-download")
async def confirm_download_identcheck(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(IdentityDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    if not doc.recruiter_verified:
        raise HTTPException(status_code=400, detail="Must be verified before download")
    if doc.status != "VERIFIED":
        raise HTTPException(status_code=400, detail="Must complete verification workflow")

    audit = AuditLog(
        candidate_id=doc.candidate_id,
        action="IDENTCHECK_EXPORT",
        details={"document_id": document_id, "surname": doc.surname}
    )
    db.add(audit)
    doc.status = "EXPORTED"
    await db.commit()

    return {
        "download_url": f"/api/v1/identcheck/{document_id}/download-file",
        "expires_in": "1 hour"
    }
