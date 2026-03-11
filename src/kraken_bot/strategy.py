from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .config import BotConfig
from .indicators import atr, ema, sma, stddev
from .models import Position, StrategyDefinition, TradeSignal


class BaseStrategy:
    name = "base"

    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.copy()

    def generate_signal(self, df: pd.DataFrame, position: Position | None) -> TradeSignal:
        raise NotImplementedError


class BreakoutTrendStrategy(BaseStrategy):
    name = "breakout"

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        enriched = df.copy()
        enriched["ema_fast"] = ema(enriched["close"], self.config.ema_fast)
        enriched["ema_slow"] = ema(enriched["close"], self.config.ema_slow)
        enriched["atr"] = atr(enriched, self.config.atr_period)
        enriched["highest_high"] = enriched["high"].rolling(self.config.breakout_lookback).max().shift(1)
        enriched["lowest_low"] = enriched["low"].rolling(self.config.breakout_lookback).min().shift(1)
        enriched["trend_gap_pct"] = (enriched["ema_fast"] - enriched["ema_slow"]) / enriched["close"]
        enriched["atr_pct"] = enriched["atr"] / enriched["close"]
        return enriched

    def generate_signal(self, df: pd.DataFrame, position: Position | None) -> TradeSignal:
        row = self.enrich(df).iloc[-1]
        close = float(row["close"])
        atr_value = float(row["atr"])

        if pd.isna(row["highest_high"]) or pd.isna(atr_value):
            return TradeSignal(action="hold", reason="Pas assez d'historique")

        trend_gap_pct = float(row["trend_gap_pct"])
        atr_pct = float(row["atr_pct"])
        trend_up = trend_gap_pct > self.config.min_trend_gap_pct
        trend_down = trend_gap_pct < -self.config.min_trend_gap_pct
        breakout_up = close > row["highest_high"]
        breakout_down = close < row["lowest_low"]
        volatility_ok = atr_pct >= self.config.min_atr_pct

        if position is None:
            if volatility_ok and trend_up and breakout_up:
                stop = close - atr_value * self.config.atr_stop_multiplier
                target = close + (close - stop) * self.config.take_profit_rr
                return TradeSignal("buy", "Breakout haussier confirmé", side="long", stop_loss=stop, take_profit=target)
            if volatility_ok and trend_down and breakout_down:
                stop = close + atr_value * self.config.atr_stop_multiplier
                target = close - (stop - close) * self.config.take_profit_rr
                return TradeSignal("sell", "Breakout baissier confirmé", side="short", stop_loss=stop, take_profit=target)
            if not volatility_ok:
                return TradeSignal(action="hold", reason="Volatilité insuffisante")
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


class EmaTrendStrategy(BaseStrategy):
    name = "ema_trend"

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        enriched = df.copy()
        enriched["ema_fast"] = ema(enriched["close"], self.config.ema_fast)
        enriched["ema_slow"] = ema(enriched["close"], self.config.ema_slow)
        enriched["atr"] = atr(enriched, self.config.atr_period)
        enriched["atr_pct"] = enriched["atr"] / enriched["close"]
        enriched["trend_gap_pct"] = (enriched["ema_fast"] - enriched["ema_slow"]) / enriched["close"]
        return enriched

    def generate_signal(self, df: pd.DataFrame, position: Position | None) -> TradeSignal:
        row = self.enrich(df).iloc[-1]
        if pd.isna(row["atr"]):
            return TradeSignal(action="hold", reason="Pas assez d'historique")
        close = float(row["close"])
        atr_value = float(row["atr"])
        trend_gap_pct = float(row["trend_gap_pct"])
        atr_pct = float(row["atr_pct"])
        trend_up = trend_gap_pct > self.config.min_trend_gap_pct
        trend_down = trend_gap_pct < -self.config.min_trend_gap_pct
        volatility_ok = atr_pct >= self.config.min_atr_pct

        if position is None:
            if volatility_ok and trend_up:
                stop = close - atr_value * self.config.atr_stop_multiplier
                target = close + (close - stop) * self.config.take_profit_rr
                return TradeSignal("buy", "Trend EMA haussier", side="long", stop_loss=stop, take_profit=target)
            if volatility_ok and trend_down:
                stop = close + atr_value * self.config.atr_stop_multiplier
                target = close - (stop - close) * self.config.take_profit_rr
                return TradeSignal("sell", "Trend EMA baissier", side="short", stop_loss=stop, take_profit=target)
            return TradeSignal(action="hold", reason="Pas de tendance exploitable")

        if position.side == "long" and trend_down:
            return TradeSignal(action="close", reason="Croisement baissier")
        if position.side == "short" and trend_up:
            return TradeSignal(action="close", reason="Croisement haussier")
        if position.side == "long":
            if close <= position.stop_loss:
                return TradeSignal(action="close", reason="Stop long touché")
            if close >= position.take_profit:
                return TradeSignal(action="close", reason="Take profit long touché")
        else:
            if close >= position.stop_loss:
                return TradeSignal(action="close", reason="Stop short touché")
            if close <= position.take_profit:
                return TradeSignal(action="close", reason="Take profit short touché")
        return TradeSignal(action="hold", reason="Position conservée")


