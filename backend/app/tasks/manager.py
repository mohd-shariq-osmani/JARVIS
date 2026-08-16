import os
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("TaskManager")
TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'tasks.json')

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    action: str  # Instruction or prompt to run with the agent
    schedule_type: str  # "once", "interval", "daily"
    schedule_value: Any  # delay in seconds, interval in minutes/seconds, or "09:00" for daily
    status: str = "active"  # "active", "completed", "paused", "failed"
    created_at: str
    next_run: float  # Unix timestamp
    last_run: Optional[str] = None
    last_result: Optional[str] = None

import re

def parse_time_to_24h(val: Any) -> str:
    """Parses any time format (e.g. '1:45 PM', '145 PM', '1.45 pm', '13:45', '145') into 24-hour HH:MM format."""
    s = str(val).strip().lower()
    
    # Normalize p.m. -> pm, a.m. -> am
    s = re.sub(r'\bp\.?m\.?\b', 'pm', s)
    s = re.sub(r'\ba\.?m\.?\b', 'am', s)
    
    # 3-digit: '145 pm' -> '1:45 pm', '930 am' -> '9:30 am'
    s = re.sub(r'\b([1-9])([0-5][0-9])\s*(am|pm)\b', r'\1:\2 \3', s)
    # 4-digit: '1045 pm' -> '10:45 pm', '1130 am' -> '11:30 am', '1245 pm' -> '12:45 pm'
    s = re.sub(r'\b(1[0-2])([0-5][0-9])\s*(am|pm)\b', r'\1:\2 \3', s)

    # 1. Check with AM/PM
    m_ampm = re.search(r'\b(\d{1,2})[:.](\d{2})\s*(am|pm)\b', s)
    if m_ampm:
        hr, mn, meridiem = int(m_ampm.group(1)), int(m_ampm.group(2)), m_ampm.group(3)
        if meridiem == 'pm' and hr < 12: hr += 12
        if meridiem == 'am' and hr == 12: hr = 0
        return f"{hr:02d}:{mn:02d}"

    # 2. Check bare number with am/pm (e.g. '1 pm', '2 pm')
    m_bare = re.search(r'\b(\d{1,2})\s*(am|pm)\b', s)
    if m_bare:
        hr, meridiem = int(m_bare.group(1)), m_bare.group(2)
        if meridiem == 'pm' and hr < 12: hr += 12
        if meridiem == 'am' and hr == 12: hr = 0
        return f"{hr:02d}:00"

    # 3. Check 24h format HH:MM
    m_24 = re.search(r'\b(\d{1,2})[:.](\d{2})\b', s)
    if m_24:
        hr, mn = int(m_24.group(1)), int(m_24.group(2))
        return f"{hr:02d}:{mn:02d}"

    return str(val)

