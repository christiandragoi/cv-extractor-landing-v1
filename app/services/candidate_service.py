from pathlib import Path
from uuid import uuid4
import hashlib
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

    @staticmethod
    def _file_hash(content: bytes) -> str:
        """SHA-256 hash of file content for duplicate detection."""
        return hashlib.sha256(content).hexdigest()

    async def _find_duplicate(self, filename: str, content_hash: str) -> Candidate:
        """Check if an identical file was already uploaded. Returns existing candidate or None."""
        # Primary: match by content hash (catches identical files with different names)
        result = await self.db.execute(
            select(Candidate).where(Candidate.original_filename == filename)
        )
        candidates = result.scalars().all()
        for c in candidates:
            # Read stored file and compare hash
            try:
                stored = await self.storage.read(c.original_file_path)
                if hashlib.sha256(stored).hexdigest() == content_hash:
                    return c
            except Exception:
                continue
        return None

    async def create_candidate(self, filename: str, content: bytes, job_profile_id=None, recruiter_notes=None) -> Candidate:
        # Duplicate detection: reject if exact same file already exists
        dup = await self._find_duplicate(filename, self._file_hash(content))
        if dup:
            # Return existing candidate instead of creating a duplicate
            return await self.get_candidate(dup.id)
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
        
        # Explicit eager load step before returning the object to Pydantic
        return await self.get_candidate(candidate_id)

    async def get_candidate(self, candidate_id: str) -> Candidate:
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Candidate)
            .options(
                selectinload(Candidate.employment_history),
                selectinload(Candidate.skill_records),
                selectinload(Candidate.language_records)
            )
            .where(Candidate.id == candidate_id)
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
