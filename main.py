from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from kraken_bot.backtest import Backtester, optimize
from kraken_bot.bot import TradingBot
from kraken_bot.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Kraken Futures Bot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Lancer le bot")
    run_parser.add_argument("--csv", help="Chemin CSV OHLCV pour simulation", default=None)
    run_parser.add_argument("--once", action="store_true", help="Exécuter une seule itération")

    backtest_parser = subparsers.add_parser("backtest", help="Backtest sur CSV ou marché Kraken")
    backtest_parser.add_argument("--csv", help="Chemin CSV OHLCV")

    optimize_parser = subparsers.add_parser("optimize", help="Comparer plusieurs paramètres")
    optimize_parser.add_argument("--csv", help="Chemin CSV OHLCV")
    optimize_parser.add_argument("--top", type=int, default=10, help="Nombre de résultats à afficher")

    tickers_parser = subparsers.add_parser("tickers", help="Récupérer les tickers Kraken Futures")

    args = parser.parse_args()
    config = load_config()

    if args.command == "backtest":
        if args.csv:
            import pandas as pd
            df = pd.read_csv(args.csv)
        else:
            from kraken_bot.exchange import KrakenFuturesClient
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        result = Backtester(config).run(df)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.command == "optimize":
        if args.csv:
            import pandas as pd
            df = pd.read_csv(args.csv)
        else:
            from kraken_bot.exchange import KrakenFuturesClient
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
        result = optimize(df, config)[: args.top]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.command == "tickers":
        from kraken_bot.exchange import KrakenFuturesClient
        result = KrakenFuturesClient(config).fetch_tickers()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.command == "run":
        bot = TradingBot(config)
        if args.once:
            print(json.dumps(bot.step(csv_path=args.csv), indent=2, ensure_ascii=False))
        else:
            bot.run_forever(csv_path=args.csv)


if __name__ == "__main__":
    main()
