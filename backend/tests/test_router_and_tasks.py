import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import config_manager
from app.ai.router import AIRouter
from app.tasks.manager import TaskManager
from app.tools.registry import ToolRegistry
from app.tools.task_tools import register_task_tools

async def test_all():
    print("=== 1. Testing AIRouter Dynamic Provider Switch ===")
    router = AIRouter()
    print(f"Initial active provider: {router.active_provider_name}")
    assert router.active_provider_name in ["lmstudio", "openrouter", "auto"]

    # Switch to OpenRouter dynamically
    config_manager.update_settings({"provider": "openrouter", "openrouter_key": "test-key", "openrouter_model": "google/gemini-2.0-flash"})
    print(f"Provider after update: {router.active_provider_name}")
    assert router.active_provider_name == "openrouter"
    assert router.openrouter.api_key == "test-key"

    # Switch to Auto mode dynamically
    config_manager.update_settings({"provider": "auto"})
    print(f"Provider after auto update: {router.active_provider_name}")
    assert router.active_provider_name == "auto"

    # Switch back to LM Studio
    config_manager.update_settings({"provider": "lmstudio"})
    print(f"Provider after lmstudio update: {router.active_provider_name}")
    assert router.active_provider_name == "lmstudio"

    print("=== 2. Testing TaskManager and Task Scheduling ===")
    tm = TaskManager()
    
    # Create a 1-second test task
    task = tm.create_task(
        title="Test Quick Task",
        action="echo hello",
        schedule_type="once",
        schedule_value=1,
        description="A 1-second test task"
    )
    print(f"Created task: [{task.id[:8]}] {task.title}, Next run: {task.next_run}")
    assert task.id in tm.tasks
    assert task.status == "active"

    # Create an interval task
    int_task = tm.create_task(
        title="Test Recurring Check",
        action="check battery",
        schedule_type="interval",
        schedule_value=300
    )
    print(f"Created interval task: [{int_task.id[:8]}] {int_task.title}")
    assert int_task.schedule_type == "interval"

    # Toggle task
    tm.toggle_task(int_task.id)
    assert tm.get_task(int_task.id).status == "paused"
    tm.toggle_task(int_task.id)
    assert tm.get_task(int_task.id).status == "active"

    print("=== 3. Testing Task Tools via ToolRegistry ===")
    registry = ToolRegistry()
    register_task_tools(registry, tm)

    # Test schedule_task tool
    tool_sched = await registry.execute_tool("schedule_task", '{"title": "Tool Created Task", "action": "Speak reminder", "delay_seconds": 120}')
    print("Tool schedule_task result:", tool_sched)
    assert "Scheduled task" in tool_sched

    # Test list_scheduled_tasks tool
    tool_list = await registry.execute_tool("list_scheduled_tasks", "{}")
    print("Tool list_scheduled_tasks output:\n", tool_list)
    assert "Tool Created Task" in tool_list

    # Test cancel_scheduled_task tool
    tool_cancel = await registry.execute_tool("cancel_scheduled_task", f'{{"task_id": "{task.id[:8]}"}}')
    print("Tool cancel_scheduled_task result:", tool_cancel)
    assert "Successfully cancelled" in tool_cancel

    # Clean up test task
    tm.delete_task(int_task.id)

    print("\n ALL PHASE 10 & 11 UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_all())
