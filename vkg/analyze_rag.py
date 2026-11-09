"""Evidence coverage and paired comparison for the retrieval runs (no LLM involved).
python -m vkg.analyze_rag            -> coverage of the gold answer in the passages (needs only the cache)
python -m vkg.analyze_rag --results  -> also joins model outcomes (results/runs/openworld_*) by question id
Coverage = the gold string appears in the passage under the strict matcher / the lenient token matcher.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from . import tasks
from .grade_open import grade, lenient
from .tasks import matches

ROOT = Path(__file__).resolve().parent.parent


def coverage(items):
    strict = sum(matches(it.gold, it.passage) for it in items)
    len_ = sum(strict_or_len(it) for it in items)
    return strict, len_


def strict_or_len(it):
    return matches(it.gold, it.passage) or lenient(it.gold[0], it.passage)


def main(with_results):
    n, seed = 300, 3000
    ev = {"search": tasks.simpleqa_rag(n, seed, "search"), "oracle": tasks.simpleqa_rag(n, seed, "oracle")}
    cov = {}
    for mode, items in ev.items():
        s, l = coverage(items)
        empty = sum(i.passage.startswith("(no text") for i in items)
        print(f"{mode}: n={len(items)} passages with no text={empty}; gold answer present in passage: strict {s} ({s/len(items):.3f}), lenient {l} ({l/len(items):.3f})")
        cov[mode] = {it.id: strict_or_len(it) for it in items}
    common = set(cov["search"]) & set(cov["oracle"])
    print(f"on the {len(common)} questions that have an oracle page: search coverage {sum(cov['search'][i] for i in common)/len(common):.3f}, "
          f"oracle coverage {sum(cov['oracle'][i] for i in common)/len(common):.3f}")
    if not with_results:
        return
    for mode, tag in (("search", "simpleqa_rag"), ("oracle", "simpleqa_oracle")):
        f = ROOT / "results" / "runs" / f"openworld_{tag}_qwen3.8-27b_s3000_n{len(ev[mode])}.jsonl"
        if not f.exists():
            print(mode, "results not found", f.name)
            continue
        rows = [json.loads(l) for l in open(f, encoding="utf-8")]
        by = defaultdict(list)
        for r in rows:
            r["g"] = grade(r)
            by[r["system"]].append(r)
        print(f"\n{mode}: outcome split by whether the evidence contained the answer")
        print("| system | evidence has answer: correct | abstain | wrong | evidence lacks answer: correct | abstain | wrong |")
        print("|---|---|---|---|---|---|---|")
        for s, x in by.items():
            row = []
            for has in (True, False):
                sub = [r for r in x if cov[mode].get(r["id"]) == has]
                c = sum(r["g"] in ("correct_strict", "correct_lenient") for r in sub)
                a = sum(r["g"] == "abstain" for r in sub)
                w = sum(r["g"] == "wrong" for r in sub)
                row += [f"{c}/{len(sub)}", f"{a}", f"{w}"]
            print(f"| {s} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    main("--results" in sys.argv)
