"""Local English Wikipedia, SQLite FTS5 index (BM25) over title + text; no network at query time. Two sources (CC BY-SA):
  fw2025 (default): HuggingFaceFW/finewiki data/enwiki, parsed from the official Wikimedia Enterprise HTML dumps of August 2025
                    (templates rendered; redirects/disambiguation removed). Infobox key-values are appended to each article as
                    an "Infobox" section. Files verified against data/wiki/finewiki_en/official_sha256.txt.
  hf2023          : wikimedia/wikipedia 20231101.en (data/wiki/official_sha256.txt). Known flaw: many major articles missing
                    (Japan, Iran, Eiffel Tower ...); kept only for comparison.
Select with the environment variable VKG_LOCALWIKI (fw2025 | hf2023).
  build : python -B -m vkg.localwiki build [fw2025|hf2023]   (idle priority)
  search(query, k)  -> list of titles, BM25-ranked (title column weighted 5x)
  page_text(title)  -> article text ('' if absent)
Facts added to Wikipedia after the snapshot date are absent (reported as a limitation)."""
import json
import os
import re
import sqlite3
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"fw2025": (ROOT / "data" / "wiki" / "finewiki_en", "*.parquet", ROOT / "data" / "wiki" / "enwiki_fw2025.sqlite"),
           "hf2023": (ROOT / "data" / "wiki" / "20231101.en", "train-*.parquet", ROOT / "data" / "wiki" / "enwiki_20231101.sqlite")}
WIKI = os.environ.get("VKG_LOCALWIKI", "fw2025")
DB = SOURCES[WIKI][2]
STOP = set("a an the of in on at to for by with from and or is was were are be been as that this which who whom what when where why how "
           "did does do it its his her their there than then into about after before during under over between".split())
_local = threading.local()


def _con():
    if not hasattr(_local, "c"):
        _local.c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, check_same_thread=False)
    return _local.c


def _infobox_text(js):
    """Flatten FineWiki's JSON infoboxes into 'key: value' lines."""
    try:
        boxes = json.loads(js) if js else []
    except ValueError:
        return ""
    lines = []
    for b in boxes or []:
        for k, v in (b.get("data") or {}).items():
            v = "; ".join(map(str, v)) if isinstance(v, list) else str(v)
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def _rows(batch, fw):
    titles, texts = batch.column("title").to_pylist(), batch.column("text").to_pylist()
    if not fw:
        return list(zip(titles, texts))
    boxes = batch.column("infoboxes").to_pylist()
    return [(t, x + ("\n\n## Infobox\n" + ib if ib else "")) for t, x, b in zip(titles, texts, boxes) for ib in [_infobox_text(b)]]


def build(which="fw2025"):
    import psutil
    import pyarrow.parquet as pq
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    src, pat, db = SOURCES[which]
    fw = which == "fw2025"
    tmp = db.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    c = sqlite3.connect(tmp)
    c.executescript("""PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA cache_size=-1000000;
        CREATE TABLE articles(rowid INTEGER PRIMARY KEY, title TEXT, text TEXT);
        CREATE VIRTUAL TABLE fts USING fts5(title, text, content='articles', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2');""")
    files = sorted(src.glob(pat))
    n = 0
    for i, f in enumerate(files, 1):
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=20000, columns=["title", "text"] + (["infoboxes"] if fw else [])):
            rows = _rows(batch, fw)
            c.executemany("INSERT INTO articles(title, text) VALUES (?, ?)", rows)
            n += len(rows)
        c.commit()
        print(f"  loaded {i}/{len(files)} files, {n} articles", flush=True)
    c.execute("CREATE INDEX idx_title ON articles(title)")
    print("  building FTS index ...", flush=True)
    c.execute("INSERT INTO fts(fts) VALUES('rebuild')")
    c.commit()
    c.execute("INSERT INTO fts(fts) VALUES('optimize')")
    c.execute("CREATE VIRTUAL TABLE vocab USING fts5vocab('fts', 'row')")
    c.commit()
    c.close()
    tmp.replace(db)
    print("done", n)


MAX_DF = 300_000      # terms in more than ~5% of articles are too common to filter on


def _terms(query):
    words = list(dict.fromkeys(w for w in re.findall(r"\w+", query.lower()) if w not in STOP and len(w) > 1))
    if not words:
        return []
    q = ",".join("?" * len(words))
    df = dict(_con().execute(f"SELECT term, doc FROM vocab WHERE term IN ({q})", words).fetchall())
    return sorted((w for w in words if 0 < df.get(w, 0) <= MAX_DF), key=lambda w: df[w])   # rarest first


def search(query, k=10):
    """AND of the content terms (rarest first); if fewer than k hits, drop the most common term and retry.
    Ranked by BM25 (title weighted 5x). Fast because the AND set is small."""
    terms = _terms(query)
    out = []
    while terms and len(out) < k:
        m = " ".join(f'"{w}"' for w in terms)
        for (t,) in _con().execute("SELECT a.title FROM fts JOIN articles a ON a.rowid = fts.rowid WHERE fts MATCH ? "
                                   "ORDER BY bm25(fts, 5.0, 1.0) LIMIT ?", (m, k)):
            if t not in out:
                out.append(t)
        terms = terms[:-1]
    return out[:k]


def page_text(title):
    r = _con().execute("SELECT text FROM articles WHERE title = ? LIMIT 1", (title,)).fetchone()
    return r[0] if r else ""


if __name__ == "__main__":
    {"build": build}[sys.argv[1]](*sys.argv[2:])
