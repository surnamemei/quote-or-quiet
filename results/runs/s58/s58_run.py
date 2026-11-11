"""S40 copy of results/runs/s29/s29_run.py for the S40 sealed questions (set name w3; outputs in results/runs/s58/run_<search>). Original docstring follows.
S29 run of the FROZEN S19 pipeline (generation limit 40 tokens, original parser, three evidence sources, Phi-4 veto) on the new Wikidata question sets, with the web source selectable:
  S29_SEARCH=fsm : URL lists from the free-search-mcp pool, prefetched into results/cache/web_fsm (see fsm_prefetch.py); pages fetched live into the same cache
  S29_SEARCH=ddg : DuckDuckGo through vkg/websearch.py (default cache), as in the certified S19 run
Set names: wdp = pilot (144 questions), wd = sealed (3,959). Outputs in results/runs/s29/run_<search>/. Nothing in vkg/ is edited; items, output directory and the cache path are patched at run time.
usage: S29_SEARCH=fsm|ddg VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 python -B results/runs/s29/s29_run.py <wdp|wd> <gen|phi4|alias>"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
SEARCH = os.environ["S29_SEARCH"]
OUT = ROOT / "results/runs/s58" / f"run_{SEARCH}"
OUT.mkdir(parents=True, exist_ok=True)


def items(name):
    rows = [json.loads(l) for l in open(ROOT / "results/runs/s58/sealed/items.jsonl", encoding="utf-8")]
    return [{"id": r["id"], "question": r["q"], "gold": r["gold"], "stratum": r["relation"], "meta": {"stratum": r["stratum"], "qid": r["qid"]}} for r in rows]


def patch():
    from vkg import s17_run as R, websearch as W
    R.items = items
    R.OUT = OUT
    if SEARCH == "fsm":
        W.CACHE = ROOT / "results/cache/web_fsm"
        W.CACHE.mkdir(parents=True, exist_ok=True)
    return R


def gen(name):
    R = patch()
    sys.argv = ["s17_run", name]
    R.main()


def phi4(name):
    sys.path.insert(0, str(ROOT / "results/runs/s20"))
    import no_retrieval2  # noqa: F401  (this stage does no retrieval; keeps the 37 GB embedding table out of RAM)
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
    from vkg.lite import CAUTIOUS, parse
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    patch()
    its = items(name)
    ev = json.load(open(OUT / f"{name}_ev_combo.json", encoding="utf-8"))

    def one(e):
        p = ev.get(e["id"], {}).get("passage")
        rec = {"id": e["id"], "answer": None}
        if p:
            raw = chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=p, q=e["question"])}], temperature=0.0, seed=0,
                       max_tokens=40, think=False, json_mode=False, num_ctx=24576)
            rec["answer"], rec["raw"] = parse(raw), raw       # frozen: 40 tokens, original parser
        return rec
    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, its))
    with open(OUT / f"{name}_phi4.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("phi4", name, len(rows), flush=True)


def alias(name):
    sys.path.insert(0, str(ROOT / "results/runs/s20"))
    import no_retrieval2  # noqa: F401  (this stage does no retrieval; keeps the 37 GB embedding table out of RAM)
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
    from vkg import pod
    from vkg.s21_judge import needed, J
    keys = [f"{s}_{k}" for s in ("web", "wiki", "combo") for k in ("plain", "cautious")]
    todo = []
    for r in map(json.loads, open(OUT / f"{name}_outputs.jsonl", encoding="utf-8")):
        for k in keys:
            for t in needed(r["question"], r["gold"], r.get(k)):
                if t not in todo:
                    todo.append(t)
    print("alias labels", name, len(todo), flush=True)
    with open(ROOT / "results/grader5/judge_grades.jsonl", "a", encoding="utf-8") as f:
        for s in range(0, len(todo), 32):
            part = todo[s:s + 32]
            for (q, g, a), gr in zip(part, pod.judge_many(part, 2)):
                f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": gr}, ensure_ascii=False) + "\n")
                J[(q, g, a)] = gr
            f.flush()
    pod.unload_judge()


if __name__ == "__main__":
    {"gen": gen, "phi4": phi4, "alias": alias}[sys.argv[2]](sys.argv[1])
