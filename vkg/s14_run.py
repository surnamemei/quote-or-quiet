"""S14: web corroboration for every item (Qwen3-4B), plus the equal-budget "plain + web" baseline.
For all 500 FRESH+DEV items: web passage exactly as S13 (question + the 4B's first two S11 queries -> DuckDuckGo -> up to 8 pages ->
contamination guard -> BM25+dense 1500 words), then the cautious and the plain prompt on that web passage.
Systems are formed in vkg/s14_eval.py from: round0 (cautious on the Wikipedia passage), web_cautious, web_plain.
If web search is blocked (bot check), the run waits 30 min and retries the same item; it never solves a CAPTCHA.
No gold is used. Run (venv_gpu, via vkg.s14_wait): python -B -m vkg.s14_run -> results/runs/s14/outputs.jsonl"""
import json
import time

from . import retrieval2 as R2
from . import websearch as W
from .probe_gen import ROOT, parse
from .s11_run import QPROMPT, Small, items, queries
from .s13_run import MAX_PAGES, web_passage
from .s6b_run import CAUTIOUS, PLAIN

OUT = ROOT / "results" / "runs" / "s14"


def urls_for(qs):
    while True:
        try:
            urls = []
            for q in qs:
                for u in W.search(q, 5):
                    if u not in urls:
                        urls.append(u)
            return urls[:MAX_PAGES]
        except RuntimeError as e:
            print(f"  search blocked ({e}); waiting 30 min", flush=True)
            time.sleep(1800)


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
            t0 = time.time()
            rec = {"set": e["set"], "id": e["id"], "question": e["question"], "gold": e["gold"], "round0": e["round0"],
                   "web_cautious": None, "web_plain": None, "gen_tokens": 0, "prompt_tokens": 0}
            qtxt, pi, gi = sm.gen(QPROMPT.format(q=e["question"]))
            rec["prompt_tokens"] += pi
            rec["gen_tokens"] += gi
            qs = [e["question"]] + queries(qtxt)[:2]
            urls = urls_for(qs)
            p, kept, dropped = web_passage(e["question"], urls)
            rec.update(queries=qs, urls=urls, kept=kept, dropped_contaminated=dropped, passage=p)
            if p:
                for key, tmpl in (("web_cautious", CAUTIOUS), ("web_plain", PLAIN)):
                    t, pi, gi = sm.gen(tmpl.format(p=p, q=e["question"]), 40)
                    rec[key] = parse(t)
                    rec["prompt_tokens"] += pi
                    rec["gen_tokens"] += gi
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
