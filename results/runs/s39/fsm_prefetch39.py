"""Prefetch free-search-mcp results for a question set into a separate URL cache (results/cache/web_fsm, the same file format as vkg/websearch.py: s_<sha256(query)>.json = list of URLs),
so the frozen pipeline can run with this search pool without touching the DuckDuckGo cache. No gold, no model, counts only. Keyless pool, no browser, one query at a time, 2 s apart, idle priority.
F:/Projects/tools/fsm_venv/Scripts/python.exe -B results/runs/s29/fsm_prefetch.py pilot|sealed"""
import asyncio, ctypes, hashlib, json, sys, time
from pathlib import Path
from urllib.parse import urlparse
ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)
ROOT = Path(r"F:\Projects\AI hallucinations")
CACHE = ROOT / "results/cache/web_fsm"; CACHE.mkdir(parents=True, exist_ok=True)
BLOCK = ("huggingface.co", "github.com", "githubusercontent.com", "gitlab.com", "kaggle.com", "arxiv.org", "paperswithcode.com",
         "openai.com", "openreview.net", "aclanthology.org", "semanticscholar.org", "researchgate.net", "scale.com", "llm-stats.com")   # as in vkg/websearch.py
from search_mcp import server


def blocked(u):
    h = urlparse(u).netloc.lower()
    return any(h == b or h.endswith("." + b) for b in BLOCK)


async def main(which):
    items = [json.loads(l) for l in open(ROOT / "results/runs/s39" / which / "items.jsonl", encoding="utf-8")]
    n_ok = n_err = 0; t0 = time.time(); fails = 0
    for e in items:
        if False:    # dropped after the pilot adjudication
            continue
        q = e["q"]; f = CACHE / f"s_{hashlib.sha256(q.encode('utf-8')).hexdigest()}.json"
        if f.exists():
            continue
        try:
            res = await server.search(q, max_results=10, use_cache=False, format="json")
            urls = []
            for r in res.get("results", []):
                u = r["url"]
                if u.startswith("http") and not blocked(u) and u not in urls:
                    urls.append(u)
            if not urls:
                raise RuntimeError("empty")
            f.write_text(json.dumps(urls[:8]), encoding="utf-8"); n_ok += 1; fails = 0
        except Exception as ex:
            n_err += 1; fails += 1
            print("error", e["id"], str(ex)[:80], flush=True)
            if fails >= 5:
                print("stopped after repeated failures (bot checks are never bypassed)"); break
        if (n_ok + n_err) % 25 == 0:
            print(n_ok, n_err, f"{time.time()-t0:.0f}s", flush=True)
        await asyncio.sleep(2)
    print("done", which, "ok", n_ok, "errors", n_err, f"{time.time()-t0:.0f}s")

asyncio.run(main(sys.argv[1]))
