"""Unblind an S22 blind web adjudication (sheet + key from combo_s21test.py). Verdicts must already be quote-checked
(quote_check.py). Validity: injected-false decoys must be called "answer wrong" in at least 95% of rows.
usage: python -B adj_unblind.py <set> <checked_verdicts.csv> [<raw_verdicts.csv>]"""
import csv, json, math, sys
from collections import Counter
from pathlib import Path
from scipy.stats import beta
D = Path(__file__).resolve().parent
N = sys.argv[1]
key = {d["row"]: d["kind"] for d in json.load(open(D / f"{N}_adj_key.json", encoding="utf-8"))}
sheet = {int(r["row"]): r for r in csv.DictReader(open(D / f"{N}_adj_sheet.csv", encoding="utf-8"))}
ver = {int(r["row"]): r for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))}
raw = {int(r["row"]): r for r in csv.DictReader(open(sys.argv[3], encoding="utf-8"))} if len(sys.argv) > 3 else {}
RUB = ("gold wrong", "answer wrong", "both acceptable", "matches gold", "ambiguous question", "cannot tell")
REM = ("gold wrong", "both acceptable", "matches gold")
KINDS = ("system", "decoy_baseline_wrong", "decoy_system_correct", "decoy_injected_false")
V = lambda r, src=ver: ((src.get(r, {}).get("verdict") or "cannot tell").strip().casefold())
by = {k: Counter() for k in KINDS}
byraw = {k: Counter() for k in KINDS}
for r, k in key.items():
    v = V(r); by[k][v if v in RUB else "INVALID"] += 1
    if raw:
        byraw[k][V(r, raw) if V(r, raw) in RUB else "INVALID"] += 1
L = [f"# S22 blind web adjudication on {N} (fresh agents, sheet only; quote-checked)", "",
     "| kind | n | " + " | ".join(RUB) + " | removed |", "|---|---|" + "---|" * (len(RUB) + 1)]
for k, c in by.items():
    n = sum(c.values()); rem = sum(c[x] for x in REM)
    L.append(f"| {k} | {n} | " + " | ".join(str(c[x]) for x in RUB) + f" | {rem} ({rem / max(n, 1):.2f}) |")
if raw:
    L += ["", "Before the quote check (removed per kind): " + ", ".join(
        f"{k} {byraw[k]['gold wrong'] + byraw[k]['both acceptable']}" for k in KINDS)]
inj = by["decoy_injected_false"]; ni = sum(inj.values()); vi = inj["answer wrong"] / max(ni, 1)
L += ["", f"Validity (injected-false called answer wrong): {inj['answer wrong']} / {ni} = {vi:.3f} -> {'VALID' if vi >= 0.95 else 'VOID (falls back to gold-relative k)'}"]
s = by["system"]; ks = sum(s.values()) - sum(s[x] for x in REM)
L += [f"System errors kept after adjudication: k_adj = {ks} of {sum(s.values())}"]
L += ["", "## System rows", ""] + [f"- r{r} {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | **{V(r)}**"
      + (f" (raw: {V(r, raw)})" if raw and V(r, raw) != V(r) else "") + f" | {ver.get(r, {}).get('reason', '')}"
      for r, k in sorted(key.items()) if k == "system"]
L += ["", "## Injected-false not called answer wrong", ""] + [f"- r{r} {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | {V(r)} | {ver.get(r, {}).get('reason', '')}"
      for r, k in sorted(key.items()) if k == "decoy_injected_false" and V(r) != "answer wrong"]
L += ["", "## System-correct called answer wrong", ""] + [f"- r{r} {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | {ver.get(r, {}).get('reason', '')}"
      for r, k in sorted(key.items()) if k == "decoy_system_correct" and V(r) == "answer wrong"]
L += ["", "## Baseline-wrong removed", ""] + [f"- r{r} {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | {V(r)} | {ver.get(r, {}).get('reason', '')}"
      for r, k in sorted(key.items()) if k == "decoy_baseline_wrong" and V(r) in REM]
(D / f"{N}_adj_result.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L[:20]))
