from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from .config import BotConfig
from .models import Position
from .risk import RiskManager
from .strategy import BreakoutTrendStrategy


class Backtester:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.strategy = BreakoutTrendStrategy(config)
        self.risk = RiskManager(config)

    def run(self, df: pd.DataFrame) -> dict:
        capital = self.config.starting_capital
        peak_capital = capital
        max_drawdown = 0.0
        wins = 0
        losses = 0
        trades: list[dict] = []
        position: Position | None = None

        enriched = self.strategy.enrich(df)
        for i in range(len(enriched)):
            current = enriched.iloc[: i + 1]
            signal = self.strategy.generate_signal(current, position)
            row = current.iloc[-1]
            price = float(row["close"])
            timestamp = str(row["timestamp"])

            if signal.action in {"buy", "sell"} and position is None and signal.stop_loss and signal.take_profit:
                size = self.risk.position_size(capital, price, signal.stop_loss)
                if size > 0:
                    position = Position(
                        side="long" if signal.action == "buy" else "short",
                        entry_price=price,
                        size=size,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit,
                        opened_at=timestamp,
                    )
            elif signal.action == "close" and position is not None:
                pnl = (price - position.entry_price) * position.size
                if position.side == "short":
                    pnl *= -1
                capital += pnl
                peak_capital = max(peak_capital, capital)
                drawdown = (peak_capital - capital) / peak_capital if peak_capital else 0.0
                max_drawdown = max(max_drawdown, drawdown)
                wins += 1 if pnl > 0 else 0
                losses += 1 if pnl <= 0 else 0
                trades.append(
                    {
                        "opened_at": position.opened_at,
                        "closed_at": timestamp,
                        "side": position.side,
                        "entry_price": position.entry_price,
                        "exit_price": price,
                        "size": position.size,
                        "pnl": pnl,
                        "reason": signal.reason,
                    }
                )
                position = None

        total_trades = wins + losses
        win_rate = wins / total_trades if total_trades else 0.0
        return {
            "starting_capital": self.config.starting_capital,
            "ending_capital": capital,
            "net_pnl": capital - self.config.starting_capital,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "open_position": asdict(position) if position else None,
            "trades": trades,
        }
