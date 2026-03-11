from __future__ import annotations

from urllib.parse import quote_plus

import requests

POSITIVE = {"yes", "approved", "approval", "cuts", "bullish", "win", "support"}
NEGATIVE = {"no", "rejected", "rejection", "hike", "bearish", "ban", "lawsuit"}


EVENT_QUERIES = {
    "PF_XBTUSD": ["bitcoin etf approval", "fed rate cuts crypto", "bitcoin regulation"],
    "PF_ETHUSD": ["ethereum etf approval", "fed rate cuts crypto", "ethereum regulation"],
    "PF_SOLUSD": ["solana etf", "crypto regulation solana"],
    "PF_BNBUSD": ["binance regulation", "bnb regulation"],
    "PF_LINKUSD": ["chainlink adoption", "defi regulation oracle"],
}


def fetch_polymarket_sentiment(symbol: str) -> dict:
    queries = EVENT_QUERIES.get(symbol, [symbol])
    headlines = []
    score = 0
    for query in queries[:3]:
        url = f"http://localhost:8080/search?q={quote_plus('site:polymarket.com ' + query)}&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("results", [])[:3]:
            title = str(item.get("title", ""))
            content = str(item.get("content", ""))
            text = f"{title} {content}".lower()
            for word in POSITIVE:
                if word in text:
                    score += 1
            for word in NEGATIVE:
                if word in text:
                    score -= 1
            headlines.append({"title": title, "url": item.get("url", "")})
    return {"symbol": symbol, "score": score, "headlines": headlines[:8]}
