from __future__ import annotations

from dataclasses import asdict

from .backtest import Backtester
from .config import BotConfig
from .exchange import KrakenFuturesClient
from .news import fetch_news
from .strategy import build_strategy, config_with_strategy


def analyze_symbol(config: BotConfig, symbol: str) -> list[dict]:
    client = KrakenFuturesClient(config)
    df = client.fetch_ohlcv(symbol)
    results: list[dict] = []
    for strategy_name in ["breakout", "ema_trend", "mean_reversion"]:
        local = config_with_strategy(config, strategy_name)
        local.symbol = symbol
        strategy = build_strategy(local)
        signal = strategy.generate_signal(df, None)
        backtest = Backtester(local).run(df)
        news = fetch_news(symbol, config.news_query_terms) if config.news_enabled else {"score": 0, "headlines": []}
        regime_score = _regime_score(signal.action, signal.reason)
        total_score = (
            (backtest["profit_factor"] or 0.0) * 2.0
            + backtest["win_rate"] * 2.0
            + max(0.0, backtest["net_pnl"] / 200.0)
            - backtest["max_drawdown"] * 5.0
            + regime_score
            + news["score"] * 0.25
        )
        results.append(
            {
                "symbol": symbol,
                "strategy": strategy_name,
                "signal": asdict(signal),
                "backtest_summary": {
                    "net_pnl": backtest["net_pnl"],
                    "win_rate": backtest["win_rate"],
                    "profit_factor": backtest["profit_factor"],
                    "max_drawdown": backtest["max_drawdown"],
                    "total_trades": backtest["total_trades"],
                },
                "news": news,
                "score": total_score,
            }
        )
    return sorted(results, key=lambda item: item["score"], reverse=True)


def scan_market(config: BotConfig) -> list[dict]:
    market: list[dict] = []
    for symbol in config.symbols:
        try:
            best = analyze_symbol(config, symbol)[0]
            market.append(best)
        except Exception as exc:
            market.append({"symbol": symbol, "error": str(exc), "score": -999})
    return sorted(market, key=lambda item: item.get("score", -999), reverse=True)


def _regime_score(action: str, reason: str) -> float:
    if action in {"buy", "sell"}:
        return 1.0
    if "volatilité insuffisante" in reason.lower():
        return -0.5
    return 0.0
