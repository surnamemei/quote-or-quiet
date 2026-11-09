"""Dev measurement for ROADMAP S2: how often does the gold answer appear in the passage, per retrieval variant?
Dev questions = SimpleQA Verified minus the 300 test ids (first 300 of the seed-3000 sample); 150 drawn with seed 4000.
No answering model is involved except the query-rewrite step. Usage: python -m vkg.dev_retrieval [n]
"""
import os
import random
import sys
import time

from . import retrieval as R
from . import retrieval2 as R2
from .grade_open import lenient, repaired
from .tasks import matches

MODEL = "qwen3.8-27b"


def dev_items(n=150, seed=4000):
    os.environ.setdefault("HF_HOME", str(R.ROOT / "data" / "hf"))
    from datasets import load_dataset
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    test = set(random.Random(3000).sample(range(len(d)), 300))
    pool = [i for i in range(len(d)) if i not in test]
    idx = random.Random(seed).sample(pool, n)
    return [(i, d[i]["problem"], d[i]["answer"], d[i]["urls"]) for i in idx]


def has(gold, psg):
    return matches([gold], psg) or lenient(gold, psg) or repaired(gold, psg, hedge_check=False)   # repaired matcher added after the audit


def main(n):
    items = dev_items(n)
    variants = {
        "A baseline (k5 pages, BM25, 900w)": lambda q: R.build_passage(q, R.search(q)),
        "B bigger budget (k5, BM25, 1500w)": lambda q: R2.passage(q, R2.titles_for(q, 5), 1500, dense=False),
        "C more pages (k10, BM25, 1500w)": lambda q: R2.passage(q, R2.titles_for(q, 10, per_query=10), 1500, dense=False),
        "D hybrid (k5, BM25+dense, 1500w)": lambda q: R2.passage(q, R2.titles_for(q, 5), 1500),
        "E rewrite+hybrid (k10, 1500w)": lambda q: R2.passage(q, R2.titles_for(q, 10, MODEL), 1500),
    }
    print(f"dev questions: {len(items)} (disjoint from the 300 test ids)")
    for name, fn in variants.items():
        t0 = time.time()
        hit = words = 0
        for _, q, gold, _ in items:
            p = fn(q)
            hit += has(gold, p)
            words += len(p.split())
        R2.save_cache()
        print(f"{name:40s} gold in passage {hit}/{len(items)} = {hit/len(items):.3f}   mean words {words/len(items):.0f}   {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
