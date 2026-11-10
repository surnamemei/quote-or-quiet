"""Unblind S52 (rule R on Mintaka releases). misleading = both reviewers 'not' for the quote. Counts only in M_result.md; python -B results/runs/s52/a_unblind.py"""
import csv, json, os, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s52"
K = json.load(open(D / "M_key.json")); W = json.load(open(D / "m_witness.json"))
S = {s["id"]: s for s in map(json.loads, open(D / "m_cands.jsonl", encoding="utf-8"))}
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
V = {}
for p, ks in K.items():
    vs = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"M_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            vs.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().strip("'\"").casefold())
    for k in ks:
        V[(k["id"], k["kind"])] = vs[k["row"]]
dec = [v for (i, kd), v in V.items() if kd == "decoy"]
nd = sum(v == ["not", "not"] for v in dec)
ids = sorted({i for (i, kd) in V if kd == "frozen"})
def verdict_rule(i):                       # the quote that rule R shows for release i, and its verdicts (the frozen row when the witness is the same quote)
    k = W[i]
    if k is None: return None
    return V.get((i, "rule")) or V[(i, "frozen")]
fz = [V[(i, "frozen")] for i in ids]; rl = [verdict_rule(i) for i in ids if W[i] is not None]
fz_kept = [V[(i, "frozen")] for i in ids if W[i] is not None]
def row(name, vs):
    n = len(vs); m = sum(v == ["not", "not"] for v in vs); s = sum(v == ["states", "states"] for v in vs)
    return f"| {name} | {n} | {m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {s} ({100*s/max(1,n):.1f}%) |"
out = ["# S52 (rule R on Mintaka releases): relation-free witness rule R on the Mintaka test releases of the frozen system (quote-only blind review)", "",
       f"Decoys misleading for both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 0.9*len(dec) else 'INVALID'}).", "",
       "| Quotes | n | misleading for both | 'states' for both |", "|---|---|---|---|",
       row("Frozen display (first accepted span), 300 releases", fz), row("Frozen display, the releases that rule R keeps", fz_kept), row("Rule R witness, kept releases", rl),
       "", f"Rule R keeps {len(rl)} of the 300 sampled releases ({100*len(rl)/len(ids):.1f}%)."]
(D / "M_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# S52 listing (not for release)", ""]
for i in ids:
    if V[(i, "frozen")] == ["not", "not"] or (W[i] is not None and verdict_rule(i) == ["not", "not"]):
        lst.append(f"- {S[i]['question']} | {S[i]['answer']} | frozen {V[(i,'frozen')]} rule {verdict_rule(i)}")
(D / "M_verdict_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