class MeanReversionStrategy(BaseStrategy):
    name = "mean_reversion"

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        enriched = df.copy()
        enriched["basis"] = sma(enriched["close"], self.config.mean_reversion_period)
        enriched["std"] = stddev(enriched["close"], self.config.mean_reversion_period)
        enriched["upper"] = enriched["basis"] + self.config.bollinger_std * enriched["std"]
        enriched["lower"] = enriched["basis"] - self.config.bollinger_std * enriched["std"]
        enriched["zscore"] = (enriched["close"] - enriched["basis"]) / enriched["std"]
        enriched["atr"] = atr(enriched, self.config.atr_period)
        return enriched

    def generate_signal(self, df: pd.DataFrame, position: Position | None) -> TradeSignal:
        row = self.enrich(df).iloc[-1]
        if pd.isna(row["zscore"]) or pd.isna(row["atr"]):
            return TradeSignal(action="hold", reason="Pas assez d'historique")
        close = float(row["close"])
        basis = float(row["basis"])
        zscore = float(row["zscore"])
        atr_value = float(row["atr"])

        if position is None:
            if zscore <= -self.config.zscore_entry:
                stop = close - atr_value * self.config.atr_stop_multiplier
                target = basis
                return TradeSignal("buy", "Excès baissier vers moyenne", side="long", stop_loss=stop, take_profit=target)
            if zscore >= self.config.zscore_entry:
                stop = close + atr_value * self.config.atr_stop_multiplier
                target = basis
                return TradeSignal("sell", "Excès haussier vers moyenne", side="short", stop_loss=stop, take_profit=target)
            return TradeSignal(action="hold", reason="Pas d'excès statistique")

        if position.side == "long":
            if close <= position.stop_loss:
                return TradeSignal(action="close", reason="Stop long touché")
            if zscore >= -self.config.zscore_exit or close >= position.take_profit:
                return TradeSignal(action="close", reason="Retour vers la moyenne")
        else:
            if close >= position.stop_loss:
                return TradeSignal(action="close", reason="Stop short touché")
            if zscore <= self.config.zscore_exit or close <= position.take_profit:
                return TradeSignal(action="close", reason="Retour vers la moyenne")
        return TradeSignal(action="hold", reason="Position conservée")


def build_strategy(config: BotConfig) -> BaseStrategy:
    strategies = {
        "breakout": BreakoutTrendStrategy,
        "ema_trend": EmaTrendStrategy,
        "mean_reversion": MeanReversionStrategy,
    }
    if config.strategy_name not in strategies:
        raise ValueError(f"Stratégie inconnue: {config.strategy_name}")
    return strategies[config.strategy_name](config)


def known_strategies(config: BotConfig) -> list[StrategyDefinition]:
    return [
        StrategyDefinition("breakout", {"breakout_lookback": config.breakout_lookback}),
        StrategyDefinition("ema_trend", {"ema_fast": config.ema_fast, "ema_slow": config.ema_slow}),
        StrategyDefinition("mean_reversion", {"mean_reversion_period": config.mean_reversion_period, "zscore_entry": config.zscore_entry}),
    ]


def config_with_strategy(config: BotConfig, strategy_name: str, **overrides: object) -> BotConfig:
    return replace(config, strategy_name=strategy_name, **overrides)
