"""Unblind the S29 pilot adjudication: join two blind verdict files with the key. python -B adj_unblind.py"""
import csv, json
from collections import Counter
from pathlib import Path
D = Path(__file__).parent
key = {k["row"]: k for k in json.load(open(D / "S29_pilot_key.json"))}
sheet = {int(r["row"]): r for r in csv.DictReader(open(D / "S29_pilot_sheet_blank.csv", encoding="utf-8"))}
def load(s):
    out = {}
    for r in csv.DictReader(open(D / f"verdict_{s}.csv", encoding="utf-8")):
        v = [x for k, x in r.items() if k.startswith("verdict")][0].strip().casefold()
        out[int(r["row"])] = (v, r.get("source_url", ""), r.get("verbatim_quote", ""), r.get("note", ""))
    return out
A, B = load("A"), load("B")
ACC = {"gold wrong", "both acceptable"}      # answer acceptable
lines = []
for kind in ("system_wrong", "system_right", "decoy_injected_false"):
    rows = [i for i, k in key.items() if k["kind"] == kind]
    ca, cb = Counter(A[i][0] for i in rows), Counter(B[i][0] for i in rows)
    both_wrong = sum(A[i][0] == "answer wrong" and B[i][0] == "answer wrong" for i in rows)
    either_wrong = sum("answer wrong" in (A[i][0], B[i][0]) for i in rows)
    agree = sum(A[i][0] == B[i][0] for i in rows)
    lines.append(f"{kind} n={len(rows)} | A {dict(ca)} | B {dict(cb)} | both 'answer wrong' {both_wrong} | either {either_wrong} | verdict agreement {agree}")
lines.append("")
for i in sorted(key):
    if key[i]["kind"] == "system_wrong" or (key[i]["kind"] == "system_right" and "answer wrong" in (A[i][0], B[i][0])):
        s = sheet[i]
        lines.append(f"[{key[i]['kind']}] row {i}: {s['question']} | gold {s['gold']} | ans {s['answer']} | A: {A[i][0]} ({A[i][3][:110]}) | B: {B[i][0]} ({B[i][3][:110]})")
print("\n".join(lines))
(D / "S29_pilot_adjudication.md").write_text("# S29 pilot blind adjudication (two agents, key withheld)\n\n" + "\n".join(lines), encoding="utf-8")
