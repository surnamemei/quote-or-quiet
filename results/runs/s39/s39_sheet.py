"""S39 review (docs/S39_PLAN.md): every release added beyond the frozen system on the 1,200 design questions by
 - indep: independent title retrieval combined as in S23 (score_indep.combo, unchanged), and
 - cell: the two-source cell, V2 = registered wording (missing source is the wiki reader pair, both abstained), V2b = any missing source (secondary),
plus 30 random frozen releases and 20 injected-false decoys; blind sheet with question and answer only.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s39/s39_sheet.py"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s23"))
src = (ROOT / "results/runs/s23/score_indep.py").read_text(encoding="utf-8").split("\nlines = [")[0]     # functions only
G = {"__file__": str(ROOT / "results/runs/s23/score_indep.py"), "__name__": "si"}
exec(src, G)
releases, combo, grade = G["releases"], G["combo"], G["grade"]
S, C, LW, agree, ans = G["S"], G["C"], G["LW"], G["agree"], G["ans"]
D = ROOT / "results/runs/s39"; F = D / "run_fsm"; I = D / "indep"; N = "s39d"
NAMES = ("web", "wiki", "combo")
frozen = releases(F / f"{N}_outputs.jsonl", F / f"{N}_phi4.jsonl", False)
froz = {i: v for i, v in frozen.items() if v[1]}
s19f = releases(F / f"{N}_outputs.jsonl", F / f"{N}_phi4.jsonl", True)
fin = combo(s19f, releases(I / f"{N}_outputs.jsonl", I / f"{N}_phi4.jsonl", True))
added = {}
for i, (r, rel, src_) in fin.items():
    if i not in froz:
        added[(i, str(rel).strip().casefold())] = {"id": i, "stratum": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(rel),
                                                  "rules": ["indep"], "grade": grade(r["question"], r["gold"], rel)}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(F / f"{N}_phi4.jsonl", encoding="utf-8"))}
for r in map(json.loads, open(F / f"{N}_outputs.jsonl", encoding="utf-8")):
    if r["id"] in froz:
        continue
    a, s = S.cand(r)
    if not ans(a) or s != 2:
        continue
    miss = [NAMES[k] for k, sr in enumerate(S.SRCS) if not any(ans(r[x]) and agree(a, r[x]) for x in sr)][0]
    if any(ans(r[x]) for x in S.SRCS[NAMES.index(miss)]):
        continue
    p = phi.get(r["id"])
    if not (ans(p) and agree(str(a), str(p))):
        continue
    if not C.release2(r["question"], a, r["wiki_titles"], LW.page_text)[0]:
        continue
    k = (r["id"], str(a).strip().casefold())
    x = added.setdefault(k, {"id": r["id"], "stratum": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(a), "rules": [],
                             "grade": grade(r["question"], r["gold"], a)})
    x["rules"] += ["V2", "V2b"] if miss == "wiki" else ["V2b"]
added = list(added.values())
with open(D / "S39_added.jsonl", "w", encoding="utf-8") as f:
    for x in added:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
rng = random.Random(3939)
rows = [(x, "added") for x in added]
fl = [{"id": i, "stratum": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(rel), "rules": [], "grade": grade(r["question"], r["gold"], rel)}
      for i, (r, rel, _) in sorted(froz.items())]
for x in rng.sample(fl, 30):
    rows.append((x, "frozen_sample"))
ok = [x for x in fl if x["grade"] is True]
for x in rng.sample(ok, 20):
    other = rng.choice([y for y in ok if y["stratum"] == x["stratum"] and y["answer"].casefold() != x["answer"].casefold()
                        and y["question"].split()[:3] == x["question"].split()[:3]] or
                       [y for y in ok if y["stratum"] == x["stratum"] and y["answer"].casefold() != x["answer"].casefold()])
    rows.append(({**x, "answer": other["answer"], "grade": None, "rules": []}, "decoy"))
rng.shuffle(rows)
half = (len(rows) + 1) // 2
parts = (("1", rows[:half]), ("2", rows[half:]))
for p, sl in parts:
    with open(D / f"S39_sheet_part{p}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
        for n_, (x, k) in enumerate(sl, 1):
            w.writerow([n_, x["question"], x["answer"], "", "", "", ""])
json.dump({p: [{"row": n_, "kind": k, **x} for n_, (x, k) in enumerate(sl, 1)] for p, sl in parts}, open(D / "S39_key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
from collections import Counter
print("frozen releases", len(froz), "of", len(frozen), "| added", Counter(r for x in added for r in x["rules"]),
      "| gold-wrong", Counter(r for x in added if x["grade"] is False for r in x["rules"]), "| sheet rows", len(rows), half, len(rows) - half)
