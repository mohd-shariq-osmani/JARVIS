from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None):
        pass

    @abstractmethod
    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], model: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_structured(self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def vision(self, prompt: str, base64_image: str, model: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def cancel(self):
        pass

    @abstractmethod
    async def shutdown(self):
        pass
