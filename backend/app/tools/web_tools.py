import httpx
import re
import urllib.parse
import logging
import os
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("WebTools")

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
    Searches the web for live, up-to-date information, facts, answers, or news.
    
    Args:
        query: The search query (e.g. 'who is CEO of Apple', 'latest stock price TSLA', 'who won the match today').
    """
    actual_query = (query or kwargs.get("q") or kwargs.get("search") or "").strip()
    if not actual_query:
        return "Error: No search query provided."

    results_text = []

    # 1. DuckDuckGo Instant Answer API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(actual_query)}&format=json&no_html=1&skip_disambig=1"
            res = await client.get(ddg_url, headers={"User-Agent": "JARVIS-Assistant"})
            if res.status_code == 200:
                data = res.json()
                if data.get("AbstractText"):
                    results_text.append(f"Abstract: {data['AbstractText']}")
                if data.get("Answer"):
                    results_text.append(f"Direct Answer: {data['Answer']}")
                
                # Related topics
                topics = data.get("RelatedTopics", [])
                for t in topics[:3]:
                    if isinstance(t, dict) and t.get("Text"):
                        results_text.append(f"- {t['Text']}")
    except Exception as e:
        logger.warning(f"DuckDuckGo API search error: {e}")

    # 2. DuckDuckGo HTML Search Scrape for snippets
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
    
    return f"No direct search summary found for '{actual_query}'. Try querying a browser directly."

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
        # Modern ChatGPT accepts ?q= query parameter to immediately start answering
        url = f"https://chatgpt.com/?q={encoded_prompt}"
        os.system(f'start "" "{url}"')
        
        # Also wait a moment and type/press enter as fallback
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
        description="Searches the live web for facts, answers, news, definitions, prices, or sports scores. Use this whenever the user asks for real-time information.",
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
