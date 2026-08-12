from fastapi import APIRouter
from app.ai.lmstudio import LMStudioProvider
from app.ai.openrouter import OpenRouterProvider

router = APIRouter()
lmstudio = LMStudioProvider()
openrouter = OpenRouterProvider()

@router.get("/diagnostics")
async def run_diagnostics():
    lm_status = await lmstudio.health_check()
    or_status = await openrouter.health_check()
    
    import psutil
    import platform
    
    return {
        "AI Providers": {
            "LM Studio Local": "Online" if lm_status else "Offline",
            "OpenRouter Cloud": "Online" if or_status else "Offline or Missing Key"
        },
        "System": {
            "OS": platform.system(),
            "Release": platform.release(),
            "CPU Usage": f"{psutil.cpu_percent()}%",
            "RAM Usage": f"{psutil.virtual_memory().percent}%"
        },
        "Overall Status": "Healthy"
    }
