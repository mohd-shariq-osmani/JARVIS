import os
import shutil
import logging
import subprocess
import re
import string
import asyncio
from typing import List, Optional

logger = logging.getLogger("FileTools")

def get_available_drives() -> List[str]:
    """Returns all mounted and available drive letters on Windows."""
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(f"{letter}:")
    return drives

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".ico", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma"}
DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".xls", ".pptx", ".ppt", ".html", ".htm", ".json", ".xml", ".py", ".js", ".ts", ".css"}

def _get_user_folder(name: str) -> str:
    """Returns the actual existing path for a standard Windows user folder, checking OneDrive and user home."""
    user_home = os.path.expanduser("~")
    candidates = []
    onedrive_env = os.environ.get("OneDrive")
    if onedrive_env:
        candidates.append(os.path.join(onedrive_env, name))
    candidates.append(os.path.join(user_home, "OneDrive", name))
    candidates.append(os.path.join(user_home, name))
    
    for c in candidates:
        if os.path.exists(c):
            return os.path.normpath(c)
    return os.path.normpath(os.path.join(user_home, name))

def _get_search_directories() -> List[str]:
    user_home = os.path.expanduser("~")
    dirs = [
        _get_user_folder("Downloads"),
        _get_user_folder("Desktop"),
        _get_user_folder("Documents"),
        _get_user_folder("Pictures"),
        os.path.join(_get_user_folder("Pictures"), "Screenshots"),
        _get_user_folder("Videos"),
        os.path.join(_get_user_folder("Videos"), "Captures"),
        _get_user_folder("Music"),
        os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp"),
    ]
    seen = set()
    res = []
    for d in dirs:
        norm = os.path.normpath(d)
        if norm not in seen and os.path.exists(norm):
            seen.add(norm)
            res.append(norm)
    return res

def _clean_natural_target_name(text: str) -> str:
    """Extracts clean target folder or file name from natural speech."""
    t = text
    t = re.sub(r'(?i)\b(?:create|make|add|new|folder|file|directory|named|called|a|an|the)\b', '', t)
    t = re.sub(r'\s+', ' ', t).strip().strip('"').strip("'")
    return t

