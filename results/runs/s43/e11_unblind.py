"""Unblind S43 part C (E11) (docs/E11_LONGFORM_AND_AMBIGUITY_PLAN.md). Counts only in E11_result.md; per-item list in E11_verdict_listing.md (not for release).
misleading = both reviewers 'not' for the quote; false = both reviewers 'wrong' for the claim.
python -B results/runs/s43/e11_unblind.py"""
import csv, json, os, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s43"
S = {s["id"]: s for s in map(json.loads, open(D / "e11_cands.jsonl", encoding="utf-8"))}
K = json.load(open(D / "E11_key.json", encoding="utf-8"))


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0


rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for r in csv.DictReader(open(D / f"E11_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append((r["quote_verdict"].strip().strip("'\"").casefold(), r["true_verdict"].strip().strip("'\"").casefold()))
    for k in ks:
        v = V[k["row"]]; assert len(v) == 2, (p, k["row"])
        q = [a for a, _ in v]; t = [b for _, b in v]
        rows.append({**k, "q": q, "t": t, "mis": q == ["not", "not"], "states": q == ["states", "states"], "false": t == ["wrong", "wrong"], "f1": "wrong" in t})


def line(name, sel, quote=True):
    n = len(sel); f = sum(r["false"] for r in sel); m = sum(r["mis"] for r in sel); s = sum(r["states"] for r in sel)
    return (f"| {name} | {n} | {f} ({100*f/max(1,n):.1f}%, upper {up(f,n):.1f}%) | " +
            (f"{m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {s} ({100*s/max(1,n):.1f}%) |" if quote else "NA | NA |"))


kept = [r for r in rows if r["kind"] == "kept"]; drop = [r for r in rows if r["kind"] == "dropped"]; dec = [r for r in rows if r["kind"].startswith("decoy")]
nd = sum(r["mis"] or r["false"] for r in dec)
persons = {}
for r in kept:
    persons.setdefault(S[r["id"]]["person"], []).append(r["false"])
import random
rng = random.Random(7); boot = []
names = list(persons)
for _ in range(10000):
    ks = ns = 0
    for nme in (rng.choice(names) for _ in names):
        ks += sum(persons[nme]); ns += len(persons[nme])
    boot.append(ks / ns)
boot.sort()
out = ["# E11: sentence-level witnesses for long-form claims (50 design biographies)", "",
       f"Decoys misleading or false for both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 27 else 'INVALID'}).",
       f"Reviewers' agreement: quote verdict same in {sum(r['q'][0]==r['q'][1] for r in rows if r['kind']!='dropped')}/{len(rows)-len(drop)}; truth verdict same in {sum(r['t'][0]==r['t'][1] for r in rows)}/{len(rows)}.", "",
       "| Rows | n | False for both (claim) | Misleading for both (quote) | Quote 'states' for both |", "|---|---|---|---|---|",
       line("Kept slots", kept), line("Random dropped slots", drop, False), "",
       f"Kept slots false for either reviewer: {sum(r['f1'] for r in kept)}. Cluster-bootstrap (by biography) 97.5th percentile of the false share among kept: {100*boot[int(0.975*len(boot))]:.1f}%.",
       f"Kept slots: {len(kept)} of 1,492 ({100*len(kept)/1492:.1f}%); S41 kept 147 (9.9%)."]
(D / "E11_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# S43 per-item listing (not for release)", ""]
for title, sel in (("Kept, false for both", [r for r in kept if r["false"]]), ("Kept, misleading quote", [r for r in kept if r["mis"]]), ("Kept, false for one", [r for r in kept if r["f1"] and not r["false"]]),
                   ("Dropped, false for both", [r for r in drop if r["false"]])):
    lst += ["", f"## {title} ({len(sel)})", ""]
    for r in sel:
        s = S[r["id"]]; c = s["cands"][r["k"]]["quote"][:200] if r["k"] is not None else ""
        lst.append(f"- {r['q']} {r['t']} | {s['person']} | {s['question']} | {s['value']} | {c}")
(D / "E11_verdict_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
