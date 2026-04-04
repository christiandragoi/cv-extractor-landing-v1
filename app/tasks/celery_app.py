try:
    from celery import Celery
    from app.config import settings

    celery_app = Celery(
        "cv_extractor",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.tasks.extraction_tasks"]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        worker_prefetch_multiplier=1,
    )
except ImportError:
    # Local dev: celery not installed — stub it so imports don't fail
    import logging
    logging.getLogger(__name__).warning("Celery not installed — running in local mode without async task queue")

    class _StubTask:
        def delay(self, *args, **kwargs):
            return type("FakeTask", (), {"id": "local-sync"})()

    class _StubCelery:
        def task(self, *args, **kwargs):
            def decorator(fn):
                return _StubTask()
            return decorator

    celery_app = _StubCelery()
