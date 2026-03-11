from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.trades_jsonl = self.base / 'trades.jsonl'
        self.trades_csv = self.base / 'trades.csv'
        self.scans_jsonl = self.base / 'scans.jsonl'
        self.status_json = self.base / 'status.json'

    def append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')

    def append_trade(self, payload: dict[str, Any]) -> None:
        self.append_jsonl(self.trades_jsonl, payload)
        existing_rows = []
        fieldnames = list(payload.keys())
        if self.trades_csv.exists():
            with self.trades_csv.open('r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
                fieldnames = list(dict.fromkeys((reader.fieldnames or []) + fieldnames))
        normalized_rows = []
        for row in existing_rows:
            normalized_rows.append({key: row.get(key, '') for key in fieldnames})
        normalized_rows.append({key: payload.get(key, '') for key in fieldnames})
        with self.trades_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized_rows)

    def append_scan(self, payload: dict[str, Any]) -> None:
        self.append_jsonl(self.scans_jsonl, payload)

    def write_status(self, payload: dict[str, Any]) -> None:
        with self.status_json.open('w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
