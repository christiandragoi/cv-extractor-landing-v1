import asyncio
from app.tasks.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.extraction_service import ExtractionService


@celery_app.task(bind=True, max_retries=3)
def extract_candidate_cv(self, candidate_id: str):
    try:
        asyncio.run(_run_extraction(candidate_id))
        return {"status": "completed", "candidate_id": candidate_id}
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _run_extraction(candidate_id: str):
    async with AsyncSessionLocal() as db:
        service = ExtractionService(db)
        await service.extract_and_process(candidate_id)
