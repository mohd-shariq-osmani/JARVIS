from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.tasks.manager import TaskManager, Task

router = APIRouter(prefix="/tasks", tags=["tasks"])
task_manager: Optional[TaskManager] = None

class CreateTaskRequest(BaseModel):
    title: str
    action: str
    schedule_type: Optional[str] = "once"
    schedule_value: Optional[Any] = 60
    description: Optional[str] = ""

@router.get("/")
async def list_tasks():
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager not initialized")
    tasks = task_manager.get_tasks()
    return {"status": "success", "count": len(tasks), "tasks": [t.dict() for t in tasks]}

@router.post("/")
async def create_task_endpoint(req: CreateTaskRequest):
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager not initialized")
    task = task_manager.create_task(
        title=req.title,
        action=req.action,
        schedule_type=req.schedule_type or "once",
        schedule_value=req.schedule_value or 60,
        description=req.description or ""
    )
    return {"status": "success", "task": task.dict()}

@router.delete("/{task_id}")
async def delete_task_endpoint(task_id: str):
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager not initialized")
    if task_manager.delete_task(task_id):
        return {"status": "success", "deleted_id": task_id}
    raise HTTPException(status_code=404, detail="Task not found")

@router.post("/{task_id}/toggle")
async def toggle_task_endpoint(task_id: str):
    if not task_manager:
        raise HTTPException(status_code=500, detail="TaskManager not initialized")
    task = task_manager.toggle_task(task_id)
    if task:
        return {"status": "success", "task": task.dict()}
    raise HTTPException(status_code=404, detail="Task not found")
