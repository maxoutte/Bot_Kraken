from __future__ import annotations

from .config import BotConfig


class RiskManager:
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def position_size(self, capital: float, entry_price: float, stop_price: float) -> float:
        risk_amount = capital * self.config.risk_per_trade
        per_unit_risk = abs(entry_price - stop_price)
        if per_unit_risk <= 0:
            return 0.0
        raw_size = risk_amount / per_unit_risk
        max_notional = capital * self.config.max_leverage
        max_size_by_leverage = max_notional / entry_price
        return max(0.0, min(raw_size, max_size_by_leverage))
