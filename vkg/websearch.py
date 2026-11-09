"""Keyless open-web search for the search-on-abstain experiments (user direction 2026-11-06: no API key, "just search online").
search(query)  : DuckDuckGo's HTML endpoint (html.duckduckgo.com, made for non-JS browsers), at most one request per ~4 s, cached.
fetch(url)     : GET the page (HTML only, 20 s timeout, 3 MB cap), strip scripts/styles/tags, cached.
Contamination guard (Search-Time Data Contamination, arXiv 2508.13180):
  - blocked domains: benchmark and dataset mirrors and code hosts (huggingface, github, kaggle, arxiv, paperswithcode, openai, ...);
  - a fetched page is dropped if it contains the question verbatim (normalised, first 60 characters or the whole question)
    or mentions SimpleQA.
Page text is data for the model, never instructions to this harness."""
import hashlib
import html as H
import json
import re
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "results" / "cache" / "web"
CACHE.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) vkg-research-harness/0.1 (local academic experiment)"}
BLOCK = ("huggingface.co", "github.com", "githubusercontent.com", "gitlab.com", "kaggle.com", "arxiv.org", "paperswithcode.com",
         "openai.com", "openreview.net", "aclanthology.org", "semanticscholar.org", "researchgate.net", "scale.com", "llm-stats.com")
_LOCK = threading.Lock()
_LAST = [0.0]


def _key(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def blocked(url):
    host = urlparse(url).netloc.lower()
    return any(host == b or host.endswith("." + b) for b in BLOCK)


def search(query, k=6):
    """Returns a list of result URLs (blocked domains removed). Raises after repeated failures (never silently empty)."""
    f = CACHE / f"s_{_key(query)}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))[:k]
    for attempt in range(6):
        with _LOCK:
            wait = 5.0 - (time.time() - _LAST[0])   # amendment 2026-11-06 05:10: 4 s -> 10 s after a DuckDuckGo bot check; 2026-11-07 18:3x: 10 s -> 5 s at the user's request (S19 closed; bot checks still never bypassed)
            if wait > 0:
                time.sleep(wait)
            _LAST[0] = time.time()
            try:
                r = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=HDR, timeout=30)
            except requests.RequestException:
                r = None
        if r is not None and r.status_code == 200 and "result__a" in r.text:
            urls = []
            for u in re.findall(r'class="result__a" href="([^"]+)"', r.text):
                u = H.unescape(u)
                if "duckduckgo.com/l/?" in u:                      # redirect wrapper
                    u = unquote(parse_qs(urlparse(u).query).get("uddg", [u])[0])
                if u.startswith("http") and not blocked(u) and u not in urls:
                    urls.append(u)
            f.write_text(json.dumps(urls), encoding="utf-8")
            return urls[:k]
        if r is not None and r.status_code == 200 and "No results" in r.text:
            f.write_text("[]", encoding="utf-8")
            return []
        time.sleep(min(30 * (attempt + 1), 180))                  # rate-limited or anomaly page: back off
    raise RuntimeError(f"web search failed repeatedly: {query!r}")


def _text(html):
    html = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header|form)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|section|article|table)>", "\n", html)
    t = H.unescape(re.sub(r"(?s)<[^>]+>", " ", html))
    lines = [re.sub(r"[ \t\r\f\v]+", " ", x).strip() for x in t.split("\n")]
    return "\n".join(x for x in lines if len(x.split()) >= 4)


def fetch(url):
    """Page text ('' on failure or non-HTML). Cached."""
    f = CACHE / f"p_{_key(url)}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))["text"]
    text = ""
    try:
        with requests.get(url, headers=HDR, timeout=20, stream=True) as r:
            if r.status_code == 200 and "html" in r.headers.get("content-type", "").lower():
                raw = r.raw.read(3_000_000, decode_content=True)
                enc = r.encoding or "utf-8"
                text = _text(raw.decode(enc, errors="ignore"))
    except Exception:
        text = ""
    f.write_text(json.dumps({"url": url, "text": text}), encoding="utf-8")
    return text


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def contaminated(text, question):
    t = _norm(text)
    q = _norm(question)
    return (q in t) or (len(q) > 60 and q[:60] in t) or ("simpleqa" in t)
