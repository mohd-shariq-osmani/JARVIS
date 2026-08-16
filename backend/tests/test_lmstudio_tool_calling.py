import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.ai.lmstudio import LMStudioProvider
from app.tools.registry import ToolRegistry
from app.tools.files import register_file_tools

async def main():
    ai = LMStudioProvider()
    healthy = await ai.initialize()
    print("LM Studio healthy:", healthy)
    if not healthy:
        print("LM Studio is not reachable on localhost:1234")
        return

    models = await ai.list_models()
    print("Models in LM Studio:", models)

    registry = ToolRegistry()
    register_file_tools(registry)
    schemas = registry.get_tool_schemas()
    print(f"Registered {len(schemas)} tools.")

    test_queries = [
        "there is only one image file in the downloads folder can you please open it",
        "where is the html file in download folder can you open it",
        "create a folder in Downloads folder called pen fight"
    ]

    for q in test_queries:
        print(f"\n================ QUERY: '{q}' ================")
        system_prompt = """You are JARVIS, an advanced AI desktop assistant.
CRITICAL: You MUST call a tool function when asked to open, read, write, create, or modify files or folders. NEVER reply with text claiming you did it without calling the tool.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": q}
        ]
        res = await ai.generate_with_tools(messages, schemas)
        print("Raw response from generate_with_tools:")
        print("Content:", res.get("content"))
        print("Tool Calls:", res.get("tool_calls"))

if __name__ == "__main__":
    asyncio.run(main())
