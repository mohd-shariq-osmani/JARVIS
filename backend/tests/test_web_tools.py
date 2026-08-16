import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.tools.web_tools import get_weather, search_information, get_current_time, register_web_tools
from app.tools.registry import ToolRegistry

async def test_live_web_tools():
    print("=== 1. Testing get_current_time ===")
    time_pakistan = await get_current_time("Pakistan")
    print("Pakistan Time:", time_pakistan)
    assert "Pakistan" in time_pakistan
    assert "PKT" in time_pakistan or "UTC" in time_pakistan

    time_tokyo = await get_current_time("Tokyo")
    print("Tokyo Time:", time_tokyo)
    assert "Tokyo" in time_tokyo

    time_local = await get_current_time("")
    print("Local Time:", time_local)
    assert "Current local time:" in time_local

    print("=== 2. Testing get_weather ===")
    weather_res = await get_weather("Hyderabad")
    print("Live Weather Output:", weather_res)
    assert "Hyderabad" in weather_res
    assert "°C" in weather_res

    print("=== 3. Testing search_information ===")
    search_res = await search_information("Python programming language")
    print("Live Search Output:\n", search_res)
    assert len(search_res) > 20

    print("=== 4. Testing ToolRegistry integration ===")
    registry = ToolRegistry()
    register_web_tools(registry)
    
    res = await registry.execute_tool("get_current_time", '{"location": "Pakistan"}')
    print("Registry get_current_time result:", res)
    assert "Pakistan" in res

    print("\n ALL LIVE WEB & TIME TOOLS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_live_web_tools())
