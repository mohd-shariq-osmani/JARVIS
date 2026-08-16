import logging
from typing import List, Dict, Any, Optional
from .provider import AIProvider
from .lmstudio import LMStudioProvider
from .openrouter import OpenRouterProvider
from app.core.config import config_manager, AISettings

logger = logging.getLogger("AIRouter")

class AIRouter(AIProvider):
    def __init__(self):
        self.lmstudio = LMStudioProvider()
        self.openrouter = OpenRouterProvider()
        self.config: AISettings = config_manager.get_settings()
        self.active_provider_name = self.config.provider
        
        # Register listener for dynamic setting changes
        config_manager.add_listener(self.on_config_changed)
        self.reload_from_config(self.config)

    def on_config_changed(self, new_settings: AISettings):
        logger.info(f"AIRouter detected config change: provider={new_settings.provider}")
        self.reload_from_config(new_settings)

    def reload_from_config(self, settings: AISettings):
        self.config = settings
        self.active_provider_name = settings.provider.lower()
        
        # Update LM Studio provider
        self.lmstudio.base_url = settings.lmstudio_url
        self.lmstudio.client.base_url = settings.lmstudio_url
        
        # Update OpenRouter provider
        self.openrouter.api_key = settings.openrouter_key
        self.openrouter.client.headers["Authorization"] = f"Bearer {settings.openrouter_key}"
        
        logger.info(f"AIRouter reconfigured. Active provider: {self.active_provider_name}")

    def get_provider(self) -> AIProvider:
        """Returns the appropriate provider based on active settings."""
        if self.active_provider_name == "openrouter":
            return self.openrouter
        return self.lmstudio

    async def initialize(self) -> bool:
        await self.lmstudio.initialize()
        if self.config.openrouter_key:
            await self.openrouter.initialize()
        return True

    async def health_check(self) -> bool:
        provider = self.get_provider()
        return await provider.health_check()

    async def list_models(self) -> List[str]:
        provider = self.get_provider()
        return await provider.list_models()

    async def chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None) -> str:
        if self.active_provider_name == "auto":
            # Auto mode: try local first, fallback to cloud
            try:
                local_model = model or self.config.lmstudio_model
                res = await self.lmstudio.chat(messages, model=local_model)
                if not res.startswith("Error"):
                    return res
                logger.warning("Local LM Studio failed in auto mode, falling back to OpenRouter...")
            except Exception as e:
                logger.warning(f"LM Studio error in auto mode: {e}. Falling back to OpenRouter...")
            
            cloud_model = model or self.config.openrouter_model
            return await self.openrouter.chat(messages, model=cloud_model)

        elif self.active_provider_name == "openrouter":
            cloud_model = model or self.config.openrouter_model
            return await self.openrouter.chat(messages, model=cloud_model)
        else:
            local_model = model or self.config.lmstudio_model
            return await self.lmstudio.chat(messages, model=local_model)

    async def stream_chat(self, messages: List[Dict[str, Any]], model: Optional[str] = None):
        if self.active_provider_name == "openrouter":
            cloud_model = model or self.config.openrouter_model
            async for chunk in self.openrouter.stream_chat(messages, model=cloud_model):
                yield chunk
        else:
            local_model = model or self.config.lmstudio_model
            async for chunk in self.lmstudio.stream_chat(messages, model=local_model):
                yield chunk

    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], model: Optional[str] = None) -> Dict[str, Any]:
        if self.active_provider_name == "auto":
            try:
                local_model = model or self.config.lmstudio_model
                res = await self.lmstudio.generate_with_tools(messages, tools, model=local_model)
                if "Error" not in res.get("content", ""):
                    return res
                logger.warning("LM Studio tool call failed in auto mode, falling back to OpenRouter...")
            except Exception as e:
                logger.warning(f"LM Studio tool call error in auto mode: {e}. Falling back to OpenRouter...")
            
            cloud_model = model or self.config.openrouter_model
            return await self.openrouter.generate_with_tools(messages, tools, model=cloud_model)

        elif self.active_provider_name == "openrouter":
            cloud_model = model or self.config.openrouter_model
            return await self.openrouter.generate_with_tools(messages, tools, model=cloud_model)
        else:
            local_model = model or self.config.lmstudio_model
            return await self.lmstudio.generate_with_tools(messages, tools, model=local_model)

    async def generate_structured(self, messages: List[Dict[str, Any]], schema: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
        provider = self.get_provider()
        target_model = (self.config.openrouter_model if self.active_provider_name == "openrouter" else self.config.lmstudio_model) if not model else model
        return await provider.generate_structured(messages, schema, model=target_model)

    async def vision(self, prompt: str, base64_image: str, model: Optional[str] = None) -> str:
        if self.active_provider_name == "openrouter":
            cloud_model = model or self.config.openrouter_model
            return await self.openrouter.vision(prompt, base64_image, model=cloud_model)
        else:
            local_model = model or self.config.lmstudio_model
            return await self.lmstudio.vision(prompt, base64_image, model=local_model)

    async def cancel(self):
        await self.lmstudio.cancel()
        await self.openrouter.cancel()

    async def shutdown(self):
        await self.lmstudio.shutdown()
        await self.openrouter.shutdown()
