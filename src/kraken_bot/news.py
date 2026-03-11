from __future__ import annotations

import json
from urllib.parse import quote_plus

import requests

POSITIVE_WORDS = {
    "approval", "approved", "bullish", "surge", "record", "breakout", "rally", "adoption", "inflows", "launch",
}
NEGATIVE_WORDS = {
    "hack", "exploit", "lawsuit", "ban", "bearish", "crash", "outflows", "liquidation", "fraud", "delay", "rejected",
}
SYMBOL_KEYWORDS = {
    "PF_XBTUSD": ["bitcoin", "btc", "xbt"],
    "PF_ETHUSD": ["ethereum", "eth"],
    "PF_SOLUSD": ["solana", "sol"],
    "PF_BNBUSD": ["bnb", "binance"],
    "PF_LINKUSD": ["chainlink", "link"],
}


def fetch_news(symbol: str, extra_terms: str = "") -> dict:
    base_terms = SYMBOL_KEYWORDS.get(symbol, [])
    query = " ".join(base_terms + ([extra_terms] if extra_terms else []))
    if not query.strip():
        query = symbol
    url = f"http://localhost:8080/search?q={quote_plus(query)}&format=json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", [])[:5]
    headlines = []
    score = 0
    for item in results:
        title = str(item.get("title", ""))
        content = str(item.get("content", ""))
        text = f"{title} {content}".lower()
        for word in POSITIVE_WORDS:
            if word in text:
                score += 1
        for word in NEGATIVE_WORDS:
            if word in text:
                score -= 1
        headlines.append({
            "title": title,
            "url": item.get("url", ""),
        })
    return {
        "symbol": symbol,
        "query": query,
        "score": score,
        "headlines": headlines,
    }
