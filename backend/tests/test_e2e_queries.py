import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ai.lmstudio import LMStudioProvider
from app.tools.registry import ToolRegistry
from app.tools.files import register_file_tools
from app.memory.vector_memory import MemoryManager
from app.agent.orchestrator import AgentOrchestrator

async def main():
    ai = LMStudioProvider()
    await ai.initialize()
    
    registry = ToolRegistry()
    register_file_tools(registry)
    
    memory = MemoryManager()
    
    orchestrator = AgentOrchestrator(ai, registry, memory)
    
    test_queries = [
        "where is the html file in download folder can you open it",
        "open all image files and download folder",
        "there is only one image file in the downloads folder can you please open it",
        "create a folder in Downloads folder called pen fight"
    ]
    
    for q in test_queries:
        print(f"\n================ TESTING QUERY: '{q}' ================")
        resp = await orchestrator.handle_request(q)
        print("FINAL JARVIS RESPONSE:", resp)

if __name__ == "__main__":
    asyncio.run(main())
