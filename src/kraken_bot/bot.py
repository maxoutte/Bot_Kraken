from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

from .config import BotConfig
from .exchange import KrakenFuturesClient
from .models import Position
from .risk import RiskManager
from .scanner import scan_market
from .storage import Storage
from .strategy import build_strategy, config_with_strategy


class TradingBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.exchange = KrakenFuturesClient(config)
        self.strategy = build_strategy(config)
        self.risk = RiskManager(config)
        self.position: Position | None = None
        self.capital = config.starting_capital
        self.storage = Storage(str(Path(__file__).resolve().parents[2] / 'data'))
        self.active_symbol = config.symbol
        self.active_strategy = config.strategy_name

    def step(self, csv_path: str | None = None) -> dict:
        local_config = config_with_strategy(self.config, self.active_strategy)
        local_config.symbol = self.active_symbol
        strategy = build_strategy(local_config)
        df = self.exchange.fetch_ohlcv(self.active_symbol, csv_path=csv_path)
        signal = strategy.generate_signal(df, self.position)
        last = df.iloc[-1]
        price = float(last['close'])
        timestamp = str(last['timestamp'])
        result = {
            'timestamp': timestamp,
            'strategy': self.active_strategy,
            'symbol': self.active_symbol,
            'price': price,
            'signal': asdict(signal),
            'position': asdict(self.position) if self.position else None,
            'capital': self.capital,
            'action_result': None,
        }
        if signal.action in {'buy', 'sell'} and self.position is None and signal.stop_loss and signal.take_profit:
            size = self.risk.position_size(self.capital, price, signal.stop_loss)
            if size > 0:
                order = self.exchange.place_order(self.active_symbol, 'long' if signal.action == 'buy' else 'short', size, price, signal.reason)
                self.position = Position(side='long' if signal.action == 'buy' else 'short', entry_price=price, size=size, stop_loss=signal.stop_loss, take_profit=signal.take_profit, opened_at=timestamp)
                result['action_result'] = asdict(order)
                result['position'] = asdict(self.position)
                self.storage.append_trade({'timestamp': timestamp, 'event': 'open', 'symbol': self.active_symbol, 'strategy': self.active_strategy, 'side': self.position.side, 'entry_price': price, 'size': size, 'stop_loss': signal.stop_loss, 'take_profit': signal.take_profit, 'capital': self.capital, 'reason': signal.reason})
        elif signal.action == 'close' and self.position is not None:
            pnl = (price - self.position.entry_price) * self.position.size
            if self.position.side == 'short':
                pnl *= -1
            self.capital += pnl
            close_result = self.exchange.close_position(self.active_symbol, self.position, price, signal.reason)
            result['action_result'] = close_result | {'pnl': pnl, 'capital_after': self.capital}
            self.storage.append_trade({'timestamp': timestamp, 'event': 'close', 'symbol': self.active_symbol, 'strategy': self.active_strategy, 'side': self.position.side, 'entry_price': self.position.entry_price, 'exit_price': price, 'size': self.position.size, 'pnl': pnl, 'capital': self.capital, 'reason': signal.reason})
            self.position = None
            result['position'] = None
            result['capital'] = self.capital
        self.storage.write_status({'timestamp': timestamp, 'symbol': self.active_symbol, 'strategy': self.active_strategy, 'position': asdict(self.position) if self.position else None, 'capital': self.capital, 'last_result': result})
        return result

    def scan_and_log(self) -> list[dict]:
        result = scan_market(self.config)
        self.storage.append_scan({'timestamp': int(time.time()), 'results': result})
        self.storage.write_status({'timestamp': int(time.time()), 'capital': self.capital, 'position': asdict(self.position) if self.position else None, 'best_setup': result[0] if result else None, 'symbol': self.active_symbol, 'strategy': self.active_strategy})
        return result

    def auto_watch_cycle(self) -> dict:
        opportunities = self.scan_and_log()
        best = opportunities[0] if opportunities else None
        action = 'watch'
        if self.position is None and best:
            signal = best.get('signal', {})
            if self.config.auto_trade_enabled and best.get('score', 0) >= self.config.auto_trade_score_threshold and signal.get('action') in {'buy', 'sell'}:
                self.active_symbol = best['symbol']
                self.active_strategy = best['strategy']
                trade_result = self.step()
                action = 'paper_trade_opened' if trade_result.get('action_result') else 'watch'
                return {'action': action, 'best_setup': best, 'trade_result': trade_result}
        elif self.position is not None:
            trade_result = self.step()
            action = 'position_managed'
            return {'action': action, 'best_setup': best, 'trade_result': trade_result}
        return {'action': action, 'best_setup': best}

    def run_forever(self, csv_path: str | None = None) -> None:
        while True:
            if self.config.auto_trade_enabled:
                print(self.auto_watch_cycle())
            else:
                print(self.step(csv_path=csv_path))
            time.sleep(self.config.loop_seconds)
