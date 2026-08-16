from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.core.config import config_manager, AISettings
import httpx

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/")
async def get_settings():
    return config_manager.get_settings()

@router.post("/")
async def update_settings(settings: Dict[str, Any]):
    try:
        config_manager.update_settings(settings)
        return {"status": "success", "settings": config_manager.get_settings()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-connection")
async def test_connection(payload: Dict[str, Any]):
    provider = payload.get("provider", "lmstudio")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "lmstudio":
                url = payload.get("lmstudio_url", "http://127.0.0.1:1234/v1")
                res = await client.get(f"{url.rstrip('/')}/models")
                if res.status_code == 200:
                    models = [m.get("id") for m in res.json().get("data", [])]
                    return {"status": "success", "message": f"Connected! Found {len(models)} model(s).", "models": models}
                return {"status": "error", "message": f"LM Studio responded with HTTP {res.status_code}"}
            elif provider == "openrouter":
                key = payload.get("openrouter_key", "")
                if not key:
                    return {"status": "error", "message": "API key is empty"}
                headers = {
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": "http://localhost:5173",
                    "X-Title": "JARVIS Assistant"
                }
                res = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
                if res.status_code == 200:
                    return {"status": "success", "message": "OpenRouter API Key is valid and active!"}
                return {"status": "error", "message": f"OpenRouter authentication failed: HTTP {res.status_code}"}
            else:
                return {"status": "error", "message": f"Unknown provider: {provider}"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}
