from typing import List, Dict, Type
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
from app.models.ai_provider import AIProvider
from app.ai.base_provider import BaseAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.circuit_breaker import CircuitBreaker
from app.config import settings

PROVIDER_MAP: Dict[str, Type[BaseAIProvider]] = {
    "OPENAI": OpenAIProvider,
    "OPENROUTER": OpenAIProvider,
    "TOGETHER": OpenAIProvider,
    "XAI": OpenAIProvider,
    "DEEPSEEK": OpenAIProvider,
    "MINIMAX": OpenAIProvider,
    "KIMI": OpenAIProvider,
    "QWEN": OpenAIProvider,
    "GROQ": OpenAIProvider,
}

PROVIDER_BASE_URLS = {
    "OPENROUTER": "https://openrouter.ai/api/v1",
    "TOGETHER": "https://api.together.xyz/v1",
    "XAI": "https://api.x.ai/v1",
    "DEEPSEEK": "https://api.deepseek.com",
    "KIMI": "https://api.moonshot.cn/v1",
    "QWEN": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "GROQ": "https://api.groq.com/openai/v1",
}


class ProviderManager:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self._fernet = Fernet(settings.encryption_key_bytes)

    def encrypt_key(self, plain_key: str) -> bytes:
        return self._fernet.encrypt(plain_key.encode())

    def decrypt_key(self, encrypted_key: bytes) -> str:
        return self._fernet.decrypt(encrypted_key).decode()

    def get_provider_instance(self, provider: AIProvider) -> BaseAIProvider:
        provider_class = PROVIDER_MAP.get(provider.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider.provider_type}")
        api_key = self.decrypt_key(provider.api_key_encrypted)
        base_url = provider.base_url or PROVIDER_BASE_URLS.get(provider.provider_type)
        return provider_class(api_key, provider.model_selected, base_url)

    async def get_active_providers(self, db: AsyncSession) -> List[AIProvider]:
        from sqlalchemy import select
        result = await db.execute(
            select(AIProvider)
            .where(AIProvider.is_active == True)
            .order_by(AIProvider.priority)
        )
        return result.scalars().all()

    async def try_extraction(self, messages: List[Dict], db: AsyncSession) -> tuple[str, str, str]:
        providers = await self.get_active_providers(db)
        if not providers:
            raise Exception("No active AI providers configured")

        for provider in providers:
            if not self.circuit_breaker.can_attempt(provider):
                continue
            try:
                instance = self.get_provider_instance(provider)
                result = await instance.chat_complete(messages)
                self.circuit_breaker.record_success(provider)
                return result, provider.display_name, provider.model_selected
            except Exception:
                self.circuit_breaker.record_failure(provider)
                continue

        raise Exception("All AI providers failed")
