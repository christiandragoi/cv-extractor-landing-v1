"""
Database type compatibility layer.
Uses JSONB on PostgreSQL, JSON on SQLite (local dev).
Uses UUID on PostgreSQL, String on SQLite.
"""
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from app.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    from sqlalchemy import JSON

    class PGUUID(TypeDecorator):
        """Platform-independent GUID type.
        Uses PostgreSQL's UUID type, otherwise uses
        CHAR(36), storing as stringified hex values.
        """
        impl = CHAR
        cache_ok = True

        def load_dialect_impl(self, dialect):
            return dialect.type_descriptor(CHAR(36))

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            else:
                if not isinstance(value, uuid.UUID):
                    return str(uuid.UUID(str(value)))
                else:
                    return str(value)

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            else:
                if not isinstance(value, uuid.UUID):
                    value = uuid.UUID(str(value))
                return value

    JSONB = JSON
else:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB  # noqa: F401

__all__ = ["PGUUID", "JSONB"]
