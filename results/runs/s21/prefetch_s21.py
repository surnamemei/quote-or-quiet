"""Prefetch raw DuckDuckGo evidence for S21 (no gold, no model, no grading; prints counts only), as was done for FRESH-5:
DEV slices first (design data), then the sealed TEST samples. Query = the question alone, up to 8 URLs, the first 8 pages fetched
(vkg.websearch caches both; the contamination guard applies at passage-build time). DuckDuckGo at one search per 5 s (10 s until 2026-11-07 18:3x; changed at the user's request)
(vkg/websearch.py); bot checks are never bypassed: after 5 consecutive failures the script stops. Idle CPU priority.
usage: python -B results/runs/s21/prefetch_s21.py"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"F:\Projects\AI hallucinations")
sys.path.insert(0, str(ROOT))
try:
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
except Exception:
    pass
from vkg import evidence_fast as E, websearch as W  # noqa: E402

S21 = ROOT / "results/runs/s21"
FAIL = [0]


def one(e):
    if FAIL[0] >= 5:
        return e["id"], {"error": "stopped after repeated search failures"}
    try:
        urls = E.urls_for([e["question"]], "ddg", 8, 8)
        FAIL[0] = 0
    except Exception as x:
        FAIL[0] += 1
        return e["id"], {"error": str(x)[:200]}
    for u in urls:
        try:
            W.fetch(u)
        except Exception:
            pass
    return e["id"], {"urls": urls}


# csqa_dev: the Kimi session's Chinese SimpleQA DEV slice (questions only; meta.source_urls never used), added at its request
SRC = {"csqa_dev": Path(r"E:\Models\halluc_runs\s21c\csqa_dev.json")}
for name in ("popqa_dev", "mintaka_dev", "csqa_dev", "popqa_test", "mintaka_test"):
    dest = S21 / f"prefetch_ddg_{name}.json"
    if dest.exists():
        continue
    items = [{"id": e["id"], "question": e["question"]} for e in json.load(open(SRC.get(name, S21 / f"{name}.json"), encoding="utf-8"))]
    t = time.time()
    with ThreadPoolExecutor(4) as ex:
        out = dict(ex.map(one, items))
    dest.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    err = sum("error" in v for v in out.values())
    print(f"{name}: {len(out)} items, {err} errors, mean urls {sum(len(v.get('urls', [])) for v in out.values()) / len(out):.1f}, {time.time() - t:.0f}s", flush=True)
    if FAIL[0] >= 5:
        print("STOPPED: repeated DuckDuckGo failures (possible bot check); not retrying", flush=True)
        break
print("PREFETCH_DONE", flush=True)
