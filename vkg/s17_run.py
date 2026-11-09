"""S17 pipeline (three independent evidence sources; designed on DEV, see results/runs/s16/). For an item set:
  1. evidence  web  : Serper(question), first 8 unblocked pages, vkg.s13_run.web_passage logic          (vkg/evidence_fast.build)
               wiki : local FineWiki (Aug 2025) top-5 titles for the question, retrieval2.passage logic     (evidence_fast.wiki_build)
               combo: the kept web pages + the wiki pages in one 1500-word passage                      (evidence_fast.combo_passage)
     Embeddings: official HF Qwen3-Embedding-0.6B on the pod (VKG_EMB=hf). Contamination guard as in S13 on every page.
  2. generate     : Qwen3-4B-Instruct-2507 on the pod, batched greedy, 40 tokens, PLAIN and CAUTIOUS prompts on each passage
                    -> {web,wiki,combo}_{plain,cautious}
  3. judge        : grader 6.1's judge (qwen3.8-27b e0a7cdbef002, pod), labels appended to results/grader5/judge_grades.jsonl
No gold is used before step 3. Every stage is saved and resumable.
Run: VKG_EMB=hf python -B -m vkg.s17_run <set>     sets: fresh (200, used before) | fresh3, fresh4 (1000 each, sealed; S18)  -> results/runs/s17/<set>_outputs.jsonl"""
import json
import os
import sys
import time

from . import evidence_fast as E
from . import pod
from .lite import CAUTIOUS, PLAIN, parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# S19 (docs/S19_DESIGN.md): VKG_WEB=ddg swaps the web backend to DuckDuckGo (vkg/websearch.py) and writes to results/runs/s19;
# everything else (k = 8 results, 8 pages, wiki, combo, prompts, generation, judge) is unchanged. Default stays Serper / s17.
WEB = os.environ.get("VKG_WEB", "serper")
OUT = ROOT / "results" / "runs" / ("s19" if WEB == "ddg" else "s17")
SRC = ("web", "wiki", "combo")


def items(name):
    if name == "fresh":
        return [{"id": e["id"], "question": e["question"], "gold": e["gold"]}
                for e in json.load(open(ROOT / "results" / "runs" / "s8" / "fresh_items.json", encoding="utf-8"))]
    if name == "dev":
        return [{"id": e["id"], "question": e["question"], "gold": e["gold"]}
                for e in json.load(open(ROOT / "results" / "runs" / "s6b" / "eval_items.json", encoding="utf-8")) if e["suite"] == "simpleqa_E"]
    if name in ("fresh3", "fresh4", "fresh5"):
        return json.load(open(ROOT / "results" / "runs" / name / "items.json", encoding="utf-8"))
    if name in ("popqa_dev", "mintaka_dev", "popqa_test", "mintaka_test"):   # S21 sets (results/runs/s21/seal.py), added 2026-11-07
        return json.load(open(ROOT / "results" / "runs" / "s21" / f"{name}.json", encoding="utf-8"))
    raise KeyError(name)


