# Kraken Futures Bot

Bot de trading Kraken Futures en Python, conçu pour démarrer en mode simulation avant passage en réel.

## Principes

- **Simulation d'abord** : aucune exécution réelle par défaut.
- **Architecture modulaire** : stratégie, risk management, exchange client, backtest.
- **Config simple** via variables d'environnement.
- **Stratégie initiale** : breakout de volatilité avec filtre de tendance.

## Structure

- `src/kraken_bot/config.py` — chargement de configuration
- `src/kraken_bot/models.py` — modèles de données
- `src/kraken_bot/indicators.py` — indicateurs techniques
- `src/kraken_bot/strategy.py` — stratégie V1
- `src/kraken_bot/risk.py` — sizing et garde-fous
- `src/kraken_bot/exchange.py` — interface exchange + mock Kraken
- `src/kraken_bot/backtest.py` — moteur de backtest simple
- `src/kraken_bot/bot.py` — orchestration de boucle bot
- `main.py` — point d'entrée CLI

## Installation

```bash
cd kraken-futures-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copier `.env.example` vers `.env` puis ajuster.

Variables principales :

- `KRAKEN_SYMBOL=PF_XBTUSD`
- `TIMEFRAME_MINUTES=15`
- `PAPER_TRADING=true`
- `RISK_PER_TRADE=0.01`
- `MAX_LEVERAGE=2`
- `BREAKOUT_LOOKBACK=20`
- `ATR_PERIOD=14`
- `ATR_STOP_MULTIPLIER=1.5`
- `TAKE_PROFIT_RR=2.0`

## Usage

### Backtest sur CSV

Le CSV doit contenir au minimum : `timestamp,open,high,low,close,volume`

```bash
python main.py backtest --csv data/sample_ohlcv.csv
```

### Run bot en simulation

```bash
python main.py run
```

## Roadmap immédiate

1. brancher l'API Kraken Futures réelle
2. ajouter persistance positions / ordres
3. brancher WebSocket temps réel
4. ajouter dashboard / reporting
5. comparer plusieurs stratégies sur historique

## Avertissement

Ce code est une base technique. Il faut **backtester sérieusement**, faire du **paper trading**, puis valider les risques avant tout passage en réel.