def _resolve_path(path_or_name: str) -> str:
    """
    Intelligently resolves relative or friendly paths, drive letters, natural queries,
    categories (e.g. 'image in download folder', 'html file in downloads'), partial filenames, Desktop, Downloads to absolute paths.
    """
    clean = path_or_name.strip().strip('"').strip("'")
    if not clean:
        return os.path.expanduser("~")
        
    user_home = os.path.expanduser("~")

    # 1. Drive check FIRST (to prevent Windows treating 'C:' as current working directory)
    if len(clean) == 2 and clean[1] == ':' and clean[0].isalpha():
        return f"{clean[0].upper()}:\\"
    if len(clean) == 3 and clean[1:3] in [":\\", ":/"] and clean[0].isalpha():
        return f"{clean[0].upper()}:\\"

    drive_match = re.search(r'^\b([a-zA-Z])\s*(?:drive|\:)\b', clean, re.IGNORECASE)
    if drive_match:
        return f"{drive_match.group(1).upper()}:\\"
        
    if clean.lower().startswith("drive ") and len(clean.split()) == 2 and len(clean.split()[1]) == 1:
        return f"{clean.split()[1].upper()}:\\"

    # 2. Direct folder aliases
    folder_aliases = {
        "desktop": _get_user_folder("Desktop"),
        "downloads": _get_user_folder("Downloads"),
        "download": _get_user_folder("Downloads"),
        "documents": _get_user_folder("Documents"),
        "document": _get_user_folder("Documents"),
        "pictures": _get_user_folder("Pictures"),
        "picture": _get_user_folder("Pictures"),
        "videos": _get_user_folder("Videos"),
        "video": _get_user_folder("Videos"),
        "music": _get_user_folder("Music"),
    }
    lowered = clean.lower()
    if lowered in folder_aliases:
        return folder_aliases[lowered]

    # 3. Paths starting with a user folder (e.g. "Downloads/pen fight", "Desktop/test.txt")
    for alias, folder_path in folder_aliases.items():
        if lowered.startswith(f"{alias}/") or lowered.startswith(f"{alias}\\"):
            rel_part = clean[len(alias)+1:].lstrip('/\\')
            return os.path.normpath(os.path.join(folder_path, rel_part))

    # 4. Handle natural prepositional queries (e.g. "folder pen fight in downloads", "pen in download folder", "notes on desktop")
    if any(k in lowered for k in [" in download", " in the download", " inside download", " to download", " into download"]):
        cleaned_text = re.sub(r'(?i)\s*(?:in|inside|to|into)\s*(?:the\s*)?downloads?\s*(?:folder|directory)?', '', clean)
        cleaned_name = _clean_natural_target_name(cleaned_text)
        if cleaned_name and not any(w in cleaned_name.lower() for w in ["image", "video", "photo", "picture", "screenshot", "html", "htm", "webpage", "file", "document"]):
            return os.path.normpath(os.path.join(_get_user_folder("Downloads"), cleaned_name))

    if any(k in lowered for k in [" on desktop", " on the desktop", " in desktop", " in the desktop"]):
        cleaned_text = re.sub(r'(?i)\s*(?:on|in|inside)\s*(?:the\s*)?desktop\s*(?:folder|directory)?', '', clean)
        cleaned_name = _clean_natural_target_name(cleaned_text)
        if cleaned_name and not any(w in cleaned_name.lower() for w in ["image", "video", "photo", "picture", "screenshot", "html", "htm", "webpage", "file", "document"]):
            return os.path.normpath(os.path.join(_get_user_folder("Desktop"), cleaned_name))

    if any(k in lowered for k in [" in document", " in the document", " in documents", " in the documents"]):
        cleaned_text = re.sub(r'(?i)\s*(?:in|inside)\s*(?:the\s*)?documents?\s*(?:folder|directory)?', '', clean)
        cleaned_name = _clean_natural_target_name(cleaned_text)
        if cleaned_name and not any(w in cleaned_name.lower() for w in ["image", "video", "photo", "picture", "screenshot", "html", "htm", "webpage", "file", "document"]):
            return os.path.normpath(os.path.join(_get_user_folder("Documents"), cleaned_name))

    # 5. If it's already an existing absolute path, return normalized path
    if os.path.exists(clean) and (os.path.isabs(clean) or os.sep in clean or "/" in clean):
        return os.path.abspath(clean)

    search_dirs = _get_search_directories()

    # 6. Exact match in standard search dirs
    for d in search_dirs:
        candidate = os.path.join(d, clean)
        if os.path.exists(candidate):
            return candidate

    # 7. Prioritize specific directory if mentioned in query
    explicit_dir = None
    target_dirs = search_dirs
    if any(k in lowered for k in ["download", "downloads"]):
        explicit_dir = _get_user_folder("Downloads")
        target_dirs = [explicit_dir] + [d for d in search_dirs if d != explicit_dir]
    elif any(k in lowered for k in ["desktop"]):
        explicit_dir = _get_user_folder("Desktop")
        target_dirs = [explicit_dir] + [d for d in search_dirs if d != explicit_dir]
    elif any(k in lowered for k in ["document", "documents"]):
        explicit_dir = _get_user_folder("Documents")
        target_dirs = [explicit_dir] + [d for d in search_dirs if d != explicit_dir]
    elif any(k in lowered for k in ["picture", "pictures", "photos", "screenshots", "screenshot"]):
        explicit_dir = _get_user_folder("Pictures")
        target_dirs = [
            os.path.join(explicit_dir, "Screenshots"),
            explicit_dir,
            _get_user_folder("Downloads"),
            _get_user_folder("Desktop"),
        ] + [d for d in search_dirs if d not in [explicit_dir, _get_user_folder("Downloads")]]

    # 8. Category / Extension / Recency match
    target_extensions = set()
    if any(w in lowered for w in ["html", "htm", "webpage", "web page", "site"]):
        target_extensions = {".html", ".htm"}
    elif any(w in lowered for w in ["image", "photo", "picture", "screenshot", "pic", "img", "png", "jpg", "jpeg", "webp"]):
        target_extensions = IMAGE_EXTENSIONS
    elif any(w in lowered for w in ["video", "recording", "clip", "movie", "mp4", "mkv", "mov", "avi"]):
        target_extensions = VIDEO_EXTENSIONS
    elif any(w in lowered for w in ["audio", "music", "song", "voice", "sound", "mp3", "wav"]):
        target_extensions = AUDIO_EXTENSIONS
    elif any(w in lowered for w in ["pdf"]):
        target_extensions = {".pdf"}
    elif any(w in lowered for w in ["document", "doc", "docx", "word", "text", "sheet", "report", "invoice", "notes"]):
        target_extensions = DOC_EXTENSIONS

    # Find matching files in target directories
    candidate_files = []
    for d in target_dirs:
        if os.path.exists(d):
            is_explicit = False
            if explicit_dir:
                try:
                    is_explicit = os.path.samefile(d, explicit_dir) or (os.path.exists(os.path.join(explicit_dir, "Screenshots")) and os.path.samefile(d, os.path.join(explicit_dir, "Screenshots")))
                except Exception:
                    is_explicit = (os.path.normpath(d) == os.path.normpath(explicit_dir))
            
            try:
                for fname in os.listdir(d):
                    full_path = os.path.join(d, fname)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(fname)[1].lower()
                        # If target extension matches
                        if target_extensions and ext in target_extensions:
                            score = 10
                            if is_explicit:
                                score += 50
                            if "screenshot" in lowered and "screenshot" in fname.lower():
                                score += 15
                            elif "recording" in lowered and "recording" in fname.lower():
                                score += 15
                            elif "voice" in lowered and "voice" in fname.lower():
                                score += 15
                            elif "html" in lowered and "html" in fname.lower():
                                score += 15
                            mtime = os.path.getmtime(full_path)
                            candidate_files.append((score, mtime, full_path))
                        # Substring match on filename
                        clean_keyword = re.sub(r'[^a-zA-Z0-9]', ' ', lowered).strip()
                        keywords = [k for k in clean_keyword.split() if k not in {"there", "is", "a", "an", "the", "in", "on", "folder", "directory", "can", "you", "open", "it", "file", "please", "only", "one", "where"}]
                        if keywords and all(k in fname.lower() for k in keywords):
                            score = 25
                            if is_explicit:
                                score += 50
                            mtime = os.path.getmtime(full_path)
                            candidate_files.append((score, mtime, full_path))
            except Exception:
                pass

    if candidate_files:
        candidate_files.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidate_files[0][2]

    # 9. Screenshot fallback if explicitly requested and none exists on disk
    if "screenshot" in lowered and any(k in lowered for k in ["take", "capture", "latest screenshot"]):
        temp_shot = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "latest_screenshot.png")
        try:
            import mss
            os.makedirs(os.path.dirname(temp_shot), exist_ok=True)
            with mss.mss() as sct:
                sct.shot(output=temp_shot)
            return temp_shot
        except Exception:
            pass

    return os.path.abspath(clean)

