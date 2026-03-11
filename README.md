# Kraken Futures Bot

Bot de trading **Kraken Futures** en **Python**, avec :
- scan multi-paires,
- stratégies multiples,
- paper trading,
- logs,
- application web locale interactive avec boutons.

## Application graphique locale

L'interface principale est maintenant une **application web locale** avec :
- choix de la **paire**,
- choix de la **stratégie**,
- **un bouton par fonctionnalité / commande**,
- affichage live de l'état,
- top opportunités,
- derniers trades,
- sortie détaillée de chaque action.

## Lancer l'application

```bash
cd kraken-futures-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py serve
```

Puis ouvrir :

```bash
http://127.0.0.1:8765
```

## Boutons inclus

- Tickers
- Scan
- Scan + Log
- Analyze
- Compare
- Backtest
- Optimize
- Run Once
- Start Watch / Stop Watch
- Refresh

## Auto paper trading

Activable dans `.env` :
- `AUTO_TRADE_ENABLED=true`
- `AUTO_TRADE_SCORE_THRESHOLD=6.0`

## Fichiers utiles

- `data/status.json`
- `data/scans.jsonl`
- `data/trades.jsonl`
- `data/trades.csv`

## But

Avoir une interface pilotable visuellement, avec boutons, état live et historique, sans dépendre d'une stack desktop lourde.
