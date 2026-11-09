"""Derivation-certificate census (design data: closed S21 Mintaka sets). For numerical-answer questions: question type, whether
gold occurs verbatim in the pinned pages, whether the S22 combination rule already releases it, time-sensitivity.
usage: python -B census.py mintaka_test"""
import json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from ceiling_dev import present, qtype                               # noqa: E402
from temporal import time_sensitive                                  # noqa: E402
N = sys.argv[1]
items = json.load(open(ROOT / f"results/runs/s21/{N}.json", encoding="utf-8"))
pin = {r["id"]: r for r in map(json.loads, open(ROOT / f"results/runs/s22/pin/{N}_outputs.jsonl", encoding="utf-8"))}
rel = {r["id"]: r for r in map(json.loads, open(ROOT / f"results/runs/s22/{N}_releases.jsonl", encoding="utf-8"))} if (ROOT / f"results/runs/s22/{N}_releases.jsonl").exists() else {}
c = Counter(); rows = []
for e in items:
    if e["meta"].get("answerType") != "numerical":
        continue
    t = qtype(e["question"]); ts = time_sensitive(e["question"])
    pres = present(e["gold"], pin[e["id"]]["wiki_titles"])
    c[(t, "time" if ts else "stable", "gold on page" if pres else "gold NOT on page", "released" if e["id"] in rel else "unreleased")] += 1
    rows.append({"id": e["id"], "q": e["question"], "gold": e["gold"], "type": t, "time": ts, "present": pres, "released": e["id"] in rel})
for k, v in sorted(c.items()): print(v, k)
json.dump(rows, open(f"census_{N}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
