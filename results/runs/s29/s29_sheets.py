"""Blind review sheets for the S29 sealed run (rules pre-registered in docs/SEALED_SET_DESIGN.md and docs/CRITERIA_REVISION_L1.md).
L2 sheet (earlier protocol, gold shown): all gold-wrong system releases + 24 gold-correct system releases + 12 injected-false decoys.
L1 sheet (S36 protocol, gold hidden): gold-wrong releases of the system and of the agreement-score baseline (score >= t, shared answers once),
  30 gold-correct releases made only by each rule, 40 random gold-wrong answers of each standard baseline B0-B3, 15 decoys.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s29_sheets.py <wd|wdp>   (needs s29_score.py first; B0/B1 only if wd_closed.jsonl exists)"""
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
D = ROOT / "results/runs/s29/run_fsm"; OUT = ROOT / "results/runs/s29/review" / name; OUT.mkdir(parents=True, exist_ok=True)
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")
rows = {r["id"]: r for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
S = {r["id"]: r for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
rng = random.Random(2929)
def it(i, a, g, **k):
    r = rows[i]; return {"id": i, "relation": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(a), "grade": g, **k}
# baseline: agreement score, strictest t with releases >= system releases (edge interpolation done at analysis time)
sc = {}
for i, r in rows.items():
    c = r.get("combo_plain")
    if ans(c):
        sc[i] = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(c), str(r[k]))) + int(bool(ans(phi.get(i))) and agree(str(c), str(phi.get(i))))
t = next(t for t in range(6, -1, -1) if sum(1 for v in sc.values() if v >= t) >= len(S))
base = {i: it(i, rows[i]["combo_plain"], grade(rows[i]["question"], rows[i]["gold"], rows[i]["combo_plain"]), score=v) for i, v in sc.items() if v >= t}
meta = {"n": len(rows), "t": t, "sys_released": len(S), "base_n_top": sum(1 for v in sc.values() if v > t), "base_n_edge": sum(1 for v in sc.values() if v == t)}
# ---- L2 sheet
sw = [it(i, x["answer"], x["grade"]) for i, x in S.items() if x["grade"] is False]
sc_ok = [it(i, x["answer"], x["grade"]) for i, x in S.items() if x["grade"] is True]
l2 = [(x, "system_wrong") for x in sw] + [(x, "system_right") for x in rng.sample(sc_ok, min(24, len(sc_ok)))]
for x in rng.sample(sc_ok, min(12, len(sc_ok))):
    g = x["gold"][0]
    if g.isdigit():
        a = str(int(g) + rng.choice([-3, -2, -1, 1, 2, 3]))
    else:
        a = rng.choice([y["answer"] for y in sc_ok if y["relation"] == x["relation"] and y["answer"].casefold() != x["answer"].casefold()] or ["unknown"])
    l2.append(({**x, "answer": a, "grade": None}, "decoy"))
rng.shuffle(l2)
with open(OUT / "L2_sheet.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["row", "question", "gold", "answer", "verdict (gold wrong / answer wrong / both acceptable / ambiguous question / cannot tell)", "source_url", "verbatim_quote", "note"])
    for n_, (x, k) in enumerate(l2, 1):
        w.writerow([n_, x["question"], " | ".join(x["gold"]), x["answer"], "", "", "", ""])
# ---- L1 sheet
items = {}
def add(x, who):
    key = (x["id"], x["answer"].strip().casefold())
    e = items.setdefault(key, {**x, "who": set(), "kind": "gold_wrong"}); e["who"].add(who)
    if who == "base": e["score"] = x.get("score")
for x in sw: add(x, "sys")
for x in base.values():
    if x["grade"] is False: add(x, "base")
for (i, a), e in items.items():
    if i in S and S[i]["answer"].strip().casefold() == a: e["who"].add("sys")
    if i in base and base[i]["answer"].strip().casefold() == a: e["who"].add("base"); e["score"] = base[i]["score"]
l1 = [{**e, "who": sorted(e["who"])} for e in items.values()]
so = [it(i, x["answer"], True) for i, x in S.items() if x["grade"] is True and not (i in base and base[i]["answer"].strip().casefold() == x["answer"].strip().casefold())]
bo = [x for i, x in base.items() if x["grade"] is True and not (i in S and S[i]["answer"].strip().casefold() == x["answer"].strip().casefold())]
l1 += [{**x, "who": ["sys"], "kind": "gold_correct_sample"} for x in rng.sample(so, min(30, len(so)))]
l1 += [{**x, "who": ["base"], "kind": "gold_correct_sample"} for x in rng.sample(bo, min(30, len(bo)))]
std = {"B2": {i: r.get("combo_plain") for i, r in rows.items()}, "B3": {i: r.get("combo_cautious") for i, r in rows.items()}}
cl = D / f"{name}_closed.jsonl"
if cl.exists():
    C = {r["id"]: r for r in map(json.loads, open(cl, encoding="utf-8"))}
    std["B0"] = {i: C[i]["b0"] for i in rows if i in C}; std["B1"] = {i: C[i]["b1"] for i in rows if i in C}
for b, A in std.items():
    wrong = [it(i, a, False) for i, a in A.items() if ans(a) and grade(rows[i]["question"], rows[i]["gold"], a) is False]
    l1 += [{**x, "who": [b], "kind": "std_wrong_sample"} for x in rng.sample(wrong, min(40, len(wrong)))]
for x in rng.sample(sc_ok, min(15, len(sc_ok))):
    other = rng.choice([y for y in sc_ok if y["answer"].casefold() != x["answer"].casefold()])
    l1.append({**x, "answer": other["answer"], "grade": None, "who": [], "kind": "decoy"})
rng.shuffle(l1)
half = (len(l1) + 1) // 2
for p, sl in (("1", l1[:half]), ("2", l1[half:])):
    with open(OUT / f"L1_sheet_part{p}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
        for n_, x in enumerate(sl, 1):
            w.writerow([n_, x["question"], x["answer"], "", "", "", ""])
json.dump({"meta": meta, "L2": [{"row": n_, "kind": k, **x} for n_, (x, k) in enumerate(l2, 1)],
           "L1": {p: [{"row": n_, **x} for n_, x in enumerate(sl, 1)] for p, sl in (("1", l1[:half]), ("2", l1[half:]))}},
          open(OUT / "key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
from collections import Counter
print(meta, "L2 rows", len(l2), Counter(k for _, k in l2), "L1 rows", len(l1), Counter(x["kind"] for x in l1))
