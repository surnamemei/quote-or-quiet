"""Item 9 of docs/SEALED_SET_DESIGN.md: L1 at V2's coverage needs the agreement-score baseline at threshold t = 4 (edge share interpolation).
The L1 sheet reviewed baseline gold-wrong answers only at t >= 5. This sheet adds every baseline gold-wrong answer with score exactly 4 that has
not been judged in the L1 or V2 reviews, plus 10 injected-false decoys, question and answer only (same S36/S38 rubric).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s29_v2l1_sheet.py wd"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402
name = sys.argv[1]
D = ROOT / "results/runs/s29/run_fsm"; R = ROOT / "results/runs/s29/review" / name
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")
rows = {r["id"]: r for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
S = {r["id"]: r for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
K = json.load(open(R / "key.json", encoding="utf-8")); KV = json.load(open(R / "V2_key.json", encoding="utf-8"))
seen = {(k["id"], k["answer"].strip().casefold()) for lst in K["L1"].values() for k in lst if k["kind"] != "decoy"}
seen |= {(k["id"], k["answer"].strip().casefold()) for lst in KV.values() for k in lst if k["kind"] != "decoy"}
todo = []
for i, r in rows.items():
    c = r.get("combo_plain")
    if not ans(c):
        continue
    s_ = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(c), str(r[k]))) + int(bool(ans(phi.get(i))) and agree(str(c), str(phi.get(i))))
    if s_ == 4 and grade(r["question"], r["gold"], c) is False and (i, str(c).strip().casefold()) not in seen:
        todo.append({"id": i, "question": r["question"], "gold": r["gold"], "answer": str(c), "kind": "edge4_gold_wrong"})
rng = random.Random(2931)
ok = [{"id": i, "question": x["question"], "gold": x["gold"], "answer": x["answer"]} for i, x in S.items() if x["grade"] is True]
for x in rng.sample(ok, 10):
    other = rng.choice([y for y in ok if y["answer"].casefold() != x["answer"].casefold() and y["question"].split()[:3] == x["question"].split()[:3]] or
                       [y for y in ok if y["answer"].casefold() != x["answer"].casefold()])
    todo.append({**x, "answer": other["answer"], "kind": "decoy"})
rng.shuffle(todo)
with open(R / "E4_sheet.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
    for n_, x in enumerate(todo, 1):
        w.writerow([n_, x["question"], x["answer"], "", "", "", ""])
json.dump([{"row": n_, **x} for n_, x in enumerate(todo, 1)], open(R / "E4_key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("rows", len(todo), "edge4 gold-wrong unseen", sum(x["kind"] != "decoy" for x in todo))
