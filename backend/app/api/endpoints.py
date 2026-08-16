from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.agent.orchestrator import AgentOrchestrator

router = APIRouter()
agent: Optional[AgentOrchestrator] = None
queue_manager = None # Injected by main.py

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not agent:
        return {"error": "Agent not initialized"}
    
    clean = request.message.lower().strip()
    if clean in ["stop", "stop jarvis", "cancel", "quiet"]:
        if queue_manager:
            await queue_manager.stop_all()
        return {"status": "stopped", "response": "Stopped."}

    if queue_manager:
        result = await queue_manager.enqueue(request.message, is_voice=False)
        return result
    else:
        response = await agent.handle_request(request.message)
        return {"response": response}

@router.post("/chat/stop")
async def stop_chat_endpoint():
    """Immediately stops all speech, active agent processing, and clears the queue."""
    if queue_manager:
        await queue_manager.stop_all()
        return {"status": "success", "message": "All execution and speech halted."}
    return {"status": "ok"}

class AccessResponse(BaseModel):
    request_id: str
    grant: bool

@router.get("/api/access/requests")
async def get_access_requests():
    from app.security.access_manager import access_manager
    return [r.dict() for r in access_manager.pending_requests.values() if r.status == "pending"]

@router.post("/api/access/respond")
async def respond_access_request(body: AccessResponse):
    from app.security.access_manager import access_manager
    success = access_manager.respond_to_request(body.request_id, body.grant)
    return {"status": "ok", "success": success, "decision": "granted" if body.grant else "denied"}

@router.get("/api/access/authorized")
async def get_authorized_resources():
    from app.security.access_manager import access_manager
    return {"authorized": list(access_manager.authorized_resources)}
