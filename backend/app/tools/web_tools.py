import httpx
import re
import urllib.parse
import logging
import os
import asyncio
import datetime
import pytz
from typing import Optional, Dict, Any

logger = logging.getLogger("WebTools")

async def get_current_time(location: str = "", **kwargs) -> str:
    """
    Gets the current live time, date, day of week, and timezone for any city, country, or location worldwide (or local system time).
    
    Args:
        location: City, country, or timezone name (e.g. 'Pakistan', 'London', 'New York', 'Tokyo', 'Sydney', 'India', 'California'). If empty, returns local time.
    """
    loc_clean = (location or kwargs.get("city") or kwargs.get("country") or "").strip().lower()
    
    # Common country and city aliases
    alias_tz_map = {
        "": None,
        "local": None,
        "here": None,
        "pakistan": "Asia/Karachi",
        "karachi": "Asia/Karachi",
        "lahore": "Asia/Karachi",
        "islamabad": "Asia/Karachi",
        "india": "Asia/Kolkata",
        "hyderabad": "Asia/Kolkata",
        "delhi": "Asia/Kolkata",
        "mumbai": "Asia/Kolkata",
        "bangalore": "Asia/Kolkata",
        "us": "America/New_York",
        "usa": "America/New_York",
        "united states": "America/New_York",
        "california": "America/Los_Angeles",
        "los angeles": "America/Los_Angeles",
        "san francisco": "America/Los_Angeles",
        "new york": "America/New_York",
        "nyc": "America/New_York",
        "texas": "America/Chicago",
        "chicago": "America/Chicago",
        "uk": "Europe/London",
        "london": "Europe/London",
        "japan": "Asia/Tokyo",
        "tokyo": "Asia/Tokyo",
        "dubai": "Asia/Dubai",
        "uae": "Asia/Dubai",
        "saudi arabia": "Asia/Riyadh",
        "riyadh": "Asia/Riyadh",
        "qatar": "Asia/Qatar",
        "doha": "Asia/Qatar",
        "germany": "Europe/Berlin",
        "berlin": "Europe/Berlin",
        "france": "Europe/Paris",
        "paris": "Europe/Paris",
        "australia": "Australia/Sydney",
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "canada": "America/Toronto",
        "toronto": "America/Toronto",
        "singapore": "Asia/Singapore",
        "china": "Asia/Shanghai",
        "beijing": "Asia/Shanghai",
        "russia": "Europe/Moscow",
        "moscow": "Europe/Moscow"
    }

    tz_target = alias_tz_map.get(loc_clean)

    # Search pytz timezones if not in alias map
    if not tz_target and loc_clean:
        query_fmt = loc_clean.replace(" ", "_")
        for tz in pytz.all_timezones:
            if query_fmt in tz.lower():
                tz_target = tz
                break

    try:
        if tz_target:
            tz = pytz.timezone(tz_target)
            now = datetime.datetime.now(tz)
            time_str = now.strftime('%I:%M %p (%Z, UTC%z)')
            date_str = now.strftime('%A, %B %d, %Y')
            return f"Current time in {location.title()}: {time_str} on {date_str}."
        else:
            now = datetime.datetime.now()
            time_str = now.strftime('%I:%M %p')
            date_str = now.strftime('%A, %B %d, %Y')
            return f"Current local time: {time_str} on {date_str}."
    except Exception as e:
        logger.error(f"Error calculating time for {location}: {e}")
        return f"Error retrieving time for {location}."

async def get_weather(city: str = "Hyderabad", **kwargs) -> str:
    """
    Fetches real-time live weather information for any city or location.
    
    Args:
        city: Name of the city (e.g. 'Hyderabad', 'New York', 'London', 'Tokyo').
    """
    clean_city = (city or kwargs.get("location") or "Hyderabad").strip()
    
    # Try wttr.in JSON API first
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            encoded_city = urllib.parse.quote(clean_city)
            res = await client.get(f"https://wttr.in/{encoded_city}?format=j1", headers={"User-Agent": "JARVIS-Assistant"})
            if res.status_code == 200:
                data = res.json()
                current = data.get("current_condition", [{}])[0]
                temp_c = current.get("temp_C", "N/A")
                feels_like_c = current.get("FeelsLikeC", temp_c)
                desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
                humidity = current.get("humidity", "N/A")
                wind_kmph = current.get("windspeedKmph", "N/A")
                
                # Check today's forecast high/low
                forecast = data.get("weather", [{}])[0]
                max_temp = forecast.get("maxtempC", "")
                min_temp = forecast.get("mintempC", "")
                forecast_str = f" Today's High: {max_temp}°C, Low: {min_temp}°C." if max_temp and min_temp else ""

                return (
                    f"Current Weather in {clean_city.title()}: {temp_c}°C ({desc}, feels like {feels_like_c}°C). "
                    f"Humidity: {humidity}%, Wind: {wind_kmph} km/h.{forecast_str}"
                )
    except Exception as e:
        logger.warning(f"wttr.in lookup failed: {e}. Trying Open-Meteo...")

    # Fallback to Open-Meteo geocoding + weather API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            geo_res = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(clean_city)}&count=1")
            if geo_res.status_code == 200:
                results = geo_res.json().get("results", [])
                if results:
                    lat = results[0]["latitude"]
                    lon = results[0]["longitude"]
                    name = results[0]["name"]
                    
                    weather_res = await client.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m")
                    if weather_res.status_code == 200:
                        cur = weather_res.json().get("current", {})
                        temp = cur.get("temperature_2m")
                        feels = cur.get("apparent_temperature")
                        hum = cur.get("relative_humidity_2m")
                        wind = cur.get("wind_speed_10m")
                        return f"Weather in {name}: {temp}°C (feels like {feels}°C), Humidity: {hum}%, Wind: {wind} km/h."
    except Exception as e:
        logger.error(f"Open-Meteo fallback failed: {e}")

    return f"Unable to fetch live weather for '{clean_city}' at the moment."

