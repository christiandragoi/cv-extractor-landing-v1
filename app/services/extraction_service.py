import json
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.candidate import Candidate
from app.models.employment import EmploymentRecord
from app.models.skill import SkillRecord
from app.models.language import LanguageRecord
from app.domain.normalization import strip_gdpr_data, detect_gaps
from app.ai.provider_manager import ProviderManager


class ExtractionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider_manager = ProviderManager()

    async def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file."""
        from pathlib import Path
        import aiofiles
        full_path = Path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = full_path.suffix.lower()
        if suffix == ".pdf":
            import pdfplumber
            text_parts = []
            with pdfplumber.open(str(full_path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
        elif suffix in (".docx", ".doc"):
            from docx import Document
            doc = Document(str(full_path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    async def extract_and_process(self, candidate_id: str):
        candidate = await self.db.get(Candidate, candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        candidate.status = "EXTRACTING"
        await self.db.commit()

        try:
            from app.config import settings
            from app.storage.local import LocalStorage
            storage = LocalStorage(settings.STORAGE_ROOT)
            raw_bytes = await storage.read(candidate.original_file_path)

            # Write to temp file for text extraction
            import tempfile
            from pathlib import Path
            suffix = Path(candidate.original_filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(raw_bytes)
                tmp_path = tmp.name

            try:
                raw_text = await self.extract_text_from_file(tmp_path)
            finally:
                import os
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            cleaned_text, removed_pii = strip_gdpr_data(raw_text)

            messages = [
                {"role": "system", "content": "You are a German recruitment CV parser. Extract structured data and return ONLY valid JSON."},
                {"role": "user", "content": f"""Extract from this CV text and return JSON with these fields:
{{
  "full_name": "string",
  "date_of_birth": "YYYY-MM-DD or null",
  "nationality": "string",
  "employment_history": [{{"company_name":"","job_title":"","start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD or null","is_current":false,"description":[]}}],
  "skills": [{{"name":"","category":"TECHNICAL|SOFT|LANGUAGE|SONSTIGES","level":"EXPERTE|FORTGESCHRITTEN|KENNTNISSE","evidence":""}}],
  "languages": [{{"language":"","level_raw":"","level_normalized":"A1|A2|B1|B2|C1|C2|NATIVE"}}]
}}

CV TEXT:
{cleaned_text[:4000]}"""}
            ]

            start_time = time.time()
            result_json, provider_name, model = await self.provider_manager.try_extraction(messages, self.db)
            duration_ms = int((time.time() - start_time) * 1000)

            result = json.loads(result_json)

            candidate.extraction_provider = provider_name
            candidate.extraction_model = model
            candidate.extraction_duration_ms = duration_ms
            candidate.full_name = result.get("full_name")
            candidate.nationality = result.get("nationality")

            dob_str = result.get("date_of_birth")
            if dob_str:
                try:
                    from datetime import datetime
                    candidate.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except Exception:
                    pass

            employment_data = result.get("employment_history", [])
            gaps = detect_gaps(employment_data)

            for emp in employment_data + gaps:
                from datetime import datetime
                def parse_date(d):
                    if not d:
                        return None
                    try:
                        return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                    except Exception:
                        return None

                record = EmploymentRecord(
                    candidate_id=candidate_id,
                    company_name=emp.get("company_name", "Unknown"),
                    job_title=emp.get("job_title", "Unknown"),
                    job_title_original=emp.get("job_title"),
                    start_date=parse_date(emp.get("start_date")),
                    end_date=parse_date(emp.get("end_date")),
                    is_current=emp.get("is_current", False),
                    description=emp.get("description", []),
                    is_gap_record=emp.get("is_gap_record", False),
                    gap_type=emp.get("gap_type"),
                    gap_note=emp.get("gap_note"),
                    inferred=emp.get("is_gap_record", False) or emp.get("inferred", False),
                    needs_review=True
                )
                self.db.add(record)

            for skill in result.get("skills", []):
                record = SkillRecord(
                    candidate_id=candidate_id,
                    skill_name=skill.get("name", ""),
                    category=skill.get("category", "SONSTIGES"),
                    level=skill.get("level", "KENNTNISSE"),
                    evidence=skill.get("evidence"),
                    inferred=True,
                    needs_review=True
                )
                self.db.add(record)

            for lang in result.get("languages", []):
                record = LanguageRecord(
                    candidate_id=candidate_id,
                    language=lang.get("language", ""),
                    level_raw=lang.get("level_raw"),
                    level_normalized=lang.get("level_normalized", "A1"),
                    inferred=True,
                    needs_review=True
                )
                self.db.add(record)

            candidate.status = "EXTRACTED"
            candidate.needs_review = True
            await self.db.commit()

        except Exception as e:
            candidate.status = "FAILED"
            candidate.error_log = {"error": str(e)}
            await self.db.commit()
            raise
