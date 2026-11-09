"""S13: open-web search on abstain for the small model (user direction 2026-11-06: no API key, search online).
Only round-0 abstentions of the 4B cautious prompt (FRESH 78, DEV 120) are touched; one web round:
  queries = the question text + the 4B's own first two queries (S11 prompt) -> DuckDuckGo HTML results (vkg/websearch.py), blocked
  benchmark/code domains removed -> up to 8 pages fetched -> pages with the question verbatim or mentioning SimpleQA dropped
  (contamination guard) -> 120-word chunks ranked by BM25 + dense fusion (as retrieval2) -> 1500 words, chunks labelled [domain].
  acceptance as S12: cautious answer, confirmed by the plain prompt on the same passage; also logs the unfiltered cautious answer.
No gold information is used. Run (venv_gpu, via vkg.s13_wait): python -B -m vkg.s13_run -> results/runs/s13/outputs.jsonl"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from . import retrieval as R
from . import retrieval2 as R2
from . import websearch as W
from .probe_gen import ROOT, parse
from .s11_run import QPROMPT, Small, items, queries
from .s12_run import agree
from .s6b_run import CAUTIOUS, PLAIN
from .s8_eval import non_answer

OUT = ROOT / "results" / "runs" / "s13"
MAX_PAGES = 8


def web_passage(question, urls, max_words=1500):
    with ThreadPoolExecutor(4) as ex:
        texts = list(ex.map(W.fetch, urls))
    kept, dropped = [], []
    for u, t in zip(urls, texts):
        if not t:
            continue
        (dropped if W.contaminated(t, question) else kept).append((u, t))
    chunks = []
    for u, t in kept:
        dom = urlparse(u).netloc.replace("www.", "")
        for c in R._chunks(t, 120):
            chunks.append((dom, c))
    if not chunks:
        return "", [u for u, _ in kept], [u for u, _ in dropped]
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
    return "\n\n".join(f"[{chunks[i][0]}] {chunks[i][1]}" for i in picked), [u for u, _ in kept], [u for u, _ in dropped]


def main():
    import os
    import pickle
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    sm = Small()
    path = OUT / "outputs.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for k, e in enumerate(items(), 1):
            if e["id"] in done:
                continue
            rec = {"set": e["set"], "id": e["id"], "question": e["question"], "gold": e["gold"], "round0": e["round0"], "rounds": [],
                   "final": e["round0"], "final_nofilter": e["round0"], "gen_tokens": 0, "prompt_tokens": 0, "pages_fetched": 0, "sec": 0.0}
            if non_answer(e["round0"]):
                t0 = time.time()
                qtxt, pi, gi = sm.gen(QPROMPT.format(q=e["question"]))
                rec["prompt_tokens"] += pi
                rec["gen_tokens"] += gi
                qs = [e["question"]] + queries(qtxt)[:2]
                urls = []
                for q in qs:
                    for u in W.search(q, 5):
                        if u not in urls:
                            urls.append(u)
                urls = urls[:MAX_PAGES]
                p, kept, dropped = web_passage(e["question"], urls)
                rec["pages_fetched"] = len(urls)
                rnd = {"round": 1, "queries": qs, "urls": urls, "kept": kept, "dropped_contaminated": dropped, "passage": p, "cautious": None, "plain": None}
                if p:
                    c, pi, gi = sm.gen(CAUTIOUS.format(p=p, q=e["question"]), 40)
                    rec["prompt_tokens"] += pi
                    rec["gen_tokens"] += gi
                    rnd["cautious"] = parse(c)
                    if not non_answer(rnd["cautious"]):
                        rec["final_nofilter"] = rnd["cautious"]
                        pl, pi, gi = sm.gen(PLAIN.format(p=p, q=e["question"]), 40)
                        rec["prompt_tokens"] += pi
                        rec["gen_tokens"] += gi
                        rnd["plain"] = parse(pl)
                        if agree(rnd["cautious"], rnd["plain"]):
                            rec["final"] = rnd["cautious"]
                rec["rounds"].append(rnd)
                rec["sec"] = round(time.time() - t0, 1)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if k % 25 == 0:
                print(f"  {k}/500", flush=True)
    tmp = R2.EMB_FILE.with_suffix(".tmp")
    pickle.dump(dict(R2._EMB), open(tmp, "wb"))
    os.replace(tmp, R2.EMB_FILE)
    print("done")


if __name__ == "__main__":
    main()
