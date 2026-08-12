import platform
import logging
import base64
import os
from io import BytesIO

logger = logging.getLogger("WindowsComputerProvider")

class WindowsComputerProvider:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        if not self.is_windows:
            logger.warning("WindowsComputerProvider initialized on non-Windows system")
    
    async def open_application(self, app_name: str) -> str:
        if not self.is_windows:
            return "Error: Cannot run Windows commands on this OS."
            
        import os
        import glob
        try:
            app_lower = app_name.lower().strip()
            if app_lower == "settings" or app_lower == "windows settings":
                app_name = "ms-settings:"
                
            # If it's a direct file path, just open it
            if os.path.exists(app_name):
                os.system(f'start "" "{app_name}"')
                return f"Attempted to open {app_name}"
                
            # Try to find it in Start Menu if not a path
            paths = [
                os.path.join(os.environ.get('PROGRAMDATA', ''), r'Microsoft\Windows\Start Menu\Programs\**\*.lnk'),
                os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\**\*.lnk')
            ]
            links = []
            for p in paths:
                links.extend(glob.glob(p, recursive=True))
                
            for link in links:
                if app_lower in os.path.basename(link).lower():
                    os.system(f'start "" "{link}"')
                    return f"Found and opened {os.path.basename(link)} for {app_name}"
            
            # Fallback to general start command (for things in PATH)
            os.system(f'start "" "{app_name}"')
            return f"Attempted to open {app_name} from PATH"
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return f"Failed to open {app_name}: {str(e)}"
            
    async def open_website(self, url: str) -> str:
        if not self.is_windows: return "Unknown"
        import os
        try:
            if not url.startswith("http"):
                url = "https://" + url
            os.system(f'start "" "{url}"')
            return f"Attempted to open website {url}"
        except Exception as e:
            return f"Failed to open website: {str(e)}"
    
    async def close_application(self, app_name: str) -> str:
        if not self.is_windows:
            return "Error: Cannot run Windows commands on this OS."
            
        import os
        try:
            os.system(f'taskkill /F /IM {app_name}.exe')
            return f"Attempted to close {app_name}"
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
        except ImportError:
            return "win32gui not installed"
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
            
            # Save to temporary file in the backend
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
        description="Opens a Windows application by name or path",
        parameters={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        func=provider.open_application,
        permission_level=1
    )
    
    registry.register(
        name="open_website",
        description="Opens a URL in the default web browser (e.g., 'facebook.com')",
        parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        func=provider.open_website,
        permission_level=1
    )
    
    registry.register(
        name="close_application",
        description="Closes a Windows application by name (without .exe)",
        parameters={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        func=provider.close_application,
        permission_level=1
    )
    
    registry.register(
        name="computer_click",
        description="Clicks the mouse at the specified x, y coordinates",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]},
        func=provider.click,
        permission_level=1
    )

    registry.register(
        name="computer_type",
        description="Types the given text using the keyboard. DO NOT use this for keyboard shortcuts (like Ctrl+C).",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        func=provider.type_text,
        permission_level=1
    )

    registry.register(
        name="computer_hotkey",
        description="Presses a combination of keys (e.g. ['ctrl', 'c'] or ['win', 'd']). Use this for all keyboard shortcuts.",
        parameters={"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]},
        func=provider.hotkey,
        permission_level=1
    )

    registry.register(
        name="computer_screenshot",
        description="Takes a screenshot of the primary monitor and saves it to a temp file",
        parameters={"type": "object", "properties": {}},
        func=provider.screenshot,
        permission_level=0
    )
