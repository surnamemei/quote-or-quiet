"""Build the blind adjudication sheet for the S29 pilot: every wrong release (union of both search pools) + gold-matching releases + injected-false decoys.
Seeded shuffle; the key (kind per row) is written separately and is not given to adjudicators. python -B adj_build.py"""
import csv, json, random
from pathlib import Path
D = Path(__file__).parent
rel = {}
for s in ("fsm", "ddg"):
    for r in map(json.loads, open(D / f"run_{s}/wdp_releases.jsonl", encoding="utf-8")):
        rel.setdefault(r["id"], r)
wrong = [r for r in rel.values() if r["grade"] is False]
right = [r for r in rel.values() if r["grade"] is True]
rng = random.Random(2911)
rng.shuffle(right)
n_dec = 12
dec_src, keep = right[:n_dec], right[n_dec:]
decoys = []
for r in dec_src:
    g = r["gold"][0]
    if r["relation"] in ("birth_year", "death_year", "founded"):
        a = str(int(g) + rng.choice([-3, -2, -1, 1, 2, 3]))
    else:
        others = [x["answer"] for x in right if x["relation"] == r["relation"] and x["answer"].casefold() != r["answer"].casefold()]
        a = rng.choice(others)
    decoys.append({**r, "answer": a})
rows = [(r, "system_wrong") for r in wrong] + [(r, "system_right") for r in keep[:24]] + [(r, "decoy_injected_false") for r in decoys]
rng.shuffle(rows)
with open(D / "adj/S29_pilot_sheet_blank.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["row", "question", "gold", "answer", "verdict (gold wrong / answer wrong / both acceptable / ambiguous question / cannot tell)", "source_url", "verbatim_quote", "note"])
    for i, (r, k) in enumerate(rows, 1):
        w.writerow([i, r["question"], " | ".join(r["gold"]), r["answer"], "", "", "", ""])
json.dump([{"row": i, "kind": k, "id": r["id"]} for i, (r, k) in enumerate(rows, 1)], open(D / "adj/S29_pilot_key.json", "w"), indent=1)
from collections import Counter
print(len(rows), Counter(k for _, k in rows))
