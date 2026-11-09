"""Combine two independent quote-checked adjudications: an error is removed only if BOTH adjudicators remove it
(gold wrong / both acceptable / matches gold). Otherwise the verdict kept is the stricter one (answer wrong > ambiguous > cannot tell).
usage: python -B adj_combine.py checkedA.csv checkedB.csv out.csv"""
import csv, sys
REM = ("gold wrong", "both acceptable", "matches gold")
ORDER = ("answer wrong", "ambiguous question", "cannot tell")
rd = lambda p: {int(r["row"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}
A, B = rd(sys.argv[1]), rd(sys.argv[2])
agree = tot = 0
with open(sys.argv[3], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["row", "verdict", "reason"])
    for r in sorted(A):
        va, vb = (A[r]["verdict"] or "cannot tell").strip().casefold(), (B[r]["verdict"] or "cannot tell").strip().casefold()
        if va in REM and vb in REM:
            v = va if va == vb else "both acceptable"
        else:
            cands = [x for x in (va, vb) if x not in REM]
            v = min(cands, key=lambda x: ORDER.index(x) if x in ORDER else 0)
        tot += 1; agree += (va == vb)
        w.writerow([r, v, f"A={va}; B={vb}"])
print("rows", tot, "identical verdicts", agree)
