from __future__ import annotations

from .backtest import Backtester, compare_known_strategies, optimize
from .bot import TradingBot
from .config import load_config
from .exchange import KrakenFuturesClient
from .scanner import analyze_symbol, scan_market
from .strategy import config_with_strategy


def run_action(action: str, symbol: str | None = None, strategy: str | None = None) -> object:
    config = load_config()
    if symbol:
        config.symbol = symbol
    if strategy:
        config = config_with_strategy(config, strategy)
        if symbol:
            config.symbol = symbol

    if action == 'tickers':
        return KrakenFuturesClient(config).fetch_tickers()
    if action == 'scan':
        return scan_market(config)
    if action == 'scan-run':
        return TradingBot(config).scan_and_log()
    if action == 'analyze':
        return analyze_symbol(config, config.symbol)
    if action == 'compare':
        df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        return compare_known_strategies(df, config)
    if action == 'backtest':
        df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        return Backtester(config).run(df)
    if action == 'optimize':
        df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        return optimize(df, config)[:10]
    if action == 'run-once':
        return TradingBot(config).step()
    if action == 'watch-cycle':
        return TradingBot(config).auto_watch_cycle()
    raise ValueError(f'Action inconnue: {action}')
