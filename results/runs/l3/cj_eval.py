"""Validate the conditional-truth judge on DEV: agreement with hand labels (system items) and false credit on injected
negatives. Pre-set bars (stated before the judge ran, docs/L3_QUALIFIED_DESIGN.md section 9): false credit (SUPPORTED on a
false item) at most 1% on easy and 5% on hard negatives; on system items, SUPPORTED on hand-labelled false items at most 1 in 10,
and NOT_SUPPORTED on hand-labelled true items at most 1 in 10."""
import json
from collections import Counter
from pathlib import Path
from scipy.stats import beta
R = Path(__file__).resolve().parent
import sys
JF = sys.argv[1] if len(sys.argv) > 1 else "cj_items_dev_judged.jsonl"
LF = sys.argv[2] if len(sys.argv) > 2 else "cj_labels_dev.json"
J = [json.loads(l) for l in open(R / JF, encoding="utf-8")]
L = {x["line"]: x["label"] for x in json.load(open(R / LF, encoding="utf-8"))}
tab = Counter()
bad = []
for i, x in enumerate(J):
    lab = L[i]
    tab[(x["kind"], lab, x["cj"])] += 1
    if (lab == "false" and x["cj"] == "SUPPORTED") or (lab == "true" and x["cj"] != "SUPPORTED"):
        bad.append(f"- [{x['kind']}] {x['question'][:60]} | E={x['sense'][:30]} | A={x['answer'][:30]} | label {lab} | judge {x['cj']}")
def up(k, n): return beta.ppf(0.95, k + 1, n - k) if n and k < n else 1.0
lines = ["# Conditional-truth judge on DEV (results/runs/l3/cj_eval.py)", "", "| kind | label | SUPPORTED | NOT_SUPPORTED | UNCLEAR |", "|---|---|---|---|---|"]
for kind in ("system", "neg_easy", "neg_hard"):
    for lab in ("true", "false", "unclear"):
        n = sum(tab[(kind, lab, v)] for v in ("SUPPORTED", "NOT_SUPPORTED", "UNCLEAR"))
        if n:
            lines.append(f"| {kind} | {lab} | {tab[(kind, lab, 'SUPPORTED')]} | {tab[(kind, lab, 'NOT_SUPPORTED')]} | {tab[(kind, lab, 'UNCLEAR')]} |")
for kind in ("neg_easy", "neg_hard"):
    n = sum(v for (k, lab, _), v in tab.items() if k == kind and lab == "false")
    k = tab[(kind, "false", "SUPPORTED")]
    lines.append(f"\n{kind}: false credit {k}/{n} (95% upper {up(k, n):.3f})")
lines += ["", "Disagreements:", ""] + bad
(R / ("cj_eval_" + Path(JF).stem + ".md")).write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