class TaskManager:
    def __init__(self):
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        self.tasks: Dict[str, Task] = {}
        self.agent = None
        self.voice_manager = None
        self._running = False
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        task = Task(**item)
                        self.tasks[task.id] = task
                logger.info(f"Loaded {len(self.tasks)} tasks from disk.")
            except Exception as e:
                logger.error(f"Failed to load tasks from {TASKS_FILE}: {e}")
        else:
            self.save_tasks()

    def save_tasks(self):
        try:
            with open(TASKS_FILE, 'w') as f:
                json.dump([t.dict() for t in self.tasks.values()], f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save tasks to {TASKS_FILE}: {e}")

    def calculate_next_run(self, schedule_type: str, schedule_value: Any) -> float:
        now = time.time()
        if schedule_type == "once":
            # schedule_value is delay in seconds
            delay = float(schedule_value)
            return now + delay
        elif schedule_type == "interval":
            # schedule_value is interval in seconds or minutes
            interval = float(schedule_value)
            return now + interval
        elif schedule_type == "daily":
            try:
                time_24 = parse_time_to_24h(schedule_value)
                target_hour, target_minute = map(int, time_24.strip().split(":"))
                now_dt = datetime.now()
                target_dt = now_dt.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                if target_dt <= now_dt:
                    target_dt += timedelta(days=1)
                return target_dt.timestamp()
            except Exception as e:
                logger.error(f"Invalid daily time format: {schedule_value} ({e})")
                return now + 3600
        return now + 60

    def edit_task(self, query: str, new_time: str = "", new_title: str = "") -> Optional[Task]:
        """Edits an existing task or reminder by query matching title/id."""
        q_clean = query.strip().lower()
        tasks = list(self.tasks.values())
        if not tasks:
            return None

        target_task = None
        # 1. Match by ID
        for t in tasks:
            if t.id == query or t.id.startswith(query):
                target_task = t
                break

        # 2. Match by title substring
        if not target_task:
            for t in reversed(tasks):
                if q_clean in t.title.lower() or t.title.lower() in q_clean:
                    target_task = t
                    break

        # 3. Fallback to latest task
        if not target_task and tasks:
            target_task = tasks[-1]

        if target_task:
            if new_title:
                target_task.title = new_title.strip()
            if new_time:
                target_task.schedule_type = "daily"
                target_task.schedule_value = parse_time_to_24h(new_time)
                target_task.next_run = self.calculate_next_run("daily", target_task.schedule_value)
                target_task.status = "active"
            self.save_tasks()
            logger.info(f"Updated task '{target_task.title}' to time: {target_task.schedule_value}")
            return target_task

        return None

    def create_task(self, title: str, action: str, schedule_type: str = "once", schedule_value: Any = 60, description: str = "") -> Task:
        task_id = str(uuid.uuid4())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        next_run = self.calculate_next_run(schedule_type, schedule_value)
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            action=action,
            schedule_type=schedule_type,
            schedule_value=schedule_value,
            status="active",
            created_at=created_at,
            next_run=next_run
        )
        self.tasks[task.id] = task
        self.save_tasks()
        logger.info(f"Created task '{title}' [id={task_id}], next run: {datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')}")
        return task

    def get_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
            logger.info(f"Deleted task {task_id}")
            return True
        return False

    def toggle_task(self, task_id: str) -> Optional[Task]:
        task = self.tasks.get(task_id)
        if task:
            task.status = "paused" if task.status == "active" else "active"
            if task.status == "active" and task.next_run <= time.time():
                task.next_run = self.calculate_next_run(task.schedule_type, task.schedule_value)
            self.save_tasks()
            return task
        return None

    async def execute_task(self, task: Task):
        logger.info(f"Executing scheduled task '{task.title}' (action: {task.action})")
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.last_run = timestamp_str

        try:
            action_lower = task.action.lower().strip()
            
            # Check if this task is an active command to execute vs a user reminder/notification
            is_command = (
                task.action.startswith("COMMAND:") or 
                task.action.startswith("RUN:") or
                any(action_lower.startswith(prefix) for prefix in ["open ", "search ", "get ", "check ", "organize ", "play "])
            ) and "scheduled a reminder" not in action_lower

            if is_command and self.agent:
                cmd_text = task.action.removeprefix("COMMAND:").removeprefix("RUN:").strip()
                result = await self.agent.handle_request(cmd_text)
                alert_text = f"Scheduled task '{task.title}' completed. {result}"
            else:
                # Clean reminder / notification
                reminder_content = task.description or task.title
                alert_text = f"Reminder alert: {task.title}. Time to {reminder_content.lower().removeprefix('reminder:').strip()}."

            task.last_result = alert_text
            logger.info(f"Task '{task.title}' finished: {alert_text}")

            # Speak outcome if voice is active
            if self.voice_manager and alert_text:
                await self.voice_manager.speak(alert_text)

            if task.schedule_type == "once":
                task.status = "completed"
            else:
                task.next_run = self.calculate_next_run(task.schedule_type, task.schedule_value)
        except Exception as e:
            logger.error(f"Error executing task '{task.title}': {e}")
            task.last_result = f"Error: {e}"
            task.status = "failed" if task.schedule_type == "once" else "active"

        self.save_tasks()

    async def run_scheduler(self, agent=None, voice_manager=None):
        self.agent = agent
        self.voice_manager = voice_manager
        self._running = True
        logger.info("Task Scheduler loop started.")

        while self._running:
            try:
                now = time.time()
                for task in list(self.tasks.values()):
                    if task.status == "active" and now >= task.next_run:
                        asyncio.create_task(self.execute_task(task))
            except Exception as e:
                logger.error(f"Scheduler loop exception: {e}")
            await asyncio.sleep(1)

    def stop_scheduler(self):
        self._running = False