def log(name, m):
    print(m, flush=True)
    with open(OUT / f"{name}.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def stage(path, fn):
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    v = fn()
    tmp = path.with_suffix(".tmp")
    json.dump(v, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, path)
    return v


def main():
    assert os.environ.get("VKG_EMB") == "hf", "run with VKG_EMB=hf (the embedder S17 was designed with)"
    name = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    its = items(name)
    nogold = [{"id": e["id"], "question": e["question"]} for e in its]           # evidence and generation never see gold
    t = time.time()
    def web_ev():
        if WEB == "ddg":      # keyless; one search per 10 s inside vkg/websearch.py; mostly served from the S19 prefetch cache
            return E.build(nogold, backend="ddg", k=8, max_pages=8, workers=4)
        # Serper budget rule (pre-registered in docs/S18_PROTOCOL.md): if the account balance is smaller than the number of
        # uncached question searches, the LAST items in file order get no web search (empty web evidence, flagged); they stay
        # in n. Nothing else changes.
        import requests
        from . import websearch2 as W2
        uncached = [e for e in nogold if not (W2.CACHE / f"s_{W2._key(e['question'])}.json").exists()]
        bal = requests.get("https://google.serper.dev/account", headers={"X-API-KEY": W2._api_key()}, timeout=30).json()["balance"]
        skip = {e["id"] for e in uncached[max(0, bal - 5):]} if len(uncached) > bal - 5 else set()   # keep 5 credits spare for retries
        log(name, f"serper: {len(uncached)} uncached searches, balance {bal}, skipped for budget {len(skip)}")
        ev = E.build([e for e in nogold if e["id"] not in skip], backend="serper", k=8, max_pages=8, workers=8)
        for i in skip:
            ev[i] = {"queries": [], "urls": [], "kept": [], "dropped_contaminated": [], "passage": "", "skipped": "serper budget"}
        return ev
    web = stage(OUT / f"{name}_ev_web.json", web_ev)
    log(name, f"evidence web done ({time.time() - t:.0f}s)")
    wiki = stage(OUT / f"{name}_ev_wiki.json", lambda: E.wiki_build(nogold, workers=8))
    log(name, f"evidence wiki done ({time.time() - t:.0f}s)")

    def combo():
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(8) as ex:
            return dict(ex.map(lambda e: (e["id"], {"passage": E.combo_passage(e["question"], web[e["id"]]["kept"], wiki[e["id"]]["titles"])}), nogold))
    cmb = stage(OUT / f"{name}_ev_combo.json", combo)
    log(name, f"evidence combo done ({time.time() - t:.0f}s)")
    ev = {"web": web, "wiki": wiki, "combo": cmb}
    gens = {}
    for s in SRC:
        has = [e for e in nogold if ev[s][e["id"]]["passage"]]
        for key, tmpl in (("plain", PLAIN), ("cautious", CAUTIOUS)):
            def run(has=has, s=s, tmpl=tmpl):
                outs = pod.gen([tmpl.format(p=ev[s][e["id"]]["passage"], q=e["question"]) for e in has], 40)
                return {e["id"]: [parse(o[0]), o[1], o[2]] for e, o in zip(has, outs)}
            gens[f"{s}_{key}"] = stage(OUT / f"{name}_gen_{s}_{key}.json", run)
            log(name, f"gen {s}_{key}: {len(has)} items ({time.time() - t:.0f}s)")
    pod.unload_gen()
    rows = []
    for e in its:
        r = {"set": name, "id": e["id"], "stratum": e.get("stratum"), "question": e["question"], "gold": e["gold"],
             "web_urls": web[e["id"]]["urls"], "web_kept": web[e["id"]]["kept"], "web_dropped": web[e["id"]]["dropped_contaminated"],
             "wiki_titles": wiki[e["id"]]["titles"], "prompt_tokens": 0, "gen_tokens": 0}
        for k, g in gens.items():
            v = g.get(e["id"])
            r[k] = v[0] if v else None
            if v:
                r["prompt_tokens"] += v[1]
                r["gen_tokens"] += v[2]
        rows.append(r)
    pod.wait_free(24, log=lambda m: log(name, m))
    J = ROOT / "results" / "grader5" / "judge_grades.jsonl"
    done = {(x["question"], x["gold"], x["answer"]) for x in map(json.loads, open(J, encoding="utf-8"))}
    todo = []
    for r in rows:
        for k in gens:
            t3 = (r["question"], r["gold"][0], r[k])
            if r[k] is not None and t3 not in done and t3 not in todo:
                todo.append(t3)
    with open(J, "a", encoding="utf-8") as f:
        for s in range(0, len(todo), 64):
            part = todo[s:s + 64]
            for (q, g, a), gr in zip(part, pod.judge_many(part, 4)):
                f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": gr}, ensure_ascii=False) + "\n")
            f.flush()
    pod.unload_judge()
    log(name, f"judge: {len(todo)} new labels ({time.time() - t:.0f}s)")
    with open(OUT / f"{name}_outputs.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(name, f"DONE {len(rows)} items ({time.time() - t:.0f}s)")


if __name__ == "__main__":
    main()
