"""E7 dev: share of dev Verified items that keep a witness under the candidate rule F and S and G (first passing span in page order)."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(Path(__file__).parent))
import no_retrieval2  # noqa
from vkg.s12_run import agree
from vkg.s14_eval import ans
import e7_lib as L
D = ROOT / "results/runs/s42"
X = {x["id"]: x for x in map(json.loads, open(D / "e6_items.jsonl", encoding="utf-8"))}
CD = {c["id"]: c["cands"] for c in map(json.loads, open(D / "e7_cands.jsonl", encoding="utf-8"))}
OUT = json.load(open(D / "e7_dev_out.json", encoding="utf-8"))
K = json.load(open(D / "E6_key.json", encoding="utf-8"))
ids = {k["id"] for ks in K.values() for k in ks if k["kind"] == "verified"}
def said(o):
    o = str(o or "").strip().strip("'\"."); return o if ans(o) and not o.upper().startswith("NONE") else None
n = first = anyw = moved = 0
for i in ids:
    x = X[i]; n += 1; got = None
    for k in range(len(CD[i])):
        key = f"{i}|{k}"
        if key not in OUT: continue
        c = CD[i][k]; a = said(OUT[key][0])
        if c["F"] and L.subject_link(x["question"], c["doc"], c["quote"]) and a and agree(x["answer"], a):
            got = k; break
    first += got == 0; anyw += got is not None; moved += bool(got)
print(f"dev Verified {n}: witness is the first span {first} ({100*first/n:.1f}%); a later span {moved}; any witness {anyw} ({100*anyw/n:.1f}%)")
