from __future__ import annotations

import pandas as pd

from .config import BotConfig
from .indicators import atr, ema
from .models import Position, TradeSignal


class BreakoutTrendStrategy:
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        enriched = df.copy()
        enriched["ema_fast"] = ema(enriched["close"], self.config.ema_fast)
        enriched["ema_slow"] = ema(enriched["close"], self.config.ema_slow)
        enriched["atr"] = atr(enriched, self.config.atr_period)
        enriched["highest_high"] = enriched["high"].rolling(self.config.breakout_lookback).max().shift(1)
        enriched["lowest_low"] = enriched["low"].rolling(self.config.breakout_lookback).min().shift(1)
        return enriched

    def generate_signal(self, df: pd.DataFrame, position: Position | None) -> TradeSignal:
        row = self.enrich(df).iloc[-1]
        close = float(row["close"])
        atr_value = float(row["atr"])

        if pd.isna(row["highest_high"]) or pd.isna(atr_value):
            return TradeSignal(action="hold", reason="Pas assez d'historique")

        trend_up = row["ema_fast"] > row["ema_slow"]
        trend_down = row["ema_fast"] < row["ema_slow"]
        breakout_up = close > row["highest_high"]
        breakout_down = close < row["lowest_low"]

        if position is None:
            if trend_up and breakout_up:
                stop = close - atr_value * self.config.atr_stop_multiplier
                target = close + (close - stop) * self.config.take_profit_rr
                return TradeSignal("buy", "Breakout haussier confirmé", side="long", stop_loss=stop, take_profit=target)
            if trend_down and breakout_down:
                stop = close + atr_value * self.config.atr_stop_multiplier
                target = close - (stop - close) * self.config.take_profit_rr
                return TradeSignal("sell", "Breakout baissier confirmé", side="short", stop_loss=stop, take_profit=target)
            return TradeSignal(action="hold", reason="Aucun setup valide")

        if position.side == "long":
            if close <= position.stop_loss:
                return TradeSignal(action="close", reason="Stop long touché")
            if close >= position.take_profit:
                return TradeSignal(action="close", reason="Take profit long touché")
            if trend_down:
                return TradeSignal(action="close", reason="Renversement de tendance")
        else:
            if close >= position.stop_loss:
                return TradeSignal(action="close", reason="Stop short touché")
            if close <= position.take_profit:
                return TradeSignal(action="close", reason="Take profit short touché")
            if trend_up:
                return TradeSignal(action="close", reason="Renversement de tendance")

        return TradeSignal(action="hold", reason="Position conservée")
