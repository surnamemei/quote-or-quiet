"""Unblind S42 E7 (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 9, rule W1). misleading = both reviewers 'not'.
Writes E7_result.md (counts only) and E7_verdict_listing.md (per-item, stays out of the release).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e7_unblind.py"""
import csv, json, os, sys
from collections import Counter
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s42"
X = {x["id"]: x for x in map(json.loads, open(D / "e6_items.jsonl", encoding="utf-8"))}
CD = {c["id"]: c["cands"] for c in map(json.loads, open(D / "e7_cands.jsonl", encoding="utf-8"))}
K = json.load(open(D / "E7_key.json", encoding="utf-8"))


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0


rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for r in csv.DictReader(open(D / f"E7_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            v = r["verdict"].strip().strip("'\"").casefold()
            assert v in ("states", "incomplete", "not"), (p, rv, r["row"], v)
            V.setdefault(int(r["row"]), []).append(v)
    for k in ks:
        v = V[k["row"]]; assert len(v) == 2, (p, k["row"])
        rows.append({**k, "v": v, "mis": v == ["not", "not"], "states": v == ["states", "states"], "either": "not" in v})


def line(name, sel):
    n = len(sel); m = sum(r["mis"] for r in sel); s = sum(r["states"] for r in sel)
    return f"| {name} | {n} | {m} | {100*m/max(1,n):.2f}% | {up(m,n):.2f}% | {s} ({100*s/max(1,n):.1f}%) | {sum(r['either'] for r in sel)} |"


ver = [r for r in rows if r["kind"] == "verified"]; qua = [r for r in rows if r["kind"] == "qualified"]
dec = [r for r in rows if r["kind"].startswith("decoy")]; nd = sum(r["mis"] for r in dec)
out = ["# S42 E7: witness selection, blind test (rule W1: F and S and G, first passing span)", "",
       f"Decoys misleading for both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 0.9 * len(dec) else 'INVALID'}).",
       f"Reviewers gave the same verdict in {sum(r['v'][0]==r['v'][1] for r in rows)}/{len(rows)} rows.", "",
       "| Rows | n | Misleading (both 'not') | Rate | 97.5% upper | States for both | 'not' for either |", "|---|---|---|---|---|---|---|",
       line("Verified witnesses", ver), line("  witness is the first span", [r for r in ver if r["k"] == 0]),
       line("  witness is a later span", [r for r in ver if r["k"] > 0]), line("Qualified witnesses (sample)", qua), "",
       "Verified witnesses by relation:", "", "| Relation | n | Misleading | Rate | 97.5% upper | States for both | 'not' for either |", "|---|---|---|---|---|---|---|"]
out += [line(rel, [r for r in ver if X[r["id"]]["relation"] == rel]) for rel in sorted({X[r["id"]]["relation"] for r in ver})]
nv = len(ver)
out += ["", f"Verified test items with a witness: {nv} of 1,090 ({100*nv/1090:.1f}%).",
        f"Coverage estimate on the S29 population: 1,765 Verified x {nv/1090:.3f} for the test share = {1765*nv/1090:.0f} releases ({100*1765*nv/1090/3359:.1f}% of 3,359 questions); dev Verified witness share was 93.2%."]
(D / "E7_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# E7 per-item listing (not for release)", ""]
for title, sel in (("Verified, misleading", [r for r in ver if r["mis"]]), ("Verified, split with one 'not'", [r for r in ver if r["either"] and not r["mis"]]),
                   ("Qualified, misleading", [r for r in qua if r["mis"]]), ("Decoys not caught", [r for r in dec if not r["mis"]])):
    lst += ["", f"## {title} ({len(sel)})", ""]
    for r in sel:
        c = CD[r["id"]][r["k"]]; x = X[r["id"]]
        lst.append(f"- {r['v']} | k {r['k']} | {x['question']} | {x['answer']} | {c['doc']}: {c['quote'][:200]}")
(D / "E7_verdict_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
