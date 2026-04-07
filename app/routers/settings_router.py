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


@router.patch("/providers/{provider_id}")
async def update_provider(provider_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    provider = await db.get(AIProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if "display_name" in data:
        provider.display_name = data["display_name"]
    if "priority" in data:
        provider.priority = data["priority"]
    if "model_selected" in data:
        provider.model_selected = data["model_selected"]
    if "api_key" in data and data["api_key"]:
        manager = ProviderManager()
        provider.api_key_encrypted = manager.encrypt_key(data["api_key"])
        provider.api_key_hint = data["api_key"][-4:] if len(data["api_key"]) >= 4 else "****"
    
    await db.commit()
    return {"status": "success"}


from app.models.system_setting import SystemSetting
from app.schemas.settings import SystemSettingRead

@router.get("/system", response_model=List[SystemSettingRead])
async def list_system_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting))
    return result.scalars().all()

@router.patch("/system/{setting_id}")
async def update_system_setting(setting_id: str, data: dict, db: AsyncSession = Depends(get_db)):
    setting = await db.get(SystemSetting, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if "value" in data and data["value"]:
        manager = ProviderManager()
        setting.value_encrypted = manager.encrypt_key(data["value"])
        setting.value_hint = data["value"][-4:] if len(data["value"]) >= 4 else "****"
    
    if "is_active" in data:
        setting.is_active = data["is_active"]
        
    await db.commit()
    return {"status": "success"}

