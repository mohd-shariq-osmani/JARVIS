from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.core.config import config_manager, AISettings

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
