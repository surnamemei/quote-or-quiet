"""S8 fresh test set: SimpleQA Verified questions 301-500 of the seed-3000 sample (never used, never inspected), with the SAME
variant-E retrieval as the frozen 300 (27B-written queries + baseline search, 10 pages, BM25+dense fusion, 1500 words).
Stages:
  build : python -B -m vkg.s8_fresh build            (system python; needs Ollama qwen3.8-27b + embeddings + Wikipedia)
  big   : python -B -m vkg.s8_fresh big              (27B B1_abstain, B2_strict via the frozen systems.py)
  small : venv_gpu python -B -m vkg.s8_fresh small   (4B plain + cautious prompts from S6b)
No gold information is used in retrieval or generation. Outputs: results/runs/s8/.
"""
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKERS = int(os.environ.get("S8_WORKERS", "2"))     # 1 = lighter on the machine (only speed changes, not results)
OUT = ROOT / "results" / "runs" / "s8"
S6B_ITEMS = ROOT / "results" / "runs" / "s6b" / "eval_items.json"


def stage_build():
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    from datasets import load_dataset
    from . import retrieval2 as R2
    from concurrent.futures import ThreadPoolExecutor
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    idx = random.Random(3000).sample(range(len(d)), 500)          # same draw as tasks.simpleqa(500, 3000)
    old = [e["id"] for e in json.load(open(S6B_ITEMS, encoding="utf-8")) if e["suite"] == "simpleqa_E"]
    assert old == [f"sqa-{d[i]['original_index']}" for i in idx[:300]], "prefix property broken"
    fresh = idx[300:500]
    assert not ({f"sqa-{d[i]['original_index']}" for i in fresh} & set(old))
    OUT.mkdir(parents=True, exist_ok=True)

    def one(i):
        q = d[i]["problem"]
        titles = R2.titles_for(q, 10, "qwen3.8-27b")
        psg = R2.passage(q, titles, 1500) or "(no text was retrieved)"
        return {"suite": "simpleqa_F", "id": f"sqa-{d[i]['original_index']}", "kind": "answerable", "question": q, "passage": psg,
                "gold": [d[i]["answer"]], "titles": titles, "topic": d[i]["topic"], "answer_type": d[i]["answer_type"]}
    items = []
    with ThreadPoolExecutor(WORKERS) as ex:    # no cache save inside the loop: R2.save_cache() races with the worker threads
        for k, it in enumerate(ex.map(one, fresh), 1):
            items.append(it)
            if k % 10 == 0:
                print(f"  built {k}/200", flush=True)
                json.dump(items, open(OUT / "fresh_items.partial.json", "w", encoding="utf-8"), ensure_ascii=False)
    import pickle
    tmp = R2.EMB_FILE.with_suffix(".tmp")
    pickle.dump(dict(R2._EMB), open(tmp, "wb"))
    os.replace(tmp, R2.EMB_FILE)
    empty = sum(it["passage"] == "(no text was retrieved)" for it in items)
    json.dump(items, open(OUT / "fresh_items.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("fresh items", len(items), "empty passages", empty)


def _items():
    from .tasks import Item
    return [Item(e["id"], "sqa_hyb", "answerable", e["question"], passage=e["passage"], gold=e["gold"]) for e in json.load(open(OUT / "fresh_items.json", encoding="utf-8"))]


def stage_big():
    from .run import evaluate
    rows = evaluate("qwen3.8-27b", ["B1_abstain", "B2_strict"], _items(), WORKERS)
    (OUT / "fresh_27b.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print("27B rows", len(rows))


def stage_small():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from .s6b_run import MODEL, PLAIN, CAUTIOUS, gen
    ev = json.load(open(OUT / "fresh_items.json", encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    res = {"plain": gen(tok, m, ev, PLAIN), "cautious": gen(tok, m, ev, CAUTIOUS)}
    with open(OUT / "fresh_4b.jsonl", "w", encoding="utf-8") as f:
        for i, e in enumerate(ev):
            f.write(json.dumps({"id": e["id"], "question": e["question"], "gold": e["gold"], "plain": res["plain"][i], "cautious": res["cautious"][i]}, ensure_ascii=False) + "\n")
    print("4B rows", len(ev))


if __name__ == "__main__":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)      # never compete with the user's foreground work
    {"build": stage_build, "big": stage_big, "small": stage_small}[sys.argv[1]]()
