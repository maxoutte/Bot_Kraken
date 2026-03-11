from __future__ import annotations

import json
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Any

from .backtest import Backtester, compare_known_strategies, optimize
from .bot import TradingBot
from .config import BotConfig, load_config
from .dashboard import _build_state
from .exchange import KrakenFuturesClient
from .scanner import analyze_symbol, scan_market
from .strategy import config_with_strategy


class KrakenBotGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Kraken Futures Bot")
        self.root.geometry("1400x900")
        self.config = load_config()
        self.bot = TradingBot(self.config)
        self.watch_thread: threading.Thread | None = None
        self.watch_stop = threading.Event()
        self.data_dir = Path(__file__).resolve().parents[2] / "data"

        self.strategy_var = tk.StringVar(value=self.config.strategy_name)
        self.symbol_var = tk.StringVar(value=self.config.symbol)
        self.status_var = tk.StringVar(value="Prêt")
        self.auto_refresh_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._refresh_live_panels()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Paire").pack(side="left")
        ttk.Entry(top, textvariable=self.symbol_var, width=16).pack(side="left", padx=6)
        ttk.Label(top, text="Stratégie").pack(side="left")
        ttk.Combobox(top, textvariable=self.strategy_var, values=["breakout", "ema_trend", "mean_reversion"], width=18, state="readonly").pack(side="left", padx=6)
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        buttons = ttk.LabelFrame(self.root, text="Commandes", padding=10)
        buttons.pack(fill="x", padx=10, pady=6)

        actions = [
            ("Tickers", self.run_tickers),
            ("Scan", self.run_scan),
            ("Scan + Log", self.run_scan_log),
            ("Analyze", self.run_analyze),
            ("Compare", self.run_compare),
            ("Backtest", self.run_backtest),
            ("Optimize", self.run_optimize),
            ("Run Once", self.run_once),
            ("Dashboard HTML", self.build_dashboard),
            ("Start Watch", self.start_watch),
            ("Stop Watch", self.stop_watch),
            ("Refresh", self.refresh_now),
        ]
        for i, (label, fn) in enumerate(actions):
            ttk.Button(buttons, text=label, command=fn).grid(row=i // 6, column=i % 6, padx=6, pady=6, sticky="ew")

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=6)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=3)
        main.add(right, weight=2)

        self.output = scrolledtext.ScrolledText(left, wrap="word", font=("DejaVu Sans Mono", 10))
        self.output.pack(fill="both", expand=True)

        right_top = ttk.LabelFrame(right, text="État live", padding=8)
        right_top.pack(fill="both", expand=True)
        self.live_status = scrolledtext.ScrolledText(right_top, height=18, wrap="word", font=("DejaVu Sans Mono", 9))
        self.live_status.pack(fill="both", expand=True)

        right_mid = ttk.LabelFrame(right, text="Top opportunités", padding=8)
        right_mid.pack(fill="both", expand=True, pady=6)
        self.live_scans = scrolledtext.ScrolledText(right_mid, height=14, wrap="word", font=("DejaVu Sans Mono", 9))
        self.live_scans.pack(fill="both", expand=True)

        right_bottom = ttk.LabelFrame(right, text="Derniers trades", padding=8)
        right_bottom.pack(fill="both", expand=True)
        self.live_trades = scrolledtext.ScrolledText(right_bottom, height=12, wrap="word", font=("DejaVu Sans Mono", 9))
        self.live_trades.pack(fill="both", expand=True)

        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x")
        ttk.Checkbutton(footer, text="Auto-refresh live", variable=self.auto_refresh_var).pack(side="left")
        ttk.Button(footer, text="Quitter", command=self.on_close).pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def current_config(self) -> BotConfig:
        config = load_config()
        config.symbol = self.symbol_var.get().strip() or config.symbol
        config = config_with_strategy(config, self.strategy_var.get())
        config.symbol = self.symbol_var.get().strip() or config.symbol
        return config

    def append_output(self, title: str, payload: Any) -> None:
        self.output.insert("end", f"\n=== {title} ===\n")
        if isinstance(payload, str):
            self.output.insert("end", payload + "\n")
        else:
            self.output.insert("end", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        self.output.see("end")

    def _run_async(self, title: str, fn) -> None:
        self.status_var.set(f"Exécution: {title}")
        def worker() -> None:
            try:
                result = fn()
                self.root.after(0, lambda: self.append_output(title, result))
                self.root.after(0, lambda: self.status_var.set(f"OK: {title}"))
                self.root.after(0, self._refresh_live_panels)
            except Exception as exc:
                self.root.after(0, lambda: self.append_output(f"Erreur {title}", str(exc)))
                self.root.after(0, lambda: self.status_var.set(f"Erreur: {title}"))
        threading.Thread(target=worker, daemon=True).start()

    def run_tickers(self) -> None:
        self._run_async("Tickers", lambda: KrakenFuturesClient(self.current_config()).fetch_tickers())

    def run_scan(self) -> None:
        self._run_async("Scan", lambda: scan_market(self.current_config()))

    def run_scan_log(self) -> None:
        self._run_async("Scan + Log", lambda: TradingBot(self.current_config()).scan_and_log())

    def run_analyze(self) -> None:
        self._run_async("Analyze", lambda: analyze_symbol(self.current_config(), self.symbol_var.get().strip() or self.current_config().symbol))

    def run_compare(self) -> None:
        def job():
            config = self.current_config()
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
            return compare_known_strategies(df, config)
        self._run_async("Compare", job)

    def run_backtest(self) -> None:
        def job():
            config = self.current_config()
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
            return Backtester(config).run(df)
        self._run_async("Backtest", job)

    def run_optimize(self) -> None:
        def job():
            config = self.current_config()
            df = KrakenFuturesClient(config).fetch_ohlcv(config.symbol)
            return optimize(df, config)[:10]
        self._run_async("Optimize", job)

    def run_once(self) -> None:
        self._run_async("Run Once", lambda: TradingBot(self.current_config()).step())

    def build_dashboard(self) -> None:
        from .dashboard import build_dashboard
        self._run_async("Dashboard HTML", lambda: {"dashboard": build_dashboard(str(Path(__file__).resolve().parents[2] / "dashboard.html"), self.current_config().dashboard_refresh_seconds)})

    def start_watch(self) -> None:
        if self.watch_thread and self.watch_thread.is_alive():
            messagebox.showinfo("Watch", "La boucle watch tourne déjà.")
            return
        self.watch_stop.clear()
        def loop() -> None:
            self.status_var.set("Watch actif")
            while not self.watch_stop.is_set():
                try:
                    result = self.bot.auto_watch_cycle()
                    self.root.after(0, lambda r=result: self.append_output("Watch Cycle", r))
                    self.root.after(0, self._refresh_live_panels)
                except Exception as exc:
                    self.root.after(0, lambda: self.append_output("Erreur Watch", str(exc)))
                time.sleep(self.bot.config.loop_seconds)
            self.root.after(0, lambda: self.status_var.set("Watch arrêté"))
        self.watch_thread = threading.Thread(target=loop, daemon=True)
        self.watch_thread.start()

    def stop_watch(self) -> None:
        self.watch_stop.set()
        self.status_var.set("Arrêt demandé")

    def refresh_now(self) -> None:
        self._refresh_live_panels()

    def _refresh_live_panels(self) -> None:
        try:
            state = _build_state(self.data_dir)
        except Exception as exc:
            state = {"status": {"error": str(exc)}, "latestScans": [], "latestTrades": []}
        self._set_text(self.live_status, state.get("status", {}))
        self._set_text(self.live_scans, state.get("latestScans", []))
        self._set_text(self.live_trades, state.get("latestTrades", []))
        if self.auto_refresh_var.get():
            self.root.after(5000, self._refresh_live_panels)

    @staticmethod
    def _set_text(widget: scrolledtext.ScrolledText, payload: Any) -> None:
        widget.delete("1.0", "end")
        widget.insert("end", json.dumps(payload, indent=2, ensure_ascii=False))

    def on_close(self) -> None:
        self.watch_stop.set()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def launch_gui() -> None:
    KrakenBotGUI().run()
