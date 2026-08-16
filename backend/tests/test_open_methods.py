import os
import sys
import subprocess

def test_methods():
    target = os.path.normpath(r"C:\Users\shari\Downloads\Screenshot_20260813-043107.png")
    print(f"Testing target: {target}")
    print(f"Exists: {os.path.exists(target)}")
    
    # Check default file assoc via assoc and ftype
    try:
        assoc = subprocess.run(["cmd", "/c", "assoc", ".png"], capture_output=True, text=True)
        print("assoc .png:", assoc.stdout.strip())
        if "=" in assoc.stdout:
            file_type = assoc.stdout.strip().split("=")[1]
            ftype = subprocess.run(["cmd", "/c", "ftype", file_type], capture_output=True, text=True)
            print("ftype:", ftype.stdout.strip())
    except Exception as e:
        print("assoc error:", e)

    # Method 1: os.startfile
    print("\nTrying os.startfile...")
    try:
        os.startfile(target)
        print("os.startfile returned without exception.")
    except Exception as e:
        print("os.startfile failed:", e)

    # Method 2: ShellExecute
    try:
        import win32api
        import win32con
        code = win32api.ShellExecute(0, "open", target, None, None, win32con.SW_SHOWNORMAL)
        print(f"win32api.ShellExecute return code: {code} (values > 32 mean success)")
    except Exception as e:
        print("win32api.ShellExecute failed:", e)

    # Method 3: PowerShell Start-Process
    try:
        res = subprocess.run(["powershell", "-Command", f"Start-Process -FilePath '{target}'"], capture_output=True, text=True)
        print("PowerShell Start-Process returncode:", res.returncode, res.stdout, res.stderr)
    except Exception as e:
        print("PowerShell Start-Process failed:", e)

if __name__ == "__main__":
    test_methods()
