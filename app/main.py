import uuid
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.routers import candidates, processing, review, settings_router, identcheck, downloads, templates, extraction
import app.models  # <--- CRITICAL: Import all models so Base.metadata populates BEFORE create_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified OK")
    except Exception as e:
        logger.error(f"Database init failed (will retry on requests): {e}")
    yield
    await engine.dispose()


app = FastAPI(title="CV Extractor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc),
            "request_id": request_id
        }
    )


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


app.include_router(candidates.router, prefix="/api/v1")
app.include_router(processing.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1/settings")
app.include_router(identcheck.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1/templates")
app.include_router(extraction.router, prefix="/api/v1/extraction")

# Only mount static files if the directory exists (prevents crash in containers)
_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.isdir(_static_dir):
    _static_dir = "static"

if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
    logger.info(f"Static files mounted from: {_static_dir}")
else:
    logger.warning("Static directory not found — skipping static file mount")


@app.get("/")
async def root():
    return {"service": "CV Extractor API", "version": "1.0.0", "docs": "/docs"}

