import os
import subprocess
import time
import win32gui

def enum_windows():
    wins = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if t:
                wins.append((hwnd, t))
    win32gui.EnumWindows(cb, None)
    return wins

target = os.path.normpath(r"C:\Users\shari\Downloads\Screenshot_20260813-043107.png")
print("Before launch, visible windows:", [w[1] for w in enum_windows() if any(k in w[1].lower() for k in ["photo", "paint", "image", "screenshot", "picture", "viewer"])])

# Try start command via shell
print("Launching via cmd /c start...")
subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)

time.sleep(2)
print("After launch, visible windows:", [w[1] for w in enum_windows() if any(k in w[1].lower() for k in ["photo", "paint", "image", "screenshot", "picture", "viewer"])])
