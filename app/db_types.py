"""
Database type compatibility layer.
Uses JSONB on PostgreSQL, JSON on SQLite (local dev).
Uses UUID on PostgreSQL, String on SQLite.
"""
from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    from sqlalchemy import JSON, String as _String

    class PGUUID(_String):
        """UUID as String for SQLite compatibility."""
        def __init__(self, as_uuid=True, *args, **kwargs):
            super().__init__(length=36)

    JSONB = JSON
else:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB  # noqa: F401

__all__ = ["PGUUID", "JSONB"]
