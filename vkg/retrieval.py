"""Wikipedia retrieval for the open-world route. Live public site, on-disk cache, no gold information used in 'search' mode.
search(question)  -> candidate page titles from Wikipedia full-text search on a keyword query built from the question.
page_text(title)  -> article text from the raw wikitext (infobox fields kept as 'key: value'; templates, refs, files removed).
build_passage(question, titles) -> top chunks by BM25 across the pages, capped by words.
Why index.php and not the API: the API / REST endpoints answered this client with HTTP 429 after ~10 requests (retry-after ~44 s),
while index.php (search page, action=raw) was not throttled.
"""
import hashlib
import json
import math
import re
import threading
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "results" / "cache" / "wiki"
CACHE.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "vkg-research-harness/0.1 (local academic experiment)"}
INDEX = "https://en.wikipedia.org/w/index.php"
STOP = set("""a an the of in on at to for by with from and or is are was were be been being as that this these those which who whom whose
what when where why how did does do has have had it its his her their he she they them than then also into over after before during
about between against under up out one two many much more most first last name named called""".split())

_SEM = threading.Semaphore(4)


def _fetch(params):
    """Cached GET of index.php. 4 connections at a time, honours Retry-After on HTTP 429, raises after 12 failures:
    a failed fetch must never look like 'no result'. Returns (final_url, text); a 404 is cached as empty text."""
    key = hashlib.sha256(("idx" + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return d["url"], d["text"]
    with _SEM:
        for attempt in range(12):
            try:
                r = requests.get(INDEX, params=params, headers=HDR, timeout=60)
            except requests.RequestException:
                time.sleep(min(5 * (attempt + 1), 60))
                continue
            if r.status_code in (200, 404):
                text = r.text if r.status_code == 200 else ""
                f.write_text(json.dumps({"url": r.url, "text": text}), encoding="utf-8")
                return r.url, text
            if r.status_code == 429:
                time.sleep(min(int(r.headers.get("retry-after", "30")) + 2, 120))
            else:
                time.sleep(min(5 * (attempt + 1), 60))
    raise RuntimeError(f"Wikipedia request failed repeatedly: {params}")


def keywords(q, limit=10):
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", q)
    seen, out = set(), []
    for t in toks:
        tl = t.lower()
        if tl in STOP or tl in seen:
            continue
        seen.add(tl)
        out.append(t)
    caps = [t for t in out if t[0].isupper() or t[0].isdigit()]
    rest = sorted([t for t in out if t not in caps], key=len, reverse=True)
    return (caps + rest)[:limit]


def _search_titles(query, k):
    url, html = _fetch({"search": query, "fulltext": 1, "ns0": 1, "limit": k})
    path = urlparse(url).path
    if path.startswith("/wiki/"):          # exact title match: Wikipedia redirects straight to the article
        return [unquote(path[len("/wiki/"):]).replace("_", " ")]
    raw = re.findall(r'class="mw-search-result-heading"><a href="/wiki/([^"#]+)"', html)
    return [unquote(t).replace("_", " ") for t in raw[:k]]


def search(question, k=5):
    """If the AND-query finds nothing, retry with fewer keywords (10 -> 6 -> 4 -> 3)."""
    for n in (10, 6, 4, 3):
        res = _search_titles(" ".join(keywords(question, n)), k)
        if res:
            return res
    return []


# ---- wikitext -> text
def _inline(t):
    t = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<br\s*/?>", ", ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", t, flags=re.I)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[https?://[^\s\]]+\s*([^\]]*)\]", r"\1", t)
    t = t.replace("'''", "").replace("''", "")
    return re.sub(r"[ \t]+", " ", t)


_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _split_args(block):
    args, depth, cur, i = [], 0, [], 0
    while i < len(block):
        two = block[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            cur.append(two)
            i += 2
        elif block[i] == "|" and depth == 0:
            args.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(block[i])
            i += 1
    args.append("".join(cur))
    return args


def _render_template(block):
    """Keep the information carried by common value templates (units, dates, lists); drop everything else (cites, navboxes...)."""
    args = _split_args(block)
    name = re.sub(r"\s+", " ", args[0].strip().lower())
    pos = [_inline(_strip_templates(a)).strip() for a in args[1:] if "=" not in a.split("{{")[0]]
    if name in ("convert", "cvt", "convert/"):
        return f"{pos[0]} {pos[1]}" if len(pos) >= 2 else (pos[0] if pos else "")
    if name in ("birth date", "birth date and age", "death date", "death date and age", "start date", "end date",
                "birth-date", "dob", "start date and age", "birth date and age2"):
        nums = [p for p in pos if p.isdigit()]
        if len(nums) >= 3 and 1 <= int(nums[1]) <= 12:
            return f"{int(nums[2])} {_MONTHS[int(nums[1]) - 1]} {nums[0]}"
        return " ".join(nums)
    if name in ("nowrap", "small", "nobr", "abbr", "tooltip", "nbsp", "val", "lang-en", "transl"):
        return " ".join(pos[:2] if name == "val" else pos[:1])
    if name.startswith("lang") or name in ("langx",):
        return pos[1] if len(pos) > 1 else (pos[0] if pos else "")
    if name in ("plainlist", "ubl", "unbulleted list", "flatlist", "hlist", "plain list", "bulleted list", "unbulleted"):
        return ", ".join(p for p in pos if p)
    return ""


def _strip_templates(t):
    """Remove {{...}} templates (nested) but keep Infobox fields as 'key: value' lines."""
    out, i, n = [], 0, len(t)
    while i < n:
        if t.startswith("{{", i):
            depth, j = 0, i
            while j < n:
                if t.startswith("{{", j):
                    depth += 1
                    j += 2
                elif t.startswith("}}", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            block = t[i + 2:j - 2]
            if not re.match(r"\s*(infobox|taxobox|speciesbox)", block, re.I):
                out.append(_render_template(block))
            if re.match(r"\s*(infobox|taxobox|speciesbox)", block, re.I):
                for fld in re.split(r"\n\s*\|", block)[1:]:
                    if "=" in fld:
                        k, v = fld.split("=", 1)
                        v = _inline(_strip_templates(v)).strip()
                        if v:
                            out.append(f"\n{k.strip().replace('_', ' ')}: {v}\n")
            i = j
        else:
            out.append(t[i])
            i += 1
    return "".join(out)


def _clean(wikitext):
    t = re.sub(r"<!--.*?-->", "", wikitext, flags=re.S)
    t = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = _strip_templates(t)
    lines = []
    for ln in t.split("\n"):
        ln = ln.strip()
        if not ln or ln.startswith(("{|", "|}", "|-", "__", "[[Category:")):
            continue
        if ln[:1] in "!|":                              # table cell: drop 'style=... |' prefix, keep the cell text
            ln = re.sub(r"^[!|]+\s*(?:[^|\[]*\|(?!\|))?\s*", "", ln)
        ln = re.sub(r"^=+\s*(.*?)\s*=+$", r"\1", ln)
        ln = re.sub(r"^[*#:;]+\s*", "", ln)
        ln = _inline(ln).strip()
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def page_text(title, _depth=0):
    _, wt = _fetch({"title": title, "action": "raw"})
    m = re.match(r"\s*#redirect\s*\[\[([^\]|#]+)", wt, re.I)
    if m and _depth < 2:
        return page_text(m.group(1).strip(), _depth + 1)
    return _clean(wt) if wt else ""


def _chunks(text, size=120):
    out = []
    for para in re.split(r"\n+", text):
        w = para.split()
        for i in range(0, len(w), size):
            seg = " ".join(w[i:i + size])
            if len(seg.split()) >= 8:
                out.append(seg)
    return out


def _tok(s):
    return [t for t in re.findall(r"\w+", s.lower()) if t not in STOP]


def build_passage(question, titles, max_words=900):
    chunks = []
    for t in titles:
        for c in _chunks(page_text(t)):
            chunks.append((t, c))
    if not chunks:
        return ""
    docs = [_tok(c) for _, c in chunks]
    N = len(docs)
    avg = sum(map(len, docs)) / N
    df = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    qt = _tok(question)
    scores = []
    for i, d in enumerate(docs):
        tf = {}
        for w in d:
            tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w in set(qt):
            if w in tf:
                idf = math.log(1 + (N - df[w] + .5) / (df[w] + .5))
                s += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(d) / avg))
        scores.append(s)
    order = sorted(range(N), key=lambda i: -scores[i])
    picked, words = [], 0
    for i in order:
        n = len(chunks[i][1].split())
        if words + n > max_words:
            continue
        picked.append(i)
        words += n
    picked.sort()                      # keep article order inside the passage
    return "\n\n".join(f"[{chunks[i][0]}] {chunks[i][1]}" for i in picked)


def wiki_titles_from_urls(urls):
    out = []
    for u in str(urls).split(","):
        m = re.search(r"wikipedia\.org/wiki/([^#?\s]+)", u)
        if m:
            out.append(unquote(m.group(1)).replace("_", " "))
    return out
