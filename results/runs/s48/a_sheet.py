"""S48 part A: apply rule R (docs/S48_RELATION_FREE_PLAN.md) and draw the quote-only blind sheet: for a random 300 releases the frozen display quote (first
accepted span) and, where it differs, the witness of rule R; plus 30 decoys (answer swapped with another release's). Writes A_sheet_part*.csv, A_key.json.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s48/a_sheet.py"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s48"
S = [json.loads(l) for l in open(D / "a_cands.jsonl", encoding="utf-8")]
OUT = json.load(open(D / "a_out.json", encoding="utf-8"))
yes = lambda o: str(o or "").strip().upper().startswith("YES")
ctrl = [0, 0]
for s in S:
    s["k"] = None; n = 0
    for k, c in enumerate(s["cands"]):
        key = f"{s['id']}|{k}"
        if key not in OUT:
            continue
        ctrl[0] += 1; ctrl[1] += yes(OUT[key][1])
        if s["k"] is None and yes(OUT[key][0]) and not yes(OUT[key][1]):
            s["k"] = k
kept = [s for s in S if s["k"] is not None]
print(f"releases {len(S)} | rule R keeps {len(kept)} ({100*len(kept)/len(S):.1f}%) | witness is the first accepted span {sum(s['k']==0 for s in kept)} | control: judge YES to swapped answer {ctrl[1]} of {ctrl[0]} ({100*ctrl[1]/max(1,ctrl[0]):.2f}%)")
json.dump({s["id"]: s["k"] for s in S}, open(D / "a_witness.json", "w"))
rng = random.Random(4802)
sample = rng.sample(S, 300); rows = []
for s in sample:
    rows.append(dict(kind="frozen", s=s, answer=s["answer"], quote=s["cands"][0]["quote"], doc=s["cands"][0]["doc"]))
    if s["k"] not in (None, 0) and s["cands"][s["k"]]["quote"] != s["cands"][0]["quote"]:
        c = s["cands"][s["k"]]; rows.append(dict(kind="rule", s=s, answer=s["answer"], quote=c["quote"], doc=c["doc"]))
for _ in range(30):
    s = rng.choice(sample); o = rng.choice([x for x in S if x["answer"].casefold() != s["answer"].casefold()])
    rows.append(dict(kind="decoy", s=s, answer=o["answer"], quote=s["cands"][0]["quote"], doc=s["cands"][0]["doc"]))
rng.shuffle(rows)
P = 3; key = {}
for p in range(P):
    part = rows[p::P]
    with open(D / f"A_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
        for i, r in enumerate(part, 1):
            w.writerow([i, r["s"]["question"], r["answer"], r["doc"], r["quote"]])
    key[str(p + 1)] = [{"row": i, "id": r["s"]["id"], "kind": r["kind"]} for i, r in enumerate(part, 1)]
json.dump(key, open(D / "A_key.json", "w"))
print("sheet rows", len(rows), [len(rows[p::P]) for p in range(P)])
