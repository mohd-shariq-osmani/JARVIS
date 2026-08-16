from datetime import datetime
from typing import Optional
from app.tasks.manager import TaskManager

def register_task_tools(registry, task_manager: TaskManager):
    
    async def schedule_task(title: str, action: str, delay_seconds: Optional[int] = None, interval_seconds: Optional[int] = None, daily_time: Optional[str] = None, **kwargs) -> str:
        """
        Schedules a task or reminder.
        
        Args:
            title: Short description or reminder name (e.g. 'Meeting Reminder', 'Check GPU Temp').
            action: The exact prompt or task instruction JARVIS should execute when triggered.
            delay_seconds: Run once after this many seconds (e.g. 300 for 5 minutes).
            interval_seconds: Run repeatedly every N seconds (e.g. 3600 for every hour).
            daily_time: Run daily at a specific 24h time like "09:00" or "18:30".
        """
        # Resolve schedule type
        if daily_time:
            task = task_manager.create_task(title=title, action=action, schedule_type="daily", schedule_value=daily_time)
            return f"Scheduled daily task '{title}' at {daily_time}. Next run: {datetime.fromtimestamp(task.next_run).strftime('%Y-%m-%d %H:%M:%S')}"
        elif interval_seconds and interval_seconds > 0:
            task = task_manager.create_task(title=title, action=action, schedule_type="interval", schedule_value=interval_seconds)
            return f"Scheduled recurring task '{title}' every {interval_seconds} seconds."
        else:
            delay = delay_seconds or kwargs.get("seconds") or 60
            task = task_manager.create_task(title=title, action=action, schedule_type="once", schedule_value=delay)
            return f"Scheduled task '{title}' in {delay} seconds (at {datetime.fromtimestamp(task.next_run).strftime('%H:%M:%S')})."

    async def list_scheduled_tasks(**kwargs) -> str:
        """Lists all active and scheduled automation tasks."""
        tasks = task_manager.get_tasks()
        if not tasks:
            return "No scheduled tasks found."
        
        output = "Scheduled Tasks:\n"
        for t in tasks:
            next_str = datetime.fromtimestamp(t.next_run).strftime('%Y-%m-%d %H:%M:%S') if t.status == 'active' else 'N/A'
            output += f"- [{t.id[:8]}] {t.title} | Type: {t.schedule_type} | Status: {t.status} | Next Run: {next_str}\n"
        return output

    async def cancel_scheduled_task(task_id: str, **kwargs) -> str:
        """Cancels and removes a scheduled task by ID."""
        # Find matching task by full or partial ID
        tasks = task_manager.get_tasks()
        target_id = None
        for t in tasks:
            if t.id == task_id or t.id.startswith(task_id):
                target_id = t.id
                break
                
        if target_id and task_manager.delete_task(target_id):
            return f"Successfully cancelled scheduled task [{target_id[:8]}]."
        return f"Task '{task_id}' not found."

    registry.register(
        name="schedule_task",
        description="Schedule a reminder, timer, or future automation task to be executed by JARVIS",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title or label for the task/reminder"},
                "action": {"type": "string", "description": "What JARVIS should do or say when triggered"},
                "delay_seconds": {"type": "integer", "description": "Seconds from now to run once (e.g. 60 for 1 minute, 3600 for 1 hour)"},
                "interval_seconds": {"type": "integer", "description": "Run repeatedly every N seconds"},
                "daily_time": {"type": "string", "description": "24-hour time format HH:MM (e.g. '09:00')"}
            },
            "required": ["title", "action"]
        },
        func=schedule_task,
        permission_level=1
    )

    registry.register(
        name="list_scheduled_tasks",
        description="List all currently active or past scheduled automation tasks and timers",
        parameters={"type": "object", "properties": {}},
        func=list_scheduled_tasks,
        permission_level=0
    )

    registry.register(
        name="cancel_scheduled_task",
        description="Cancel or delete a scheduled task by its ID",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The ID or partial ID of the task to cancel"}
            },
            "required": ["task_id"]
        },
        func=cancel_scheduled_task,
        permission_level=1
    )
