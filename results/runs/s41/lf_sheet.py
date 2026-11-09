"""S41 blind sheet: every kept slot as (question, answer), 20 injected-false decoys (values swapped between kept slots of the same type,
different person) and 20 random dropped slots. Question and answer only. python -B results/runs/s41/lf_sheet.py"""
import csv, json, random
from pathlib import Path
D = Path(__file__).parent
X = [json.loads(l) for l in open(D / "verified.jsonl", encoding="utf-8")]
kept = [x for x in X if x["keep"]]
drop = [x for x in X if not x["keep"]]
rng = random.Random(4141)
rows = [(x, "kept") for x in kept] + [(x, "dropped") for x in rng.sample(drop, 20)]
for x in rng.sample(kept, 20):
    pool = [y for y in kept if y["type"] == x["type"] and y["person"] != x["person"] and y["value_clean"].casefold() != x["value_clean"].casefold()] or \
           [y for y in kept if y["person"] != x["person"] and y["value_clean"].casefold() != x["value_clean"].casefold()]
    rows.append(({**x, "value_clean": rng.choice(pool)["value_clean"]}, "decoy"))
rng.shuffle(rows)
half = (len(rows) + 1) // 2
parts = (("1", rows[:half]), ("2", rows[half:]))
for p, sl in parts:
    with open(D / f"S41_sheet_part{p}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
        for n, (x, k) in enumerate(sl, 1):
            w.writerow([n, x["question"], x["value_clean"], "", "", "", ""])
json.dump({p: [{"row": n, "kind": k, "id": x["id"], "person": x["person"], "type": x["type"], "question": x["question"], "answer": x["value_clean"]}
               for n, (x, k) in enumerate(sl, 1)] for p, sl in parts}, open(D / "S41_key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("kept", len(kept), "of", len(X), "| rows", len(rows), half, len(rows) - half)
