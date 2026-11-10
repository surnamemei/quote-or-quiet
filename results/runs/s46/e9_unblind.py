"""Unblind S46 part B. misleading = both reviewers 'not' for the quote; false = both 'wrong' for the answer to the reading. Counts only in E9_result.md.
python -B results/runs/s46/e9_unblind.py"""
import csv, json, os, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s46"
K = json.load(open(D / "E9_key.json", encoding="utf-8")); items = {x["id"]: x for x in map(json.loads, open(D / "e9_items.jsonl", encoding="utf-8"))}
def up(k, n): return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
rows = []
for p, ks in K.items():
    V = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"E9_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append((r["quote_verdict"].strip().casefold(), r["true_verdict"].strip().casefold()))
    for k in ks:
        v = V[k["row"]]; q = [a for a, _ in v]; t = [b for _, b in v]
        rows.append({**k, "q": q, "t": t, "mis": q == ["not", "not"], "states": q == ["states", "states"], "false": t == ["wrong", "wrong"]})
rd = [r for r in rows if r["kind"] == "reading"]; dec = [r for r in rows if r["kind"] == "decoy"]
nd = sum(r["mis"] or r["false"] for r in dec)
def line(name, sel):
    n = len(sel); f = sum(r["false"] for r in sel); m = sum(r["mis"] for r in sel); s = sum(r["states"] for r in sel)
    return f"| {name} | {n} | {f} ({100*f/max(1,n):.1f}%, upper {up(f,n):.1f}%) | {m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {s} ({100*s/max(1,n):.1f}%) |"
out = ["# S46 part B: one answer per reading of an ambiguous name (rule W1 per reading page)", "",
       f"Decoys misleading or false for both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 18 else 'INVALID'}).", "",
       "| Rows | n | answer false for both | quote misleading for both | quote 'states' for both |", "|---|---|---|---|---|",
       line("All readings with a witness", rd), line("Film readings (director)", [r for r in rd if items[r["id"]]["relation"] == "director"]),
       line("Person readings (birth year)", [r for r in rd if items[r["id"]]["relation"] == "birth_year"])]
(D / "E9_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# E9 listing (not for release)", ""]
for r in rd:
    if r["mis"] or r["false"]:
        lst.append(f"- {r['q']} {r['t']} | {items[r['id']]['question']} | {r['reading']}")
(D / "E9_verdict_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
