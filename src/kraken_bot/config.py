from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class BotConfig:
    api_key: str
    api_secret: str
    base_url: str
    charts_url: str
    symbol: str
    timeframe_minutes: int
    paper_trading: bool
    live_enabled: bool
    risk_per_trade: float
    max_leverage: float
    max_open_positions: int
    breakout_lookback: int
    ema_fast: int
    ema_slow: int
    atr_period: int
    atr_stop_multiplier: float
    take_profit_rr: float
    min_trend_gap_pct: float
    min_atr_pct: float
    loop_seconds: int
    starting_capital: float
    fee_rate: float


TIMEFRAME_MAP = {
    1: "1m",
    5: "5m",
    15: "15m",
    30: "30m",
    60: "1h",
    240: "4h",
    1440: "1d",
}


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


def load_config() -> BotConfig:
    load_dotenv()
    return BotConfig(
        api_key=os.getenv("KRAKEN_API_KEY", ""),
        api_secret=os.getenv("KRAKEN_API_SECRET", ""),
        base_url=os.getenv("KRAKEN_BASE_URL", "https://futures.kraken.com/derivatives/api/v3"),
        charts_url=os.getenv("KRAKEN_CHARTS_URL", "https://futures.kraken.com/api/charts/v1/trade"),
        symbol=os.getenv("KRAKEN_SYMBOL", "PF_XBTUSD"),
        timeframe_minutes=int(os.getenv("TIMEFRAME_MINUTES", "15")),
        paper_trading=_get_bool("PAPER_TRADING", True),
        live_enabled=_get_bool("LIVE_ENABLED", False),
        risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.01")),
        max_leverage=float(os.getenv("MAX_LEVERAGE", "2")),
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "1")),
        breakout_lookback=int(os.getenv("BREAKOUT_LOOKBACK", "20")),
        ema_fast=int(os.getenv("EMA_FAST", "20")),
        ema_slow=int(os.getenv("EMA_SLOW", "50")),
        atr_period=int(os.getenv("ATR_PERIOD", "14")),
        atr_stop_multiplier=float(os.getenv("ATR_STOP_MULTIPLIER", "1.5")),
        take_profit_rr=float(os.getenv("TAKE_PROFIT_RR", "2.0")),
        min_trend_gap_pct=float(os.getenv("MIN_TREND_GAP_PCT", "0.0015")),
        min_atr_pct=float(os.getenv("MIN_ATR_PCT", "0.0025")),
        loop_seconds=int(os.getenv("LOOP_SECONDS", "60")),
        starting_capital=float(os.getenv("STARTING_CAPITAL", "10000")),
        fee_rate=float(os.getenv("FEE_RATE", "0.0005")),
    )


def timeframe_code(minutes: int) -> str:
    if minutes not in TIMEFRAME_MAP:
        raise ValueError(f"Timeframe non supporté: {minutes} minutes")
    return TIMEFRAME_MAP[minutes]
