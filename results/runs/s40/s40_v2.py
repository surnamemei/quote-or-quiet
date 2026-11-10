"""S29 secondary test (docs/SEALED_SET_DESIGN.md items 7-9): two-source cell releases added beyond the frozen system on the sealed outputs.
V2  = registered wording: support 2 of 3, Phi-4 agrees, deductive gate passes, the missing source is the Wikipedia reader pair and both abstained.
V2b = the broader cell S38 actually reviewed (whichever source is missing, both its readers abstained); secondary.
Writes review/<set>/V2_added.jsonl and a blind sheet (question and answer only) with 15 injected-false decoys and 15 random frozen releases.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s40/s40_v2.py wd"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM; any use of vkg.retrieval2 raises)
from abstain_dev import grade                                  # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW   # noqa: E402
from vkg.s12_run import agree                                  # noqa: E402
from vkg.s14_eval import ans                                   # noqa: E402
name = sys.argv[1]
D = ROOT / "results/runs/s40/run_fsm"; OUT = ROOT / "results/runs/s40/review" / name; OUT.mkdir(parents=True, exist_ok=True)
NAMES = ("web", "wiki", "combo")
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
_rf = D / f"{name}_frozen_releases.jsonl"   # after s40_merge.py the releases file holds version 2; the cell is computed against the frozen rule
REL = {r["id"]: r for r in map(json.loads, open(_rf if _rf.exists() else D / f"{name}_releases.jsonl", encoding="utf-8"))}
added = []
for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8")):
    if r["id"] in REL:
        continue
    a, s = S.cand(r)
    if not ans(a) or s != 2:
        continue
    miss = [NAMES[i] for i, src in enumerate(S.SRCS) if not any(ans(r[k]) and agree(a, r[k]) for k in src)][0]
    if any(ans(r[k]) for k in S.SRCS[NAMES.index(miss)]):
        continue
    p = phi.get(r["id"])
    if not (ans(p) and agree(str(a), str(p))):
        continue
    if not C.release2(r["question"], a, r["wiki_titles"], LW.page_text)[0]:
        continue
    added.append({"id": r["id"], "relation": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(a), "miss": miss,
                  "rules": ["V2", "V2b"] if miss == "wiki" else ["V2b"], "grade": grade(r["question"], r["gold"], a)})
with open(OUT / "V2_added.jsonl", "w", encoding="utf-8") as f:
    for x in added:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
rng = random.Random(2930)
rows = [(x, "added") for x in added]
froz = [{"id": i, "relation": x.get("relation", ""), "question": x["question"], "gold": x["gold"], "answer": x["answer"], "grade": x["grade"], "rules": []}
        for i, x in REL.items()]
for x in rng.sample(froz, 15):
    rows.append((x, "frozen_sample"))
ok = [x for x in froz if x["grade"] is True]
for x in rng.sample(ok, 15):
    other = rng.choice([y for y in ok if y["answer"].casefold() != x["answer"].casefold() and y["question"].split()[:3] == x["question"].split()[:3]] or
                       [y for y in ok if y["answer"].casefold() != x["answer"].casefold()])
    rows.append(({**x, "answer": other["answer"], "grade": None}, "decoy"))
rng.shuffle(rows)
half = (len(rows) + 1) // 2
parts = (("1", rows[:half]), ("2", rows[half:]))
for p, sl in parts:
    with open(OUT / f"V2_sheet_part{p}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "verdict", "source_url", "verbatim_quote", "note"])
        for n_, (x, k) in enumerate(sl, 1):
            w.writerow([n_, x["question"], x["answer"], "", "", "", ""])
json.dump({p: [{"row": n_, "kind": k, **x} for n_, (x, k) in enumerate(sl, 1)] for p, sl in parts}, open(OUT / "V2_key.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("added V2", sum("V2" in x["rules"] for x in added), "V2b", len(added), "gold-wrong V2", sum(x["grade"] is False and "V2" in x["rules"] for x in added),
      "V2b", sum(x["grade"] is False for x in added), "sheet rows", len(rows))
