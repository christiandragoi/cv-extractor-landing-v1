import httpx
from typing import List, Dict
from app.ai.base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = None):
        super().__init__(api_key, model, base_url)
        self.api_url = (base_url or "https://api.openai.com/v1") + "/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.1) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def validate(self) -> tuple[bool, int]:
        import time
        start = time.time()
        try:
            await self.chat_complete(
                [{"role": "user", "content": 'Reply with JSON: {"status": "ok"}'}],
                max_tokens=50
            )
            latency = int((time.time() - start) * 1000)
            return True, latency
        except Exception:
            latency = int((time.time() - start) * 1000)
            return False, latency