async def search_information(query: str, **kwargs) -> str:
    """
    Searches the live web and encyclopedias for real-time information, answers, definitions, news, facts, people, or events.
    
    Args:
        query: The search query (e.g. 'current time in Pakistan', 'who is CEO of Apple', 'latest stock price TSLA', 'who won the match today').
    """
    actual_query = (query or kwargs.get("q") or kwargs.get("search") or "").strip()
    if not actual_query:
        return "Error: No search query provided."

    results_text = []

    # 1. Quick Wikipedia lookup for entity/knowledge queries
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(actual_query)}"
            w_res = await client.get(wiki_url, headers={"User-Agent": "JARVIS-Assistant"})
            if w_res.status_code == 200:
                w_data = w_res.json()
                if w_data.get("extract"):
                    results_text.append(f"Summary: {w_data['extract']}")
    except Exception:
        pass

    # 2. DuckDuckGo Instant Answer API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(actual_query)}&format=json&no_html=1&skip_disambig=1"
            res = await client.get(ddg_url, headers={"User-Agent": "JARVIS-Assistant"})
            if res.status_code == 200:
                data = res.json()
                if data.get("AbstractText") and not results_text:
                    results_text.append(f"Abstract: {data['AbstractText']}")
                if data.get("Answer"):
                    results_text.append(f"Direct Answer: {data['Answer']}")
                
                topics = data.get("RelatedTopics", [])
                for t in topics[:3]:
                    if isinstance(t, dict) and t.get("Text"):
                        results_text.append(f"- {t['Text']}")
    except Exception as e:
        logger.warning(f"DuckDuckGo API search error: {e}")

    # 3. DuckDuckGo HTML Search Scrape for snippets
    if not results_text or len(results_text) < 2:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(actual_query)}"
                res = await client.get(html_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if res.status_code == 200:
                    snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', res.text, re.DOTALL)
                    for s in snippets[:4]:
                        clean_s = re.sub(r'<.*?>', '', s).strip()
                        if clean_s:
                            results_text.append(f"- {clean_s}")
        except Exception as e:
            logger.warning(f"DuckDuckGo HTML search error: {e}")

    if results_text:
        return f"Search results for '{actual_query}':\n" + "\n".join(results_text)
    
    return f"No direct search summary found for '{actual_query}'."

async def fetch_url_content(url: str) -> str:
    """Fetches text content from a given web URL."""
    try:
        clean_url = url.strip()
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
            
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            res = await client.get(clean_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if res.status_code == 200:
                text = re.sub(r'<script.*?</script>', '', res.text, flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<.*?>', ' ', text)
                clean_lines = [line.strip() for line in text.split('\n') if line.strip()]
                return "\n".join(clean_lines[:50])
            return f"Failed to fetch URL: HTTP {res.status_code}"
    except Exception as e:
        return f"Error fetching URL: {e}"

async def open_and_prompt_chatgpt(prompt: str) -> str:
    """Opens ChatGPT in the user's browser with the prompt preloaded and submitted."""
    try:
        encoded_prompt = urllib.parse.quote_plus(prompt.strip())
        url = f"https://chatgpt.com/?q={encoded_prompt}"
        os.system(f'start "" "{url}"')
        
        await asyncio.sleep(2.5)
        try:
            import pyautogui
            pyautogui.press('enter')
        except Exception:
            pass
            
        return f"Opened ChatGPT with prompt: '{prompt}'"
    except Exception as e:
        return f"Failed to open ChatGPT: {e}"

def register_web_tools(registry):
    registry.register(
        name="get_current_time",
        description="Get current live time, date, and timezone for any city, country, or location worldwide (e.g. 'Pakistan', 'London', 'Tokyo', 'New York', 'local')",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or country name (e.g. 'Pakistan', 'London', 'Tokyo', 'local')"}
            }
        },
        func=get_current_time,
        permission_level=0
    )

    registry.register(
        name="get_weather",
        description="Get real-time live weather, temperature, humidity, wind, and forecast for any city or location (e.g. 'Hyderabad', 'Mumbai', 'London')",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City or location name"}
            },
            "required": ["city"]
        },
        func=get_weather,
        permission_level=0
    )

    registry.register(
        name="search_information",
        description="Searches the live web and internet for ANY facts, answers, news, definitions, prices, questions, or real-time info. Use this whenever asked about anything in the world.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to look up"}
            },
            "required": ["query"]
        },
        func=search_information,
        permission_level=0
    )

    registry.register(
        name="fetch_url_content",
        description="Fetches and extracts clean readable text content from any website URL",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full website URL to read"}
            },
            "required": ["url"]
        },
        func=fetch_url_content,
        permission_level=0
    )

    registry.register(
        name="open_and_prompt_chatgpt",
        description="Opens ChatGPT in the browser and automatically submits a prompt",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt to ask ChatGPT in the browser"}
            },
            "required": ["prompt"]
        },
        func=open_and_prompt_chatgpt,
        permission_level=1
    )
