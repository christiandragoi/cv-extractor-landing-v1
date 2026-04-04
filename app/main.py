import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.routers import candidates, processing, review, settings_router, identcheck, downloads


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="CV Extractor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")
