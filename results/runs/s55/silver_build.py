"""S55: silver rows for distillation (docs/S55_DISTILLATION_PLAN.md). CPU. python -B results/runs/s55/silver_build.py"""
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s55"
gold_q = {r["question"] for r in map(json.loads, open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8"))}
m_sample = {k["id"] for ks in json.load(open(ROOT / "results/runs/s52/M_key.json")).values() for k in ks}
rng = random.Random(5501); out = []


def take(path, src, cap, skip_ids=()):
    rows = []
    for s in map(json.loads, open(path, encoding="utf-8")):
        if s["id"] in skip_ids or s["question"] in gold_q:
            continue
        cs = [c for c in s["cands"] if c.get("sent")][:15]
        for c in cs:
            rows.append({"src": src, "id": s["id"], "question": s["question"], "answer": s["answer"], "title": c.get("doc") or c.get("domain"), "quote": c["quote"]})
    rng.shuffle(rows); return rows[:cap]


out += take(ROOT / "results/runs/s52/m_cands.jsonl", "mintaka", 4000, m_sample)
out += take(ROOT / "results/runs/s48/a_cands.jsonl", "fresh5", 4000)
out += take(ROOT / "results/runs/s49/c_cands.jsonl", "web", 4000)
with open(D / "silver_rows.jsonl", "w", encoding="utf-8") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
print(len(out), Counter(r["src"] for r in out))
