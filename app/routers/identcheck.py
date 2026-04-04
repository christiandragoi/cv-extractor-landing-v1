from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.identity_document import IdentityDocument
from app.models.candidate import Candidate
from app.models.audit_log import AuditLog
from app.storage.local import LocalStorage
from app.config import settings

router = APIRouter()


@router.post("/candidates/{candidate_id}/identcheck/upload")
async def upload_identity_document(
    candidate_id: str,
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    storage = LocalStorage(settings.STORAGE_ROOT)
    folder = f"candidates/{candidate_id}/identcheck"

    front_content = await front_image.read()
    front_path = f"{folder}/front_{front_image.filename}"
    await storage.save(front_path, front_content)

    back_path = None
    if back_image and back_image.filename:
        back_content = await back_image.read()
        back_path = f"{folder}/back_{back_image.filename}"
        await storage.save(back_path, back_content)

    doc = IdentityDocument(
        candidate_id=candidate_id,
        document_type=document_type,
        file_path_front=front_path,
        file_path_back=back_path,
        status="UPLOADED",
        requires_manual_review=True,
        recruiter_verified=False
    )
    db.add(doc)

    audit = AuditLog(
        candidate_id=candidate_id,
        action="IDENTCHECK_UPLOAD",
        details={"document_type": document_type}
    )
    db.add(audit)
    await db.commit()

    return {"id": str(doc.id), "status": "UPLOADED", "message": "Document uploaded. Ready for OCR (Phase 2)."}


@router.get("/candidates/{candidate_id}/identcheck")
async def get_identcheck_status(candidate_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IdentityDocument).where(IdentityDocument.candidate_id == candidate_id)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(doc.id),
            "document_type": doc.document_type,
            "status": doc.status,
            "requires_manual_review": doc.requires_manual_review,
            "recruiter_verified": doc.recruiter_verified,
            "extracted_data": {
                "surname": doc.surname,
                "given_names": doc.given_names,
                "date_of_birth": doc.date_of_birth.isoformat() if doc.date_of_birth else None,
                "place_of_birth": doc.place_of_birth,
                "nationality": doc.nationality,
                "document_number": doc.document_number,
                "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            } if doc.status != "UPLOADED" else None
        } for doc in docs
    ]


@router.post("/identcheck/{document_id}/verify")
async def verify_identity_document(document_id: str, verified_data: dict, db: AsyncSession = Depends(get_db)):
    doc = await db.get(IdentityDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field in ["surname", "given_names", "place_of_birth", "nationality", "document_number"]:
        if field in verified_data:
            setattr(doc, field, verified_data[field])

    if "date_of_birth" in verified_data and verified_data["date_of_birth"]:
        from datetime import datetime
        try:
            doc.date_of_birth = datetime.strptime(verified_data["date_of_birth"], "%Y-%m-%d").date()
        except Exception:
            pass

    if "expiry_date" in verified_data and verified_data["expiry_date"]:
        from datetime import datetime
        try:
            doc.expiry_date = datetime.strptime(verified_data["expiry_date"], "%Y-%m-%d").date()
        except Exception:
            pass

    doc.recruiter_verified = True
    doc.requires_manual_review = False
    doc.status = "VERIFIED"

    audit = AuditLog(
        candidate_id=doc.candidate_id,
        action="IDENTCHECK_VERIFIED",
        details={"document_id": document_id, "surname": doc.surname}
    )
    db.add(audit)
    await db.commit()
    return {"status": "VERIFIED", "message": "Identity data verified by recruiter"}
