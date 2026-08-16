import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.platform.windows.system_control import WindowsSystemControl, register_system_control_tools
from app.tools.online_tools import get_financial_quote, convert_currency_or_units, define_word, register_online_tools
from app.tools.productivity_tools import add_note, list_notes, search_notes, get_daily_briefing, register_productivity_tools
from app.tools.registry import ToolRegistry

async def test_all_suites():
    print("=== 1. Testing System Control Suite ===")
    sys_ctrl = WindowsSystemControl()
    
    # Test clipboard
    await sys_ctrl.copy_to_clipboard("JARVIS Full Feature Suite Test")
    clip = await sys_ctrl.read_clipboard()
    print("Clipboard Output:", clip)
    assert "JARVIS Full Feature Suite Test" in clip

    # Test battery
    batt = await sys_ctrl.get_battery_status()
    print("Battery Output:", batt)
    assert len(batt) > 5

    # Test list open windows
    win_list = await sys_ctrl.list_open_windows()
    print("Open Windows:\n", win_list)

    print("\n=== 2. Testing Online & Financial Suite ===")
    # Test stock quote
    nvda_quote = await get_financial_quote("NVDA")
    print("NVDA Quote:", nvda_quote)
    assert "NVDA" in nvda_quote
    assert "$" in nvda_quote

    # Test crypto quote
    btc_quote = await get_financial_quote("BTC")
    print("BTC Quote:", btc_quote)
    assert "BTC" in btc_quote
    assert "$" in btc_quote

    # Test currency conversion
    curr_conv = await convert_currency_or_units(100, "USD", "INR")
    print("Currency Conversion:", curr_conv)
    assert "INR" in curr_conv

    # Test unit conversion
    unit_conv = await convert_currency_or_units(10, "KM", "MILES")
    print("Unit Conversion:", unit_conv)
    assert "MILES" in unit_conv.upper()

    # Test dictionary
    word_def = await define_word("serendipity")
    print("Dictionary Def:\n", word_def)
    assert "serendipity" in word_def.lower()

    print("\n=== 3. Testing Productivity & Daily Briefing Suite ===")
    # Test notes
    await add_note("Project Upgrade", "Implemented all desktop automation and intelligence tools.", tags=["dev"])
    notes_list = await list_notes()
    print("Notes List:\n", notes_list)
    assert "Project Upgrade" in notes_list

    # Test search notes
    searched = await search_notes("upgrade")
    print("Search Notes Output:\n", searched)
    assert "Project Upgrade" in searched

    # Test daily briefing
    briefing = await get_daily_briefing("Hyderabad")
    print("Daily Briefing Output:\n", briefing)
    assert "Good day, sir" in briefing
    assert "Hyderabad" in briefing

    print("\n=== 4. Testing Complete Tool Registry ===")
    registry = ToolRegistry()
    register_system_control_tools(registry)
    register_online_tools(registry)
    register_productivity_tools(registry)
    
    schemas = registry.get_tool_schemas()
    print(f"Total New Tools Registered: {len(schemas)}")
    names = [s["function"]["name"] for s in schemas]
    print("Tool names:", names)
    assert "get_financial_quote" in names
    assert "get_daily_briefing" in names
    assert "set_system_volume" in names

    print("\n ALL SYSTEM CONTROL, ONLINE INTELLIGENCE & PRODUCTIVITY SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_all_suites())
