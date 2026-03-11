from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Side = Literal["long", "short"]
SignalType = Literal["buy", "sell", "close", "hold"]


@dataclass
class MarketCandle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TradeSignal:
    action: SignalType
    reason: str
    side: Optional[Side] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class Position:
    side: Side
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    opened_at: str


@dataclass
class OrderResult:
    accepted: bool
    mode: str
    symbol: str
    side: Side
    size: float
    price: float
    reason: str


@dataclass
class StrategyDefinition:
    name: str
    params: dict
