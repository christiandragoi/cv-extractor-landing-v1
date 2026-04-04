from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: Optional[str] = None
    DATABASE_URL: str = "postgresql+asyncpg://cv_user:cv_pass@localhost:5432/cvextractor"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "/app/storage"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost"]

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def encryption_key_bytes(self) -> bytes:
        import base64
        if not self.ENCRYPTION_KEY:
            return base64.urlsafe_b64encode(b'development-key-32bytes-long!!!')
        try:
            return base64.urlsafe_b64decode(self.ENCRYPTION_KEY)
        except Exception:
            return base64.urlsafe_b64encode(self.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0'))

    class Config:
        env_file = ".env"


settings = Settings()
