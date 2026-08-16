import asyncio
import httpx
import os
import shutil

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check status
        res = await client.get("http://127.0.0.1:8000/status")
        print("Status:", res.json())
        
        # Test creating folder in Downloads
        print("\n--- Testing folder creation ---")
        chat_res = await client.post("http://127.0.0.1:8000/chat", json={"message": "create a folder in Downloads folder called pen fight"})
        print("Enqueue response:", chat_res.json())
        
        # Give queue worker 2 seconds to process
        await asyncio.sleep(2)
        
        # Check real Downloads folder
        user_home = os.path.expanduser("~")
        real_dl_folder = os.path.join(user_home, "Downloads", "pen fight")
        print("Checking real Downloads for 'pen fight':", real_dl_folder)
        print("Exists in real Downloads:", os.path.exists(real_dl_folder))
        assert os.path.exists(real_dl_folder)
        
        # Check backend/Downloads to ensure nothing is wrongly created there
        backend_dl = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Downloads")
        print("Checking backend/Downloads (should NOT exist):", backend_dl)
        print("Exists in backend/Downloads:", os.path.exists(backend_dl))
        assert not os.path.exists(backend_dl)

        print("\n ALL LIVE ENDPOINT CHECKS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
