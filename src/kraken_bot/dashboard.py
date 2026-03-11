from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HTML_TEMPLATE = """<!doctype html>
<html lang=\"fr\"><head><meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
<title>Kraken Bot Dashboard</title>
<style>
body{font-family:Inter,Arial,sans-serif;max-width:1200px;margin:24px auto;padding:0 16px;background:#0f172a;color:#e2e8f0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card{background:#111827;padding:16px;border-radius:12px}
pre{white-space:pre-wrap;word-break:break-word;background:#020617;padding:12px;border-radius:8px;max-height:420px;overflow:auto}.ok{color:#34d399}.warn{color:#fbbf24}
</style></head><body><h1>Kraken Futures Bot — Live Dashboard</h1><div class=\"grid\"><div class=\"card\"><h2>État</h2><pre id=\"status\"></pre></div><div class=\"card\"><h2>Résumé</h2><pre id=\"summary\"></pre></div></div><div class=\"grid\"><div class=\"card\"><h2>Top opportunités</h2><pre id=\"scans\"></pre></div><div class=\"card\"><h2>Trades</h2><pre id=\"trades\"></pre></div></div>
<script>
async function load(){
 const data=await fetch('/api/state').then(r=>r.json());
 document.getElementById('status').textContent=JSON.stringify(data.status,null,2);
 document.getElementById('summary').textContent=JSON.stringify(data.summary,null,2);
 document.getElementById('scans').textContent=JSON.stringify(data.latestScans,null,2);
 document.getElementById('trades').textContent=JSON.stringify(data.latestTrades,null,2);
}
load(); setInterval(load, REFRESH_MS);
</script></body></html>"""


def build_dashboard(output_path: str, refresh_seconds: int) -> str:
    path = Path(output_path)
    path.write_text(HTML_TEMPLATE.replace('REFRESH_MS', str(refresh_seconds * 1000)), encoding='utf-8')
    return str(path)


def serve_dashboard(data_dir: str, host: str, port: int, refresh_seconds: int) -> None:
    base = Path(data_dir)
    build_dashboard(str(base.parent / 'dashboard.html'), refresh_seconds)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str = 'text/html', code: int = 200) -> None:
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path in ['/', '/dashboard.html']:
                html = (base.parent / 'dashboard.html').read_text(encoding='utf-8')
                return self._send(html.encode('utf-8'))
            if self.path == '/api/state':
                payload = _build_state(base)
                return self._send(json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8'), 'application/json')
            self._send(b'Not found', 'text/plain', 404)

    ThreadingHTTPServer((host, port), Handler).serve_forever()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def _read_jsonl(path: Path, limit: int = 10) -> list[Any]:
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return [json.loads(line) for line in lines[-limit:]]


def _build_state(base: Path) -> dict[str, Any]:
    status = _read_json(base / 'status.json', {})
    scans = _read_jsonl(base / 'scans.jsonl', 5)
    trades = _read_jsonl(base / 'trades.jsonl', 10)
    summary = {
        'open_position': status.get('position'),
        'capital': status.get('capital'),
        'best_setup': status.get('best_setup'),
        'trade_count': len(trades),
        'scan_count': len(scans),
    }
    latest_scans = scans[-1]['results'][:5] if scans else []
    return {'status': status, 'summary': summary, 'latestScans': latest_scans, 'latestTrades': trades}
