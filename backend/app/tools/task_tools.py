from datetime import datetime
from typing import Optional
from app.tasks.manager import TaskManager

def register_task_tools(registry, task_manager: TaskManager):
    
    async def schedule_task(title: str, action: str = "", delay_seconds: Optional[int] = None, interval_seconds: Optional[int] = None, daily_time: Optional[str] = None, **kwargs) -> str:
        """
        Schedules a task, reminder, or timer.
        
        Args:
            title: Short description or reminder name (e.g. 'Meeting Reminder', 'Fix Watch', 'Check GPU Temp').
            action: What to remind or execute. If empty, uses title.
            delay_seconds: Run once after this many seconds (e.g. 60 for 1 minute, 300 for 5 minutes).
            interval_seconds: Run repeatedly every N seconds (e.g. 3600 for every hour).
            daily_time: Run daily at a specific 24h time like "09:00" or "13:32".
        """
        # Clean action text if model passed conversational output
        clean_action = (action or title).strip()
        if "scheduled a reminder" in clean_action.lower() or "i have scheduled" in clean_action.lower():
            clean_action = title

        # Resolve schedule type
        if daily_time:
            task = task_manager.create_task(title=title, action=clean_action, schedule_type="daily", schedule_value=daily_time)
            return f"Scheduled daily task '{title}' at {daily_time}. Next run: {datetime.fromtimestamp(task.next_run).strftime('%Y-%m-%d %H:%M:%S')}"
        elif interval_seconds and interval_seconds > 0:
            task = task_manager.create_task(title=title, action=clean_action, schedule_type="interval", schedule_value=interval_seconds)
            return f"Scheduled recurring task '{title}' every {interval_seconds} seconds."
        else:
            delay = delay_seconds or kwargs.get("seconds") or 60
            task = task_manager.create_task(title=title, action=clean_action, schedule_type="once", schedule_value=delay)
            return f"Scheduled reminder '{title}' in {delay} seconds (at {datetime.fromtimestamp(task.next_run).strftime('%H:%M:%S')})."

    async def list_scheduled_tasks(**kwargs) -> str:
        """Lists all active and scheduled automation tasks, timers, and reminders."""
        tasks = task_manager.get_tasks()
        if not tasks:
            return "No scheduled tasks or reminders currently active."
        
        output = f"Scheduled Tasks & Reminders ({len(tasks)}):\n"
        for t in tasks:
            next_str = datetime.fromtimestamp(t.next_run).strftime('%Y-%m-%d %H:%M:%S') if t.status == 'active' else 'N/A'
            output += f"- [{t.id[:8]}] {t.title} | Type: {t.schedule_type} | Status: {t.status} | Next Run: {next_str}\n"
        return output

    async def cancel_scheduled_task(task_id: str = "", name: str = "", query: str = "", **kwargs) -> str:
        """
        Cancels, removes, or deletes a scheduled task or reminder by name, title, keyword, or ID.
        
        Args:
            task_id: Task ID, partial ID, title (e.g. 'Fix Watch', 'watch', 'that reminder', or 'all').
            name: Alternative parameter for task/reminder name.
            query: Alternative parameter for query keyword.
        """
        target_term = (task_id or name or query or kwargs.get("title") or kwargs.get("name_or_id") or "").strip().lower()
        tasks = task_manager.get_tasks()
        if not tasks:
            return "No scheduled tasks or reminders currently exist."

        # If user says "all" / "all reminders"
        if target_term in ["all", "all tasks", "all reminders", "everything", "cancel all"]:
            count = len(tasks)
            for t in list(tasks):
                task_manager.delete_task(t.id)
            return f"Cancelled all {count} scheduled task(s) and reminder(s)."

        # If empty or generic "that reminder" / "the reminder" / "last reminder" -> pick latest
        if not target_term or any(k in target_term for k in ["that reminder", "the reminder", "last reminder", "it", "that", "this", "reminder"]):
            latest = tasks[-1]
            task_manager.delete_task(latest.id)
            return f"Successfully removed reminder '{latest.title}'."

        # Match by ID or title / description substring
        for t in reversed(tasks):
            if target_term == t.id.lower() or t.id.lower().startswith(target_term):
                task_manager.delete_task(t.id)
                return f"Successfully cancelled scheduled task '{t.title}'."
            if target_term in t.title.lower() or t.title.lower() in target_term:
                task_manager.delete_task(t.id)
                return f"Successfully removed reminder '{t.title}'."
            if target_term in t.description.lower() or target_term in t.action.lower():
                task_manager.delete_task(t.id)
                return f"Successfully removed reminder '{t.title}'."

        # Fallback if only 1 task exists
        if len(tasks) == 1:
            only_task = tasks[0]
            task_manager.delete_task(only_task.id)
            return f"Removed scheduled reminder '{only_task.title}'."

        return f"Could not find a scheduled reminder matching '{target_term}'."

    async def edit_scheduled_task(task_id_or_title: str, new_time: str = "", new_title: str = "", **kwargs) -> str:
        """
        Edits or reschedules an existing reminder or task to a new time or title.
        
        Args:
            task_id_or_title: The title or ID of the task/reminder to edit (e.g. 'drinking water', 'Fix Watch', 'meeting').
            new_time: The new scheduled time (e.g. '1:45 PM', '145 PM', '13:45', '2:30 PM').
            new_title: Optional new title for the reminder.
        """
        task = task_manager.edit_task(query=task_id_or_title, new_time=new_time, new_title=new_title)
        if task:
            time_display = task.schedule_value
            return f"Successfully updated reminder for '{task.title}' to {time_display}."
        return f"Could not find a scheduled reminder matching '{task_id_or_title}'."

    registry.register(
        name="edit_scheduled_task",
        description="Edit, change, or reschedule an existing reminder or task to a new time or title (e.g. change drinking water reminder to 1:45 PM)",
        parameters={
            "type": "object",
            "properties": {
                "task_id_or_title": {"type": "string", "description": "The title or ID of the reminder to edit (e.g. 'drinking water', 'Fix Watch')"},
                "new_time": {"type": "string", "description": "The new scheduled time (e.g. '1:45 PM', '13:45', '145 PM')"},
                "new_title": {"type": "string", "description": "Optional new title"}
            },
            "required": ["task_id_or_title", "new_time"]
        },
        func=edit_scheduled_task,
        permission_level=1
    )

    registry.register(
        name="schedule_task",
        description="Schedule a reminder, timer, or future automation task to be executed by JARVIS",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title or label for the task/reminder (e.g. 'Drink Water', 'Fix Watch', 'Meeting')"},
                "action": {"type": "string", "description": "What to remind or execute (optional)"},
                "delay_seconds": {"type": "integer", "description": "Seconds from now to run once (e.g. 60 for 1 minute, 3600 for 1 hour)"},
                "interval_seconds": {"type": "integer", "description": "Run repeatedly every N seconds"},
                "daily_time": {"type": "string", "description": "24-hour time format HH:MM or 12h format (e.g. '1:45 PM', '13:45', '09:00')"}
            },
            "required": ["title"]
        },
        func=schedule_task,
        permission_level=1
    )

    registry.register(
        name="list_scheduled_tasks",
        description="List all currently active or scheduled automation tasks, timers, and reminders",
        parameters={"type": "object", "properties": {}},
        func=list_scheduled_tasks,
        permission_level=0
    )

    registry.register(
        name="cancel_scheduled_task",
        description="Removes, deletes, or cancels a scheduled task, timer, or reminder by name, title (e.g. 'Fix Watch', 'Drink Water'), keyword, or ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The title or ID of the reminder/task to remove (e.g. 'Fix Watch', 'watch', 'that reminder', 'all')"}
            }
        },
        func=cancel_scheduled_task,
        permission_level=1
    )
