"""Unblind the S29 V2 review (docs/SEALED_SET_DESIGN.md items 7-8 and the 2026-11-10 clarification).
python -B results/runs/s40/s40_v2_unblind.py wd"""
import csv, json, sys
from pathlib import Path
from scipy.stats import beta
D = Path(__file__).parent / "review" / sys.argv[1]
K = json.load(open(D / "V2_key.json", encoding="utf-8"))
rows = []
for p in ("1", "2"):
    V = {}
    for rv in ("A", "B"):
        for x in csv.DictReader(open(D / f"V2_verdict_part{p}_{rv}.csv", encoding="utf-8")):
            V.setdefault(int(x["row"]), []).append(x["verdict"].strip().casefold())
    for k in K[p]:
        v = V[k["row"]]
        rows.append({**k, "part": p, "v": v, "err": v == ["wrong", "wrong"], "either": "wrong" in v, "amb": "correct for one reading" in v})
dec = [r for r in rows if r["kind"] == "decoy"]
nd = sum(r["err"] for r in dec)
out = ["# S29 secondary test: two-source cell (V2) on the sealed set, judged against the facts", "",
       f"Decoys called wrong by both: {nd}/{len(dec)} ({'VALID' if nd >= 13 else 'INVALID'}; by either {sum(r['either'] for r in dec)})",
       f"Random frozen releases called wrong by both: {sum(r['err'] for r in rows if r['kind'] == 'frozen_sample')}/{sum(r['kind'] == 'frozen_sample' for r in rows)}", "",
       "| rule | added | gold-wrong | truth-wrong (both) | rate | one-sided 90% upper | wrong by either | right for one reading | pass (>= 40, <= 3%, upper <= 6%) |",
       "|---|---|---|---|---|---|---|---|---|"]
A = [r for r in rows if r["kind"] == "added"]
res = {}
for rule in ("V2", "V2b"):
    R = [r for r in A if rule in r["rules"]]
    n = len(R); k = sum(r["err"] for r in R)
    up = beta.ppf(0.90, k + 1, n - k) if n else 1.0
    ok = n >= 40 and k / n <= 0.03 and up <= 0.06
    res[rule] = {"n": n, "k": k, "upper90": float(up), "pass": bool(ok)}
    out.append(f"| {rule} | {n} | {sum(r['grade'] is False for r in R)} | {k} | {100*k/max(1,n):.1f}% | {100*up:.1f}% | {sum(r['either'] for r in R)} | {sum(r['amb'] for r in R)} | {'PASS' if ok else 'fail'} |")
out += ["", "Truth-relative errors among added (both reviewers):", ""] + \
       [f"- [{','.join(r['rules'])}/{r['relation']}] {r['question']} | ans {r['answer']} | gold {r['gold'][:2]} | gold-grade {r['grade']}" for r in A if r["err"]]
out += ["", "Wrong by one reviewer only:", ""] + [f"- [{','.join(r['rules'])}] {r['question']} | ans {r['answer']} | {r['v']}" for r in A if r["either"] and not r["err"]]
out += ["", "Gold-wrong but judged correct by both:", ""] + [f"- [{','.join(r['rules'])}] {r['question']} | ans {r['answer']} | gold {r['gold'][:2]} | {r['v']}" for r in A if r["grade"] is False and not r["either"]]
out += ["", "Decoys not caught by both:", ""] + [f"- {r['question']} | decoy ans {r['answer']} | gold {r['gold'][:2]} | {r['v']}" for r in dec if not r["err"]]
(D / "V2_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
json.dump({**res, "decoys_caught": nd, "n_decoys": len(dec), "err_ids": [r["id"] for r in A if r["err"]]}, open(D / "V2_result.json", "w"), indent=1)
print("\n".join(out))
