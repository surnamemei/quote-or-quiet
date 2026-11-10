"""S54: how much do the headline 'misleading' numbers depend on the rule 'both reviewers say not'? Per source: Cohen's kappa between the two reviewers on the 3-class label, the share 'not' for both,
for either, and 'states' for both. Also writes the public subset (Wikipedia-derived rows without benchmark questions) to data/quote_sufficiency_public.jsonl. python -B results/runs/s54/reviewer_robustness.py"""
import json
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
rows = [json.loads(l) for l in open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8")]
C = ["states", "incomplete", "not"]


def kappa(pairs):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    pa = Counter(a for a, _ in pairs); pb = Counter(b for _, b in pairs)
    pe = sum(pa[c] * pb[c] for c in C) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


NAMES = {"e6": "S29 displayed quotes (E6)", "e7": "S29 W1 witnesses (E7)", "s43": "bios, value-string witness", "e11": "bios, sentence witness", "w4": "bios, rule W4, closed-book (sealed)",
         "r4": "bios, from the page (design)", "f5": "bios, from the page (sealed)", "e9": "ambiguous names", "s48": "open questions, FRESH-5", "web": "web pages"}
out = ["# S54: sensitivity of the 'misleading' counts to the two-reviewer rule", "",
       "| Source | rows | kappa (3 classes) | 'not' for both | 'not' for either | 'states' for both |", "|---|---|---|---|---|---|"]
for s, name in NAMES.items():
    rs = [r for r in rows if r["src"] == s]
    n = len(rs); pairs = [tuple(r["labels"]) for r in rs]
    both = sum(a == b == "not" for a, b in pairs); either = sum("not" in p for p in pairs); st = sum(a == b == "states" for a, b in pairs)
    out.append(f"| {name} | {n} | {kappa(pairs):.2f} | {both} ({100*both/n:.1f}%) | {either} ({100*either/n:.1f}%) | {st} ({100*st/n:.1f}%) |")
allp = [tuple(r["labels"]) for r in rows]
out.append(f"| all | {len(rows)} | {kappa(allp):.2f} | {sum(a==b=='not' for a,b in allp)} | {sum('not' in p for p in allp)} | {sum(a==b=='states' for a,b in allp)} |")
(ROOT / "results/runs/s54/Reviewer_robustness.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
pub = [r for r in rows if r["src"] in ("s43", "e11", "w4", "r4", "f5", "e9")]
with open(ROOT / "data/quote_sufficiency_public.jsonl", "w", encoding="utf-8") as f:
    for r in pub:
        f.write(json.dumps({"set": r["src"], "question": r["question"], "answer": r["answer"], "page_title": r["title"], "quote": r["quote"], "labels": r["labels"]}, ensure_ascii=False) + "\n")
print("public rows", len(pub))
