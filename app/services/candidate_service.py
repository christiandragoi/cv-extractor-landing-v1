from pathlib import Path
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.candidate import Candidate
from app.models.audit_log import AuditLog
from app.storage.local import LocalStorage
from app.config import settings


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = LocalStorage(settings.STORAGE_ROOT)

    async def create_candidate(self, filename: str, content: bytes, job_profile_id=None, recruiter_notes=None) -> Candidate:
        candidate_id = str(uuid4())
        folder_path = f"candidates/{candidate_id}"
        file_path = f"{folder_path}/original_{filename}"

        await self.storage.save(file_path, content)

        candidate = Candidate(
            id=candidate_id,
            status="UPLOADED",
            original_filename=filename,
            original_file_path=file_path,
            job_profile_id=job_profile_id,
            recruiter_notes=recruiter_notes,
            needs_review=True
        )
        self.db.add(candidate)
        await self.db.flush()

        audit = AuditLog(
            candidate_id=candidate_id,
            action="UPLOAD",
            details={"filename": filename, "size": len(content)}
        )
        self.db.add(audit)
        await self.db.commit()
        return candidate

    async def get_candidate(self, candidate_id: str) -> Candidate:
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, candidate_id: str, status: str, error_log=None):
        candidate = await self.get_candidate(candidate_id)
        if candidate:
            candidate.status = status
            if error_log:
                candidate.error_log = error_log
            await self.db.commit()
        return candidate
