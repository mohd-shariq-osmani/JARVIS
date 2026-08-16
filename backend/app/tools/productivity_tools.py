import os
import json
import shutil
import logging
import datetime
import psutil
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ProductivityTools")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

def _load_notes() -> List[Dict[str, Any]]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_notes(notes: List[Dict[str, Any]]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2)

async def add_note(title: str, content: str, tags: list = [], **kwargs) -> str:
    """
    Saves a quick note, memo, or reminder to your persistent local scratchpad.
    
    Args:
        title: Short title or subject for the note.
        content: The text/body of the note.
        tags: Optional list of categories/tags (e.g. ['work', 'ideas']).
    """
    notes = _load_notes()
    note_id = str(len(notes) + 1)
    new_note = {
        "id": note_id,
        "title": title.strip(),
        "content": content.strip(),
        "tags": tags or [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }
    notes.append(new_note)
    _save_notes(notes)
    return f"Saved note #{note_id}: '{title}'."

async def list_notes(**kwargs) -> str:
    """Lists all saved quick notes."""
    notes = _load_notes()
    if not notes:
        return "No notes found in scratchpad."
    output = [f"Saved Notes ({len(notes)}):"]
    for n in notes[-8:]:
        output.append(f"- [#{n['id']}] {n['title']} ({n['created_at']}): {n['content'][:80]}")
    return "\n".join(output)

async def search_notes(query: str, **kwargs) -> str:
    """Searches your saved notes by title, content, or tag."""
    q_clean = (query or kwargs.get("q") or "").strip().lower()
    notes = _load_notes()
    matches = [
        n for n in notes 
        if q_clean in n['title'].lower() or q_clean in n['content'].lower() or any(q_clean in str(t).lower() for t in n.get('tags', []))
    ]
    if not matches:
        return f"No notes matching '{query}' were found."
    return f"Found {len(matches)} note(s):\n" + "\n".join([f"- [#{n['id']}] {n['title']}: {n['content']}" for n in matches])

async def delete_note(note_id: str, **kwargs) -> str:
    """Deletes a note by its ID."""
    notes = _load_notes()
    filtered = [n for n in notes if str(n['id']) != str(note_id).strip()]
    if len(filtered) == len(notes):
        return f"Note #{note_id} not found."
    _save_notes(filtered)
    return f"Deleted note #{note_id}."

async def organize_folder(folder_path: str = "downloads", **kwargs) -> str:
    """
    Automatically organizes files in a folder (e.g. Downloads or Desktop) into subcategories (Images, Documents, Installers, Archives, Media, Code).
    
    Args:
        folder_path: 'downloads', 'desktop', or an absolute directory path.
    """
    user_home = os.path.expanduser("~")
    target_dir = os.path.join(user_home, "Downloads") if folder_path.lower() == "downloads" else (
        os.path.join(user_home, "Desktop") if folder_path.lower() == "desktop" else folder_path
    )

    if not os.path.exists(target_dir):
        return f"Directory '{target_dir}' does not exist."

    category_map = {
        "Images": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp", ".ico"],
        "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".csv", ".pptx", ".txt", ".md"],
        "Installers": [".exe", ".msi", ".dmg", ".pkg", ".iso"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Media": [".mp4", ".mkv", ".mp3", ".wav", ".flac", ".mov"],
        "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".cpp", ".c", ".rs"]
    }

    moved_count = 0
    try:
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isfile(item_path):
                _, ext = os.path.splitext(item)
                ext_lower = ext.lower()

                for cat_name, extensions in category_map.items():
                    if ext_lower in extensions:
                        cat_dir = os.path.join(target_dir, cat_name)
                        os.makedirs(cat_dir, exist_ok=True)
                        dest_path = os.path.join(cat_dir, item)
                        # Handle duplicate filenames
                        if not os.path.exists(dest_path):
                            shutil.move(item_path, dest_path)
                            moved_count += 1
                        break

        return f"Successfully organized {moved_count} file(s) in {os.path.basename(target_dir)}."
    except Exception as e:
        return f"Folder organization error: {e}"

async def get_daily_briefing(city: str = "Hyderabad", **kwargs) -> str:
    """
    Delivers a comprehensive morning / daily briefing with current time, date, local weather, hardware health, battery, and reminders.
    """
    from app.tools.web_tools import get_weather, get_current_time

    now_time = datetime.datetime.now().strftime("%I:%M %p")
    now_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    
    # Weather
    weather = await get_weather(city)
    
    # System Telemetry
    cpu_pct = psutil.cpu_percent(interval=0.2)
    mem_pct = psutil.virtual_memory().percent
    
    # Battery
    batt = psutil.sensors_battery()
    batt_str = f"Battery is at {batt.percent}%." if batt else "Running on AC Power."
    
    # Notes count
    notes = _load_notes()
    notes_str = f"You have {len(notes)} note(s) in your scratchpad." if notes else "No pending scratchpad notes."

    return (
        f"Good day, sir. Here is your daily briefing:\n"
        f"- Time: {now_time} on {now_date}.\n"
        f"- Weather: {weather}\n"
        f"- System Health: CPU is at {cpu_pct}%, Memory utilization is {mem_pct}%. {batt_str}\n"
        f"- Tasks & Notes: {notes_str}\n"
        f"All systems are operating within nominal parameters."
    )

def register_productivity_tools(registry):
    registry.register(
        name="add_note",
        description="Save a note, memo, or idea to your scratchpad",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note content"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"}
            },
            "required": ["title", "content"]
        },
        func=add_note,
        permission_level=1
    )

    registry.register(
        name="list_notes",
        description="Lists recent saved notes from your scratchpad",
        parameters={"type": "object", "properties": {}},
        func=list_notes,
        permission_level=0
    )

    registry.register(
        name="search_notes",
        description="Searches saved notes by keyword, title, or tag",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        func=search_notes,
        permission_level=0
    )

    registry.register(
        name="delete_note",
        description="Deletes a saved note by its ID",
        parameters={"type": "object", "properties": {"note_id": {"type": "string"}}, "required": ["note_id"]},
        func=delete_note,
        permission_level=1
    )

    registry.register(
        name="organize_folder",
        description="Cleans and sorts files in Downloads or Desktop into categorized subfolders (Images, Documents, Installers, etc.)",
        parameters={"type": "object", "properties": {"folder_path": {"type": "string", "description": "'downloads', 'desktop', or folder path"}}},
        func=organize_folder,
        permission_level=2
    )

    registry.register(
        name="get_daily_briefing",
        description="Generates a full structured morning / daily briefing with live time, weather, hardware health, battery, and pending items. Execute this immediately when user says 'Good morning' or asks for a briefing.",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Local city name (default is 'Hyderabad')"}
            }
        },
        func=get_daily_briefing,
        permission_level=0
    )
