# Kraken Futures Bot

Bot de trading **Kraken Futures** en **Python**, orienté **paper trading**, **backtests** et **comparaison de stratégies** sur des marchés comme **ETH/USD**.

## V3 : ce qui a été ajouté

- passage par défaut sur `PF_ETHUSD`
- comparaison de plusieurs stratégies classiques
- optimisation par famille de stratégie
- exécution d'une stratégie choisie via CLI
- garde-fous toujours actifs pour éviter le live accidentel

## Stratégies intégrées

### 1. `breakout`
Approche trend-following :
- cassure du plus haut / plus bas récent
- filtre de tendance EMA
- filtre de volatilité ATR
- stop ATR + take profit en ratio risque/rendement

### 2. `ema_trend`
Approche classique et connue :
- suivi de tendance par EMA rapide / EMA lente
- entrée dans le sens de la tendance
- stop ATR
- sortie sur stop, target ou retournement de croisement

### 3. `mean_reversion`
Approche de retour à la moyenne :
- base moyenne mobile
- écart statistique type Bollinger / z-score
- entrée quand le prix s'éloigne fortement de la moyenne
- sortie sur retour vers la moyenne

## Installation

```bash
cd kraken-futures-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Variables importantes :

- `KRAKEN_SYMBOL=PF_ETHUSD`
- `TIMEFRAME_MINUTES=15`
- `PAPER_TRADING=true`
- `LIVE_ENABLED=false`
- `STRATEGY_NAME=breakout`
- `RISK_PER_TRADE=0.01`
- `MAX_LEVERAGE=2`
- `BREAKOUT_LOOKBACK=20`
- `EMA_FAST=20`
- `EMA_SLOW=50`
- `ATR_PERIOD=14`
- `ATR_STOP_MULTIPLIER=1.5`
- `TAKE_PROFIT_RR=2.0`
- `MEAN_REVERSION_PERIOD=20`
- `BOLLINGER_STD=2.0`
- `ZSCORE_ENTRY=2.0`
- `ZSCORE_EXIT=0.5`
- `FEE_RATE=0.0005`

## Commandes utiles

### Tickers

```bash
python main.py tickers
```

### Backtest d'une stratégie précise

```bash
python main.py backtest --strategy breakout
python main.py backtest --strategy ema_trend
python main.py backtest --strategy mean_reversion
```

### Comparer les stratégies connues sur le même marché

```bash
python main.py compare
```

### Optimiser une famille de stratégie

```bash
python main.py optimize --strategy breakout --top 10
python main.py optimize --strategy ema_trend --top 10
python main.py optimize --strategy mean_reversion --top 10
```

### Exécuter une itération en paper trading

```bash
python main.py run --strategy breakout --once
```

## Important

Le but n'est pas de choisir la stratégie qui a juste le meilleur **win rate**, mais celle qui garde un bon compromis entre :
- profit factor
- drawdown
- fréquence de trade
- comportement cohérent selon les régimes de marché

## Live trading

Le live reste volontairement bloqué par défaut :

- `PAPER_TRADING=true`
- `LIVE_ENABLED=false`

Même avec les clés API, pas d'ordre réel tant que tu ne l'actives pas explicitement.

## Limites actuelles

- pas encore de websocket temps réel
- pas encore de persistance robuste des états et ordres
- pas encore de walk-forward analysis
- optimisation simple, pas encore de framework complet de recherche paramétrique

## Avertissement

Le futures crypto reste risqué.
Cette base doit servir à tester, comparer, éliminer les mauvaises idées rapidement et ne passer au live qu'après validation sérieuse.
