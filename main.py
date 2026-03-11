from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from kraken_bot.backtest import Backtester, compare_known_strategies, optimize
from kraken_bot.bot import TradingBot
from kraken_bot.config import load_config
from kraken_bot.dashboard import build_dashboard, serve_dashboard
from kraken_bot.scanner import analyze_symbol, scan_market
from kraken_bot.strategy import config_with_strategy


def main() -> None:
    parser = argparse.ArgumentParser(description='Kraken Futures Bot')
    subparsers = parser.add_subparsers(dest='command', required=True)

    run_parser = subparsers.add_parser('run', help='Lancer le bot')
    run_parser.add_argument('--csv', help='Chemin CSV OHLCV pour simulation', default=None)
    run_parser.add_argument('--once', action='store_true', help='Exécuter une seule itération')
    run_parser.add_argument('--strategy', choices=['breakout', 'ema_trend', 'mean_reversion'], default=None)

    subparsers.add_parser('scan-run', help='Scanner et journaliser les opportunités')
    subparsers.add_parser('watch', help='Boucle auto-watch avec auto paper trading')
    subparsers.add_parser('serve', help='Lancer l\'interface web live')

    backtest_parser = subparsers.add_parser('backtest', help='Backtest sur CSV ou marché Kraken')
    backtest_parser.add_argument('--csv', help='Chemin CSV OHLCV')
    backtest_parser.add_argument('--strategy', choices=['breakout', 'ema_trend', 'mean_reversion'], default=None)

    optimize_parser = subparsers.add_parser('optimize', help='Comparer plusieurs paramètres')
    optimize_parser.add_argument('--csv', help='Chemin CSV OHLCV')
    optimize_parser.add_argument('--top', type=int, default=10, help='Nombre de résultats à afficher')
    optimize_parser.add_argument('--strategy', choices=['breakout', 'ema_trend', 'mean_reversion'], default=None)

    compare_parser = subparsers.add_parser('compare', help='Comparer les stratégies connues')
    compare_parser.add_argument('--csv', help='Chemin CSV OHLCV')

    analyze_parser = subparsers.add_parser('analyze', help='Analyser une paire avec plusieurs stratégies')
    analyze_parser.add_argument('--symbol', required=True)

    subparsers.add_parser('scan', help='Scanner plusieurs paires et classer les opportunités')
    subparsers.add_parser('tickers', help='Récupérer les tickers Kraken Futures')
    subparsers.add_parser('dashboard', help='Générer le dashboard HTML')

    args = parser.parse_args()
    config = load_config()
    if getattr(args, 'strategy', None):
        config = config_with_strategy(config, args.strategy)

    if args.command == 'backtest':
        if args.csv:
            import pandas as pd
            df = pd.read_csv(args.csv)
        else:
            from kraken_bot.exchange import KrakenFuturesClient
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        print(json.dumps(Backtester(config).run(df), indent=2, ensure_ascii=False)); return

    if args.command == 'optimize':
        if args.csv:
            import pandas as pd
            df = pd.read_csv(args.csv)
        else:
            from kraken_bot.exchange import KrakenFuturesClient
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        print(json.dumps(optimize(df, config)[: args.top], indent=2, ensure_ascii=False)); return

    if args.command == 'compare':
        if args.csv:
            import pandas as pd
            df = pd.read_csv(args.csv)
        else:
            from kraken_bot.exchange import KrakenFuturesClient
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        print(json.dumps(compare_known_strategies(df, config), indent=2, ensure_ascii=False)); return

    if args.command == 'analyze':
        print(json.dumps(analyze_symbol(config, args.symbol), indent=2, ensure_ascii=False)); return

    if args.command == 'scan':
        print(json.dumps(scan_market(config), indent=2, ensure_ascii=False)); return

    if args.command == 'scan-run':
        print(json.dumps(TradingBot(config).scan_and_log(), indent=2, ensure_ascii=False)); return

    if args.command == 'watch':
        bot = TradingBot(config)
        while True:
            print(json.dumps(bot.auto_watch_cycle(), ensure_ascii=False))
            import time; time.sleep(config.loop_seconds)

    if args.command == 'serve':
        serve_dashboard(os.path.join(ROOT, 'data'), config.dashboard_host, config.dashboard_port, config.dashboard_refresh_seconds); return

    if args.command == 'tickers':
        from kraken_bot.exchange import KrakenFuturesClient
        print(json.dumps(KrakenFuturesClient(config).fetch_tickers(), indent=2, ensure_ascii=False)); return

    if args.command == 'dashboard':
        path = build_dashboard(os.path.join(ROOT, 'dashboard.html'), config.dashboard_refresh_seconds)
        print(json.dumps({'dashboard': path}, ensure_ascii=False)); return

    if args.command == 'run':
        bot = TradingBot(config)
        if args.once:
            print(json.dumps(bot.step(csv_path=args.csv), indent=2, ensure_ascii=False))
        else:
            bot.run_forever(csv_path=args.csv)


if __name__ == '__main__':
    main()
