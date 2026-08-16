import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.platform.windows.computer import WindowsComputerProvider, register_windows_tools
from app.tools.registry import ToolRegistry

async def test_tools():
    print("=== 1. Testing WindowsComputerProvider Tools Registration ===")
    provider = WindowsComputerProvider()
    registry = ToolRegistry()
    register_windows_tools(registry, provider)
    
    schemas = registry.get_tool_schemas()
    tool_names = [s["function"]["name"] for s in schemas]
    print(f"Registered {len(tool_names)} windows tools:")
    print(" ", tool_names)

    expected_tools = [
        "open_application", "open_website", "search_web", "close_application",
        "minimize_window", "maximize_window", "restore_window", "close_window",
        "resize_window", "move_window", "computer_click", "computer_type",
        "computer_type_and_enter", "computer_press_key", "wait_seconds",
        "computer_hotkey", "computer_screenshot"
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Missing tool: {exp}"

    print("=== 2. Testing Execution of Safe Tools ===")
    # Test wait_seconds
    res_wait = await registry.execute_tool("wait_seconds", '{"seconds": 0.5}')
    print("Wait tool result:", res_wait)
    assert "Waited for 0.5 seconds" in res_wait

    # Test window query/finding
    hwnd = provider._find_window("")
    print(f"Foreground window HWND: {hwnd}")

    print("\n ALL WINDOW & WEB TOOLS TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_tools())
