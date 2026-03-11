from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, base_dir: str) -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)
        self.trades_jsonl = self.base / "trades.jsonl"
        self.trades_csv = self.base / "trades.csv"
        self.scans_jsonl = self.base / "scans.jsonl"
        self.status_json = self.base / "status.json"

    def append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def append_trade(self, payload: dict[str, Any]) -> None:
        self.append_jsonl(self.trades_jsonl, payload)
        exists = self.trades_csv.exists()
        with self.trades_csv.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(payload.keys()))
            if not exists:
                writer.writeheader()
            writer.writerow(payload)

    def append_scan(self, payload: dict[str, Any]) -> None:
        self.append_jsonl(self.scans_jsonl, payload)

    def write_status(self, payload: dict[str, Any]) -> None:
        with self.status_json.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
