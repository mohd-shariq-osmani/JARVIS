import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.tools.web_tools import get_weather, search_information, register_web_tools
from app.tools.registry import ToolRegistry

async def test_live_web_tools():
    print("=== 1. Testing get_weather ===")
    weather_res = await get_weather("Hyderabad")
    print("Live Weather Output:", weather_res)
    assert "Hyderabad" in weather_res
    assert "°C" in weather_res

    print("=== 2. Testing search_information ===")
    search_res = await search_information("Python programming language")
    print("Live Search Output:\n", search_res)
    assert len(search_res) > 20

    print("=== 3. Testing ToolRegistry integration ===")
    registry = ToolRegistry()
    register_web_tools(registry)
    
    res = await registry.execute_tool("get_weather", '{"city": "Hyderabad"}')
    print("Registry get_weather result:", res)
    assert "Hyderabad" in res

    print("\n ALL LIVE WEB TOOLS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_live_web_tools())
