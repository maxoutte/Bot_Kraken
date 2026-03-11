from __future__ import annotations

import hashlib
import hmac
import base64
import time
from dataclasses import asdict

import pandas as pd
import requests

from .config import BotConfig
from .models import OrderResult, Position


class KrakenFuturesClient:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.session = requests.Session()

    def fetch_ohlcv(self, symbol: str, csv_path: str | None = None) -> pd.DataFrame:
        if csv_path:
            return pd.read_csv(csv_path)
        raise NotImplementedError("Brancher ici le fetch OHLCV Kraken Futures réel")

    def _auth_headers(self, endpoint_path: str, post_data: str, nonce: str) -> dict:
        sha256_hash = hashlib.sha256((post_data + nonce + endpoint_path).encode()).digest()
        signature = hmac.new(base64.b64decode(self.config.api_secret), sha256_hash, hashlib.sha512)
        return {
            "APIKey": self.config.api_key,
            "Authent": base64.b64encode(signature.digest()).decode(),
            "Nonce": nonce,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

    def place_order(self, symbol: str, side: str, size: float, price: float, reason: str) -> OrderResult:
        mode = "paper" if self.config.paper_trading else "live"
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
        return {
            "symbol": symbol,
            "closed": True,
            "mode": "paper" if self.config.paper_trading else "live",
            "side": position.side,
            "size": position.size,
            "price": price,
            "reason": reason,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def serialize_position(position: Position | None) -> dict | None:
        return asdict(position) if position else None
