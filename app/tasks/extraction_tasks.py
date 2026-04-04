import asyncio
import logging
from app.database import AsyncSessionLocal
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

try:
    from app.tasks.celery_app import celery_app

    @celery_app.task(bind=True, max_retries=3)
    def extract_candidate_cv(self, candidate_id: str):
        try:
            asyncio.run(_run_extraction(candidate_id))
            return {"status": "completed", "candidate_id": candidate_id}
        except Exception as exc:
            self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

except (ImportError, Exception):
    # Local mode: run extraction synchronously in background thread
    import threading

    def extract_candidate_cv(candidate_id: str):
        """Local sync fallback — runs extraction in a background thread."""
        logger.info(f"[Local mode] Starting extraction for {candidate_id}")

        def _run():
            try:
                asyncio.run(_run_extraction(candidate_id))
                logger.info(f"[Local mode] Extraction completed for {candidate_id}")
            except Exception as e:
                logger.error(f"[Local mode] Extraction failed for {candidate_id}: {e}")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return type("FakeTask", (), {"id": f"local-{candidate_id}"})()


async def _run_extraction(candidate_id: str):
    async with AsyncSessionLocal() as db:
        service = ExtractionService(db)
        await service.extract_and_process(candidate_id)

