import asyncio
import httpx
import win32gui

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Sending request: 'open the image in downloads folder'...")
        res = await client.post("http://127.0.0.1:8000/chat", json={"message": "open the image in downloads folder"})
        print("Response:", res.json())
        
        # Wait 2 seconds for worker execution and app launch
        await asyncio.sleep(2)
        
        wins = []
        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                if t and any(k in t.lower() for k in ["screenshot", "photo", "paint", "image", "viewer"]):
                    wins.append((hwnd, t))
        win32gui.EnumWindows(cb, None)
        print("Detected open image windows:", wins)
        assert len(wins) > 0, "No image viewer window was detected!"
        print("\n FILE OPENING VERIFIED ON LIVE WINDOWS DESKTOP!")

if __name__ == "__main__":
    asyncio.run(main())
