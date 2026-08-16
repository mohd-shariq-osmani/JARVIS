import platform
import logging
import base64
import os
import time
import asyncio
import urllib.parse
from typing import List, Optional
from io import BytesIO

logger = logging.getLogger("WindowsComputerProvider")

class WindowsComputerProvider:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        if not self.is_windows:
            logger.warning("WindowsComputerProvider initialized on non-Windows system")
    
    def _find_window(self, app_name_or_title: str = ""):
        """Finds window handle by title/app name, or returns active foreground window."""
        if not self.is_windows:
            return None
            
        try:
            import win32gui
            import win32process
            import psutil

            if not app_name_or_title or app_name_or_title.lower() in ["current", "active", "this", "foreground"]:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd and win32gui.IsWindow(hwnd):
                    return hwnd

            query = app_name_or_title.lower().strip()
            found_hwnds = []

            def enum_windows_cb(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if query in title:
                        found_hwnds.append(hwnd)
                        return
                    # Also check process name
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        if query in proc.name().lower():
                            found_hwnds.append(hwnd)
                    except Exception:
                        pass

            win32gui.EnumWindows(enum_windows_cb, None)
            if found_hwnds:
                return found_hwnds[0]
            
            # Fallback to foreground window
            return win32gui.GetForegroundWindow()
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return None

    async def open_application(self, app_name: str) -> str:
        if not self.is_windows:
            return "Error: Cannot run Windows commands on this OS."
            
        import glob
        import subprocess
        import difflib
        try:
            app_lower = app_name.lower().strip()
            
            # Map well-known aliases to their launch commands / URIs
            alias_map = {
                "settings": "ms-settings:",
                "windows settings": "ms-settings:",
                "chrome": "chrome",
                "google chrome": "chrome",
                "edge": "msedge",
                "microsoft edge": "msedge",
                "notepad": "notepad",
                "calculator": "calc",
                "calc": "calc",
                "vscode": "code",
                "vs code": "code",
                "visual studio code": "code",
                "explorer": "explorer",
                "file explorer": "explorer",
                "task manager": "taskmgr",
                "cmd": "cmd",
                "command prompt": "cmd",
                "terminal": "wt",
                "windows terminal": "wt",
                "paint": "mspaint",
                "wordpad": "wordpad",
                "snip": "snippingtool",
                "snipping tool": "snippingtool",
                "spotify": "spotify",
                "discord": "discord",
                "vlc": "vlc",
                "obs": "obs64",
                "lm studio": "lm studio",
                "lmstudio": "lm studio",
            }
            
            target = alias_map.get(app_lower)

            # Direct URI (ms-settings:, etc.)
            if target and target.startswith("ms-settings:"):
                subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
                return f"Opened {app_name}"

            # If alias resolved, try to run it directly
            if target:
                try:
                    result = subprocess.run(["where", target], capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
                        return f"Opened {app_name}."
                except Exception:
                    pass

            # Search Start Menu shortcuts with fuzzy matching
            start_menu_paths = [
                os.path.join(os.environ.get('PROGRAMDATA', ''), r'Microsoft\Windows\Start Menu\Programs'),
                os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
            ]
            all_links = []
            for base in start_menu_paths:
                for pattern in [r'**\*.lnk', r'**\*.url']:
                    all_links.extend(glob.glob(os.path.join(base, pattern), recursive=True))

            link_names = {os.path.splitext(os.path.basename(lnk))[0].lower(): lnk for lnk in all_links}

            # 1. Exact substring match
            matched_link = None
            for name, path in link_names.items():
                if app_lower in name or name in app_lower:
                    matched_link = path
                    break

            # 2. Fuzzy match using difflib if no exact substring hit
            if not matched_link:
                # Also try individual keywords in the app name
                keywords = [w for w in app_lower.split() if len(w) > 2]
                for name, path in link_names.items():
                    if keywords and all(kw in name for kw in keywords):
                        matched_link = path
                        break

            if not matched_link:
                closest = difflib.get_close_matches(app_lower, link_names.keys(), n=1, cutoff=0.4)
                if closest:
                    matched_link = link_names[closest[0]]

            if matched_link:
                subprocess.Popen(["cmd.exe", "/c", "start", "", matched_link], shell=False)
                display = os.path.splitext(os.path.basename(matched_link))[0]
                return f"Opened '{display}'."

            # Search common install directories for .exe files
            search_roots = [
                os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
                os.path.join(os.environ.get('APPDATA', '')),
            ]
            keywords = [w for w in app_lower.split() if len(w) > 2]
            for root in search_roots:
                if not os.path.exists(root):
                    continue
                try:
                    for dirpath, dirnames, filenames in os.walk(root):
                        # Skip deep paths to avoid long searches
                        depth = dirpath.replace(root, '').count(os.sep)
                        if depth > 3:
                            dirnames.clear()
                            continue
                        for fname in filenames:
                            if fname.endswith('.exe'):
                                fname_lower = fname.lower().replace('.exe', '')
                                if keywords and all(kw in fname_lower for kw in keywords):
                                    full_exe = os.path.join(dirpath, fname)
                                    subprocess.Popen(["cmd.exe", "/c", "start", "", full_exe], shell=False)
                                    return f"Opened '{fname.replace('.exe', '')}'."
                except Exception:
                    pass

            # Final fallback: PowerShell Start-Process with fuzzy name 
            # This lets Windows search its own app registry (UWP/Store apps)
            ps_cmd = f'Start-Process "{app_lower}" -ErrorAction SilentlyContinue'
            ps_result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
            if ps_result.returncode == 0:
                return f"Opened '{app_name}'."

            return f"Could not find an application matching '{app_name}'. Try using the exact name shown on the Start Menu."
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return f"Failed to open {app_name}: {str(e)}"
            
    async def open_website(self, url: str) -> str:
        if not self.is_windows: return "Unknown"
        try:
            url_clean = url.strip()
            if not url_clean.startswith("http://") and not url_clean.startswith("https://"):
                url_clean = "https://" + url_clean
            os.system(f'start "" "{url_clean}"')
            return f"Opened website {url_clean}"
        except Exception as e:
            return f"Failed to open website: {str(e)}"

    async def search_web(self, query: str, engine: str = "google") -> str:
        """Searches the web or ChatGPT directly with the query."""
        if not self.is_windows: return "Unknown"
        try:
            encoded_query = urllib.parse.quote_plus(query.strip())
            engine_lower = engine.lower().strip()
            
            if "chatgpt" in engine_lower or "chat gpt" in engine_lower or "chatgpt" in query.lower():
                url = f"https://chatgpt.com/?q={encoded_query}"
            elif "bing" in engine_lower:
                url = f"https://www.bing.com/search?q={encoded_query}"
            elif "duckduckgo" in engine_lower:
                url = f"https://duckduckgo.com/?q={encoded_query}"
            else:
                url = f"https://www.google.com/search?q={encoded_query}"

            os.system(f'start "" "{url}"')
            return f"Searched {engine} for '{query}'"
        except Exception as e:
            return f"Failed to search web: {str(e)}"

    async def minimize_window(self, app_name_or_title: str = "") -> str:
        """Minimizes the specified window or active window."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            import win32con
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return f"Minimized window '{win32gui.GetWindowText(hwnd)}'"
            else:
                import pyautogui
                pyautogui.hotkey('win', 'down')
                return "Minimized active window using shortcut"
        except Exception as e:
            return f"Failed to minimize window: {e}"

    async def maximize_window(self, app_name_or_title: str = "") -> str:
        """Maximizes the specified window or active window."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            import win32con
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                return f"Maximized window '{win32gui.GetWindowText(hwnd)}'"
            else:
                import pyautogui
                pyautogui.hotkey('win', 'up')
                return "Maximized active window using shortcut"
        except Exception as e:
            return f"Failed to maximize window: {e}"

    async def restore_window(self, app_name_or_title: str = "") -> str:
        """Restores a minimized/maximized window to normal size."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            import win32con
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                return f"Restored window '{win32gui.GetWindowText(hwnd)}'"
            return "No window found to restore"
        except Exception as e:
            return f"Failed to restore window: {e}"

    async def close_window(self, app_name_or_title: str = "") -> str:
        """Closes the specified window or active window gracefully."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            import win32con
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return f"Closed window '{title}'"
            else:
                import pyautogui
                pyautogui.hotkey('alt', 'f4')
                return "Closed active window with Alt+F4"
        except Exception as e:
            return f"Failed to close window: {e}"

    async def resize_window(self, width: int, height: int, app_name_or_title: str = "") -> str:
        """Resizes the specified window or active window to given width and height."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                win32gui.MoveWindow(hwnd, rect[0], rect[1], int(width), int(height), True)
                return f"Resized window '{win32gui.GetWindowText(hwnd)}' to {width}x{height}"
            return "No window found to resize"
        except Exception as e:
            return f"Failed to resize window: {e}"

    async def move_window(self, x: int, y: int, app_name_or_title: str = "") -> str:
        """Moves the window to coordinates (x, y)."""
        if not self.is_windows: return "Unknown"
        try:
            import win32gui
            hwnd = self._find_window(app_name_or_title)
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                win32gui.MoveWindow(hwnd, int(x), int(y), width, height, True)
                return f"Moved window '{win32gui.GetWindowText(hwnd)}' to ({x}, {y})"
            return "No window found to move"
        except Exception as e:
            return f"Failed to move window: {e}"
    
    async def close_application(self, app_name: str) -> str:
        if not self.is_windows:
            return "Error: Cannot run Windows commands on this OS."
            
        import psutil
        try:
            app_lower = app_name.lower().strip().removesuffix(".exe")
            alias_map = {
                "google chrome": "chrome",
                "chrome": "chrome",
                "edge": "msedge",
                "microsoft edge": "msedge",
                "vs code": "code",
                "vscode": "code",
                "calculator": "calculatorapp",
                "calc": "calc",
                "notepad": "notepad",
                "spotify": "spotify",
                "discord": "discord"
            }
            target_proc = alias_map.get(app_lower, app_lower)
            killed = 0

            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = proc.info['name'].lower().removesuffix(".exe")
                    if target_proc in pname or pname in target_proc:
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if killed > 0:
                return f"Closed {killed} instance(s) of {app_name}"
            
            # Fallback to taskkill
            os.system(f'taskkill /F /IM "{target_proc}.exe"')
            return f"Closed {app_name}"
        except Exception as e:
            return f"Failed to close {app_name}: {str(e)}"

    async def get_active_window(self) -> str:
        if not self.is_windows:
            return "Unknown"
            
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            return title
        except Exception as e:
            return f"Error: {e}"

    async def click(self, x: int, y: int) -> str:
        if not self.is_windows: return "Unknown"
        try:
            import pyautogui
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Failed to click: {e}"

    async def type_text(self, text: str) -> str:
        if not self.is_windows: return "Unknown"
        try:
            import pyautogui
            pyautogui.write(text, interval=0.01)
            return f"Typed: {text}"
        except Exception as e:
            return f"Failed to type: {e}"

    async def type_and_enter(self, text: str) -> str:
        """Types text into the active field and presses Enter."""
        if not self.is_windows: return "Unknown"
        try:
            import pyautogui
            pyautogui.write(text, interval=0.01)
            pyautogui.press('enter')
            return f"Typed '{text}' and pressed Enter"
        except Exception as e:
            return f"Failed to type and press Enter: {e}"

    async def press_key(self, key: str) -> str:
        """Presses a single key (e.g. 'enter', 'tab', 'escape', 'space', 'backspace')."""
        if not self.is_windows: return "Unknown"
        try:
            import pyautogui
            pyautogui.press(key.lower().strip())
            return f"Pressed key '{key}'"
        except Exception as e:
            return f"Failed to press key: {e}"

    async def wait_seconds(self, seconds: float = 2.0) -> str:
        """Waits/pauses for N seconds to allow applications or web pages to load."""
        try:
            delay = float(seconds)
            await asyncio.sleep(delay)
            return f"Waited for {delay} seconds"
        except Exception as e:
            return f"Wait failed: {e}"

    async def hotkey(self, keys: list) -> str:
        if not self.is_windows: return "Unknown"
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return f"Pressed hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Failed to press hotkey: {e}"

    async def screenshot(self) -> str:
        if not self.is_windows: return "Unknown"
        try:
            import mss
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            path = os.path.join(temp_dir, 'latest_screenshot.png')
            
            with mss.mss() as sct:
                sct.shot(output=path)
            
            return f"Screenshot saved to {path}"
        except Exception as e:
            return f"Failed to take screenshot: {e}"

def register_windows_tools(registry, provider: WindowsComputerProvider):
    registry.register(
        name="open_application",
        description="Opens a Windows application by name (e.g. 'chrome', 'notepad', 'calc', 'vscode', 'settings')",
        parameters={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        func=provider.open_application,
        permission_level=1
    )
    
    registry.register(
        name="open_website",
        description="Opens a specific website URL in the browser (e.g. 'https://chatgpt.com', 'google.com', 'youtube.com')",
        parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        func=provider.open_website,
        permission_level=1
    )

    registry.register(
        name="search_web",
        description="Searches the web using Google, ChatGPT, or Bing (e.g. query='weather in hyderabad today', engine='chatgpt' or 'google')",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "engine": {"type": "string", "enum": ["google", "chatgpt", "duckduckgo", "bing"], "description": "Search engine or platform to search on"}
            },
            "required": ["query"]
        },
        func=provider.search_web,
        permission_level=1
    )
    
    registry.register(
        name="close_application",
        description="Closes/terminates an application process by name (e.g. 'chrome', 'notepad', 'spotify')",
        parameters={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        func=provider.close_application,
        permission_level=2
    )

    registry.register(
        name="minimize_window",
        description="Minimizes a window. Pass app_name_or_title (e.g. 'Chrome', 'Notepad') or leave empty for active window.",
        parameters={"type": "object", "properties": {"app_name_or_title": {"type": "string"}}},
        func=provider.minimize_window,
        permission_level=1
    )

    registry.register(
        name="maximize_window",
        description="Maximizes a window. Pass app_name_or_title or leave empty for active window.",
        parameters={"type": "object", "properties": {"app_name_or_title": {"type": "string"}}},
        func=provider.maximize_window,
        permission_level=1
    )

    registry.register(
        name="restore_window",
        description="Restores a minimized or maximized window back to normal size.",
        parameters={"type": "object", "properties": {"app_name_or_title": {"type": "string"}}},
        func=provider.restore_window,
        permission_level=1
    )

    registry.register(
        name="close_window",
        description="Gracefully closes a window. Pass app_name_or_title or leave empty to close the current active window.",
        parameters={"type": "object", "properties": {"app_name_or_title": {"type": "string"}}},
        func=provider.close_window,
        permission_level=1
    )

    registry.register(
        name="resize_window",
        description="Resizes a window to the specified width and height in pixels.",
        parameters={
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "Window width in pixels (e.g. 1280, 800)"},
                "height": {"type": "integer", "description": "Window height in pixels (e.g. 720, 600)"},
                "app_name_or_title": {"type": "string", "description": "Window title or application name (optional)"}
            },
            "required": ["width", "height"]
        },
        func=provider.resize_window,
        permission_level=1
    )

    registry.register(
        name="move_window",
        description="Moves a window to screen coordinates (x, y).",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Screen X coordinate"},
                "y": {"type": "integer", "description": "Screen Y coordinate"},
                "app_name_or_title": {"type": "string", "description": "Window title or application name (optional)"}
            },
            "required": ["x", "y"]
        },
        func=provider.move_window,
        permission_level=1
    )
    
    registry.register(
        name="computer_click",
        description="Clicks the mouse at the specified screen x, y coordinates",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]},
        func=provider.click,
        permission_level=1
    )

    registry.register(
        name="computer_type",
        description="Types the given text using the keyboard.",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        func=provider.type_text,
        permission_level=1
    )

    registry.register(
        name="computer_type_and_enter",
        description="Types text and immediately presses the Enter key. Perfect for searching or submitting prompts.",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        func=provider.type_and_enter,
        permission_level=1
    )

    registry.register(
        name="computer_press_key",
        description="Presses a single key (e.g. 'enter', 'tab', 'escape', 'space', 'backspace', 'win')",
        parameters={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
        func=provider.press_key,
        permission_level=1
    )

    registry.register(
        name="wait_seconds",
        description="Pauses for N seconds to allow applications, animations, or web pages to finish loading.",
        parameters={"type": "object", "properties": {"seconds": {"type": "number", "description": "Seconds to wait (e.g. 2.0, 3.5)"}}, "required": ["seconds"]},
        func=provider.wait_seconds,
        permission_level=0
    )

    registry.register(
        name="computer_hotkey",
        description="Presses a combination of keys (e.g. ['ctrl', 'c'], ['win', 'd'], ['alt', 'tab'], ['alt', 'f4']).",
        parameters={"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]},
        func=provider.hotkey,
        permission_level=1
    )

    registry.register(
        name="computer_screenshot",
        description="Takes a screenshot of the monitor and saves it to a temp file",
        parameters={"type": "object", "properties": {}},
        func=provider.screenshot,
        permission_level=0
    )
