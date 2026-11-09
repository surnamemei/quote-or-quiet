"""Improved retrieval variants (ROADMAP S2). The frozen baseline in retrieval.py is left unchanged.
Pieces, each switchable:
  rewrite_queries : the generator model proposes short search queries (no gold information, question only).
  titles_for      : union of baseline keyword search and rewritten queries, up to K pages.
  passage         : chunks scored by BM25 and/or dense embeddings (Ollama qwen3-embedding:0.6b), fused by reciprocal rank, up to a word budget.
"""
import hashlib
import json
import math
import pickle
import re
from pathlib import Path

import requests

from . import retrieval as R
from .llm import chat

ROOT = Path(__file__).resolve().parent.parent
EMB_FILE = ROOT / "results" / "cache" / "emb.pkl"
OLLAMA = "http://localhost:11434"
EMB_MODEL = "qwen3-embedding:0.6b"
_EMB = pickle.load(open(EMB_FILE, "rb")) if EMB_FILE.exists() else {}


def save_cache():
    pickle.dump(_EMB, open(EMB_FILE, "wb"))


def _embed(texts):
    todo = [t for t in dict.fromkeys(texts) if hashlib.sha256(t.encode()).hexdigest() not in _EMB]
    for i in range(0, len(todo), 32):
        batch = todo[i:i + 32]
        r = requests.post(f"{OLLAMA}/api/embed", json={"model": EMB_MODEL, "input": batch}, timeout=600)
        r.raise_for_status()
        for t, v in zip(batch, r.json()["embeddings"]):
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            _EMB[hashlib.sha256(t.encode()).hexdigest()] = [x / n for x in v]
    return [_EMB[hashlib.sha256(t.encode()).hexdigest()] for t in texts]


def rewrite_queries(question, model, n=3):
    prompt = (f"Question: {question}\n"
              f"Write {n} different short search queries (3 to 8 words each) that would find the Wikipedia article "
              "containing the answer. Use the names, places and dates in the question; do not answer it. "
              'Reply as JSON: {"queries": ["...", "..."]}')
    txt = chat(model, [{"role": "user", "content": prompt}])
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        qs = json.loads(m.group(0)).get("queries", []) if m else []
    except json.JSONDecodeError:
        qs = []
    return [q for q in qs if isinstance(q, str) and q.strip()][:n]


def titles_for(question, k_pages=5, rewrite_model=None, per_query=5):
    titles = list(R.search(question, per_query))
    if rewrite_model:
        for q in rewrite_queries(question, rewrite_model):
            for t in R._search_titles(q, per_query):
                if t not in titles:
                    titles.append(t)
    return titles[:k_pages]


def _bm25_scores(question, docs):
    toks = [R._tok(c) for c in docs]
    N = len(toks)
    avg = sum(map(len, toks)) / N
    df = {}
    for d in toks:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    qt = set(R._tok(question))
    out = []
    for d in toks:
        tf = {}
        for w in d:
            tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w in qt:
            if w in tf:
                idf = math.log(1 + (N - df[w] + .5) / (df[w] + .5))
                s += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(d) / avg))
        out.append(s)
    return out


def passage(question, titles, max_words=1500, dense=True, bm25=True, chunk_words=120):
    chunks = []
    for t in titles:
        for c in R._chunks(R.page_text(t), chunk_words):
            chunks.append((t, c))
    if not chunks:
        return ""
    texts = [c for _, c in chunks]
    ranks = []
    if bm25:
        sc = _bm25_scores(question, texts)
        ranks.append(sorted(range(len(texts)), key=lambda i: -sc[i]))
    if dense:
        qv = _embed(["Instruct: Given a question, retrieve passages that contain the answer\nQuery: " + question])[0]
        dv = _embed([f"{t}: {c}" for t, c in chunks])
        ds = [sum(a * b for a, b in zip(qv, v)) for v in dv]
        ranks.append(sorted(range(len(texts)), key=lambda i: -ds[i]))
    fused = [0.0] * len(texts)
    for rk in ranks:
        for pos, i in enumerate(rk):
            fused[i] += 1.0 / (60 + pos)
    order = sorted(range(len(texts)), key=lambda i: -fused[i])
    picked, words = [], 0
    for i in order:
        n = len(texts[i].split())
        if words + n > max_words:
            continue
        picked.append(i)
        words += n
    picked.sort()
    return "\n\n".join(f"[{chunks[i][0]}] {chunks[i][1]}" for i in picked)
