"""L2 decision on the S29 sealed set (pre-registered in docs/SEALED_SET_DESIGN.md, section "Pre-registration of the sealed run").
Primary endpoint: adjudicated system errors k_adj with the earlier protocol: two blind reviewers (gold shown), quote check on every removing verdict
(results/runs/s22/quote_check.py: the quote must occur in the fetched page, otherwise the verdict reverts to "cannot tell"), and an error is removed
only if both reviewers remove it (results/runs/s22/adj_combine.py rule). Validity: at least 11 of 12 decoys called "answer wrong" by both.
L2 holds if the corrected Clopper-Pearson one-sided 97.5% upper bound on k_adj over all questions is below 1% and coverage is at least 35%.
Prerequisites: review/<set>/L2_verdict_A.csv and L2_verdict_B.csv, already passed through quote_check.py into L2_checked_A.csv / L2_checked_B.csv.
python -B results/runs/s40/s40_l2.py <wd|wdp>"""
import csv, json, math, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
name = sys.argv[1]
R = ROOT / "results/runs/s40/review" / name
K = json.load(open(R / "key.json", encoding="utf-8")); meta = K["meta"]
REM = ("gold wrong", "both acceptable")
F = 0.0082
rd = lambda p: {int(r["row"]): (r.get("verdict") or "cannot tell").strip().casefold() for r in csv.DictReader(open(p, encoding="utf-8"))}
A, B = rd(R / "L2_checked_A.csv"), rd(R / "L2_checked_B.csv")
dec = [k for k in K["L2"] if k["kind"] == "decoy"]
dec_ok = sum(A[k["row"]] == "answer wrong" and B[k["row"]] == "answer wrong" for k in dec)
sw = [k for k in K["L2"] if k["kind"] == "system_wrong"]
removed = [k for k in sw if A[k["row"]] in REM and B[k["row"]] in REM]
kept = [k for k in sw if k not in removed]
n, rel = meta["n"], meta["sys_released"]
k_gold, k_adj = len(sw), len(kept)


def upper(k):
    e = math.ceil(k / (1 - F))
    return 100 * beta.ppf(0.975, e + 1, n - e)


cov = rel / n
ok = dec_ok >= len(dec) - 1 and upper(k_adj) < 1.0 and cov >= 0.35
right = [k for k in K["L2"] if k["kind"] == "system_right"]
out = [f"# S29 {name}: L2 decision", "",
       f"Decoys called 'answer wrong' by both reviewers: {dec_ok}/{len(dec)} ({'VALID' if dec_ok >= len(dec) - 1 else 'INVALID'})",
       f"Gold-matching releases called 'answer wrong' by both: {sum(A[k['row']] == 'answer wrong' and B[k['row']] == 'answer wrong' for k in right)}/{len(right)}", "",
       f"n = {n}, released {rel}, coverage {cov:.3f}",
       f"gold-relative errors {k_gold}: corrected upper bound {upper(k_gold):.2f}%",
       f"adjudicated errors k_adj {k_adj} (removed {len(removed)}): corrected upper bound {upper(k_adj):.2f}%", "",
       f"L2 on the sealed set: {'MET' if ok else 'NOT MET'}", "", "Kept errors:", ""]
out += [f"- [{k['relation']}] {k['question']} | gold {k['gold'][:2]} | ans {k['answer']} | A {A[k['row']]} | B {B[k['row']]}" for k in kept]
out += ["", "Removed errors:", ""] + [f"- [{k['relation']}] {k['question']} | gold {k['gold'][:2]} | ans {k['answer']} | A {A[k['row']]} | B {B[k['row']]}" for k in removed]
(R / "L2_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:12]))
