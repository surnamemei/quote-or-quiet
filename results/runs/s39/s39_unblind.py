"""Unblind S39 (docs/S39_PLAN.md). Pass rule per rule, fixed in the plan: at least 60 added, at most 3% wrong (both reviewers), one-sided 90% upper <= 5%.
Decoys valid if at least 18 of 20 are called wrong by both (as in S38). python -B results/runs/s39/s39_unblind.py"""
import csv, json
from pathlib import Path
from scipy.stats import beta
D = Path(__file__).parent
K = json.load(open(D / "S39_key.json", encoding="utf-8"))
rows = []
for p in ("1", "2"):
    V = {}
    for rv in ("A", "B"):
        for x in csv.DictReader(open(D / f"S39_verdict_part{p}_{rv}.csv", encoding="utf-8")):
            V.setdefault(int(x["row"]), []).append(x["verdict"].strip().strip("'\"").casefold())
    for k in K[p]:
        v = V[k["row"]]
        assert len(v) == 2, (p, k["row"])
        rows.append({**k, "v": v, "err": v == ["wrong", "wrong"], "either": "wrong" in v, "amb": "correct for one reading" in v})
dec = [r for r in rows if r["kind"] == "decoy"]
nd = sum(r["err"] for r in dec)
fs = [r for r in rows if r["kind"] == "frozen_sample"]
out = ["# S39: added releases judged against the facts", "", f"Decoys called wrong by both: {nd}/{len(dec)} ({'VALID' if nd >= 18 else 'INVALID'})",
       f"Random frozen releases called wrong by both: {sum(r['err'] for r in fs)}/{len(fs)}; by either: {sum(r['either'] for r in fs)}", "",
       "| rule | added | gold-wrong | truth-wrong (both) | rate | one-sided 90% upper | wrong by either | right for one reading | pass (>= 60, <= 3%, upper <= 5%) |",
       "|---|---|---|---|---|---|---|---|---|"]
A = [r for r in rows if r["kind"] == "added"]
res = {}
for var in ("indep", "V2", "V2b"):
    R = [r for r in A if var in r["rules"]]
    n = len(R); k = sum(r["err"] for r in R)
    up = beta.ppf(0.90, k + 1, n - k) if n else 1.0
    ok = n >= 60 and k / max(1, n) <= 0.03 and up <= 0.05
    res[var] = {"n": n, "k": k, "upper90": float(up), "pass": bool(ok)}
    out.append(f"| {var} | {n} | {sum(r['grade'] is False for r in R)} | {k} | {100*k/max(1,n):.1f}% | {100*up:.1f}% | {sum(r['either'] for r in R)} | {sum(r['amb'] for r in R)} | {'PASS' if ok else 'fail'} |")
out += ["", "Truth-relative errors (both reviewers):", ""] + [f"- [{','.join(r['rules'])}/{r['stratum']}] {r['question']} | ans {r['answer']} | gold {r['gold'][:2]}" for r in A if r["err"]]
out += ["", "Wrong by one reviewer only:", ""] + [f"- [{','.join(r['rules'])}] {r['question']} | ans {r['answer']} | gold {r['gold'][:2]} | {r['v']}" for r in A if r["either"] and not r["err"]]
out += ["", "Gold-wrong but judged correct by both:", ""] + [f"- [{','.join(r['rules'])}] {r['question']} | ans {r['answer']} | gold {r['gold'][:2]} | {r['v']}" for r in A if r["grade"] is False and not r["either"]]
(D / "S39_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
json.dump({"decoys": [nd, len(dec)], **res}, open(D / "S39_result.json", "w"), indent=1)
print("\n".join(out[:10]))
