"""S51 part D: compile the two-reviewer quote-sufficiency labels of S42 to S49 into one table (question, answer, page title, quote, labels). Local only: the table holds benchmark questions and
third-party text and is not part of the release. python -B results/runs/s51/d_build.py"""
import csv, glob, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
SRC = [("e6", "s42", "E6_sheet_part{p}.csv", "E6_verdict_part{p}_{r}.csv", "verdict", 4), ("e7", "s42", "E7_sheet_part{p}.csv", "E7_verdict_part{p}_{r}.csv", "verdict", 6),
       ("s43", "s43", "S43_sheet_part{p}.csv", "S43_verdict_part{p}_{r}.csv", "quote_verdict", 2), ("e11", "s43", "E11_sheet_part{p}.csv", "E11_verdict_part{p}_{r}.csv", "quote_verdict", 2),
       ("w4", "s44", "W4_sheet_part{p}.csv", "W4_verdict_part{p}_{r}.csv", "quote_verdict", 2), ("r4", "s45", "R4_sheet_part{p}.csv", "R4_verdict_part{p}_{r}.csv", "quote_verdict", 3),
       ("f5", "s47", "F5_sheet_part{p}.csv", "F5_verdict_part{p}_{r}.csv", "quote_verdict", 3), ("e9", "s46", "E9_sheet_part{p}.csv", "E9_verdict_part{p}_{r}.csv", "quote_verdict", 2),
       ("s48", "s48", "A_sheet_part{p}.csv", "A_verdict_part{p}_{r}.csv", "quote_verdict", 3), ("web", "s49", "C_sheet_part{p}.csv", "C_verdict_part{p}_{r}.csv", "quote_verdict", 3)]
rows = []
for name, d, sh, vd, col, P in SRC:
    for p in range(1, P + 1):
        S = {int(r["row"]): r for r in csv.DictReader(open(ROOT / "results/runs" / d / sh.format(p=p), encoding="utf-8-sig"))}
        V = {rv: {int(r["row"]): r[col].strip().strip("'\"").casefold() for r in csv.DictReader(open(ROOT / "results/runs" / d / vd.format(p=p, r=rv), encoding="utf-8-sig"))} for rv in "AB"}
        for n, r in S.items():
            if not r["quote"].strip():
                continue
            a, b = V["A"].get(n), V["B"].get(n)
            if a not in ("states", "incomplete", "not") or b not in ("states", "incomplete", "not"):
                continue
            ans = r.get("answer") or r.get("value")
            rows.append({"src": name, "question": r["question"], "answer": ans, "title": r["page_title"], "quote": r["quote"], "labels": [a, b], "label": a if a == b else None,
                         "group": hashlib.sha1(r["question"].encode("utf-8")).hexdigest()[:12]})
with open(ROOT / "data/quote_sufficiency/all.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
print("rows", len(rows), "| agreed", sum(r["label"] is not None for r in rows), Counter(r["label"] for r in rows))
print(Counter((r["src"]) for r in rows))
