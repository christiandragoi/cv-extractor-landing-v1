from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AIProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_type: str
    display_name: str
    api_key_hint: str
    model_selected: str
    is_active: bool
    is_validated: bool
    priority: int
    circuit_breaker_state: str


class AIProviderCreate(BaseModel):
    provider_type: str
    display_name: str
    api_key: str
    model_selected: str
    base_url: Optional[str] = None
    priority: int = 1


class ProviderValidationResponse(BaseModel):
    is_valid: bool
    latency_ms: int
    error: Optional[str] = None
