"""Test free-search-mcp (installed in F:/Projects/tools/fsm_venv, keyless pool, no browser) against the DuckDuckGo results already cached for FRESH-5.
50 FRESH-5 questions (seed 7); one query at a time, 2 s apart. Compares result counts, share of en.wikipedia.org URLs, URL overlap with the cached DuckDuckGo list, latency,
errors, and how often a gold answer string appears in a returned snippet. Run with the tools venv:  F:/Projects/tools/fsm_venv/Scripts/python.exe -B results/runs/s29/fsm_test.py"""
import asyncio, ctypes, json, random, re, statistics as st, sys, time
from pathlib import Path
ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)   # idle priority
ROOT = Path(r"F:\Projects\AI hallucinations")
items = json.load(open(ROOT / "results/runs/fresh5/items.json", encoding="utf-8"))
ddg = json.load(open(ROOT / "results/runs/s19/fresh5_ev_web.json", encoding="utf-8"))
rng = random.Random(7)
sample = rng.sample(items, 50)
from search_mcp import server


def norm_url(u):
    u = re.sub(r"^https?://(www\.)?", "", u.strip().lower()).split("#")[0].rstrip("/")
    return u


async def main():
    rows = []
    for k, e in enumerate(sample):
        t = time.time(); res = None; err = None
        try:
            res = await server.search(e["question"], max_results=8, use_cache=False, format="json")
        except Exception as ex:
            err = str(ex)[:120]
        dt = time.time() - t
        urls, snips, errs = [], [], None
        if isinstance(res, dict):
            urls = [r["url"] for r in res.get("results", [])]
            snips = [r.get("snippet", "") for r in res.get("results", [])]
            errs = res.get("errors")
        d_urls = ddg.get(e["id"], {}).get("urls", [])[:8]
        gold = e["gold"] if isinstance(e["gold"], list) else [e["gold"]]
        hit = any(g and g.casefold() in " ".join(snips).casefold() for g in gold)
        rows.append({"id": e["id"], "n": len(urls), "wiki": sum("en.wikipedia.org" in u for u in urls), "overlap": len({norm_url(u) for u in urls} & {norm_url(u) for u in d_urls}),
                     "n_ddg": len(d_urls), "wiki_ddg": sum("en.wikipedia.org" in u for u in d_urls), "sec": dt, "err": err, "errs": errs, "gold_in_snippet": hit})
        print(k, len(urls), f"{dt:.1f}s", err or "", flush=True)
        await asyncio.sleep(2)
    ok = [r for r in rows if r["n"] > 0]
    L = ["# free-search-mcp test on 50 FRESH-5 questions (keyless pool, no browser)", "",
         f"queries {len(rows)}, with results {len(ok)}, hard errors {sum(1 for r in rows if r['err'])}",
         f"mean results per query {st.mean(r['n'] for r in rows):.1f} (DuckDuckGo cached: {st.mean(r['n_ddg'] for r in rows):.1f})",
         f"queries with an en.wikipedia.org result: {sum(1 for r in rows if r['wiki'] > 0)} (DuckDuckGo cached: {sum(1 for r in rows if r['wiki_ddg'] > 0)})",
         f"mean URL overlap with the cached DuckDuckGo top 8: {st.mean(r['overlap'] for r in rows):.1f}",
         f"latency seconds, median {st.median(r['sec'] for r in rows):.1f}, p90 {sorted(r['sec'] for r in rows)[int(0.9*len(rows))]:.1f}, total {sum(r['sec'] for r in rows):.0f}",
         f"gold string in a returned snippet: {sum(1 for r in rows if r['gold_in_snippet'])} of {len(rows)}"]
    errc = {}
    for r in rows:
        for k_, v in (r["errs"] or {}).items():
            errc[k_] = errc.get(k_, 0) + 1
    L.append(f"engine errors by name: {errc}")
    (ROOT / "results/runs/s29/fsm_test.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))

asyncio.run(main())
