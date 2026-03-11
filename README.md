# Kraken Futures Bot

Bot de trading **Kraken Futures** en **Python**, orienté **paper trading**, **backtests**, **scan multi-paires** et **filtre news**.

## V4 : philosophie

Le bot n'est plus bloqué sur une seule paire.
Il peut maintenant :
- scanner plusieurs contrats futures Kraken
- tester plusieurs stratégies connues
- classer les opportunités
- utiliser un filtre news/sentiment léger pour éviter de trader totalement à l'aveugle

## Stratégies intégrées

- `breakout` — cassure + filtre de tendance
- `ema_trend` — suivi de tendance EMA
- `mean_reversion` — retour à la moyenne via z-score / Bollinger

## Univers de marché

Par défaut :
- `PF_XBTUSD`
- `PF_ETHUSD`
- `PF_SOLUSD`
- `PF_BNBUSD`
- `PF_LINKUSD`

Modifiable via `KRAKEN_SYMBOLS` dans `.env`.

## Installation

```bash
cd kraken-futures-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Commandes utiles

### Scanner tout le marché configuré

```bash
python main.py scan
```

### Analyser une paire précise avec plusieurs stratégies

```bash
python main.py analyze --symbol PF_ETHUSD
python main.py analyze --symbol PF_XBTUSD
```

### Comparer les stratégies sur la paire courante

```bash
python main.py compare
```

### Optimiser une stratégie

```bash
python main.py optimize --strategy mean_reversion --top 10
python main.py optimize --strategy ema_trend --top 10
python main.py optimize --strategy breakout --top 10
```

## News / sentiment

Le module news interroge le moteur local SearXNG et calcule un score lexical simple à partir des headlines.

Important :
- ce n'est **pas** un oracle
- c'est un **filtre contextuel**
- il sert à pondérer une opportunité, pas à déclencher seul un trade

## Sécurité

Toujours bloqué par défaut :
- `PAPER_TRADING=true`
- `LIVE_ENABLED=false`

## Limites actuelles

- scoring news encore simple
- pas encore de pondération macro avancée
- pas encore de persistance complète d'un portefeuille multi-positions
- pas encore de walk-forward analysis multi-actifs

## But réel

Le but est de choisir, à chaque cycle, **la paire + la stratégie les plus intéressantes parmi plusieurs candidates**, au lieu d'imposer une seule idée au marché.
