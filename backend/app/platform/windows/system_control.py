import platform
import logging
import os
import ctypes
import glob
import subprocess
import psutil
import pyperclip
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SystemControl")

class WindowsSystemControl:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    async def set_system_volume(self, level: int) -> str:
        """Sets master system volume (0 to 100)."""
        if not self.is_windows: return "Only available on Windows."
        try:
            target = max(0, min(100, int(level)))
            # Set volume via PowerShell audio COM script
            ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
1..50 | ForEach-Object {{ $wsh.SendKeys([char]174) }}
$steps = [math]::Round({target} / 2)
1..$steps | ForEach-Object {{ $wsh.SendKeys([char]175) }}
"""
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
            return f"System volume set to approximately {target}%"
        except Exception as e:
            return f"Failed to set volume: {e}"

    async def media_control(self, action: str = "play_pause") -> str:
        """Controls media playback: play_pause, next, previous, stop, volume_up, volume_down, mute."""
        if not self.is_windows: return "Only available on Windows."
        import pyautogui
        act = action.lower().strip().replace(" ", "_")
        try:
            if act in ["play", "pause", "play_pause", "toggle"]:
                pyautogui.press('playpause')
                return "Toggled media play/pause."
            elif act in ["next", "next_track", "skip"]:
                pyautogui.press('nexttrack')
                return "Skipped to next track."
            elif act in ["prev", "previous", "previous_track", "back"]:
                pyautogui.press('prevtrack')
                return "Returned to previous track."
            elif act in ["stop"]:
                pyautogui.press('stop')
                return "Stopped media playback."
            elif act in ["volume_up", "louder"]:
                pyautogui.press('volumeup', presses=5)
                return "Increased volume."
            elif act in ["volume_down", "quieter"]:
                pyautogui.press('volumedown', presses=5)
                return "Decreased volume."
            elif act in ["mute", "unmute", "toggle_mute"]:
                pyautogui.press('volumemute')
                return "Toggled audio mute."
            else:
                return f"Unknown media action '{action}'."
        except Exception as e:
            return f"Media control error: {e}"

    async def set_screen_brightness(self, percent: int) -> str:
        """Sets display brightness from 0 to 100% (supported on laptops / integrated displays)."""
        if not self.is_windows: return "Only available on Windows."
        try:
            target = max(0, min(100, int(percent)))
            ps_cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {target})"
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=6)
            if res.returncode == 0:
                return f"Screen brightness adjusted to {target}%."
            return f"Brightness control is not supported on this external monitor or display."
        except Exception as e:
            return f"Failed to set brightness: {e}"

    async def lock_workstation(self) -> str:
        """Locks the computer workstation (Win+L)."""
        if not self.is_windows: return "Only available on Windows."
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Workstation locked."
        except Exception as e:
            return f"Failed to lock workstation: {e}"

    async def sleep_pc(self) -> str:
        """Puts the computer into sleep / suspend mode."""
        if not self.is_windows: return "Only available on Windows."
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Entering sleep mode..."
        except Exception as e:
            return f"Failed to sleep PC: {e}"

    async def get_battery_status(self) -> str:
        """Returns battery percentage, plugged-in status, and power estimation."""
        try:
            batt = psutil.sensors_battery()
            if not batt:
                return "Running on AC Desktop Power (No battery detected)."
            pct = batt.percent
            plugged = "Plugged in (Charging)" if batt.power_plugged else "Running on Battery"
            mins = batt.secsleft // 60 if batt.secsleft > 0 else None
            time_str = f" (~{mins//60}h {mins%60}m remaining)" if mins and not batt.power_plugged else ""
            return f"Battery: {pct}% | Status: {plugged}{time_str}."
        except Exception as e:
            return f"Battery query error: {e}"

    async def read_clipboard(self) -> str:
        """Reads and returns text currently copied to the system clipboard."""
        try:
            content = pyperclip.paste()
            if not content or not content.strip():
                return "Clipboard is currently empty."
            return f"Clipboard text:\n{content.strip()}"
        except Exception as e:
            return f"Failed to read clipboard: {e}"

    async def copy_to_clipboard(self, text: str) -> str:
        """Copies text onto the system clipboard."""
        try:
            pyperclip.copy(text)
            return f"Copied {len(text)} characters to clipboard."
        except Exception as e:
            return f"Failed to copy to clipboard: {e}"

    async def search_local_files(self, query: str, directory: str = "") -> str:
        """Searches for files matching query in user directories (Desktop, Documents, Downloads, etc.)."""
        try:
            clean_q = query.lower().strip()
            user_home = os.path.expanduser("~")
            
            search_dirs = []
            if directory and os.path.exists(directory):
                search_dirs.append(directory)
            else:
                for sub in ["Desktop", "Downloads", "Documents", "Pictures", "Videos", "Music"]:
                    p = os.path.join(user_home, sub)
                    if os.path.exists(p):
                        search_dirs.append(p)

            matches = []
            max_results = 8

            for sdir in search_dirs:
                for root, _, files in os.walk(sdir):
                    for file in files:
                        if clean_q in file.lower():
                            matches.append(os.path.join(root, file))
                            if len(matches) >= max_results:
                                break
                    if len(matches) >= max_results:
                        break

            if matches:
                return f"Found {len(matches)} matching file(s):\n" + "\n".join([f"- {m}" for m in matches])
            return f"No files matching '{query}' were found in user directories."
        except Exception as e:
            return f"File search error: {e}"

    async def focus_window(self, app_name: str) -> str:
        """Brings an application or window to the foreground."""
        if not self.is_windows: return "Only available on Windows."
        try:
            import win32gui
            import win32con
            import win32process

            query = app_name.lower().strip()
            found_hwnd = None

            def enum_cb(hwnd, _):
                nonlocal found_hwnd
                if win32gui.IsWindowVisible(hwnd) and not found_hwnd:
                    title = win32gui.GetWindowText(hwnd).lower()
                    if query in title:
                        found_hwnd = hwnd

            win32gui.EnumWindows(enum_cb, None)

            if found_hwnd:
                win32gui.ShowWindow(found_hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(found_hwnd)
                return f"Brought '{win32gui.GetWindowText(found_hwnd)}' to foreground."
            return f"Could not find an open window matching '{app_name}'."
        except Exception as e:
            return f"Error focusing window: {e}"

    async def list_open_windows(self) -> str:
        """Lists all open visible application windows on the desktop."""
        if not self.is_windows: return "Only available on Windows."
        try:
            import win32gui
            windows = []

            def enum_cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).strip()
                    if title and title not in ["Program Manager", "Settings", "Windows Input Experience"]:
                        windows.append(title)

            win32gui.EnumWindows(enum_cb, None)
            if windows:
                return f"Active Open Windows ({len(windows)}):\n" + "\n".join([f"- {w}" for w in windows[:12]])
            return "No open application windows detected."
        except Exception as e:
            return f"Error listing windows: {e}"

def register_system_control_tools(registry):
    ctrl = WindowsSystemControl()

    registry.register(
        name="set_system_volume",
        description="Sets the master system audio volume (level 0 to 100)",
        parameters={"type": "object", "properties": {"level": {"type": "integer", "description": "Volume percentage (0-100)"}}, "required": ["level"]},
        func=ctrl.set_system_volume,
        permission_level=1
    )

    registry.register(
        name="media_control",
        description="Controls music and video playback (action: 'play_pause', 'next', 'previous', 'stop', 'volume_up', 'volume_down', 'mute')",
        parameters={"type": "object", "properties": {"action": {"type": "string", "enum": ["play_pause", "next", "previous", "stop", "volume_up", "volume_down", "mute"]}}, "required": ["action"]},
        func=ctrl.media_control,
        permission_level=1
    )

    registry.register(
        name="set_screen_brightness",
        description="Adjusts screen display brightness from 0 to 100%",
        parameters={"type": "object", "properties": {"percent": {"type": "integer", "description": "Brightness percentage (0-100)"}}, "required": ["percent"]},
        func=ctrl.set_screen_brightness,
        permission_level=1
    )

    registry.register(
        name="lock_workstation",
        description="Locks the computer screen workstation (Win+L)",
        parameters={"type": "object", "properties": {}},
        func=ctrl.lock_workstation,
        permission_level=1
    )

    registry.register(
        name="sleep_pc",
        description="Puts the computer to sleep / standby mode",
        parameters={"type": "object", "properties": {}},
        func=ctrl.sleep_pc,
        permission_level=2
    )

    registry.register(
        name="get_battery_status",
        description="Get laptop battery percentage, charging state, and remaining time",
        parameters={"type": "object", "properties": {}},
        func=ctrl.get_battery_status,
        permission_level=0
    )

    registry.register(
        name="read_clipboard",
        description="Reads the text currently copied to the clipboard",
        parameters={"type": "object", "properties": {}},
        func=ctrl.read_clipboard,
        permission_level=0
    )

    registry.register(
        name="copy_to_clipboard",
        description="Copies text to the system clipboard",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        func=ctrl.copy_to_clipboard,
        permission_level=1
    )

    registry.register(
        name="search_local_files",
        description="Searches for files on the hard drive by name or extension in Desktop, Downloads, and Documents",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filename or extension to search for"},
                "directory": {"type": "string", "description": "Optional specific folder path"}
            },
            "required": ["query"]
        },
        func=ctrl.search_local_files,
        permission_level=0
    )

    registry.register(
        name="focus_window",
        description="Brings a specific open application or window to the foreground by name",
        parameters={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        func=ctrl.focus_window,
        permission_level=1
    )

    registry.register(
        name="list_open_windows",
        description="Lists all open visible desktop application windows",
        parameters={"type": "object", "properties": {}},
        func=ctrl.list_open_windows,
        permission_level=0
    )
