"""S46 part B: apply W1 (frame check F, subject link S, quote-only reader G) to every reading and draw the blind sheet:
every reading with a witness, plus 20 decoys (answer swapped for another reading's answer of the same relation). Writes E9_sheet_part*.csv, E9_key.json.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s46/e9_sheet.py"""
import csv, json, os, random, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from vkg.s12_run import agree     # noqa: E402
from vkg.s14_eval import ans      # noqa: E402
D = ROOT / "results/runs/s46"
items = {x["id"]: x for x in map(json.loads, open(D / "e9_items.jsonl", encoding="utf-8"))}
res = json.load(open(D / "e9_out.json", encoding="utf-8"))


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


for r in res:
    r["k"] = None
    for k, c in enumerate(r["cands"]):
        g = said(c["out"][0])
        if c["F"] and c["S"] and g and agree(r["answer"], g):
            r["k"] = k; break
json.dump(res, open(D / "e9_witness.json", "w", encoding="utf-8"), ensure_ascii=False)
tot = Counter(); 
for x in items.values():
    rs = [r for r in res if r["id"] == x["id"]]
    tot[x["relation"] + "_readings"] += len(rs); tot[x["relation"] + "_answered"] += sum(bool(r["answer"]) for r in rs)
    tot[x["relation"] + "_witness"] += sum(r["k"] is not None for r in rs)
    w = [r for r in rs if r["k"] is not None]
    tot[x["relation"] + "_items_with_2plus_witness"] += len(w) >= 2
    tot[x["relation"] + "_items_with_distinct_answers"] += len({r["answer"].casefold() for r in w}) >= 2
    tot[x["relation"] + "_items"] += 1
print(dict(tot))
W = [r for r in res if r["k"] is not None]
rng = random.Random(4603)
rows = [dict(kind="reading", r=r, q=r["question"], a=r["answer"]) for r in W]
for _ in range(20):
    r = rng.choice(W); rel = items[r["id"]]["relation"]
    pool = [y["answer"] for y in W if items[y["id"]]["relation"] == rel and not agree(y["answer"], r["answer"])]
    rows.append(dict(kind="decoy", r=r, q=r["question"], a=rng.choice(pool)))
rng.shuffle(rows)
P = 2; key = {}
for p in range(P):
    part = rows[p::P]
    with open(D / f"E9_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
        for i, x in enumerate(part, 1):
            w.writerow([i, x["q"], x["a"], x["r"]["reading"], x["r"]["cands"][x["r"]["k"]]["quote"]])
    key[str(p + 1)] = [{"row": i, "id": x["r"]["id"], "reading": x["r"]["reading"], "kind": x["kind"]} for i, x in enumerate(part, 1)]
json.dump(key, open(D / "E9_key.json", "w", encoding="utf-8"))
print("sheet rows", len(rows), [len(rows[p::P]) for p in range(P)])
