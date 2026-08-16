import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.memory.vector_memory import MemoryManager, register_memory_tools
from app.tools.registry import ToolRegistry

async def test_memory_flow():
    print("--- 1. Initializing MemoryManager ---")
    memory = MemoryManager()
    
    print("--- 2. Testing Memory Creation ---")
    res1 = await memory.add_memory(content="User prefers Python over C++", memory_type="preference")
    print("Add preference:", res1)
    assert "Successfully saved" in res1
    
    res2 = await memory.add_memory(text="My monitor resolution is 4K", type="device")
    print("Add device via alias:", res2)
    assert "Successfully saved" in res2
    
    print("--- 3. Testing Memory Listing ---")
    all_mem = await memory.get_all_memories()
    print(f"Total memories stored: {len(all_mem)}")
    assert len(all_mem) >= 2
    for m in all_mem:
        print(f"  - [{m['id'][:8]}] ({m['type']}) {m['content']}")
        
    print("--- 4. Testing Context Retrieval ---")
    ctx = await memory.get_context("What monitor do I have?")
    print("Context retrieved:\n", ctx)
    assert "4K" in ctx or "Python" in ctx
    
    print("--- 5. Testing Tool Execution via Registry ---")
    registry = ToolRegistry()
    register_memory_tools(registry, memory)
    
    # Test JSON string payload with 'type' keyword
    tool_res = await registry.execute_tool("remember", '{"content": "Project name is JARVIS", "type": "fact"}')
    print("Tool 'remember' result:", tool_res)
    assert "Successfully saved" in tool_res
    
    # Test tool 'search_memory'
    search_res = await registry.execute_tool("search_memory", '{"query": "Project name"}')
    print("Tool 'search_memory' result:\n", search_res)
    assert "JARVIS" in search_res
    
    print("\n ALL MEMORY SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_memory_flow())
