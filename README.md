# Kraken Futures Bot

Bot de trading **Kraken Futures** en **Python**, pensé pour être utilisé sérieusement :
**données de marché réelles**, **paper trading par défaut**, **gestion du risque stricte** et **backtests** avant tout passage en live.

## Ce que fait cette V2

- récupère de vraies bougies Kraken Futures via l'endpoint public charts
- récupère les tickers Kraken Futures via l'API publique
- exécute une stratégie initiale de type **breakout + filtre de tendance + filtre de volatilité**
- calcule la taille de position selon un risque fixe par trade
- supporte le **paper trading** par défaut
- prépare l'exécution réelle Kraken Futures avec garde-fou `LIVE_ENABLED=false` par défaut
- permet le **backtest** et une première **optimisation de paramètres**

## Architecture

- `src/kraken_bot/config.py` — configuration et mapping des timeframes
- `src/kraken_bot/models.py` — modèles métier
- `src/kraken_bot/indicators.py` — EMA / ATR
- `src/kraken_bot/strategy.py` — stratégie breakout trend following filtrée
- `src/kraken_bot/risk.py` — risk manager
- `src/kraken_bot/exchange.py` — client Kraken Futures public + base d'exécution live
- `src/kraken_bot/backtest.py` — backtest + mini optimisation
- `src/kraken_bot/bot.py` — boucle bot
- `main.py` — CLI

## Installation

```bash
cd kraken-futures-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Variables principales dans `.env` :

- `KRAKEN_SYMBOL=PF_XBTUSD`
- `TIMEFRAME_MINUTES=15`
- `PAPER_TRADING=true`
- `LIVE_ENABLED=false`
- `RISK_PER_TRADE=0.01`
- `MAX_LEVERAGE=2`
- `BREAKOUT_LOOKBACK=20`
- `EMA_FAST=20`
- `EMA_SLOW=50`
- `ATR_PERIOD=14`
- `ATR_STOP_MULTIPLIER=1.5`
- `TAKE_PROFIT_RR=2.0`
- `MIN_TREND_GAP_PCT=0.0015`
- `MIN_ATR_PCT=0.0025`
- `FEE_RATE=0.0005`

## Usage

### 1. Récupérer les tickers Kraken Futures

```bash
python main.py tickers
```

### 2. Backtest sur fichier CSV

Le CSV doit contenir : `timestamp,open,high,low,close,volume`

```bash
python main.py backtest --csv data/sample_ohlcv.csv
```

### 3. Backtest sur données Kraken Futures réelles

```bash
python main.py backtest
```

### 4. Comparer plusieurs variantes de paramètres

```bash
python main.py optimize
```

### 5. Exécuter une itération du bot en paper trading

```bash
python main.py run --once
```

### 6. Boucle continue

```bash
python main.py run
```

## Stratégie actuelle

La V2 utilise une logique volontairement simple et robuste :

- breakout du plus haut / plus bas sur `N` bougies
- filtre de tendance via croisement et écart EMA fast / EMA slow
- filtre de volatilité via ATR relatif
- stop loss basé sur ATR
- take profit basé sur un ratio risque/rendement
- fermeture anticipée si renversement de tendance

L'objectif n'est **pas** de maximiser artificiellement le taux de réussite, mais de viser une stratégie plus saine :

- espérance positive
- drawdown contenu
- comportement compréhensible
- réglages testables

## Live trading : important

Le code contient une base d'exécution réelle, mais elle est **bloquée par défaut**.

Pour éviter un accident :

- `PAPER_TRADING=true`
- `LIVE_ENABLED=false`

Même avec les clés API remplies, tant que `LIVE_ENABLED=false`, les ordres réels restent bloqués.

## Limites actuelles

Cette base est déjà utile, mais pas encore une prod institutionnelle. À ajouter ensuite :

- gestion robuste des erreurs API et retries
- persistance locale des positions / ordres / logs
- websocket temps réel
- confirmation précise des formats d'ordre live Kraken Futures selon ton compte
- dashboard de suivi
- backtests multi-périodes plus larges
- walk-forward analysis

## Avertissement

Le trading futures crypto est risqué.

Cette base doit servir à :
1. backtester,
2. paper trader,
3. observer,
4. seulement ensuite envisager le live avec petites tailles.

Ne passe pas en réel sans validation sérieuse des métriques, du drawdown et du comportement du bot sur plusieurs régimes de marché.
