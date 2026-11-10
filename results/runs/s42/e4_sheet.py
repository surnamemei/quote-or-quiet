"""S42 E4 blind sheet: every Verified sibling item, 60 random Verified control items, 20 decoys (answer swapped with another Verified
item of the same type) and the kept gold-wrong claims of E2 (a) and (c). Question and answer only; arms are not marked.
python -B results/runs/s42/e4_sheet.py"""
import csv, json, math, random, re
from pathlib import Path
D = Path(__file__).parent
X = [json.loads(l) for l in open(D / "e4_out.jsonl", encoding="utf-8")]
V = [x for x in X if x["state"] == "Verified"]
sib = [x for x in V if x["arm"] == "sibling"]; con = [x for x in V if x["arm"] == "control"]
rng = random.Random(4243)
rows = [(x, "sibling") for x in sib] + [(x, "control") for x in rng.sample(con, min(60, len(con)))]
for x in rng.sample(V, 20):
    pool = [y for y in V if y["type"] == x["type"] and y["subject"] != x["subject"] and y["answer"].casefold() not in x["answer"].casefold() and x["answer"].casefold() not in y["answer"].casefold()]
    if pool:
        rows.append(({**x, "answer": rng.choice(pool)["answer"]}, "decoy"))
for line in (D / "E2_claims.md").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^- (.+?) \| gold .+? \| claim (.+?) \| system released", line)
    if m:
        rows.append(({"id": "e2:" + m.group(1), "type": "e2", "question": m.group(1), "answer": m.group(2)}, "e2"))
rng.shuffle(rows)
k = max(1, math.ceil(len(rows) / 105)); size = math.ceil(len(rows) / k)
parts = [(str(p + 1), rows[p * size:(p + 1) * size]) for p in range(k)]
for p, sl in parts:
    with open(D / f"E4_sheet_part{p}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
        for n, (x, kind) in enumerate(sl, 1):
            w.writerow([n, x["question"], x["answer"], "", "", "", ""])
json.dump({p: [{"row": n, "kind": kind, "id": x["id"], "type": x["type"], "question": x["question"], "answer": x["answer"]} for n, (x, kind) in enumerate(sl, 1)]
           for p, sl in parts}, open(D / "E4_key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("verified sibling", len(sib), "control", len(con), "| rows", len(rows), "parts", [len(sl) for _, sl in parts])
