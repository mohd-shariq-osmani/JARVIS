import os
import json
import logging
from pydantic import BaseModel
from typing import Dict, Any, Callable, List

logger = logging.getLogger("ConfigManager")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ai.json')

class AISettings(BaseModel):
    provider: str = "lmstudio"  # "lmstudio", "openrouter", "auto"
    lmstudio_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_model: str = "local-model"
    openrouter_key: str = ""
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"
    routing_mode: str = "manual"  # "manual", "auto"

class ConfigManager:
    def __init__(self):
        self.settings = AISettings()
        self._listeners: List[Callable[[AISettings], None]] = []
        self.load()

    def add_listener(self, callback: Callable[[AISettings], None]):
        self._listeners.append(callback)

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.settings = AISettings(**data)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings.dict(), f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_settings(self) -> AISettings:
        return self.settings

    def update_settings(self, new_settings: Dict[str, Any]):
        current = self.settings.dict()
        current.update(new_settings)
        self.settings = AISettings(**current)
        self.save()
        # Notify all listeners
        for listener in self._listeners:
            try:
                listener(self.settings)
            except Exception as e:
                logger.error(f"Error executing config listener: {e}")

# Global singleton
config_manager = ConfigManager()
