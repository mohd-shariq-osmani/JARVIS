import asyncio
from app.memory.vector_memory import MemoryManager

async def main():
    mm = MemoryManager()
    await mm.add_memory("User likes neon purple.")
    print("Added memory.")
    ctx = await mm.get_context("What color does the user like?")
    print("Context retrieved:")
    print(ctx)

if __name__ == "__main__":
    asyncio.run(main())
