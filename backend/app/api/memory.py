from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.memory.vector_memory import MemoryManager

router = APIRouter(prefix="/memory", tags=["memory"])
memory_manager: Optional[MemoryManager] = None

class CreateMemoryRequest(BaseModel):
    content: str
    type: Optional[str] = "fact"
    importance: Optional[int] = 1

@router.get("/")
async def list_memories():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    memories = await memory_manager.get_all_memories()
    return {"status": "success", "count": len(memories), "memories": memories}

@router.post("/")
async def add_memory_endpoint(req: CreateMemoryRequest):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    result = await memory_manager.add_memory(content=req.content, memory_type=req.type, importance=req.importance)
    return {"status": "success", "message": result}

@router.get("/search")
async def search_memories(q: str = Query(..., description="Query text to search for")):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    result = await memory_manager.search_memory(query=q)
    return {"status": "success", "result": result}

@router.delete("/{memory_id}")
async def delete_memory_endpoint(memory_id: str):
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    success = await memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
    return {"status": "success", "deleted_id": memory_id}

@router.delete("/")
async def clear_all_memories_endpoint():
    if not memory_manager:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    success = await memory_manager.clear_all_memories()
    return {"status": "success", "message": "All memories cleared"}
