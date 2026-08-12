from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.agent.orchestrator import AgentOrchestrator

router = APIRouter()
agent: AgentOrchestrator = None # Will be injected

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not agent:
        return {"error": "Agent not initialized"}
    
    response = await agent.handle_request(request.message)
    return {"response": response}
