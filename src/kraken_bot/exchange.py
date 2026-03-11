from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import asdict
from urllib.parse import urlencode

import pandas as pd
import requests

from .config import BotConfig, timeframe_code
from .models import OrderResult, Position


class KrakenFuturesClient:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "kraken-futures-bot/1.0"})

    def fetch_ohlcv(self, symbol: str, csv_path: str | None = None, lookback: int = 250) -> pd.DataFrame:
        if csv_path:
            return self._normalize_df(pd.read_csv(csv_path))

        interval = timeframe_code(self.config.timeframe_minutes)
        url = f"{self.config.charts_url}/{symbol}/{interval}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        candles = payload.get("candles", [])[-lookback:]
        if not candles:
            raise RuntimeError(f"Aucune bougie reçue depuis {url}")
        df = pd.DataFrame(candles)
        df = df.rename(columns={"time": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
        return self._normalize_df(df)

    def fetch_tickers(self) -> dict:
        response = self.session.get(f"{self.config.base_url}/tickers", timeout=15)
        response.raise_for_status()
        return response.json()

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")
        normalized = df[required].copy()
        for col in ["open", "high", "low", "close", "volume"]:
            normalized[col] = normalized[col].astype(float)
        return normalized

    def _auth_headers(self, endpoint_path: str, payload: dict) -> dict:
        nonce = str(int(time.time() * 1000))
        post_data = urlencode(payload)
        message = (post_data + nonce + endpoint_path).encode()
        sha256_hash = hashlib.sha256(message).digest()
        signature = hmac.new(base64.b64decode(self.config.api_secret), sha256_hash, hashlib.sha512)
        return {
            "APIKey": self.config.api_key,
            "Authent": base64.b64encode(signature.digest()).decode(),
            "Nonce": nonce,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

    def _live_order(self, endpoint_path: str, payload: dict) -> dict:
        if not self.config.live_enabled:
            raise RuntimeError("LIVE_ENABLED=false : exécution réelle bloquée")
        if not self.config.api_key or not self.config.api_secret:
            raise RuntimeError("Clés API Kraken Futures manquantes")
        headers = self._auth_headers(endpoint_path, payload)
        response = self.session.post(f"{self.config.base_url}{endpoint_path}", data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def place_order(self, symbol: str, side: str, size: float, price: float, reason: str) -> OrderResult:
        mode = "paper" if self.config.paper_trading or not self.config.live_enabled else "live"
        if mode == "live":
            direction = "buy" if side == "long" else "sell"
            payload = {
                "orderType": "ioc",
                "symbol": symbol,
                "side": direction,
                "size": round(size, 8),
            }
            self._live_order("/sendorder", payload)
        return OrderResult(
            accepted=True,
            mode=mode,
            symbol=symbol,
            side=side,  # type: ignore[arg-type]
            size=size,
            price=price,
            reason=reason,
        )

    def close_position(self, symbol: str, position: Position, price: float, reason: str) -> dict:
        mode = "paper" if self.config.paper_trading or not self.config.live_enabled else "live"
        if mode == "live":
            direction = "sell" if position.side == "long" else "buy"
            payload = {
                "orderType": "ioc",
                "symbol": symbol,
                "side": direction,
                "size": round(position.size, 8),
            }
            self._live_order("/sendorder", payload)
        return {
            "symbol": symbol,
            "closed": True,
            "mode": mode,
            "side": position.side,
            "size": position.size,
            "price": price,
            "reason": reason,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def serialize_position(position: Position | None) -> dict | None:
        return asdict(position) if position else None
