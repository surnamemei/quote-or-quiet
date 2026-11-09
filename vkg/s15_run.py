"""S15: final pre-registered confirmation on FRESH-2 (docs/S15_PROTOCOL.md). 300 SimpleQA Verified items never used or inspected.
Same pipeline as S8 + S14, nothing tuned on FRESH-2:
  1. Wikipedia passage = results/runs/fresh2/items.json (variant-E retrieval, built before any S12-S14 result existed).
  2. 4B plain and cautious on that passage, batched exactly as vkg.s8_fresh.stage_small (s6b gen, left padding, 40 tokens).
  3. Web passage for every item exactly as vkg.s14_run (question + 4B's first two S11 queries, DuckDuckGo, guard, 1500 words),
     then the cautious and plain prompts on it. Bot check -> wait 30 min and retry; never bypassed.
No gold is used. Run (venv_gpu, via vkg.s15_wait): python -B -m vkg.s15_run -> results/runs/s15/outputs.jsonl"""
import json
import time

from . import retrieval2 as R2
from .probe_gen import ROOT, parse
from .s11_run import QPROMPT, Small, queries
from .s13_run import web_passage
from .s14_run import urls_for
from .s6b_run import CAUTIOUS, PLAIN, gen

OUT = ROOT / "results" / "runs" / "s15"


def main():
    import os
    import pickle
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    ev = json.load(open(ROOT / "results" / "runs" / "fresh2" / "items.json", encoding="utf-8"))
    sm = Small()
    r0 = OUT / "round0.json"
    if not r0.exists():
        sm.tok.padding_side = "left"
        res = {"plain": gen(sm.tok, sm.m, ev, PLAIN), "cautious": gen(sm.tok, sm.m, ev, CAUTIOUS)}
        sm.tok.padding_side = "right"
        json.dump(res, open(r0, "w", encoding="utf-8"), ensure_ascii=False)
    res = json.load(open(r0, encoding="utf-8"))
    path = OUT / "outputs.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for k, e in enumerate(ev, 1):
            if e["id"] in done:
                continue
            t0 = time.time()
            rec = {"set": "fresh2", "id": e["id"], "question": e["question"], "gold": e["gold"],
                   "plain": res["plain"][k - 1], "round0": res["cautious"][k - 1], "web_cautious": None, "web_plain": None,
                   "gen_tokens": 0, "prompt_tokens": 0}
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
                print(f"  {k}/300", flush=True)
    tmp = R2.EMB_FILE.with_suffix(".tmp")
    pickle.dump(dict(R2._EMB), open(tmp, "wb"))
    os.replace(tmp, R2.EMB_FILE)
    print("done")


if __name__ == "__main__":
    main()
