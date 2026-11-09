"""Fast web evidence for many items at once (torch-free; drives no GPU except the local 0.6B embedder through Ollama).
  search backend : "serper" (vkg/websearch2.py, Google results, about 5 requests/s, 1 credit per query) or "ddg" (vkg/websearch.py)
  passage        : vkg.s13_run.web_passage, executed from the frozen source text (same chunking, contamination guard,
                   BM25 + dense RRF, 1500 words), so it cannot drift from S13-S15.
  build(items, queries_of, backend, k, max_pages, workers) -> {id: {"queries", "urls", "kept", "dropped_contaminated", "passage"}}
Items run in parallel (workers); each item fetches its pages 4 at a time as before."""
import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import math
import re
from types import SimpleNamespace

from . import emb2
from . import retrieval as R
from . import websearch as W
from . import websearch2 as W2

_V = Path(__file__).resolve().parent


def _frozen(fname, name, ns):
    """Execute one top-level function from a frozen source file into ns (no import of that module)."""
    for n in ast.parse((_V / fname).read_text(encoding="utf-8")).body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            exec(compile(ast.Module([n], []), f"{fname}:{name}", "exec"), ns)
            return ns[name]
    raise KeyError(name)


# retrieval2 is not imported (its import loads the 7.7 GB embedding pickle); its BM25 scorer runs from the frozen source,
# and embeddings come from vkg/emb2.py (same values, SQLite cache).
_R2NS = {"math": math, "re": re, "R": R}
R2 = SimpleNamespace(_bm25_scores=_frozen("retrieval2.py", "_bm25_scores", _R2NS), _embed=emb2.embed)
web_passage = _frozen("s13_run.py", "web_passage", {"ThreadPoolExecutor": ThreadPoolExecutor, "urlparse": urlparse, "R": R, "R2": R2, "W": W})


def _local_page(title):
    """FineWiki article text; the appended "## Infobox" key-value lines are joined into one paragraph so that
    R._chunks (which drops paragraphs under 8 words) keeps them."""
    from . import localwiki as LW
    t = LW.page_text(title)
    head, sep, box = t.partition("\n\n## Infobox\n")
    return head + ("\n\nInfobox: " + "; ".join(l for l in box.split("\n") if l.strip()) if sep else "")


_LR = SimpleNamespace(_chunks=R._chunks, page_text=_local_page)
wiki_passage = _frozen("retrieval2.py", "passage", {"R": _LR, "_bm25_scores": R2._bm25_scores, "_embed": emb2.embed})


def wiki_build(items, k_pages=5, workers=8):
    """Local-Wikipedia evidence: localwiki.search(question) top k_pages titles -> retrieval2.passage logic (frozen source)."""
    from . import localwiki as LW

    def one(e):
        titles = LW.search(e["question"], k_pages)
        return e["id"], {"titles": titles, "passage": wiki_passage(e["question"], titles)}
    with ThreadPoolExecutor(workers) as ex:
        return dict(ex.map(one, items))


def combo_passage(question, web_kept_urls, wiki_titles, max_words=1500):
    """One passage from both sources: chunks of the kept (uncontaminated) web pages and of the local Wikipedia pages, scored
    together by BM25 + dense embeddings, fused by reciprocal rank, up to max_words (the same steps as web_passage)."""
    chunks = []
    for u in web_kept_urls:
        dom = urlparse(u).netloc.replace("www.", "")
        for c in R._chunks(W.fetch(u), 120):
            chunks.append((dom, c))
    for t in wiki_titles:
        txt = _local_page(t)
        if W.contaminated(txt, question):
            continue
        for c in R._chunks(txt, 120):
            chunks.append(("wikipedia: " + t, c))
    seen, uniq = set(), []
    for d, c in chunks:                       # the same Wikipedia text often arrives from both sources
        if c not in seen:
            seen.add(c)
            uniq.append((d, c))
    chunks = uniq
    if not chunks:
        return ""
    texts = [c for _, c in chunks]
    sc = R2._bm25_scores(question, texts)
    qv = R2._embed(["Instruct: Given a question, retrieve passages that contain the answer\nQuery: " + question])[0]
    dv = R2._embed([f"{d}: {c}" for d, c in chunks])
    ds = [sum(a * b for a, b in zip(qv, v)) for v in dv]
    fused = [0.0] * len(texts)
    for rk in (sorted(range(len(texts)), key=lambda i: -sc[i]), sorted(range(len(texts)), key=lambda i: -ds[i])):
        for pos, i in enumerate(rk):
            fused[i] += 1.0 / (60 + pos)
    picked, words = [], 0
    for i in sorted(range(len(texts)), key=lambda i: -fused[i]):
        n = len(texts[i].split())
        if words + n <= max_words:
            picked.append(i)
            words += n
    picked.sort()
    return "\n\n".join(f"[{chunks[i][0]}] {chunks[i][1]}" for i in picked)


def urls_for(qs, backend="serper", k=5, max_pages=8):
    S = W2 if backend == "serper" else W
    urls = []
    for q in qs:
        for u in S.search(q, k):
            if u not in urls:
                urls.append(u)
    return urls[:max_pages]


def build(items, queries_of=lambda e: [e["question"]], backend="serper", k=5, max_pages=8, workers=8):
    def one(e):
        qs = queries_of(e)
        urls = urls_for(qs, backend, k, max_pages)
        p, kept, dropped = web_passage(e["question"], urls)
        return e["id"], {"queries": qs, "urls": urls, "kept": kept, "dropped_contaminated": dropped, "passage": p}
    with ThreadPoolExecutor(workers) as ex:
        return dict(ex.map(one, items))
