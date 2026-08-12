import os
import json
from pydantic import BaseModel
from typing import Dict, Any

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ai.json')

class AISettings(BaseModel):
    provider: str = "lmstudio"
    lmstudio_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_model: str = "local-model"
    openrouter_key: str = ""
    openrouter_model: str = "google/gemini-pro-1.5"

class ConfigManager:
    def __init__(self):
        self.settings = AISettings()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.settings = AISettings(**data)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings.dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_settings(self) -> AISettings:
        return self.settings

    def update_settings(self, new_settings: Dict[str, Any]):
        current = self.settings.dict()
        current.update(new_settings)
        self.settings = AISettings(**current)
        self.save()

# Global singleton
config_manager = ConfigManager()
