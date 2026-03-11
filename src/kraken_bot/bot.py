from __future__ import annotations

import time
from dataclasses import asdict

from .config import BotConfig
from .exchange import KrakenFuturesClient
from .models import Position
from .risk import RiskManager
from .strategy import build_strategy


class TradingBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.exchange = KrakenFuturesClient(config)
        self.strategy = build_strategy(config)
        self.risk = RiskManager(config)
        self.position: Position | None = None
        self.capital = config.starting_capital

    def step(self, csv_path: str | None = None) -> dict:
        df = self.exchange.fetch_ohlcv(self.config.symbol, csv_path=csv_path)
        signal = self.strategy.generate_signal(df, self.position)
        last = df.iloc[-1]
        price = float(last["close"])
        timestamp = str(last["timestamp"])

        result = {
            "timestamp": timestamp,
            "strategy": self.config.strategy_name,
            "symbol": self.config.symbol,
            "price": price,
            "signal": asdict(signal),
            "position": asdict(self.position) if self.position else None,
            "capital": self.capital,
            "action_result": None,
        }

        if signal.action in {"buy", "sell"} and self.position is None and signal.stop_loss and signal.take_profit:
            size = self.risk.position_size(self.capital, price, signal.stop_loss)
            if size > 0:
                order = self.exchange.place_order(
                    symbol=self.config.symbol,
                    side="long" if signal.action == "buy" else "short",
                    size=size,
                    price=price,
                    reason=signal.reason,
                )
                self.position = Position(
                    side="long" if signal.action == "buy" else "short",
                    entry_price=price,
                    size=size,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    opened_at=timestamp,
                )
                result["action_result"] = asdict(order)
                result["position"] = asdict(self.position)

        elif signal.action == "close" and self.position is not None:
            pnl = (price - self.position.entry_price) * self.position.size
            if self.position.side == "short":
                pnl *= -1
            self.capital += pnl
            close_result = self.exchange.close_position(self.config.symbol, self.position, price, signal.reason)
            result["action_result"] = close_result | {"pnl": pnl, "capital_after": self.capital}
            self.position = None
            result["position"] = None
            result["capital"] = self.capital

        return result

    def run_forever(self, csv_path: str | None = None) -> None:
        while True:
            result = self.step(csv_path=csv_path)
            print(result)
            time.sleep(self.config.loop_seconds)
