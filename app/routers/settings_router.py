from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.ai_provider import AIProvider
from app.schemas.settings import AIProviderRead, AIProviderCreate, ProviderValidationResponse
from app.ai.provider_manager import ProviderManager

router = APIRouter()


@router.get("/providers", response_model=List[AIProviderRead])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIProvider).order_by(AIProvider.priority))
    return result.scalars().all()


@router.post("/providers", status_code=201)
async def create_provider(provider: AIProviderCreate, db: AsyncSession = Depends(get_db)):
    manager = ProviderManager()
    encrypted = manager.encrypt_key(provider.api_key)
    hint = provider.api_key[-4:] if len(provider.api_key) >= 4 else "****"

    db_provider = AIProvider(
        provider_type=provider.provider_type.upper(),
        display_name=provider.display_name,
        api_key_encrypted=encrypted,
        api_key_hint=hint,
        base_url=provider.base_url,
        model_selected=provider.model_selected,
        priority=provider.priority
    )
    db.add(db_provider)
    await db.commit()
    return {"id": str(db_provider.id), "display_name": db_provider.display_name}


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    provider = await db.get(AIProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await db.delete(provider)
    await db.commit()


@router.post("/providers/{provider_id}/validate", response_model=ProviderValidationResponse)
async def validate_provider(provider_id: str, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    provider = await db.get(AIProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    manager = ProviderManager()
    try:
        instance = manager.get_provider_instance(provider)
        is_valid, latency = await instance.validate()
        provider.is_validated = is_valid
        provider.validation_last_attempt = datetime.utcnow()
        provider.validation_latency_ms = latency
        await db.commit()
        return ProviderValidationResponse(is_valid=is_valid, latency_ms=latency)
    except Exception as e:
        provider.is_validated = False
        await db.commit()
        return ProviderValidationResponse(is_valid=False, latency_ms=0, error=str(e))
