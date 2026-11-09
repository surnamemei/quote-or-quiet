"""FRESH-2: the untouched final test set (docs/CHECKPOINTS.md P0.5). 300 SimpleQA Verified questions drawn from the 500 never
used by any earlier sample (the seed-3000 draw of 500 covers every DEV, FRESH and freeze-5/6/7 question): Random(4000).sample of
the remaining indices. Retrieval identical to FRESH (variant E: 27B-written queries + baseline search, 10 pages, BM25+dense
fusion, 1500 words), so systems are comparable with all earlier numbers. No gold information is used. Nobody looks at the items
or any output until the final pre-registered confirmation run.
Build (system python; Ollama 27B + embeddings + Wikipedia), polite: python -B -m vkg.fresh2   -> results/runs/fresh2/items.json"""
import json
import os
import pickle
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "runs" / "fresh2"


def main():
    import psutil
    import requests
    from .s8_wait import free_vram
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    while free_vram() < 22000 or psutil.virtual_memory().available / 2**30 < 10:
        time.sleep(120)
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    from datasets import load_dataset
    from . import retrieval2 as R2
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    used = set(random.Random(3000).sample(range(len(d)), 500))
    rest = [i for i in range(len(d)) if i not in used]
    pick = random.Random(4000).sample(rest, 300)
    assert not (set(pick) & used)
    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for k, i in enumerate(pick, 1):
        q = d[i]["problem"]
        titles = R2.titles_for(q, 10, "qwen3.8-27b")
        psg = R2.passage(q, titles, 1500) or "(no text was retrieved)"
        items.append({"suite": "simpleqa_F2", "id": f"sqa-{d[i]['original_index']}", "kind": "answerable", "question": q, "passage": psg,
                      "gold": [d[i]["answer"]], "titles": titles, "topic": d[i]["topic"], "answer_type": d[i]["answer_type"]})
        if k % 25 == 0:
            json.dump(items, open(OUT / "items.partial.json", "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  built {k}/300", flush=True)
    tmp = R2.EMB_FILE.with_suffix(".tmp")
    pickle.dump(dict(R2._EMB), open(tmp, "wb"))
    os.replace(tmp, R2.EMB_FILE)
    json.dump(items, open(OUT / "items.json", "w", encoding="utf-8"), ensure_ascii=False)
    for m in ("qwen3.8-27b:latest", "qwen3-embedding:0.6b"):
        requests.post("http://localhost:11434/api/generate", json={"model": m, "keep_alive": 0}, timeout=60)
    print("FRESH-2 items", len(items), "empty passages", sum(it["passage"] == "(no text was retrieved)" for it in items))


if __name__ == "__main__":
    main()