async def list_drives(**kwargs) -> str:
    """Lists all available and mounted disk drives (e.g. C:, D:, E:)."""
    drives = get_available_drives()
    if not drives:
        return "No drives detected."
    return f"Available system drives: {', '.join(drives)}"

async def open_file(filepath: str = "", **kwargs) -> str:
    """
    Opens any file, screenshot, image, document, PDF, HTML file, video, audio file, or folder in its default Windows application.
    Can resolve filenames, full paths, or descriptions (e.g. 'image in download folder', 'html file in downloads', 'latest screenshot', 'invoice.pdf').
    
    Args:
        filepath: Full path, filename, or description of the file to open.
    """
    try:
        raw_path = filepath or kwargs.get("path") or kwargs.get("filename") or kwargs.get("name") or ""
        if not raw_path:
            return "Please specify a file or path to open."
            
        target = _resolve_path(raw_path)
        
        if not os.path.exists(target):
            # Try searching user directories for partial name
            search_dirs = _get_search_directories()
            for d in search_dirs:
                candidate = os.path.join(d, os.path.basename(raw_path))
                if os.path.exists(candidate):
                    target = candidate
                    break
                    
        if not os.path.exists(target):
            clean_name = os.path.basename(raw_path) or raw_path
            return f"File '{clean_name}' not found on disk."
            
        # If target is a directory, open it in File Explorer
        if os.path.isdir(target):
            subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
            return f"Opened folder '{os.path.basename(target) or target}' in File Explorer."
            
        # Target is a file: open in default application using cmd.exe /c start for guaranteed foreground desktop activation
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
        except Exception:
            try:
                os.startfile(target)
            except Exception as e:
                subprocess.Popen(['explorer.exe', target])

        # Bring the newly opened window to foreground
        try:
            import win32gui
            import win32con
            await asyncio.sleep(0.4)
            fname_lower = os.path.basename(target).lower()
            def enum_cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    t = win32gui.GetWindowText(hwnd).lower()
                    if fname_lower in t or (len(fname_lower) > 6 and fname_lower[:8] in t):
                        try:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                        except Exception:
                            pass
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

        filename = os.path.basename(target)
        return f"Opened '{filename}' in default viewer."
    except Exception as e:
        logger.error(f"open_file exception: {e}")
        return f"Failed to open file: {e}"

