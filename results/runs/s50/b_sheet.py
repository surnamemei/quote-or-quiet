"""S50: sheet for the revised chain rule C2' (hop-2 judge ok and bridge ok; the chain-reader swap test cannot be satisfied by a 4B reader that knows the answer). 
Rows: every C2' chain, every chain rejected only by the bridge rule, 10 decoys (country swapped). python -B results/runs/s50/b_sheet.py"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s50"
I = json.load(open(D / "b_out.json", encoding="utf-8"))
c2 = [i for i in I if i.get("s2") and i.get("j2") and i.get("bridge_ok")]
br = [i for i in I if i.get("s2") and i.get("j2") and not i.get("bridge_ok")]
print("items", len(I), "| C2' accepted", len(c2), "| rejected only by the bridge rule", len(br), "| of which chain reader ok", sum(i.get("chain", False) for i in br))
rng = random.Random(5002)
rows = [dict(kind="accepted", i=i, a=i["country"]) for i in c2] + [dict(kind="bridge_rejected", i=i, a=i["country"]) for i in br]
for _ in range(10):
    i = rng.choice(c2); rows.append(dict(kind="decoy", i=i, a=rng.choice([x["country"] for x in c2 if x["country"].casefold() != i["country"].casefold()])))
rng.shuffle(rows)
with open(D / "B_sheet.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["row", "question", "answer", "page_1", "quote_1", "page_2", "quote_2"])
    for n, r in enumerate(rows, 1):
        i = r["i"]; w.writerow([n, f"In which country was {i['person']} born?", r["a"], i["wit"]["doc"], i["wit"]["quote"], i["place"], i["s2"]])
json.dump([{"row": n, "id": r["i"]["id"], "kind": r["kind"], "other_places": r["i"].get("other_places")} for n, r in enumerate(rows, 1)], open(D / "B_key.json", "w"))
print("sheet rows", len(rows))
