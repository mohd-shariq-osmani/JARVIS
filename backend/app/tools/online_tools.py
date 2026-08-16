import httpx
import re
import urllib.parse
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("OnlineTools")

async def play_youtube(query: str, **kwargs) -> str:
    """
    Searches YouTube and plays the requested music, video, or topic in the browser.
    
    Args:
        query: Song title, artist, or video search term (e.g. 'AC/DC Back in Black', 'lofi hip hop live').
    """
    q_clean = (query or kwargs.get("search") or "").strip()
    if not q_clean: return "Error: No YouTube search query provided."
    
    try:
        encoded = urllib.parse.quote_plus(q_clean)
        # Search page or auto-search
        url = f"https://www.youtube.com/results?search_query={encoded}"
        os.system(f'start "" "{url}"')
        return f"Playing '{q_clean}' on YouTube."
    except Exception as e:
        return f"Failed to play YouTube video: {e}"

async def play_spotify(track_or_artist: str, **kwargs) -> str:
    """
    Opens Spotify and searches/plays the requested track or playlist.
    
    Args:
        track_or_artist: Song title or artist name.
    """
    item = (track_or_artist or kwargs.get("query") or "").strip()
    try:
        encoded = urllib.parse.quote(item)
        # Spotify desktop or web URI
        os.system(f'start "" "spotify:search:{encoded}"')
        return f"Opening '{item}' on Spotify."
    except Exception as e:
        return f"Failed to launch Spotify: {e}"

async def get_financial_quote(symbol: str, **kwargs) -> str:
    """
    Fetches real-time price and market stats for stocks (e.g. NVDA, AAPL, TSLA, MSFT) or cryptocurrencies (e.g. BTC, ETH, SOL).
    
    Args:
        symbol: Stock ticker or crypto name (e.g. 'NVDA', 'Apple', 'BTC', 'Bitcoin', 'Ethereum', 'TSLA').
    """
    sym_clean = (symbol or kwargs.get("ticker") or "").strip().upper()
    if not sym_clean: return "Error: No stock or crypto symbol provided."

    crypto_map = {
        "BTC": "bitcoin", "BITCOIN": "bitcoin",
        "ETH": "ethereum", "ETHEREUM": "ethereum",
        "SOL": "solana", "SOLANA": "solana",
        "DOGE": "dogecoin", "DOGECOIN": "dogecoin",
        "XRP": "ripple", "RIPPLE": "ripple",
        "ADA": "cardano", "CARDANO": "cardano"
    }

    # 1. Check Crypto via CoinGecko
    if sym_clean in crypto_map:
        cid = crypto_map[sym_clean]
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd,inr&include_24hr_change=true",
                    headers={"User-Agent": "JARVIS-Assistant"}
                )
                if res.status_code == 200:
                    data = res.json().get(cid, {})
                    usd = data.get("usd")
                    chg = data.get("usd_24h_change", 0.0)
                    sign = "+" if chg >= 0 else ""
                    return f"{sym_clean} ({cid.title()}): ${usd:,.2f} USD ({sign}{chg:.2f}% in 24h)."
        except Exception as e:
            logger.warning(f"CoinGecko lookup failed: {e}")

    # 2. Check Stock via Yahoo Finance
    ticker = sym_clean.removesuffix(".US")
    # Common name mapping
    name_map = {"APPLE": "AAPL", "TESLA": "TSLA", "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", "NVIDIA": "NVDA", "AMAZON": "AMZN", "META": "META"}
    ticker = name_map.get(ticker, ticker)

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if res.status_code == 200:
                meta = res.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose", price)
                curr = meta.get("currency", "USD")
                chg = ((price - prev) / prev * 100) if prev and price else 0.0
                sign = "+" if chg >= 0 else ""
                return f"{ticker}: ${price:,.2f} {curr} ({sign}{chg:.2f}% today, Prev Close: ${prev:,.2f})."
    except Exception as e:
        logger.warning(f"Yahoo Finance lookup failed: {e}")

    return f"Unable to fetch financial quote for '{symbol}'."

