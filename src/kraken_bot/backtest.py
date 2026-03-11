from __future__ import annotations

from dataclasses import asdict
from itertools import product

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
        gross_profit = 0.0
        gross_loss = 0.0
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
                fees = ((position.entry_price * position.size) + (price * position.size)) * self.config.fee_rate
                pnl_after_fees = pnl - fees
                capital += pnl_after_fees
                peak_capital = max(peak_capital, capital)
                drawdown = (peak_capital - capital) / peak_capital if peak_capital else 0.0
                max_drawdown = max(max_drawdown, drawdown)
                if pnl_after_fees > 0:
                    wins += 1
                    gross_profit += pnl_after_fees
                else:
                    losses += 1
                    gross_loss += abs(pnl_after_fees)
                trades.append(
                    {
                        "opened_at": position.opened_at,
                        "closed_at": timestamp,
                        "side": position.side,
                        "entry_price": position.entry_price,
                        "exit_price": price,
                        "size": position.size,
                        "gross_pnl": pnl,
                        "fees": fees,
                        "net_pnl": pnl_after_fees,
                        "reason": signal.reason,
                    }
                )
                position = None

        total_trades = wins + losses
        win_rate = wins / total_trades if total_trades else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss else None
        expectancy = (capital - self.config.starting_capital) / total_trades if total_trades else 0.0
        return {
            "starting_capital": self.config.starting_capital,
            "ending_capital": capital,
            "net_pnl": capital - self.config.starting_capital,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "expectancy_per_trade": expectancy,
            "max_drawdown": max_drawdown,
            "open_position": asdict(position) if position else None,
            "trades": trades,
        }


def optimize(df: pd.DataFrame, config: BotConfig) -> list[dict]:
    results: list[dict] = []
    breakout_values = [10, 20, 30]
    atr_stop_values = [1.2, 1.5, 2.0]
    rr_values = [1.5, 2.0, 2.5]

    for breakout, atr_stop, rr in product(breakout_values, atr_stop_values, rr_values):
        local = BotConfig(**{**config.__dict__, "breakout_lookback": breakout, "atr_stop_multiplier": atr_stop, "take_profit_rr": rr})
        stats = Backtester(local).run(df)
        results.append({
            "breakout_lookback": breakout,
            "atr_stop_multiplier": atr_stop,
            "take_profit_rr": rr,
            "net_pnl": stats["net_pnl"],
            "win_rate": stats["win_rate"],
            "profit_factor": stats["profit_factor"],
            "max_drawdown": stats["max_drawdown"],
            "total_trades": stats["total_trades"],
        })

    return sorted(
        results,
        key=lambda item: (item["net_pnl"], item["profit_factor"] or 0.0, -item["max_drawdown"]),
        reverse=True,
    )
