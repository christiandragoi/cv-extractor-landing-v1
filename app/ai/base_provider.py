from abc import ABC, abstractmethod
from typing import List, Dict


class BaseAIProvider(ABC):
    def __init__(self, api_key: str, model: str, base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @abstractmethod
    async def chat_complete(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.1) -> str:
        pass

    @abstractmethod
    async def validate(self) -> tuple[bool, int]:
        pass