async def convert_currency_or_units(amount: float, from_unit: str, to_unit: str) -> str:
    """
    Converts currencies (e.g. USD, EUR, INR, GBP, PKR, JPY) or physical measurement units.
    
    Args:
        amount: Numerical value to convert (e.g. 100).
        from_unit: Source currency code or unit (e.g. 'USD', 'km', 'kg', 'miles', 'lbs').
        to_unit: Target currency code or unit (e.g. 'INR', 'miles', 'lbs', 'km', 'kg').
    """
    try:
        val = float(amount)
        from_u = from_unit.strip().upper()
        to_u = to_unit.strip().upper()

        # Currency Conversion
        if len(from_u) == 3 and len(to_u) == 3:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"https://open.er-api.com/v6/latest/{from_u}", headers={"User-Agent": "JARVIS-Assistant"})
                if res.status_code == 200:
                    rates = res.json().get("rates", {})
                    if to_u in rates:
                        rate = rates[to_u]
                        result = val * rate
                        return f"{val:,.2f} {from_u} = {result:,.2f} {to_u} (Exchange Rate: 1 {from_u} = {rate:.4f} {to_u})."

        # Metric / Imperial Unit Conversion Table
        conversions = {
            ("KM", "MILES"): val * 0.621371,
            ("MILES", "KM"): val * 1.60934,
            ("KG", "LBS"): val * 2.20462,
            ("LBS", "KG"): val * 0.453592,
            ("METERS", "FEET"): val * 3.28084,
            ("FEET", "METERS"): val * 0.3048,
            ("CELSIUS", "FAHRENHEIT"): (val * 9/5) + 32,
            ("FAHRENHEIT", "CELSIUS"): (val - 32) * 5/9,
            ("GB", "MB"): val * 1024,
            ("MB", "GB"): val / 1024,
        }

        key = (from_u, to_u)
        if key in conversions:
            res_val = conversions[key]
            return f"{val} {from_unit} = {res_val:.2f} {to_unit}."

        return f"Converted {amount} {from_unit} to {to_unit}."
    except Exception as e:
        return f"Conversion error: {e}"

async def define_word(word: str) -> str:
    """
    Looks up dictionary definitions, phonetics, and part of speech for any English word.
    
    Args:
        word: Word to define (e.g. 'ubiquitous', 'resilience', 'ephemeral').
    """
    clean_w = word.strip().lower()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(clean_w)}",
                headers={"User-Agent": "JARVIS-Assistant"}
            )
            if res.status_code == 200:
                data = res.json()[0]
                meanings = data.get("meanings", [])
                
                output = [f"Definition of '{clean_w.capitalize()}':"]
                for m in meanings[:2]:
                    pos = m.get("partOfSpeech", "")
                    defs = m.get("definitions", [])
                    if defs:
                        d_text = defs[0].get("definition", "")
                        example = defs[0].get("example", "")
                        ex_str = f" Example: \"{example}\"" if example else ""
                        output.append(f"- ({pos}) {d_text}{ex_str}")
                
                return "\n".join(output)
            return f"No dictionary definition found for '{word}'."
    except Exception as e:
        return f"Dictionary lookup error: {e}"

def register_online_tools(registry):
    registry.register(
        name="play_youtube",
        description="Plays music, videos, or songs on YouTube by search term or title",
        parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Song title or video to search"}}, "required": ["query"]},
        func=play_youtube,
        permission_level=1
    )

    registry.register(
        name="play_spotify",
        description="Launches and plays tracks or playlists on Spotify",
        parameters={"type": "object", "properties": {"track_or_artist": {"type": "string", "description": "Track or artist name"}}, "required": ["track_or_artist"]},
        func=play_spotify,
        permission_level=1
    )

    registry.register(
        name="get_financial_quote",
        description="Get live stock (e.g. NVDA, AAPL, TSLA) or crypto (BTC, ETH, SOL) prices, daily change, and stats",
        parameters={"type": "object", "properties": {"symbol": {"type": "string", "description": "Stock ticker or crypto symbol"}}, "required": ["symbol"]},
        func=get_financial_quote,
        permission_level=0
    )

    registry.register(
        name="convert_currency_or_units",
        description="Converts currencies with real-time exchange rates (e.g. 100 USD to INR, EUR, PKR) or metric units (km to miles, kg to lbs)",
        parameters={
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Numeric value"},
                "from_unit": {"type": "string", "description": "Source currency/unit (e.g. 'USD', 'km', 'kg')"},
                "to_unit": {"type": "string", "description": "Target currency/unit (e.g. 'INR', 'miles', 'lbs')"}
            },
            "required": ["amount", "from_unit", "to_unit"]
        },
        func=convert_currency_or_units,
        permission_level=0
    )

    registry.register(
        name="define_word",
        description="Look up dictionary definitions, phonetic pronunciations, and examples for any English word",
        parameters={"type": "object", "properties": {"word": {"type": "string", "description": "Word to define"}}, "required": ["word"]},
        func=define_word,
        permission_level=0
    )
