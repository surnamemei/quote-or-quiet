"""Search backend 2: Serper (Google results API), user-provided key read from %USERPROFILE%\\.serper_key (never printed or copied).
Same interface and the same contamination guard as vkg/websearch.py (blocked domains, verbatim-question / SimpleQA page filter);
pages are fetched and cached by vkg.websearch.fetch. Search results are cached under results/cache/web2/ (separate from the
DuckDuckGo cache, so the two backends are never mixed silently). Parallel-safe; at most 5 requests per second."""
import json
import threading
import time
from pathlib import Path

import requests

from .websearch import ROOT, _key, blocked, contaminated, fetch  # noqa: F401  (re-exported for callers)

CACHE = ROOT / "results" / "cache" / "web2"
CACHE.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()
_LAST = [0.0]
_KEY = []


def _api_key():
    if not _KEY:
        _KEY.append((Path.home() / ".serper_key").read_text(encoding="utf-8-sig").strip())
    return _KEY[0]


def search(query, k=6):
    """Result URLs (blocked domains removed), cached. Raises after repeated failures (never silently empty)."""
    f = CACHE / f"s_{_key(query)}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))[:k]
    err = None
    for attempt in range(5):
        with _LOCK:
            wait = 0.2 - (time.time() - _LAST[0])
            if wait > 0:
                time.sleep(wait)
            _LAST[0] = time.time()
        try:
            r = requests.post("https://google.serper.dev/search", json={"q": query, "num": 10},
                              headers={"X-API-KEY": _api_key(), "Content-Type": "application/json"}, timeout=30)
            if r.status_code == 200:
                urls = []
                for o in r.json().get("organic", []):
                    u = o.get("link", "")
                    if u.startswith("http") and not blocked(u) and u not in urls:
                        urls.append(u)
                f.write_text(json.dumps(urls), encoding="utf-8")
                return urls[:k]
            err = f"HTTP {r.status_code}"
            if r.status_code in (401, 403):
                raise RuntimeError(f"Serper rejected the key ({err}); check %USERPROFILE%\\.serper_key")
        except requests.RequestException as e:
            err = type(e).__name__
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Serper search failed repeatedly ({err}): {query!r}")
