from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: Optional[str] = None
    DATABASE_URL: str = "postgresql+asyncpg://cv_user:cv_pass@localhost:5432/cvextractor"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "/app/storage"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://localhost"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        origins = self.CORS_ORIGINS
        if origins.startswith("["):
            import json
            try:
                return json.loads(origins)
            except Exception:
                pass
        return [o.strip() for o in origins.split(",") if o.strip()]

    @property
    def encryption_key_bytes(self) -> bytes:
        import base64
        if not self.ENCRYPTION_KEY:
            return base64.urlsafe_b64encode(b'development-key-32bytes-long!!!')
        try:
            return base64.urlsafe_b64decode(self.ENCRYPTION_KEY)
        except Exception:
            return base64.urlsafe_b64encode(self.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0'))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