async def open_folder(folder_path: str = "downloads", **kwargs) -> str:
    """
    Opens a folder, directory, or drive letter in Windows File Explorer.
    
    Args:
        folder_path: Path, folder name, or drive (e.g. 'Downloads', 'Desktop', 'D:', 'the d drive', 'C:\\').
    """
    try:
        raw = folder_path or kwargs.get("path") or kwargs.get("folder") or kwargs.get("name") or "downloads"
        target = _resolve_path(raw)
        
        # Check if target is a drive letter (e.g. D:\)
        if len(target) == 3 and target[1:] == ":\\":
            drive_letter = target[0].upper()
            if not os.path.exists(target):
                drives = get_available_drives()
                return f"Drive {drive_letter}:\\ is not detected or mounted on this system. Available drives: {', '.join(drives)}."
            
            subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
            return f"Opened {drive_letter}:\\ drive in File Explorer."
            
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)
            
        subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
            
        name = os.path.basename(target) or target
        return f"Opened '{name}' in File Explorer."
    except Exception as e:
        return f"Failed to open folder: {e}"

async def create_folder(folder_path: str = "", **kwargs) -> str:
    """
    Creates a new folder or directory anywhere on the computer (e.g. 'Downloads/pen fight', 'Desktop/NewFolder').
    
    Args:
        folder_path: Path or folder name to create (e.g. 'Downloads/pen fight', 'Desktop/Project').
    """
    try:
        raw = folder_path or kwargs.get("path") or kwargs.get("name") or kwargs.get("folder") or ""
        if not raw:
            return "Please specify a folder path to create."
        target = _resolve_path(raw)
        os.makedirs(target, exist_ok=True)
        return f"Successfully created folder '{os.path.basename(target) or target}' in '{os.path.dirname(target)}'."
    except Exception as e:
        return f"Failed to create folder: {e}"

