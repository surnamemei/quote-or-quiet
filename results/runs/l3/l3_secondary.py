"""L3 secondary endpoint S1-S3 on S22 release files (read-only on results/runs/s22).
usage: python -B results/runs/l3/l3_secondary.py <set>   (e.g. mintaka_test; dry run on the closed S21 set)"""
import csv, json, math, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3"))
from qualified import decide
from scipy.stats import beta
FUP = 0.0082
name = sys.argv[1]
rels = [json.loads(l) for l in open(ROOT / f"results/runs/s22/{name}_releases.jsonl", encoding="utf-8")]
adj = {}
vp, kp = ROOT / f"results/runs/s22/{name}_adj_checked.csv", ROOT / f"results/runs/s22/{name}_adj_key.json"
if vp.exists() and kp.exists():
    key = {k["row"]: k for k in json.load(open(kp, encoding="utf-8")) if k["kind"] == "system"}
    for r in csv.DictReader(open(vp, encoding="utf-8")):
        k = key.get(int(r["row"]))
        if k:
            adj[k["id"]] = r["verdict"]
REMOVE = {"gold wrong", "both acceptable"}
tab = Counter(); detail = []
for r in rels:
    st, sense, info = decide(r["question"], r["answer"], r["release_doc"], strict=True)
    g = r["grade"]
    wrong = g is not True                     # False and "?" both count as errors (conservative)
    removed = wrong and adj.get(r["id"]) in REMOVE
    tab[(st, "ok" if not wrong else ("removed" if removed else "err"))] += 1
    if st != "Verified" or (wrong and not removed):
        detail.append({"id": r["id"], "q": r["question"], "ans": r["answer"], "state": st, "sense": sense, "grade": g, "adj": adj.get(r["id"])})
N = len(rels)
def bound(k, n):
    E = math.ceil(k / (1 - FUP)); return E, (beta.ppf(0.975, E + 1, n - E) if E < n else 1.0)
out = [f"# L3 secondary endpoint, {name} (n releases = {N}; adjudication {'applied' if adj else 'absent'})", "",
       "| state | correct | error (after adjudication) | adjudication-removed |", "|---|---|---|---|"]
for st in ("Verified", "Qualified", "Unresolved"):
    out.append(f"| {st} | {tab[(st,'ok')]} | {tab[(st,'err')]} | {tab[(st,'removed')]} |")
vr = tab[("Verified", "ok")] + tab[("Verified", "err")] + tab[("Verified", "removed")]
qr = sum(tab[("Qualified", x)] for x in ("ok", "err", "removed"))
kS1 = tab[("Verified", "err")] + tab[("Qualified", "err")]; kS2 = tab[("Verified", "err")]
nS1 = vr + qr
out += ["", f"Qualified share of released: {qr/max(1,vr+qr+tab[('Unresolved','ok')]+tab[('Unresolved','err')]+tab[('Unresolved','removed')]):.3f}",
        f"S1 (Verified+Qualified): k={kS1}, n={nS1}, E,upper = {bound(kS1, nS1)}",
        f"S2 (Verified only): k={kS2}, n={vr}, E,upper = {bound(kS2, vr)}",
        f"Completion lost to Unresolved (graded correct): {tab[('Unresolved','ok')]}", "", "## non-Verified or erroneous"]
out += [json.dumps(d, ensure_ascii=False) for d in detail]
Path(ROOT / f"results/runs/l3/secondary_{name}.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out[:16]))
