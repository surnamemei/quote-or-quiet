"""Low-memory embedding cache: SQLite (results/cache/emb.sqlite, key = sha256(text), value = float64 vector, unit-normalised),
replacing the 7.7 GB pickle that vkg/retrieval2.py loads whole into RAM (about 37 GB as Python lists).
embed(texts) computes exactly what retrieval2._embed computes (same model, same batches of 32, same normalisation, float64),
so passages built through it are identical; retrieval2.py itself is frozen (hash in freeze 7) and is not imported here.
  migrate()  one-off copy of emb.pkl into emb.sqlite:  python -B -m vkg.emb2 migrate
Thread-safe (one connection per thread; writes under a lock)."""
import hashlib
import math
import sqlite3
import sys
import threading
from array import array
from pathlib import Path

import os

import requests

ROOT = Path(__file__).resolve().parent.parent
# VKG_EMB=pod: embed on the rented pod (tunnel localhost:11435), cached in a separate file so that pod (CUDA) and
# local (Vulkan) vectors are never mixed within one run.
# VKG_EMB=hf: official HF Qwen3-Embedding-0.6B on the pod's generation server (/embed, batched; tunnel localhost:18000),
# cached in emb_hf.sqlite. The HF weights differ numerically from Ollama's GGUF, so each backend has its own cache file.
MODE = os.environ.get("VKG_EMB", "local")
_POD = MODE == "pod"
DB = ROOT / "results" / "cache" / {"pod": "emb_pod.sqlite", "hf": "emb_hf.sqlite"}.get(MODE, "emb.sqlite")
OLLAMA = "http://localhost:11435" if _POD else "http://localhost:11434"
EMB_MODEL = "qwen3-embedding:0.6b"
_local = threading.local()
_WLOCK = threading.Lock()


def _con():
    if not hasattr(_local, "c"):
        c = sqlite3.connect(DB, timeout=120, check_same_thread=False)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE IF NOT EXISTS emb(k TEXT PRIMARY KEY, v BLOB)")
        _local.c = c
    return _local.c


def _h(t):
    return hashlib.sha256(t.encode()).hexdigest()


def _get(keys):
    out, c = {}, _con()
    keys = list(keys)
    for i in range(0, len(keys), 500):
        part = keys[i:i + 500]
        for k, v in c.execute(f"SELECT k, v FROM emb WHERE k IN ({','.join('?' * len(part))})", part):
            out[k] = array("d", v).tolist()
    return out


def embed(texts):
    uniq = list(dict.fromkeys(texts))
    have = _get(_h(t) for t in uniq)
    todo = [t for t in uniq if _h(t) not in have]
    step = 512 if MODE == "hf" else 32
    for i in range(0, len(todo), step):
        batch = todo[i:i + step]
        if MODE == "hf":
            r = requests.post("http://localhost:18000/embed", json={"texts": batch}, timeout=1800)
            r.raise_for_status()
            vecs = r.json()["vecs"]
        else:
            r = requests.post(f"{OLLAMA}/api/embed", json={"model": EMB_MODEL, "input": batch}, timeout=600)
            r.raise_for_status()
            vecs = r.json()["embeddings"]
        rows = []
        for t, v in zip(batch, vecs):
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            vec = [x / n for x in v]
            have[_h(t)] = vec
            rows.append((_h(t), array("d", vec).tobytes()))
        with _WLOCK:
            _con().executemany("INSERT OR IGNORE INTO emb VALUES (?, ?)", rows)
            _con().commit()
    return [have[_h(t)] for t in texts]


def migrate():
    import pickle
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    d = pickle.load(open(ROOT / "results" / "cache" / "emb.pkl", "rb"))
    c = _con()
    items = list(d.items())
    for i in range(0, len(items), 20000):
        c.executemany("INSERT OR IGNORE INTO emb VALUES (?, ?)", [(k, array("d", v).tobytes()) for k, v in items[i:i + 20000]])
        c.commit()
    print("migrated", len(items), "->", c.execute("SELECT COUNT(*) FROM emb").fetchone()[0])


if __name__ == "__main__":
    {"migrate": migrate}[sys.argv[1]]()