async def read_file(filepath: str, **kwargs) -> str:
    """
    Reads text, code, markdown, csv, or json content from any file on the computer.
    
    Args:
        filepath: Path or filename of the file to read.
    """
    try:
        target = _resolve_path(filepath or kwargs.get("filename") or "")
        if not os.path.exists(target):
            return f"Error: File '{filepath}' not found."
            
        with open(target, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        if len(content) > 3000:
            return f"Content of {os.path.basename(target)} (truncated to 3000 chars):\n" + content[:3000] + "\n..."
        return content
    except Exception as e:
        return f"Error reading file: {e}"

async def write_file(filepath: str, content: str, **kwargs) -> str:
    """
    Writes or saves text content to any file on the computer.
    
    Args:
        filepath: Target file path.
        content: The text content to write.
    """
    try:
        target = _resolve_path(filepath or kwargs.get("filename") or "")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved to '{os.path.basename(target)}'."
    except Exception as e:
        return f"Error writing file: {e}"

async def list_directory(folder_path: str = "", **kwargs) -> str:
    """
    Lists files and subdirectories in any folder across the computer.
    
    Args:
        folder_path: Path to the directory (e.g. 'Desktop', 'Downloads', or full path).
    """
    try:
        target = _resolve_path(folder_path or kwargs.get("path") or os.path.expanduser("~"))
        if not os.path.exists(target):
            return f"Directory '{folder_path}' does not exist."
            
        items = os.listdir(target)
        if not items:
            return f"Folder '{os.path.basename(target)}' is empty."
            
        files = [f for f in items if os.path.isfile(os.path.join(target, f))]
        dirs = [d for d in items if os.path.isdir(os.path.join(target, d))]
        
        output = [f"Contents of {os.path.basename(target)} ({len(items)} items):"]
        if dirs:
            output.append("Folders: " + ", ".join(dirs[:10]))
        if files:
            output.append("Files: " + ", ".join(files[:15]))
        return "\n".join(output)
    except Exception as e:
        return f"Error listing folder: {e}"

async def delete_file(filepath: str, **kwargs) -> str:
    """Deletes a file from disk."""
    try:
        target = _resolve_path(filepath or kwargs.get("filename") or "")
        if not os.path.exists(target):
            return f"File '{filepath}' not found."
        os.remove(target)
        return f"Successfully deleted '{os.path.basename(target)}'."
    except Exception as e:
        return f"Error deleting file: {e}"

def register_file_tools(registry):
    registry.register(
        name="open_file",
        description="Opens any file, screenshot, image, PDF, HTML file, document, video, or folder in its default Windows app (Photos, Acrobat, Notepad, Chrome, Explorer, etc.)",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Full path, filename, or description (e.g. 'html in downloads', 'image in download folder', 'report.pdf', 'latest screenshot')"}
            },
            "required": ["filepath"]
        },
        func=open_file,
        permission_level=1
    )

    registry.register(
        name="open_folder",
        description="Opens any folder, directory, or disk drive in Windows File Explorer (e.g. 'Downloads', 'Desktop', 'D:', 'the d drive', 'C:\\')",
        parameters={
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Folder path or drive letter (e.g. 'Downloads', 'Desktop', 'D:', 'C:\\')"}
            }
        },
        func=open_folder,
        permission_level=1
    )

    registry.register(
        name="create_folder",
        description="Creates a new folder or directory anywhere on the computer (e.g. 'Downloads/pen fight', 'Desktop/NewFolder', 'Documents/Reports')",
        parameters={
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Path or folder name to create (e.g. 'Downloads/pen fight', 'Desktop/Projects')"}
            },
            "required": ["folder_path"]
        },
        func=create_folder,
        permission_level=1
    )

    registry.register(
        name="list_drives",
        description="Lists all available disk drives on the computer (e.g. C:, D:, E:)",
        parameters={"type": "object", "properties": {}},
        func=list_drives,
        permission_level=0
    )

    registry.register(
        name="read_file",
        description="Reads text/code content from any file on the computer",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["filepath"]
        },
        func=read_file,
        permission_level=1
    )

    registry.register(
        name="write_file",
        description="Writes or creates a file with specified content anywhere on the computer",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to create/save (e.g. 'Downloads/notes.txt', 'Desktop/report.md')"},
                "content": {"type": "string", "description": "The text content"}
            },
            "required": ["filepath", "content"]
        },
        func=write_file,
        permission_level=2
    )

    registry.register(
        name="list_directory",
        description="Lists files and folders inside any directory (Desktop, Downloads, etc.)",
        parameters={
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Directory path"}
            }
        },
        func=list_directory,
        permission_level=0
    )

    registry.register(
        name="delete_file",
        description="Deletes a file from disk",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to delete"}
            },
            "required": ["filepath"]
        },
        func=delete_file,
        permission_level=2
    )
